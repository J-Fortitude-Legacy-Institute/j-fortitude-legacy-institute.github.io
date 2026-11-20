"""Meta App Dashboard configurator.

Opens developers.facebook.com in the persistent Unk browser profile and
configures the Facebook Login for Business "Settings" page for a given app_id:
  * Client OAuth Login = ON
  * Web OAuth Login = ON
  * Valid OAuth Redirect URIs contains https://www.facebook.com/connect/blank.html
Then clicks Save Changes.

If the persistent profile is not signed into developers.facebook.com, returns
with an actionable error and a screenshot. This capability is idempotent —
if the toggles are already ON and the redirect URI already present, it just
saves (or skips save) and reports ok.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from meta_browser_configurator import (

    PROFILE_DIR,
    _safe_goto,
    _screenshot,
)
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])

DEFAULT_REDIRECT_URI = "https://www.facebook.com/connect/blank.html"


def _try_toggle_switch_on(page, label_text: str, notes: list[str]) -> bool:
    """Find a switch adjacent to `label_text` and ensure it is ON. Returns True if ON after."""
    try:
        # Locate a text element containing the label, then find nearest switch
        locators = [
            f"xpath=//*[normalize-space(text())='{label_text}']/ancestor::*[.//div[@role='switch']][1]//div[@role='switch']",
            f"xpath=//*[contains(normalize-space(.), '{label_text}')]/ancestor::*[.//div[@role='switch']][1]//div[@role='switch']",
            f"xpath=(//div[@role='switch'])[1]",
        ]
        for sel in locators:
            try:
                loc = page.locator(sel).first
                if loc.count() == 0:
                    continue
                loc.scroll_into_view_if_needed(timeout=2000)
                checked = loc.get_attribute("aria-checked")
                notes.append(f"switch_{label_text}_before:{checked}")
                if checked == "true":
                    return True
                loc.click(timeout=3000)
                time.sleep(1.2)
                checked_after = loc.get_attribute("aria-checked")
                notes.append(f"switch_{label_text}_after:{checked_after}")
                if checked_after == "true":
                    return True
            except Exception as e:
                notes.append(f"switch_{label_text}_err:{type(e).__name__}")
                continue
    except Exception as e:
        notes.append(f"switch_{label_text}_outer:{type(e).__name__}")
    return False


def _add_redirect_uri(page, redirect_uri: str, notes: list[str]) -> bool:
    """Ensure `redirect_uri` is present in the Valid OAuth Redirect URIs field."""
    try:
        # The field is a multi-token input; text may already be present.
        html = page.content()
        if redirect_uri in html:
            notes.append("redirect_uri_already_present")
            return True
        candidates = [
            "input[placeholder*='https://' i]",
            "input[aria-label*='Redirect' i]",
            "input[name*='redirect' i]",
            "textarea[aria-label*='Redirect' i]",
        ]
        for sel in candidates:
            try:
                loc = page.locator(sel).first
                if loc.count() == 0:
                    continue
                loc.scroll_into_view_if_needed(timeout=2000)
                loc.click(timeout=2500)
                loc.fill(redirect_uri, timeout=2500)
                page.keyboard.press("Enter")
                time.sleep(0.8)
                notes.append(f"redirect_uri_entered_via:{sel}")
                return True
            except Exception:
                continue
        notes.append("redirect_uri_input_not_found")
    except Exception as e:
        notes.append(f"redirect_uri_err:{type(e).__name__}")
    return False


def _click_save_changes(page, notes: list[str]) -> bool:
    selectors = [
        "button:has-text('Save changes')",
        "button:has-text('Save Changes')",
        "div[role='button']:has-text('Save changes')",
        "div[role='button']:has-text('Save Changes')",
        "button:has-text('Save')",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=800):
                loc.click(timeout=3000)
                notes.append(f"save_clicked:{sel}")
                time.sleep(3.0)
                return True
        except Exception:
            continue
    notes.append("save_button_not_found")
    return False


def configure_app_dashboard(*, app_id: str, redirect_uri: Optional[str] = None) -> dict:
    redirect_uri = (redirect_uri or DEFAULT_REDIRECT_URI).strip()
    result: dict = {
        "ok": False,
        "app_id": app_id,
        "redirect_uri": redirect_uri,
        "steps": [],
        "notes": [],
        "screenshot_path": None,
    }
    notes: list[str] = result["notes"]

    def step(name: str, ok: bool, **extra):
        result["steps"].append({"step": name, "ok": ok, **extra})

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as e:
        result["error"] = f"playwright_not_installed:{e}"
        return result

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={"width": 1400, "height": 900},
                args=_win_browser_args(["--disable-blink-features=AutomationControlled"]),
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            url = f"https://developers.facebook.com/apps/{app_id}/fb-login/settings/"
            nav = _safe_goto(page, url, notes, timeout=45000)
            step("open_settings", nav.get("ok", False), url=page.url)
            time.sleep(2.5)

            # If we got bounced to login, capture and report
            if "/login" in page.url or "login.php" in page.url:
                shot = _screenshot("dashboard_signin_required")
                try:
                    page.screenshot(path=str(shot))
                except Exception:
                    pass
                result["screenshot_path"] = str(shot)
                result["error"] = "facebook_dev_signin_required"
                result["human_required_action"] = (
                    "A Chrome window opened. Sign in to Facebook there once — "
                    "Unk keeps the session for future runs."
                )
                ctx.close()
                return result

            client_ok = _try_toggle_switch_on(page, "Client OAuth Login", notes)
            step("toggle_client_oauth", client_ok)
            web_ok = _try_toggle_switch_on(page, "Web OAuth Login", notes)
            step("toggle_web_oauth", web_ok)
            uri_ok = _add_redirect_uri(page, redirect_uri, notes)
            step("add_redirect_uri", uri_ok)

            saved = _click_save_changes(page, notes)
            step("save_changes", saved)

            shot = _screenshot("dashboard_after_save")
            try:
                page.screenshot(path=str(shot))
            except Exception:
                pass
            result["screenshot_path"] = str(shot)

            result["ok"] = bool(client_ok and web_ok and uri_ok and saved)
            if not result["ok"]:
                result["error"] = "dashboard_configure_incomplete"
                result["human_required_action"] = (
                    "The Meta app dashboard opened but Unk could not confirm all "
                    "toggles were flipped and saved. Complete manually once, then "
                    "future setups will work automatically."
                )
            ctx.close()
    except Exception as e:
        result["error"] = f"exception:{type(e).__name__}:{e}"
    return result
