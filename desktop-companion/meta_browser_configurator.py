"""
Meta Browser Configurator — auto-configure Meta Graph API credentials by
reading them out of Jason's already-signed-in Facebook Developer session.

Uses the same persistent Chrome profile as `meta_browser_publisher.py`
(~/.unk_companion/browser_profile/). If Jason is signed in there and has
accepted the Facebook Login for Business consent for his app, this script
can complete these steps without human clicks:

  1. Open Graph API Explorer.
  2. Read the currently-visible User Access Token from the token field.
  3. Optionally read the selected App ID from the app picker.
  4. Call GET /me/accounts with that token to enumerate Pages Jason admins.
  5. Pick the target Page by name (default: "J. Fortitude") or the first Page.
  6. Store app_id / page_id / page_access_token via the same keyring service
     that meta_credentials.py reads, so meta_publisher.py starts working
     immediately.
  7. Verify by GET /{page_id}?fields=id,name using the saved Page token.
  8. Return a structured receipt with masked token previews (never full).

What we deliberately do NOT try to scrape:
  - App Secret. Facebook only reveals it inside a re-auth modal, and reading
    it from the DOM is brittle + risky. We report app_secret_missing so the
    caller (or Jason) can paste it once via meta_key_capture.py. The Page
    Access Token from /me/accounts is already suitable for publishing.

Never raises through to the caller. Every path returns a dict.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
from datetime import datetime, timezone
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
PROFILE_DIR = CONFIG_DIR / "browser_profile"
SCREENSHOT_DIR = CONFIG_DIR / "meta_configurator_screenshots"
LOG_FILE = CONFIG_DIR / "meta_browser_configurator.log"

# Match the v25 owner OAuth dialog and Project K credential callback;
# Meta retired Graph v20 and an otherwise valid Page token fails discovery there.
GRAPH_BASE = "https://graph.facebook.com/v25.0"
EXPLORER_URL = "https://developers.facebook.com/tools/explorer/"
OAUTH_REDIRECT_URI = "https://www.facebook.com/connect/login_success.html"
REQUIRED_PAGE_SCOPES = [
    "pages_show_list",
    "pages_read_engagement",
    "business_management",
    "pages_manage_posts",
    "pages_manage_metadata",
    "instagram_basic",
    "instagram_content_publish",
]


def _log(event: str, **fields) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": event,
                **fields,
            }) + "\n")
    except Exception:
        pass


def _screenshot(name: str) -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return SCREENSHOT_DIR / f"{name}_{stamp}.png"


def _mask(v: Optional[str]) -> Optional[str]:
    if not v or len(v) < 8:
        return None
    return f"{v[:4]}…{v[-4:]}"


def _safe_goto(page, url: str, notes: list[str], *, wait_until: str = "domcontentloaded", timeout: int = 45000) -> dict:
    """Navigate that survives Facebook's non-2xx login/redirect responses.

    Playwright's page.goto raises ERR_HTTP_RESPONSE_CODE_FAILURE on any non-2xx
    HTTP status, which prevents our downstream "am I on a login page?" check
    from ever running. Catch that class of failure, then re-check page.url so
    the caller can decide whether it landed on login, a checkpoint, or the
    real target.
    """
    try:
        page.goto(url, wait_until=wait_until, timeout=timeout)
        return {"ok": True, "url": page.url}
    except Exception as e:
        msg = str(e)
        tolerated = any(marker in msg for marker in (
            "ERR_HTTP_RESPONSE_CODE_FAILURE",
            "ERR_ABORTED",
            "net::ERR_",
        ))
        landed = page.url or ""
        notes.append(f"goto_soft_failed:{url}:{msg.splitlines()[0][:180]}")
        if tolerated and landed and landed != "about:blank":
            return {"ok": False, "tolerated": True, "url": landed, "error": msg}
        return {"ok": False, "tolerated": False, "url": landed, "error": msg}


def _looks_like_login_wall(url: str) -> bool:
    u = (url or "").lower()
    return any(part in u for part in ("/login", "login.php", "checkpoint", "two_factor", "login/device"))


def _load_existing_app_id() -> Optional[str]:
    cfg_path = CONFIG_DIR / "meta_media_engine.json"
    if not cfg_path.exists():
        return None
    try:
        app_id = str((json.loads(cfg_path.read_text(encoding="utf-8")) or {}).get("app_id") or "").strip()
        return app_id if re.fullmatch(r"\d{8,20}", app_id) else None
    except Exception:
        return None


def _load_existing_configuration_id() -> Optional[str]:
    cfg_path = CONFIG_DIR / "meta_media_engine.json"
    if not cfg_path.exists():
        return None
    try:
        config_id = str((json.loads(cfg_path.read_text(encoding="utf-8")) or {}).get("configuration_id") or "").strip()
        return config_id if config_id else None
    except Exception:
        return None


def _extract_oauth_token(url: str) -> Optional[str]:
    parsed = urllib.parse.urlparse(url)
    for raw in (parsed.fragment, parsed.query):
        if not raw:
            continue
        values = urllib.parse.parse_qs(raw)
        token = (values.get("access_token") or [None])[0]
        if token and token.startswith(("EAA", "EAB")):
            return token
    return None


def _extract_oauth_code(url: str) -> Optional[str]:
    parsed = urllib.parse.urlparse(url)
    for raw in (parsed.query, parsed.fragment):
        if not raw:
            continue
        values = urllib.parse.parse_qs(raw)
        code = (values.get("code") or [None])[0]
        if code and len(code) > 10:
            return code
    return None


def oauth_capture_code(*, app_id: str, configuration_id: Optional[str] = None,
                       redirect_uri: Optional[str] = None, wait_seconds: int = 180) -> dict:
    """Facebook Login for Business code-flow capture. Opens the OAuth dialog
    in the persistent Unk browser profile, clicks Continue/Allow when the
    consent screen appears, then extracts the ?code= param from the redirect.
    Returns {ok, code, redirect_uri, app_id, configuration_id, notes, steps}.
    Deterministic — no config_id/response_type mismatch, no dashboard scraping.
    """
    result: dict = {
        "ok": False, "code": None,
        "app_id": app_id, "configuration_id": configuration_id,
        "redirect_uri": redirect_uri or OAUTH_REDIRECT_URI,
        "notes": [], "steps": [], "screenshot_path": None,
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

            raw_params = {
                "client_id": app_id,
                "redirect_uri": result["redirect_uri"],
                "response_type": "code",
                "scope": ",".join(REQUIRED_PAGE_SCOPES),
                "auth_type": "rerequest",
            }
            if configuration_id:
                raw_params["config_id"] = configuration_id
            params = urllib.parse.urlencode(raw_params)
            oauth_url = f"https://www.facebook.com/v25.0/dialog/oauth?{params}"
            nav = _safe_goto(page, oauth_url, notes, timeout=45000)
            step("open_oauth_dialog", nav.get("ok", False), url=page.url)

            if _looks_like_login_wall(nav.get("url", "")):
                if not _click_saved_profile_or_account_button(page, notes):
                    shot = _screenshot("signin_required")
                    try: page.screenshot(path=str(shot))
                    except Exception: pass
                    result["screenshot_path"] = str(shot)
                    result["error"] = "facebook_signin_required_in_unk_browser_profile"
                    result["human_required_action"] = "Sign in to Facebook in the Chrome window Unk opened, then retry."
                    ctx.close()
                    return result

            deadline = time.time() + wait_seconds
            last_url = page.url
            while time.time() < deadline:
                last_url = page.url
                code = _extract_oauth_code(last_url)
                if code:
                    result["ok"] = True
                    result["code"] = code
                    notes.append("oauth_code_received")
                    step("capture_code", True)
                    ctx.close()
                    return result
                parsed = urllib.parse.urlparse(last_url)
                bits = urllib.parse.parse_qs(parsed.query or parsed.fragment)
                if bits.get("error") or bits.get("error_reason"):
                    result["error"] = "oauth_denied_or_failed"
                    result["detail"] = bits
                    step("capture_code", False, error=str(bits))
                    ctx.close()
                    return result
                if _looks_like_login_wall(last_url):
                    if _click_saved_profile_or_account_button(page, notes):
                        continue
                _click_possible_oauth_continue(page, notes)
                time.sleep(1.2)

            shot = _screenshot("oauth_awaiting_consent")
            try: page.screenshot(path=str(shot))
            except Exception: pass
            result["screenshot_path"] = str(shot)
            result["error"] = "oauth_consent_timeout"
            result["human_required_action"] = "The Facebook consent screen opened but wasn't completed within the wait window. Click Continue in that Chrome window and retry."
            step("capture_code", False, error="timeout", url=last_url)
            ctx.close()
    except Exception as e:
        result["error"] = f"exception:{type(e).__name__}:{e}"
    return result



def _permission_check(access_token: str) -> dict:
    res = _graph_get("/me/permissions", access_token=access_token)
    if res.get("status") != 200:
        return {"ok": False, "status": res.get("status"), "body": res.get("body"), "granted": [], "missing": REQUIRED_PAGE_SCOPES}
    rows = (res.get("body") or {}).get("data") or []
    granted = sorted({r.get("permission") for r in rows if r.get("status") == "granted" and r.get("permission")})
    missing = [scope for scope in REQUIRED_PAGE_SCOPES if scope not in granted]
    return {"ok": not missing, "granted": granted, "missing": missing}


def _click_possible_oauth_continue(page, notes: list[str]) -> None:
    selectors = [
        # Facebook Login for Business primary button (2024+ DOM)
        "[aria-label='Continue' i]",
        "[aria-label='Continue as' i]",
        "[aria-label='Allow' i]",
        "[data-testid='cookie-policy-manage-dialog-accept-button']",
        "div[role='button'][aria-label*='Continue' i]",
        "div[role='button'][aria-label*='Allow' i]",
        # Text-based fallbacks
        "button:has-text('Continue as')",
        "div[role='button']:has-text('Continue as')",
        "button:has-text('Continue')",
        "div[role='button']:has-text('Continue')",
        "span[role='button']:has-text('Continue')",
        "button:has-text('Allow')",
        "div[role='button']:has-text('Allow')",
        "button:has-text('Save')",
        "div[role='button']:has-text('Save')",
        "button:has-text('OK')",
        "div[role='button']:has-text('OK')",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=500):
                loc.click(timeout=2500)
                notes.append(f"oauth_clicked:{sel}")
                time.sleep(2.0)
                return
        except Exception:
            continue
    # Last-ditch: press Enter — FB Login for Business focuses the primary
    # button by default, so Enter completes consent when selectors miss.
    try:
        page.keyboard.press("Enter")
        notes.append("oauth_enter_pressed_fallback")
        time.sleep(2.0)
    except Exception:
        pass



def _click_saved_profile_or_account_button(page, notes: list[str], *, wait_seconds: int = 25) -> bool:
    """Click the saved-account/profile button on Facebook login surfaces.

    Jason's desktop keeps the login path alive through the browser/Google-saved
    account chooser. That is not a human blocker. When Meta/Facebook shows a
    saved account tile (often a profile image/avatar button), Unk should click
    it instead of asking Jason for a password he does not remember.
    """
    direct_selectors = [
        "button:has-text('Continue as')",
        "div[role='button']:has-text('Continue as')",
        "a:has-text('Continue as')",
        "button:has-text('Log in as')",
        "div[role='button']:has-text('Log in as')",
        "a:has-text('Log in as')",
        "[aria-label*='Continue as' i]",
        "[aria-label*='Log in as' i]",
        "[aria-label*='Jason' i]",
        "[aria-label*='Williams' i]",
        "[data-testid='login_button']",
    ]

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        for sel in direct_selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=500):
                    loc.click(timeout=3000)
                    notes.append(f"saved_profile_clicked:{sel}")
                    time.sleep(3.0)
                    return True
            except Exception:
                continue

        # Fallback for the visual saved-login tile: a button/link/card whose
        # accessible text may be empty but contains the profile image/avatar.
        try:
            candidates = page.locator("button, a[role='button'], div[role='button'], div[tabindex='0']")
            count = min(candidates.count(), 80)
            for i in range(count):
                item = candidates.nth(i)
                try:
                    if not item.is_visible(timeout=250):
                        continue
                    label = " ".join([
                        item.inner_text(timeout=500) or "",
                        item.get_attribute("aria-label") or "",
                        item.get_attribute("title") or "",
                    ]).strip().lower()
                    has_profile_language = any(s in label for s in ("continue as", "log in as", "jason", "williams"))
                    has_avatar = item.locator("img, image, svg").count() > 0
                    box = item.bounding_box() or {}
                    wide_enough = float(box.get("width") or 0) >= 32
                    tall_enough = float(box.get("height") or 0) >= 32
                    if has_profile_language or (has_avatar and wide_enough and tall_enough and not page.locator("input[type='password']").is_visible(timeout=100)):
                        item.click(timeout=3000)
                        notes.append(f"saved_profile_clicked:visual_tile:{i}:{label[:80]}")
                        time.sleep(3.0)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Some saved-account prompts put the right tile under keyboard focus.
        # Pressing Enter is safe on a login chooser, and avoids asking Jason for
        # the forgotten password when the blue profile/avatar button is focused.
        try:
            if _looks_like_login_wall(page.url):
                page.keyboard.press("Enter")
                notes.append("saved_profile_enter_pressed")
                time.sleep(3.0)
                if not _looks_like_login_wall(page.url):
                    return True
        except Exception:
            pass

        time.sleep(1.0)
    return False


def _oauth_user_token(page, *, app_id: str, notes: list[str], configuration_id: Optional[str] = None, wait_seconds: int = 150) -> dict:
    """Get a user token through Facebook's OAuth dialog with the exact Page
    publishing scopes needed by /me/accounts. Uses the already-signed-in browser
    profile and only returns masked diagnostics; the raw token stays in memory.
    """
    raw_params = {
        "client_id": app_id,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "token",
        "scope": ",".join(REQUIRED_PAGE_SCOPES),
        "auth_type": "rerequest",
    }
    # NOTE: intentionally NOT sending config_id here. Facebook Login for Business
    # (config_id) mandates response_type=code with a server-side code exchange,
    # which we don't have. Plain OAuth implicit works for the app owner + testers
    # in dev mode and returns the access token in the URL fragment.
    params = urllib.parse.urlencode(raw_params)
    nav = _safe_goto(page, f"https://www.facebook.com/v25.0/dialog/oauth?{params}", notes, timeout=45000)
    if _looks_like_login_wall(nav.get("url", "")):
        if _click_saved_profile_or_account_button(page, notes):
            notes.append("login_wall_cleared_by_saved_profile_attempt")
        else:
            return {"ok": False, "error": "facebook_signin_required_in_unk_browser_profile", "url": nav.get("url"), "human_required_category": "password_manager_unlock"}
    if not nav.get("ok") and not nav.get("tolerated"):
        return {"ok": False, "error": "oauth_navigation_failed", "detail": nav.get("error"), "url": nav.get("url")}
    deadline = time.time() + wait_seconds
    last_url = page.url
    while time.time() < deadline:
        last_url = page.url
        token = _extract_oauth_token(last_url)
        if token:
            notes.append("oauth_token_received")
            return {"ok": True, "token": token, "url": OAUTH_REDIRECT_URI}
        parsed = urllib.parse.urlparse(last_url)
        failure_bits = urllib.parse.parse_qs(parsed.query or parsed.fragment)
        if failure_bits.get("error") or failure_bits.get("error_reason"):
            return {"ok": False, "error": "oauth_denied_or_failed", "detail": failure_bits, "url": last_url}
        if _looks_like_login_wall(last_url):
            if _click_saved_profile_or_account_button(page, notes):
                continue
            return {"ok": False, "error": "facebook_signin_required_in_unk_browser_profile", "url": last_url, "human_required_category": "password_manager_unlock"}
        _click_possible_oauth_continue(page, notes)
        time.sleep(1.0)
    return {"ok": False, "error": "oauth_token_not_returned", "url": last_url}


def _read_token_from_explorer(page) -> Optional[str]:
    """Try several stable selectors that Facebook has used for the Access
    Token field on the Graph Explorer. Returns the raw token or None."""
    selectors = [
        "input[aria-label*='Access Token' i]",
        "input[placeholder*='Access Token' i]",
        "textarea[aria-label*='Access Token' i]",
        "input[name='access_token']",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() == 0:
                continue
            val = loc.input_value(timeout=2000)
            if val and val.strip().startswith(("EAA", "EAB")):
                return val.strip()
        except Exception:
            continue
    # Last-ditch: scan every input for something that looks like an FB token.
    try:
        candidates = page.eval_on_selector_all(
            "input, textarea",
            "els => els.map(e => e.value).filter(v => typeof v === 'string' && v.length > 30)",
        )
        for v in candidates:
            if isinstance(v, str) and v.startswith(("EAA", "EAB")) and len(v) > 60:
                return v.strip()
    except Exception:
        pass
    return None


def _read_app_id_from_explorer(page) -> Optional[str]:
    """Graph Explorer shows the selected app id near the app picker; also
    appears in the request URL when the token is issued. Try DOM + URL."""
    try:
        # The app picker button often exposes text like "My App · 1234567890"
        candidates = page.eval_on_selector_all(
            "button, div, span",
            "els => els.map(e => e.textContent || '')"
            ".filter(t => /\\b\\d{15,17}\\b/.test(t)).slice(0, 20)",
        )
        for txt in candidates or []:
            m = re.search(r"\b(\d{15,17})\b", txt or "")
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def _graph_get(path: str, *, access_token: str, params: Optional[dict] = None) -> dict:
    import requests  # type: ignore
    q = dict(params or {})
    q["access_token"] = access_token
    r = requests.get(f"{GRAPH_BASE}{path}", params=q, timeout=30)
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text}
    return {"status": r.status_code, "body": body}


def _save_meta_credentials(*, app_id: Optional[str], configuration_id: Optional[str], page_id: str,
                           page_access_token: str) -> dict:
    """Persist through the same interface meta_key_capture.py uses so the
    existing meta_publisher.py picks them up with no other changes."""
    from meta_key_capture import save_secret  # type: ignore
    CONFIG_DIR.mkdir(exist_ok=True)
    cfg_path = CONFIG_DIR / "meta_media_engine.json"
    cfg: dict = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    if app_id:
        cfg["app_id"] = app_id
    if configuration_id:
        cfg["configuration_id"] = configuration_id
    cfg["page_id"] = page_id
    cfg["provider"] = "browser_configurator"
    cfg["secret_store"] = cfg.get("secret_store") or "keyring"
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    save_secret("META_PAGE_ACCESS_TOKEN", page_access_token)
    return {"config_file": str(cfg_path)}


def configure_meta_via_browser(*, preferred_page_name: Optional[str] = None, app_id: Optional[str] = None, configuration_id: Optional[str] = None) -> dict:
    """Run the end-to-end browser configuration. Returns a receipt dict."""
    notes: list[str] = []
    result: dict = {
        "ok": False,
        "steps": [],
        "notes": notes,
        "screenshot_path": None,
        "app_id": None,
        "configuration_id": configuration_id,
        "page_id": None,
        "page_name": None,
        "page_access_token_preview": None,
        "user_access_token_preview": None,
        "token_scopes": [],
        "app_secret_missing": True,  # we never scrape this
        "error": None,
    }

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as e:
        result["error"] = f"playwright_not_installed:{e}"
        return result

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    def step(name: str, ok: bool, **extra):
        result["steps"].append({"step": name, "ok": ok, **extra})

    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={"width": 1400, "height": 900},
                args=_win_browser_args(["--disable-blink-features=AutomationControlled"]),
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            app_id = app_id or _load_existing_app_id()
            configuration_id = configuration_id or _load_existing_configuration_id()
            result["configuration_id"] = configuration_id
            token = None
            token_source = None

            if not app_id:
                result["error"] = "meta_app_id_required"
                result["human_required_action"] = "Save the Meta App ID once, then rerun Meta authorization. Unk cannot construct the Facebook Login for Business approval URL without the App ID."
                step("read_app_id", False, reason="missing_meta_app_id")
                ctx.close()
                return result

            # Preferred repair path: use the app's OAuth dialog to request the
            # exact Page scopes Meta now requires for feed publishing. This
            # avoids Graph Explorer handing us a token that can list Pages but
            # still fails /feed with "Requires pages_read_engagement".
            if app_id:
                oauth = _oauth_user_token(page, app_id=app_id, configuration_id=configuration_id, notes=notes)
                if oauth.get("ok") and oauth.get("token"):
                    token = str(oauth["token"])
                    token_source = "oauth_dialog_required_scopes"
                    result["app_id"] = app_id
                    step("oauth_required_page_scopes", True, app_id=app_id)
                else:
                    notes.append(f"oauth_required_page_scopes_failed:{oauth.get('error')}")
                    step("oauth_required_page_scopes", False, error=oauth.get("error"), url=oauth.get("url"))
                    if oauth.get("error") == "facebook_signin_required_in_unk_browser_profile":
                        # Give Jason a visible window to sign in once; then the
                        # persistent Chrome profile keeps him logged in for
                        # future runs. Do NOT scrape login credentials.
                        _safe_goto(page, "https://www.facebook.com/login", notes, timeout=30000)
                        shot = _screenshot("signin_required")
                        try:
                            page.screenshot(path=str(shot))
                        except Exception:
                            pass
                        result["screenshot_path"] = str(shot)
                        result["error"] = "facebook_signin_required_in_unk_browser_profile"
                        result["human_required_action"] = "A Chrome window opened on this PC. Sign in to Facebook there once — Unk will keep you logged in for future runs. Then click Retry."
                        ctx.close()
                        return result
                    if "PLATFORM__INVALID_APP_ID" in str(oauth.get("url")) or "INVALID_APP_ID" in str(oauth.get("detail")):
                        notes.append("stored_app_id_rejected_by_meta_will_read_current_explorer_app")
                        app_id = None

            if not token:
                # The Graph API Explorer page now returns HTTP errors and cannot
                # be relied on. Instead of the dead fallback, keep the OAuth
                # dialog window open long enough for Jason to click Continue.
                shot = _screenshot("oauth_awaiting_consent")
                try:
                    page.screenshot(path=str(shot))
                except Exception:
                    pass
                result["screenshot_path"] = str(shot)
                result["error"] = "oauth_consent_required"
                result["human_required_action"] = (
                    "A Chrome window opened on this PC on the Facebook Login for "
                    "Business consent screen. Click Continue / Allow to grant "
                    "pages_read_engagement + pages_manage_posts, then click Retry."
                )
                step("oauth_consent_required", False, url=page.url)
                ctx.close()
                return result

            if not token:
                shot = _screenshot("token_not_found")
                page.screenshot(path=str(shot))
                result["screenshot_path"] = str(shot)
                result["error"] = "access_token_not_readable_from_explorer"
                step("read_user_access_token", False)
                ctx.close()
                return result
            result["user_access_token_preview"] = _mask(token)
            step("read_user_access_token", True, preview=_mask(token), source=token_source)

            app_id = app_id or _read_app_id_from_explorer(page)
            result["app_id"] = app_id
            step("read_app_id", bool(app_id), app_id=app_id)

            perm = _permission_check(token)
            result["token_scopes"] = perm.get("granted", [])
            if not perm.get("ok") and app_id and token_source != "oauth_dialog_required_scopes":
                notes.append(f"visible_token_missing_scopes:{','.join(perm.get('missing', []))}")
                oauth = _oauth_user_token(page, app_id=app_id, configuration_id=configuration_id, notes=notes)
                if oauth.get("ok") and oauth.get("token"):
                    token = str(oauth["token"])
                    token_source = "oauth_dialog_required_scopes_retry"
                    perm = _permission_check(token)
                    result["token_scopes"] = perm.get("granted", [])
            if not perm.get("ok"):
                shot = _screenshot("missing_page_permissions")
                page.screenshot(path=str(shot))
                result["screenshot_path"] = str(shot)
                result["error"] = "missing_meta_page_permissions"
                result["missing_permissions"] = perm.get("missing", REQUIRED_PAGE_SCOPES)
                step("verify_required_page_permissions", False, missing=perm.get("missing", REQUIRED_PAGE_SCOPES))
                ctx.close()
                return result
            step("verify_required_page_permissions", True, granted=perm.get("granted", []))

            # Ask the Graph API which Pages this user administers.
            accounts = _graph_get("/me/accounts",
                                  access_token=token,
                                  params={"fields": "id,name,access_token,tasks"})
            if accounts["status"] != 200:
                shot = _screenshot("me_accounts_failed")
                page.screenshot(path=str(shot))
                result["screenshot_path"] = str(shot)
                result["error"] = f"me_accounts_http_{accounts['status']}"
                result["graph_body"] = accounts["body"]
                step("list_pages", False, status=accounts["status"])
                ctx.close()
                return result

            pages = accounts["body"].get("data") or []
            if not pages:
                shot = _screenshot("no_pages_admined")
                page.screenshot(path=str(shot))
                result["screenshot_path"] = str(shot)
                result["error"] = "user_administers_no_pages"
                step("list_pages", False, count=0)
                ctx.close()
                return result

            step("list_pages", True, count=len(pages))

            chosen = None
            if preferred_page_name:
                needle = preferred_page_name.strip().lower()
                for pg in pages:
                    if (pg.get("name") or "").strip().lower() == needle:
                        chosen = pg
                        break
                if not chosen:
                    for pg in pages:
                        if needle in (pg.get("name") or "").strip().lower():
                            chosen = pg
                            break
            if not chosen:
                chosen = pages[0]
                notes.append(f"preferred_page_name_not_matched_using_first:{chosen.get('name')}")

            page_id = str(chosen.get("id") or "")
            page_name = chosen.get("name")
            page_token = chosen.get("access_token")
            result["page_id"] = page_id
            result["page_name"] = page_name

            if not page_id or not page_token:
                result["error"] = "selected_page_missing_id_or_token"
                step("select_page", False, page_id=page_id, has_token=bool(page_token))
                ctx.close()
                return result
            step("select_page", True, page_id=page_id, page_name=page_name)

            # Verify the Page token by hitting the Page endpoint.
            # NOTE: Use only id,name — fan_count requires pages_read_engagement
            # which isn't always on the scraped user token. id/name works with
            # any valid page access token.
            verify = _graph_get(f"/{page_id}", access_token=page_token,
                                params={"fields": "id,name"})

            if verify["status"] != 200:
                err = (verify.get("body") or {}).get("error") or {}
                # Some apps can publish with pages_manage_posts but cannot read
                # Page details without pages_read_engagement. The token still
                # came directly from /me/accounts in this same run, so do not
                # block credential persistence on read-only verification.
                if err.get("code") == 100 and "pages_read_engagement" in str(err.get("message", "")):
                    notes.append("page_token_read_probe_skipped_missing_pages_read_engagement")
                    step("verify_page_token", True, status=verify["status"], warning="read_probe_permission_missing")
                else:
                    result["error"] = f"page_token_verify_http_{verify['status']}"
                    result["graph_body"] = verify["body"]
                    step("verify_page_token", False, status=verify["status"])
                    ctx.close()
                    return result
            else:
                step("verify_page_token", True, page=verify["body"])

            # Persist to keyring + config file so meta_publisher.py sees it.
            try:
                save_info = _save_meta_credentials(
                    app_id=app_id,
                    configuration_id=configuration_id,
                    page_id=page_id,
                    page_access_token=page_token,
                )
                step("persist_credentials", True, **save_info)
                result["page_access_token_preview"] = _mask(page_token)
            except Exception as e:
                step("persist_credentials", False, error=str(e))
                result["error"] = f"persist_failed:{e}"
                ctx.close()
                return result

            shot = _screenshot("configured")
            page.screenshot(path=str(shot))
            result["screenshot_path"] = str(shot)
            ctx.close()

            notes.append("app_secret_not_scraped_run_meta_key_capture_once_if_you_need_long_lived_exchange")
            result["ok"] = True
            _log("meta_configured", page_id=page_id, page_name=page_name, app_id=app_id)
            return result

    except Exception as e:
        result["error"] = f"unexpected:{e}"
        _log("configurator_exception", error=str(e))
        return result
