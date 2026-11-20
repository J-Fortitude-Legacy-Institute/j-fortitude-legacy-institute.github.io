"""
vendor_browser.py — Generic vendor login via Playwright, per-service profile.

Called by unk_companion.cap_vendor_login. Fetches decrypted credentials from the
vendor-vault edge function using the device's own credentials, then attempts a
best-effort sign-in on the vendor's site. On success, the session cookie
persists in a per-service browser profile so subsequent vendor_action calls
don't need to re-authenticate.

Heuristics (deliberately generic — no per-vendor code):
  1. Navigate to service_url.
  2. Try filling any visible input matching email/username patterns.
  3. Click a submit-looking button.
  4. If a password field appears (single- or two-step flow), fill and submit.
  5. Detect success by URL change away from /signin|/login and absence of the
     password field.
  6. Detect 2FA by presence of otp/2fa/verify fields — pause and report.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


CONFIG_DIR = Path.home() / ".unk_companion"
VENDOR_PROFILES_DIR = CONFIG_DIR / "vendor_profiles"
VENDOR_SCREENSHOTS_DIR = CONFIG_DIR / "vendor_screenshots"


def _slugify(s: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in (s or "").lower())[:64] or "unknown"


def _ensure_playwright() -> tuple[bool, Optional[str]]:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "playwright"], timeout=180)
            from playwright.sync_api import sync_playwright  # noqa: F401
        except Exception as e:
            return False, f"playwright_install_failed:{e}"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            chromium_path = Path(p.chromium.executable_path)
            if chromium_path.exists():
                return True, None
    except Exception:
        pass
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], timeout=600)
        return True, None
    except Exception as e:
        return False, f"chromium_install_failed:{e}"


EMAIL_SELECTORS = [
    "input[type='email']",
    "input[name='email']",
    "input[name='username']",
    "input[name='userName']",
    "input[name='user']",
    "input[id*='email' i]",
    "input[id*='username' i]",
    "input[autocomplete='username']",
]
PASSWORD_SELECTORS = [
    "input[type='password']:not([aria-hidden='true'])",
    "input[name='password']",
    "input[id*='password' i]",
    "input[autocomplete='current-password']",
]
OTP_SELECTORS = [
    "input[name*='otp' i]",
    "input[name*='code' i]",
    "input[id*='otp' i]",
    "input[id*='verify' i]",
    "input[autocomplete='one-time-code']",
]
SUBMIT_SELECTORS = [
    "button[type='submit']",
    "button:has-text('Sign in')",
    "button:has-text('Sign In')",
    "button:has-text('Log in')",
    "button:has-text('Log In')",
    "button:has-text('Continue')",
    "button:has-text('Next')",
    "input[type='submit']",
]


def _try_fill(page, selectors: list[str], value: str) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.fill(value, timeout=3000)
                return True
        except Exception:
            continue
    return False


def _try_click(page, selectors: list[str]) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=3000)
                return True
        except Exception:
            continue
    return False


def _detect_2fa(page) -> bool:
    for sel in OTP_SELECTORS:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                return True
        except Exception:
            continue
    return False


def _still_on_login(page) -> bool:
    url = (page.url or "").lower()
    if any(marker in url for marker in ("signin", "login", "sign-in", "log-in", "auth")):
        # Also require that a password field is still visible — some sites redirect
        # to a /login URL then show a success banner without the form.
        for sel in PASSWORD_SELECTORS:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    return True
            except Exception:
                continue
    return False


def login(*, credential: dict, fetch_email_code=None, report_event=None) -> dict:
    """Attempt to sign in with the given decrypted credential dict.

    credential keys: id, service_name, service_url, account_email,
    account_username, password, totp_secret, has_2fa, notes.

    fetch_email_code(service_hint, sender_hint=None, subject_hint=None) -> dict
        Optional callback that returns {ok, code, event_id, ...} when the site
        challenges with an email verification code. If omitted, the login pauses
        on 2FA and returns needs_2fa (previous behavior).
    report_event(event_id, status, escalation_reason=None, screenshot_path=None)
        Optional callback to update the email_verification_events audit row.
    """

    ready, err = _ensure_playwright()
    if not ready:
        return {"ok": False, "error": err or "playwright_not_ready"}

    from playwright.sync_api import sync_playwright  # type: ignore

    slug = _slugify(credential.get("service_name") or "")
    profile_dir = VENDOR_PROFILES_DIR / slug
    profile_dir.mkdir(parents=True, exist_ok=True)
    VENDOR_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    shot_path = VENDOR_SCREENSHOTS_DIR / f"{slug}_{int(time.time())}.png"

    identifier = credential.get("account_email") or credential.get("account_username") or ""
    password = credential.get("password") or ""
    service_url = credential.get("service_url") or ""
    if not identifier or not password or not service_url:
        return {"ok": False, "error": "missing_credential_fields"}

    notes: list[str] = []
    result: dict = {
        "ok": False,
        "status": "failed",
        "notes": notes,
        "profile_dir": str(profile_dir),
        "screenshot_path": None,
    }

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=False,
                args=_win_browser_args(["--no-sandbox", "--disable-blink-features=AutomationControlled"]),
                viewport={"width": 1280, "height": 900},
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(service_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(1.5)

            # Step 1: fill identifier
            filled_id = _try_fill(page, EMAIL_SELECTORS, identifier)
            if not filled_id:
                notes.append("identifier_field_not_found")
                page.screenshot(path=str(shot_path))
                result["screenshot_path"] = str(shot_path)
                result["error"] = "identifier_field_not_found"
                context.close()
                return result

            # Step 2: try to reveal password if two-step
            _try_click(page, SUBMIT_SELECTORS)
            time.sleep(2.0)

            # Step 3: fill password
            filled_pw = _try_fill(page, PASSWORD_SELECTORS, password)
            if not filled_pw:
                # single-page login: identifier + password might be visible from the start.
                _try_fill(page, PASSWORD_SELECTORS, password)

            _try_click(page, SUBMIT_SELECTORS)
            time.sleep(3.5)

            # Step 4: 2FA?
            if _detect_2fa(page):
                notes.append("otp_field_detected")
                service_hint = (credential.get("service_name") or slug or "").lower()
                # Try email-based verification code (Unk's email 2FA capability)
                email_event_id = None
                if fetch_email_code is not None:
                    deadline = time.time() + 75  # wait up to 75s for the email to arrive
                    fetched = None
                    while time.time() < deadline:
                        fetched = fetch_email_code(service_hint=service_hint) or {}
                        if fetched.get("ok") and fetched.get("code"):
                            break
                        time.sleep(6.0)
                    email_event_id = (fetched or {}).get("event_id")
                    if fetched and fetched.get("ok") and fetched.get("code"):
                        code = str(fetched["code"])
                        entered = _try_fill(page, OTP_SELECTORS, code)
                        if entered:
                            _try_click(page, SUBMIT_SELECTORS)
                            time.sleep(3.5)
                            page.screenshot(path=str(shot_path))
                            result["screenshot_path"] = str(shot_path)
                            if _still_on_login(page) or _detect_2fa(page):
                                notes.append("email_code_entered_but_challenge_persists")
                                result["status"] = "needs_human"
                                result["error"] = "human_verification_required"
                                result["email_event_id"] = email_event_id
                                if report_event and email_event_id:
                                    report_event(email_event_id, "escalated",
                                                 escalation_reason="challenge_persists_after_code",
                                                 screenshot_path=str(shot_path))
                                context.close()
                                return result
                            # success
                            notes.append("email_code_accepted")
                            result["ok"] = True
                            result["status"] = "ok"
                            result["final_url"] = page.url
                            result["email_event_id"] = email_event_id
                            if report_event and email_event_id:
                                report_event(email_event_id, "entered",
                                             screenshot_path=str(shot_path))
                            context.close()
                            return result
                        # fill failed
                        notes.append("otp_input_fill_failed")
                        page.screenshot(path=str(shot_path))
                        result["screenshot_path"] = str(shot_path)
                        result["status"] = "entry_failed"
                        result["error"] = "otp_fill_failed"
                        result["email_event_id"] = email_event_id
                        if report_event and email_event_id:
                            report_event(email_event_id, "entry_failed",
                                         escalation_reason="otp_fill_failed",
                                         screenshot_path=str(shot_path))
                        context.close()
                        return result

                # No email code available — pause and escalate to Jason.
                page.screenshot(path=str(shot_path))
                result["screenshot_path"] = str(shot_path)
                result["status"] = "needs_human"
                result["error"] = "human_verification_required"
                result["email_event_id"] = email_event_id
                notes.append("no_email_code_or_challenge_not_email")
                if credential.get("totp_secret"):
                    notes.append("totp_secret_available_but_auto_2fa_not_yet_implemented")
                if report_event and email_event_id:
                    report_event(email_event_id, "escalated",
                                 escalation_reason="no_email_code_available",
                                 screenshot_path=str(shot_path))
                context.close()
                return result


            # Step 5: still on login?
            time.sleep(1.5)
            if _still_on_login(page):
                page.screenshot(path=str(shot_path))
                result["screenshot_path"] = str(shot_path)
                result["status"] = "failed"
                result["error"] = "login_did_not_complete"
                notes.append(f"final_url:{page.url}")
                context.close()
                return result

            page.screenshot(path=str(shot_path))
            result["screenshot_path"] = str(shot_path)
            result["ok"] = True
            result["status"] = "ok"
            result["final_url"] = page.url
            notes.append(f"session_persisted_to:{profile_dir}")
            context.close()
            return result
    except Exception as e:
        result["error"] = f"exception:{e}"
        return result
