"""
Meta Browser Publisher — publishes to a Facebook Page using Jason's own
logged-in Chrome profile via Playwright.

This is Option 1 from the launch plan: skip the Graph API entirely and post
by driving the browser Jason is already signed into. Nothing about credential
handling changes — the browser holds his session, Playwright just clicks.

Every publish call returns a structured dict:
    {
      "ok": bool,
      "post_url": str | None,
      "screenshot_path": str | None,
      "error": str | None,
      "notes": [str, ...],
    }

Never raises. Failures are captured into `error` + `screenshot_path` so the
companion can post a receipt back to the platform.

Requirements on the desktop:
    pip install playwright pillow requests
    playwright install chromium

The persistent Chrome profile lives at:
    ~/.unk_companion/browser_profile/
The first run will open Chromium — Jason logs into Facebook once, and from
that point on every publish reuses the saved cookies.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
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
SCREENSHOT_DIR = CONFIG_DIR / "browser_publish_screenshots"
LOG_FILE = CONFIG_DIR / "browser_publisher.log"

# Slug -> canonical Facebook Page URL. Add more here (or move to config) as
# additional pages come online.
PAGE_URLS: dict[str, str] = {
    "j-fortitude": "https://business.facebook.com/latest/composer?asset_id=100063471851317",
    "village-816": "https://www.facebook.com/TheVillage816",
    "super-saucy-ex-felon-tv": "https://www.facebook.com/SuperSaucyExFelonTV",
}

FALLBACK_PAGE_URLS: dict[str, list[str]] = {
    "j-fortitude": [
        "https://business.facebook.com/latest/composer?asset_id=100063471851317",
        "https://www.facebook.com/profile.php?id=100063471851317",
    ],
}

VERIFY_PAGE_URLS: dict[str, str] = {
    "j-fortitude": "https://www.facebook.com/profile.php?id=100063471851317",
    "village-816": "https://www.facebook.com/TheVillage816",
    "super-saucy-ex-felon-tv": "https://www.facebook.com/SuperSaucyExFelonTV",
}


def _message_probe(message: str) -> str:
    """Stable text fragment used only for post-publish verification."""
    return re.sub(r"\s+", " ", message.strip()).lower()[:80]


def _visible_post_urls(page, *, message_probe: str | None = None) -> set[str]:
    """Collect plausible Facebook permalink URLs currently visible.

    Business Suite often clears the composer without leaving the new permalink on
    the composer route. This helper is shared by pre-snapshot and post-verify
    flows; when a message_probe is provided, nearby text gets priority.
    """
    urls: set[str] = set()
    selectors = "a[href*='/posts/'], a[href*='/videos/'], a[href*='/photos/'], a[href*='permalink'], a[href*='story_fbid=']"
    try:
        anchors = page.locator(selectors)
        n = min(anchors.count(), 80)
        for i in range(n):
            try:
                a = anchors.nth(i)
                href = a.get_attribute("href") or ""
                if not re.search(r"/(posts|videos|photos)|permalink|story_fbid=", href):
                    continue
                if message_probe:
                    nearby = ""
                    try:
                        nearby = (a.locator("xpath=ancestor::*[self::div or self::article][1]").inner_text(timeout=1000) or "").lower()
                    except Exception:
                        nearby = ""
                    if nearby and message_probe not in re.sub(r"\s+", " ", nearby):
                        continue
                u = href.split("?")[0] if "story_fbid=" not in href else href
                if u.startswith("/"):
                    u = "https://www.facebook.com" + u
                urls.add(u)
            except Exception:
                continue
    except Exception:
        pass
    return urls


def _log(event: str, **fields) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _screenshot_path(prefix: str) -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return SCREENSHOT_DIR / f"{prefix}_{stamp}.png"


# ---------------------------------------------------------------------------
# Page-identity switch (handles Facebook's "Switch Now" / "See all profiles"
# prompt when the browser is signed in as a person but viewing a Page as a
# visitor). This is a normal browser action; it is NOT a human checkpoint.
# ---------------------------------------------------------------------------

_SWITCH_TEXT_RE = re.compile(
    r"switch\s*now|switch\s*into|switch\s*profile|switch\s*to\s*(page|j\.?\s*fortitude)|use\s*j\.?\s*fortitude|see\s*all\s*profiles",
    re.IGNORECASE,
)

_PAGE_MGMT_MARKERS = (
    "professional dashboard",
    "meta business suite",
    "page manager",
    "you are posting as",
    "posting as j. fortitude",
    "publishing tools",
    "your page",
    "manage page",
)


def _ensure_page_identity(page, notes: list[str], target_page_name: str = "J. Fortitude") -> dict:
    """Detect the "viewing as visitor" state and click Facebook's own identity
    switch control to activate the target Page. Returns a dict receipt:
        {"switched": bool, "control": str|None, "final_url": str,
         "management_visible": bool, "notes": [...]}
    Never raises.
    """
    receipt: dict = {"switched": False, "control": None, "final_url": None,
                     "management_visible": False, "attempts": []}
    try:
        receipt["final_url"] = page.url
    except Exception:
        pass

    # Fast-path: if Page management markers are already visible, we're good.
    try:
        body_lc = (page.content() or "").lower()
        if any(m in body_lc for m in _PAGE_MGMT_MARKERS):
            receipt["management_visible"] = True
            notes.append("page_identity_already_active")
            return receipt
    except Exception:
        pass

    # Strategy 1: click any visible role=button whose accessible text matches Switch/Use Page
    try:
        buttons = page.locator("[role='button'], button, [role='link']")
        n = min(buttons.count(), 60)
        for i in range(n):
            try:
                b = buttons.nth(i)
                txt = (b.inner_text(timeout=800) or "").strip()
            except Exception:
                continue
            if not txt or len(txt) > 60:
                continue
            if _SWITCH_TEXT_RE.search(txt):
                receipt["attempts"].append(f"click:{txt[:40]}")
                try:
                    b.click(timeout=4000)
                    time.sleep(2.5)
                    receipt["switched"] = True
                    receipt["control"] = txt[:60]
                    notes.append(f"page_identity_switch_clicked:{txt[:40]}")
                    break
                except Exception as e:
                    receipt["attempts"].append(f"click_failed:{type(e).__name__}")
                    continue
    except Exception:
        pass

    # Strategy 2: open the profile menu, then click a tile matching the Page name
    if not receipt["switched"]:
        menu_selectors = [
            "div[aria-label='Your profile'][role='button']",
            "div[aria-label='Account'][role='button']",
            "div[aria-label*='profile menu']",
            "[aria-label*='See more profiles']",
        ]
        for sel in menu_selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    loc.click(timeout=3000)
                    time.sleep(1.5)
                    receipt["attempts"].append(f"open_menu:{sel}")
                    tile = page.get_by_text(target_page_name, exact=False).first
                    if tile.count() > 0:
                        tile.click(timeout=3000)
                        time.sleep(2.5)
                        receipt["switched"] = True
                        receipt["control"] = f"profile_menu → {target_page_name}"
                        notes.append(f"page_identity_switch_menu:{target_page_name}")
                        break
            except Exception:
                continue

    # Verify management surface after switch
    try:
        receipt["final_url"] = page.url
        body_lc = (page.content() or "").lower()
        if any(m in body_lc for m in _PAGE_MGMT_MARKERS):
            receipt["management_visible"] = True
    except Exception:
        pass

    return receipt


def _normalize_media_url(url: str) -> str:
    file_match = re.search(r"drive\.google\.com/file/d/([^/]+)", url)
    open_match = re.search(r"[?&]id=([^&]+)", url) if "drive.google.com" in url else None
    file_id = file_match.group(1) if file_match else (open_match.group(1) if open_match else None)
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def _prune_browser_media_cache(dest_dir: Path, max_age_hours: int = 6) -> dict:
    """Bound generated browser-media staging so successful publishes cannot fill disk.

    Only files created by _download_media (media_<unix>.<known media ext>) are
    eligible, and only after the retention window. Current/in-flight downloads
    remain untouched. Failures are logged and never block publishing.
    """
    cutoff = time.time() - max(1, int(max_age_hours)) * 3600
    pattern = re.compile(r"^media_\\d+\\.(?:mp4|mov|jpg|jpeg|png|webp)$", re.I)
    deleted = 0
    freed = 0
    errors: list[str] = []
    try:
        if not dest_dir.exists():
            return {"deleted": 0, "freed_bytes": 0, "errors": []}
        for p in dest_dir.iterdir():
            try:
                if not p.is_file() or not pattern.match(p.name):
                    continue
                st = p.stat()
                if st.st_mtime >= cutoff:
                    continue
                size = st.st_size
                p.unlink()
                deleted += 1
                freed += size
            except Exception as e:
                errors.append(f"{p.name}:{e}")
        if deleted or errors:
            _log("browser_media_cache_pruned", deleted=deleted, freed_bytes=freed, errors=errors[:10])
    except Exception as e:
        errors.append(str(e))
        _log("browser_media_cache_prune_failed", error=str(e))
    return {"deleted": deleted, "freed_bytes": freed, "errors": errors[:10]}


def _download_media(url: str, dest_dir: Path) -> Optional[Path]:
    _prune_browser_media_cache(dest_dir)
    try:
        import requests  # type: ignore
    except Exception:
        return None
    try:
        normalized_url = _normalize_media_url(url)
        r = requests.get(normalized_url, timeout=60, stream=True, allow_redirects=True)
        r.raise_for_status()
        dest_dir.mkdir(parents=True, exist_ok=True)
        content_type = (r.headers.get("content-type") or "").lower()
        ext = Path(normalized_url.split("?")[0]).suffix.lower()
        if not ext:
            if "video" in content_type:
                ext = ".mp4"
            elif "png" in content_type:
                ext = ".png"
            elif "webp" in content_type:
                ext = ".webp"
            else:
                ext = ".jpg"
        out = dest_dir / f"media_{int(time.time())}{ext}"
        with out.open("wb") as f:
            for chunk in r.iter_content(65536):
                if chunk:
                    f.write(chunk)
        if out.stat().st_size < 1024:
            _log("media_download_too_small", url=url, normalized_url=normalized_url, bytes=out.stat().st_size, content_type=content_type)
            return None
        return out
    except Exception as e:
        _log("media_download_failed", url=url, error=str(e))
        return None


def _ensure_playwright_ready(notes: list[str]) -> tuple[bool, Optional[str]]:
    """Best-effort local repair for the browser publisher dependency.

    The companion is intentionally desktop-local, so it is safe for the PC to
    install its own Python package/browser runtime when a publish action needs
    them. This prevents queued posts from failing just because setup_unk.ps1 was
    not run after a manual ZIP swap.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as first_error:
        notes.append("playwright_missing_attempting_auto_install")
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "requests",
                    "pillow",
                    "keyring",
                    "playwright",
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            notes.append(f"playwright_pip_exit:{proc.returncode}")
            if proc.returncode != 0:
                return False, f"playwright_install_failed:{(proc.stderr or proc.stdout)[-500:]}"
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as install_error:
            _log("playwright_auto_install_failed", error=str(install_error), first_error=str(first_error))
            return False, f"playwright_not_installed:{install_error}"

    try:
        with sync_playwright() as p:
            chromium_path = Path(p.chromium.executable_path)
            if chromium_path.exists():
                notes.append("playwright_chromium_ready")
                return True, None
    except Exception as check_error:
        notes.append(f"playwright_check_warning:{check_error}")

    notes.append("playwright_chromium_missing_attempting_install")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        notes.append(f"playwright_chromium_install_exit:{proc.returncode}")
        if proc.returncode != 0:
            return False, f"playwright_chromium_install_failed:{(proc.stderr or proc.stdout)[-500:]}"
        return True, None
    except Exception as install_error:
        _log("playwright_chromium_install_failed", error=str(install_error))
        return False, f"playwright_chromium_install_failed:{install_error}"


def _release_locked_profile(notes: list[str]) -> None:
    """Release Unk's dedicated Chromium profile so a fresh launch_persistent_context
    can succeed. Fixes Playwright's 'Opening in existing browser session' error,
    which happens when a prior Chromium is still holding SingletonLock files in
    PROFILE_DIR — usually from a crashed/orphaned publisher run.

    Two-part cleanup:
      1. On Windows, kill any stray Chromium processes whose command line still
         references our dedicated profile path.
      2. On every OS, remove Chromium's Singleton* lock files inside PROFILE_DIR.
    """
    profile_token = str(PROFILE_DIR)
    profile_token_lower = profile_token.lower()

    # 1) Kill orphaned Chromium processes still holding the profile (Windows).
    if os.name == "nt":
        # Prefer PowerShell/CIM over wmic. Some Windows builds escape the WMIC
        # LIKE string differently, which was letting a real --user-data-dir
        # process survive and produce: "Opening in existing browser session".
        try:
            ps = f"""
$profile = {json.dumps(profile_token)}
$procs = Get-CimInstance Win32_Process | Where-Object {{
  ($_.Name -match '^(chrome|chromium|msedge)\\.exe$') -and
  ($_.CommandLine -like "*$profile*" -or $_.CommandLine -like "*browser_profile*")
}}
$count = 0
foreach ($p in $procs) {{
  try {{ Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop; $count++ }} catch {{}}
}}
Write-Output $count
"""
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                capture_output=True,
                text=True,
                timeout=15,
            )
            killed = int((proc.stdout or "0").strip().splitlines()[-1] or "0")
            if killed:
                notes.append(f"released_locked_browser_profile_ps:{killed}")
                time.sleep(2.0)
        except Exception as e:
            notes.append(f"profile_release_powershell_warning:{e}")

        try:
            proc = subprocess.run(
                [
                    "wmic", "process", "where",
                    "CommandLine like '%browser_profile%'",
                    "get", "ProcessId,CommandLine", "/FORMAT:CSV",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            killed = 0
            for line in proc.stdout.splitlines():
                line_lower = line.lower()
                if profile_token_lower not in line_lower and ".unk_companion" not in line_lower and "browser_profile" not in line_lower:
                    continue
                pid = line.strip().split(",")[-1]
                if not pid.isdigit():
                    continue
                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, timeout=5)
                killed += 1
            if killed:
                notes.append(f"released_locked_browser_profile:{killed}")
                time.sleep(1.5)
        except Exception as e:
            notes.append(f"profile_release_warning:{e}")

    # 2) Remove Chromium's Singleton* lock files (all platforms). These are what
    #    trigger "Opening in existing browser session" even after the owning
    #    process is gone.
    try:
        if PROFILE_DIR.exists():
            removed = 0
            for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
                for lock in PROFILE_DIR.rglob(name + "*"):
                    try:
                        lock.unlink()
                        removed += 1
                    except Exception:
                        pass
            if removed:
                notes.append(f"cleared_singleton_locks:{removed}")
            time.sleep(0.5)
    except Exception as e:
        notes.append(f"singleton_lock_cleanup_warning:{e}")


# Shared Chromium launch args for Unk's dedicated profile. Keep in sync with
# multi_platform_publisher and vendor_browser so every entry point behaves the
# same way and avoids Chrome's first-run / default-browser prompts stealing focus.
UNK_CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
]


def publish_facebook_page(
    *,
    page_slug: str,
    message: str,
    link_url: Optional[str] = None,
    image_url: Optional[str] = None,
    video_url: Optional[str] = None,
    page_url_override: Optional[str] = None,
) -> dict:
    """Publish a post to a Facebook Page using the saved browser session."""
    notes: list[str] = []
    result: dict = {"ok": False, "post_url": None, "screenshot_path": None, "error": None, "notes": notes}

    candidate_urls: list[str] = []
    if page_url_override:
        candidate_urls.append(page_url_override)
    candidate_urls.extend(FALLBACK_PAGE_URLS.get(page_slug, []))
    mapped_url = PAGE_URLS.get(page_slug)
    if mapped_url:
        candidate_urls.append(mapped_url)
    candidate_urls = list(dict.fromkeys([u for u in candidate_urls if u]))
    if not candidate_urls:
        result["error"] = f"unknown_page_slug:{page_slug}"
        return result

    ready, readiness_error = _ensure_playwright_ready(notes)
    if not ready:
        result["error"] = readiness_error or "playwright_not_ready"
        _log("playwright_not_ready", error=result["error"])
        return result

    from playwright.sync_api import sync_playwright  # type: ignore

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    local_media: Optional[Path] = None
    if image_url or video_url:
        local_media = _download_media(image_url or video_url or "", CONFIG_DIR / "browser_media")
        if not local_media:
            notes.append("media_download_failed_falling_back_to_text_only")

    full_message = message.strip()
    if link_url and link_url not in full_message:
        full_message = f"{full_message}\n\n{link_url}".strip()

    screenshot_final = _screenshot_path("final")

    try:
        with sync_playwright() as p:
            _release_locked_profile(notes)
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={"width": 1400, "height": 900},
                args=_win_browser_args(UNK_CHROMIUM_ARGS),
            )
            page = context.pages[0] if context.pages else context.new_page()
            page_url = candidate_urls[0]
            for idx, candidate_url in enumerate(candidate_urls):
                page.goto(candidate_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(4.0 if "business.facebook.com" in candidate_url else 2.5)

                # Detect the login wall. If the "Log in" form is showing, we cannot
                # proceed — Jason needs to sign in once in this profile.
                if "login" in page.url or page.locator("input[name='email']").count() > 0:
                    shot = _screenshot_path("login_required")
                    page.screenshot(path=str(shot))
                    result["screenshot_path"] = str(shot)
                    result["error"] = "facebook_login_required_in_browser_profile"
                    _log("login_required", page_slug=page_slug, attempted_url=candidate_url)
                    context.close()
                    return result

                # Detect surface: Meta Business Suite composer opens directly with a
                # textbox already visible, so there is no "Create post" affordance to
                # click. The classic Page surface requires clicking "What's on your
                # mind" to open a modal. Handle both.
                is_business_suite = "business.facebook.com" in (page.url or candidate_url)

                opened = False
                tried_selectors: list[str] = []
                suite_selectors = [
                    "div[contenteditable='true'][role='textbox']",
                    "div[contenteditable='true']",
                    "[role='textbox']",
                    "textarea",
                    "div[aria-label*='reate a post'] div[contenteditable='true']",
                    "div[aria-label*='rite something']",
                    "div[data-pagelet*='Composer']",
                ]
                if is_business_suite:
                    for ready_sel in suite_selectors:
                        tried_selectors.append(ready_sel)
                        try:
                            page.wait_for_selector(ready_sel, timeout=6000)
                            opened = True
                            notes.append(f"surface=business_suite_composer({ready_sel})")
                            break
                        except Exception:
                            continue

                classic_selectors = [
                    "div[role='button']:has-text(\"What's on your mind\")",
                    "div[role='button']:has-text('Create post')",
                    "div[role='button']:has-text('Create a post')",
                    "div[role='button']:has-text('Post')",
                    "div[role='button']:has-text('Publish')",
                    "div[role='button']:has-text('Share now')",
                    "div[role='button']:has-text('Write something')",
                    "div[aria-label*='Create'][role='button']",
                    "div[aria-label*='Write'][role='button']",
                    "span:has-text('Create post')",
                    "span:has-text('Create a post')",
                    "a[href*='/composer']",
                ]
                if not opened:
                    for sel in classic_selectors:
                        tried_selectors.append(sel)
                        loc = page.locator(sel).first
                        if loc.count() > 0:
                            try:
                                loc.click(timeout=5000)
                                time.sleep(2.0)
                                opened = True
                                notes.append(f"surface=classic_or_suite_modal({sel})")
                                break
                            except Exception:
                                continue

                if opened:
                    page_url = candidate_url
                    break
                if idx < len(candidate_urls) - 1:
                    notes.append(f"composer_not_found_trying_fallback:{candidate_url}")

            is_business_suite = "business.facebook.com" in (page.url or page_url)

            if not opened:
                # Before giving up, try the Page-identity switch playbook. If the
                # browser is signed in but viewing the Page as a visitor, Facebook
                # shows a "Switch Now" (or profile-menu → J. Fortitude) control.
                # Clicking it is a normal browser action; it is NOT a human wall.
                identity_receipt = _ensure_page_identity(page, notes)
                if identity_receipt.get("switched") or identity_receipt.get("management_visible"):
                    # Re-run composer discovery ONCE against classic selectors on
                    # whatever URL Facebook landed us on after the switch.
                    for sel in classic_selectors:
                        try:
                            loc = page.locator(sel).first
                            if loc.count() > 0:
                                loc.click(timeout=5000)
                                time.sleep(2.0)
                                opened = True
                                notes.append(f"surface=post_identity_switch({sel})")
                                break
                        except Exception:
                            continue
                    # Also retry business-suite textbox surface
                    if not opened:
                        for ready_sel in suite_selectors:
                            try:
                                page.wait_for_selector(ready_sel, timeout=4000)
                                opened = True
                                notes.append(f"surface=post_identity_switch_suite({ready_sel})")
                                break
                            except Exception:
                                continue

            if not opened:
                shot = _screenshot_path("composer_not_found")
                try:
                    page.screenshot(path=str(shot))
                except Exception:
                    pass
                # Deep diagnostics for the repair engine: capture what the page
                # actually looked like so the next selector fix is a small edit,
                # not a guessing game.
                diag: dict = {
                    "last_url": None,
                    "page_title": None,
                    "selectors_attempted": tried_selectors,
                    "visible_buttons": [],
                    "visible_headings": [],
                    "login_page_detected": False,
                    "checkpoint_detected": False,
                    "page_identity_switch_attempted": True,
                    "page_identity_switch_receipt": identity_receipt if 'identity_receipt' in locals() else None,
                    "html_len": None,
                }
                try:
                    diag["last_url"] = page.url
                except Exception:
                    pass
                try:
                    diag["page_title"] = page.title()
                except Exception:
                    pass
                try:
                    btns = page.locator("[role='button']").all_text_contents()
                    diag["visible_buttons"] = [b.strip() for b in btns if b and b.strip()][:40]
                except Exception:
                    pass
                try:
                    heads = page.locator("h1, h2, [role='heading']").all_text_contents()
                    diag["visible_headings"] = [h.strip() for h in heads if h and h.strip()][:20]
                except Exception:
                    pass
                try:
                    body_text = (page.content() or "").lower()
                    diag["html_len"] = len(body_text)
                    if any(k in body_text for k in ["log in to facebook", "log into facebook", "sign in to continue"]):
                        diag["login_page_detected"] = True
                    if any(k in (diag.get("last_url") or "") for k in ["/checkpoint", "/login"]):
                        diag["login_page_detected"] = True
                    if any(k in body_text for k in ["security check", "confirm it's you", "verify it's you", "two-factor"]):
                        diag["checkpoint_detected"] = True
                except Exception:
                    pass
                # Distinguish: if the switch was attempted but Page mgmt still not
                # visible, this is a *switch_failed*, not a generic composer miss.
                if 'identity_receipt' in locals() and identity_receipt.get("attempts") \
                        and not identity_receipt.get("management_visible"):
                    result["error"] = "facebook_page_identity_switch_failed"
                else:
                    result["error"] = "composer_not_found"
                result["screenshot_path"] = str(shot)
                result["diagnostics"] = diag
                result["notes"] = notes + [f"final_url={diag.get('last_url')}"]
                _log(result["error"], page_slug=page_slug, url=diag.get("last_url"),
                     title=diag.get("page_title"), login_detected=diag.get("login_page_detected"))
                context.close()
                return result



            time.sleep(1.5)

            # Type the message.
            typed = False
            textbox_selectors = (
                [
                    "div[contenteditable='true'][role='textbox']",
                    "div[contenteditable='true']",
                    "[role='textbox']",
                    "textarea",
                    "div[aria-label*='reate a post'] div[contenteditable='true']",
                    "div[aria-label*=\"hat's on your mind\"] div[contenteditable='true']",
                ]
                if is_business_suite
                else [
                    "div[role='dialog'] div[contenteditable='true'][role='textbox']",
                    "div[contenteditable='true'][role='textbox']",
                ]
            )
            typed_via = None
            for sel in textbox_selectors:
                loc = page.locator(sel).first
                if loc.count() == 0:
                    continue
                try:
                    loc.click(timeout=4000)
                    loc.type(full_message, delay=8, timeout=15000)
                    typed = True; typed_via = f"locator.type({sel})"
                    break
                except Exception:
                    pass
                try:
                    loc.click(timeout=4000)
                    loc.focus()
                    page.keyboard.type(full_message, delay=8)
                    typed = True; typed_via = f"keyboard.type({sel})"
                    break
                except Exception:
                    pass
                try:
                    loc.evaluate(
                        "(el, txt) => { el.focus(); el.innerText = txt; "
                        "el.dispatchEvent(new InputEvent('input', {bubbles:true, data: txt, inputType:'insertText'})); }",
                        full_message,
                    )
                    typed = True; typed_via = f"js.innerText({sel})"
                    break
                except Exception:
                    continue
            if typed and typed_via:
                notes.append(f"typed_via={typed_via}")
            if not typed:
                try:
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                    tb = page.locator("div[contenteditable='true'][role='textbox']").first
                    if tb.count() > 0:
                        tb.click()
                        page.keyboard.type(full_message, delay=10)
                        typed = True
                        notes.append("typed_via=escape_then_keyboard")
                except Exception:
                    pass
            if not typed:
                shot = _screenshot_path("type_failed")
                page.screenshot(path=str(shot))
                result["screenshot_path"] = str(shot)
                result["error"] = "could_not_type_message"
                result["notes"] = notes
                context.close()
                return result

            # Attach media (image or video) if we successfully downloaded one.
            if local_media and local_media.exists():
                try:
                    scope = "div[role='dialog'] " if not is_business_suite else ""
                    file_inputs = page.locator(f"{scope}input[type='file']")
                    if file_inputs.count() == 0:
                        file_inputs = page.locator("input[type='file']")
                    if file_inputs.count() > 0:
                        file_inputs.first.set_input_files(str(local_media))
                        time.sleep(6.0)  # let the upload preview render (videos take longer)
                        notes.append("media_attached")
                    else:
                        notes.append("no_file_input_found_posting_text_only")
                except Exception as e:
                    notes.append(f"media_attach_failed:{e}")

            # BEFORE clicking Post, snapshot the URLs already visible on the
            # page. Later we require a NEW url to appear — otherwise we've
            # scraped a pre-existing pinned/old post and would be lying.
            probe = _message_probe(full_message)
            pre_urls = _visible_post_urls(page)
            notes.append(f"pre_publish_url_count={len(pre_urls)}")

            # Click Post / Publish.
            posted = False
            post_selectors = (
                [
                    "div[aria-label='Publish'][role='button']",
                    "div[role='button']:has-text('Publish')",
                    "div[aria-label='Post'][role='button']",
                    "div[role='button']:has-text('Post')",
                    "button:has-text('Publish')",
                    "button:has-text('Post')",
                ]
                if is_business_suite
                else [
                    "div[role='dialog'] div[aria-label='Post'][role='button']",
                    "div[role='dialog'] div[role='button']:has-text('Post')",
                    "div[aria-label='Post'][role='button']",
                ]
            )
            for sel in post_selectors:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    try:
                        loc.click(timeout=8000)
                        posted = True
                        notes.append(f"submit_clicked({sel})")
                        break
                    except Exception:
                        continue
            if not posted:
                shot = _screenshot_path("post_click_failed")
                page.screenshot(path=str(shot))
                result["screenshot_path"] = str(shot)
                result["error"] = "post_button_not_clickable"
                context.close()
                return result

            # Wait for composer to clear.
            composer_cleared = False
            if is_business_suite:
                time.sleep(8.0)
                for _ in range(60):
                    time.sleep(1.0)
                    try:
                        tb = page.locator("div[contenteditable='true'][role='textbox']").first
                        if tb.count() == 0 or (tb.inner_text() or "").strip() == "":
                            composer_cleared = True
                            break
                    except Exception:
                        composer_cleared = True
                        break
            else:
                for _ in range(45):
                    time.sleep(1.0)
                    if page.locator("div[role='dialog']").count() == 0:
                        composer_cleared = True
                        break
            notes.append(f"composer_cleared={composer_cleared}")
            time.sleep(3.0)

            # PROOF-OF-PUBLISH: require a permalink that wasn't visible before.
            # This is the fix for "Unk said published but nothing appeared."
            post_url: Optional[str] = None
            try:
                for _ in range(15):
                    now_urls = _visible_post_urls(page)
                    fresh = now_urls - pre_urls
                    if fresh:
                        for u in fresh:
                            if "/posts/" in u or "/videos/" in u or "/photos/" in u:
                                post_url = u
                                break
                        post_url = post_url or next(iter(fresh))
                        break
                    time.sleep(2.0)
            except Exception:
                pass

            # Business Suite frequently does not expose the new permalink on the
            # composer route. If the composer cleared, navigate to the public Page
            # and look for a fresh permalink near the exact message text.
            if not post_url and composer_cleared:
                verify_url = VERIFY_PAGE_URLS.get(page_slug)
                if verify_url:
                    try:
                        page.goto(verify_url, wait_until="domcontentloaded", timeout=45000)
                        time.sleep(6.0)
                        for _ in range(10):
                            matched = _visible_post_urls(page, message_probe=probe)
                            fresh = matched - pre_urls
                            if fresh:
                                post_url = sorted(fresh)[0]
                                notes.append("verified_on_public_page_feed")
                                break
                            time.sleep(2.0)
                    except Exception as verify_error:
                        notes.append(f"public_page_verify_failed:{verify_error}")

            page.screenshot(path=str(screenshot_final))
            context.close()

            if not post_url:
                result["ok"] = False
                result["error"] = "publish_unverified_no_new_permalink"
                result["screenshot_path"] = str(screenshot_final)
                result["notes"] = notes + ["refused_to_claim_success_without_proof"]
                _log("publish_unverified", page_slug=page_slug, notes=notes)
                return result

            result["ok"] = True
            result["post_url"] = post_url
            result["screenshot_path"] = str(screenshot_final)
            result["notes"] = notes + [f"verified_new_permalink={post_url}"]
            _log("published", page_slug=page_slug, post_url=post_url, notes=notes)
            return result

    except Exception as e:
        result["error"] = f"unexpected:{e}"
        _log("unexpected_failure", error=str(e))
        return result


def open_signin(url: str = "https://business.facebook.com/", timeout_seconds: int = 600) -> dict:
    """Launch the persistent Chrome profile at `url` headful so the user can
    sign into Facebook / Business Suite. Polls every 5s for the login form to
    disappear, closes early on success, or after `timeout_seconds`.

    Returns {ok, signed_in, url, elapsed_seconds, notes}.
    """
    from playwright.sync_api import sync_playwright  # local import to avoid load cost

    result: dict = {"ok": False, "signed_in": False, "url": url, "notes": []}
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    poll_every = 5
    try:
        with sync_playwright() as p:
            _release_locked_profile(result["notes"])
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={"width": 1400, "height": 900},
                args=_win_browser_args(UNK_CHROMIUM_ARGS),
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            _log("signin_opened", url=url)

            deadline = started + max(60, int(timeout_seconds))
            signed_in = False
            while time.time() < deadline:
                try:
                    login_form_visible = (
                        "login" in page.url
                        or page.locator("input[name='email']").count() > 0
                        or page.locator("input[name='pass']").count() > 0
                    )
                except Exception:
                    login_form_visible = True
                if not login_form_visible:
                    signed_in = True
                    break
                time.sleep(poll_every)

            elapsed = int(time.time() - started)
            try:
                context.close()
            except Exception:
                pass
            result["ok"] = True
            result["signed_in"] = signed_in
            result["elapsed_seconds"] = elapsed
            if not signed_in:
                result["notes"].append("timeout_reached_without_signin")
            _log("signin_closed", signed_in=signed_in, elapsed=elapsed)
            return result
    except Exception as e:
        result["error"] = f"signin_failed:{e}"
        _log("signin_unexpected_failure", error=str(e))
        return result


# --- Instagram / LinkedIn sign-in helpers (share PROFILE_DIR with FB) ------
_PLATFORM_SIGNIN: dict[str, dict] = {
    "instagram": {
        "url": "https://www.instagram.com/accounts/login/",
        "login_indicators": ["input[name='username']", "input[name='password']"],
        "signed_in_indicators": [
            "a[href='/direct/inbox/']",
            "svg[aria-label='Home']",
            "a[href*='/accounts/edit/']",
            "a[href='/explore/']",
        ],
        "signed_in_url_fragments": ["/accounts/onetap", "instagram.com/?", "/direct/", "/explore"],
    },
    "linkedin": {
        "url": "https://www.linkedin.com/login",
        "login_indicators": [
            "input[name='session_key']",
            "input[name='session_password']",
            "input#username",
        ],
        "signed_in_indicators": [
            "a[data-test-global-nav-link='mynetwork']",
            "img.global-nav__me-photo",
            "div.global-nav__me",
        ],
        "signed_in_url_fragments": ["/feed", "/in/", "/mynetwork", "/checkpoint/challenge"],
    },
}


# --- Cross-process profile lock -------------------------------------------
PROFILE_LOCK_FILE = CONFIG_DIR / "browser_profile.lock"


class ProfileLockTimeout(Exception):
    pass


class profile_lock:
    """Cross-process exclusive lock around PROFILE_DIR. Wait rather than run
    two Chromium instances against the same user_data_dir (which corrupts
    cookies + returns the user to /accounts/emailsignup)."""

    def __init__(self, owner: str, timeout_s: int = 300, poll_s: float = 2.0):
        self.owner = owner
        self.timeout_s = timeout_s
        self.poll_s = poll_s
        self.fd = None
        self.acquired = False
        self.waited_s = 0.0
        self.conflict = False

    def __enter__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout_s
        first = True
        while True:
            try:
                fd = os.open(str(PROFILE_LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(fd, f"{self.owner}:{os.getpid()}:{int(time.time())}".encode())
                self.fd = fd
                self.acquired = True
                _log("profile_lock_acquired", owner=self.owner, waited=self.waited_s, had_conflict=self.conflict)
                return self
            except FileExistsError:
                if first:
                    self.conflict = True
                    try:
                        holder = PROFILE_LOCK_FILE.read_text()[:200]
                    except Exception:
                        holder = "?"
                    _log("profile_lock_wait", owner=self.owner, holder=holder)
                    first = False
                # Stale lock reaper: if lock is older than 15 min, break it.
                try:
                    if PROFILE_LOCK_FILE.stat().st_mtime < time.time() - 900:
                        PROFILE_LOCK_FILE.unlink(missing_ok=True)
                        _log("profile_lock_stale_reaped", owner=self.owner)
                        continue
                except Exception:
                    pass
                if time.time() > deadline:
                    raise ProfileLockTimeout(f"profile_locked_timeout owner={self.owner}")
                time.sleep(self.poll_s)
                self.waited_s += self.poll_s

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.fd is not None:
                os.close(self.fd)
        except Exception:
            pass
        try:
            PROFILE_LOCK_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        _log("profile_lock_released", owner=self.owner)
        return False


# --- Instagram / LinkedIn preflight (proof of persisted session) -----------
INSTAGRAM_AUTH_COOKIE = "sessionid"
LINKEDIN_AUTH_COOKIE = "li_at"


def _cookie_summary(cookies: list, auth_name: str) -> dict:
    names: list[str] = []
    for c in cookies or []:
        try:
            names.append(str(c.get("name", "")))
        except Exception:
            continue
    return {
        "cookie_names": sorted(set(n for n in names if n)),
        "cookie_count": len(names),
        f"{auth_name}_present": auth_name in names,
    }


def preflight_platform_auth(platform: str, dwell_seconds: int = 4) -> dict:
    """Launch the persistent profile silently, navigate
    to the platform home, classify auth state, and read cookies. This is what
    the publisher must call BEFORE opening the composer, so we never click
    Create on a signed-out page and mis-classify the result as selector drift.

    Returns:
      {
        ok, platform, url, authenticated, state,
        cookie_names[], cookie_count, sessionid_present|li_at_present,
        notes[], error?
      }
    """
    from playwright.sync_api import sync_playwright

    slug = (platform or "").strip().lower()
    if slug not in ("instagram", "linkedin"):
        return {"ok": False, "error": f"unsupported_platform:{platform}", "platform": slug}

    home_url = "https://www.instagram.com/" if slug == "instagram" else "https://www.linkedin.com/feed/"
    auth_name = INSTAGRAM_AUTH_COOKIE if slug == "instagram" else LINKEDIN_AUTH_COOKIE

    result: dict = {"ok": False, "platform": slug, "notes": [], "profile_dir": str(PROFILE_DIR)}
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    lock = profile_lock(owner=f"preflight_{slug}", timeout_s=180)
    try:
        with lock:
            with sync_playwright() as p:
                _release_locked_profile(result["notes"])
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(PROFILE_DIR),
                    headless=True,
                    viewport={"width": 1200, "height": 800},
                    # A preflight is diagnostic automation, never a request for
                    # human input. Missing auth is returned as a reason code.
                    args=_win_browser_args(UNK_CHROMIUM_ARGS),
                )
                page = context.pages[0] if context.pages else context.new_page()
                try:
                    page.goto(home_url, wait_until="domcontentloaded", timeout=45000)
                except Exception as e:
                    result["notes"].append(f"goto_failed:{e}")
                time.sleep(max(1, int(dwell_seconds)))
                try:
                    url_now = page.url or ""
                except Exception:
                    url_now = ""
                result["url"] = url_now

                # Classify auth state from URL first (authoritative)
                state = "authenticated"
                if slug == "instagram":
                    if "/accounts/login" in url_now:
                        state = "instagram_login_required"
                    elif "/accounts/emailsignup" in url_now or "/accounts/signup" in url_now:
                        state = "instagram_session_not_persisted"
                    elif "/challenge" in url_now or "/checkpoint" in url_now:
                        state = "instagram_checkpoint"
                else:
                    if "/checkpoint/challenge" in url_now or "/checkpoint" in url_now:
                        state = "linkedin_checkpoint"
                    elif "/uas/login" in url_now or "/login" in url_now or "authwall" in url_now:
                        state = "linkedin_login_required"

                cookies = []
                try:
                    cookies = context.cookies()
                except Exception as e:
                    result["notes"].append(f"cookies_read_failed:{e}")
                summary = _cookie_summary(cookies, auth_name)
                result.update(summary)

                # Final authoritative check: auth cookie must be present.
                if state == "authenticated" and not summary[f"{auth_name}_present"]:
                    state = (
                        "instagram_session_not_persisted"
                        if slug == "instagram"
                        else "linkedin_login_required"
                    )
                    result["notes"].append("auth_cookie_missing_despite_url")

                # SELF-HEAL — Jason is already signed in inside his own Chrome.
                # Adopt that session into Unk's profile instead of blocking the
                # queue and asking him to sign in again.
                if state != "authenticated":
                    try:
                        import chrome_cookie_import as _cci

                        domains = (
                            ["instagram.com", "facebook.com"]
                            if slug == "instagram"
                            else ["linkedin.com"]
                        )
                        imported = _cci.import_into_context(context, domains)
                        names = {str(c.get("name", "")) for c in context.cookies()}
                        if auth_name not in names:
                            assisted = _cci.import_via_chrome_clone(p, context, domains)
                            imported["ok"] = imported.get("ok") or assisted.get("ok")
                            imported["injected"] = int(imported.get("injected", 0)) + int(
                                assisted.get("injected", 0)
                            )
                        result["cookie_adoption"] = {
                            "ok": imported.get("ok"),
                            "injected": imported.get("injected", 0),
                            "sources": imported.get("sources", [])[:4],
                        }
                        if imported.get("ok"):
                            try:
                                page.goto(home_url, wait_until="domcontentloaded", timeout=45000)
                                time.sleep(3)
                                url_now = page.url or url_now
                                result["url"] = url_now
                            except Exception as e:
                                result["notes"].append(f"adoption_reload_failed:{e}")
                            try:
                                cookies = context.cookies()
                            except Exception:
                                cookies = []
                            summary = _cookie_summary(cookies, auth_name)
                            result.update(summary)
                            if summary[f"{auth_name}_present"] and "login" not in url_now:
                                state = "authenticated"
                                result["notes"].append("auth_recovered_via_cookie_adoption")
                    except Exception as e:
                        result["notes"].append(f"cookie_adoption_failed:{e}")

                result["state"] = state
                result["authenticated"] = state == "authenticated"

                # Clean shutdown: close pages BEFORE context to avoid profile-lock rot
                try:
                    for pg in list(context.pages):
                        try:
                            pg.close()
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    context.close()
                except Exception:
                    pass
                result["ok"] = True
                _log(f"preflight_{slug}", state=state, url=url_now, cookies=summary["cookie_count"])
                return result
    except ProfileLockTimeout as e:
        result["error"] = str(e)
        result["state"] = "profile_lock_conflict"
        return result
    except Exception as e:
        result["error"] = f"preflight_failed:{e}"
        _log(f"preflight_{slug}_unexpected_failure", error=str(e))
        return result


# --- Google SSO click helper (LinkedIn / Instagram) ------------------------
def _try_google_sso(context, page, google_email: str, notes: list, screenshot_dir) -> dict:
    """Attempt to complete Continue-with-Google on the currently open vendor
    login page. Never types passwords. If an existing Google session tile for
    google_email is present -> click it. Otherwise fills the email input and
    clicks Next; if a password screen appears we STOP and escalate.

    Returns {"clicked": bool, "google_stage": str, "blocked_reason": str|None,
    "screenshot": str|None}."""
    from playwright.sync_api import Page  # noqa: F401
    out = {"clicked": False, "google_stage": "start", "blocked_reason": None, "screenshot": None}
    email = (google_email or "").strip().lower()

    def _snap(tag: str) -> str | None:
        try:
            path = screenshot_dir / f"sso_{tag}_{int(time.time())}.png"
            page.screenshot(path=str(path), full_page=False)
            return str(path)
        except Exception:
            return None

    # 1. Click "Continue with Google" on the vendor page.
    candidates = [
        "button:has-text('Continue with Google')",
        "a:has-text('Continue with Google')",
        "button:has-text('Sign in with Google')",
        "a:has-text('Sign in with Google')",
        "div[role='button']:has-text('Continue with Google')",
        "iframe[src*='accounts.google.com']",  # Google One Tap iframe (IG)
    ]
    started = time.time()
    google_url_seen = False
    while time.time() - started < 25:
        try:
            for sel in candidates:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    if "iframe" in sel:
                        # GSI button lives INSIDE the iframe — click through it
                        # with a frame locator instead of giving up.
                        notes.append("google_gsi_iframe_detected")
                        try:
                            fl = page.frame_locator(sel)
                            for inner in ("div[role='button']", "button", "#container",
                                          "text=Sign in with Google", "text=Continue with"):
                                try:
                                    ib = fl.locator(inner).first
                                    if ib.count() > 0:
                                        ib.click(timeout=4000)
                                        out["clicked"] = True
                                        out["google_stage"] = "clicked_gsi_iframe_button"
                                        break
                                except Exception:
                                    continue
                        except Exception as e:
                            notes.append(f"gsi_iframe_click_failed:{e}")
                        if out["clicked"]:
                            break
                    else:
                        try:
                            loc.click(timeout=4000)
                            out["clicked"] = True
                            out["google_stage"] = "clicked_continue_with_google"
                            break
                        except Exception as e:
                            notes.append(f"sso_click_failed:{sel}:{e}")
        except Exception:
            pass
        if out["clicked"]:
            break
        try:
            if "accounts.google.com" in (page.url or ""):
                google_url_seen = True
                out["google_stage"] = "google_page_reached"
                break
        except Exception:
            pass
        time.sleep(1)

    # Fallback: drive LinkedIn's own Google entry point directly.
    if not out["clicked"] and not google_url_seen:
        try:
            if "linkedin.com" in (page.url or ""):
                page.goto("https://www.linkedin.com/checkpoint/rp/request-password-reset" if False
                          else "https://www.linkedin.com/uas/login?fromSignIn=true",
                          wait_until="domcontentloaded", timeout=45000)
                time.sleep(3)
                for sel in candidates:
                    try:
                        loc = page.locator(sel).first
                        if loc.count() > 0 and loc.is_visible():
                            if "iframe" in sel:
                                fl = page.frame_locator(sel)
                                for inner in ("div[role='button']", "button", "#container"):
                                    try:
                                        ib = fl.locator(inner).first
                                        if ib.count() > 0:
                                            ib.click(timeout=4000)
                                            out["clicked"] = True
                                            break
                                    except Exception:
                                        continue
                            else:
                                loc.click(timeout=4000)
                                out["clicked"] = True
                        if out["clicked"]:
                            out["google_stage"] = "clicked_after_login_page_retry"
                            break
                    except Exception:
                        continue
        except Exception as e:
            notes.append(f"login_page_retry_failed:{e}")

    if not out["clicked"] and not google_url_seen:
        out["blocked_reason"] = "google_sso_button_not_found"
        out["screenshot"] = _snap("no_sso_button")
        return out


    # 2. Wait for accounts.google.com or a popup with it.
    google_page = page
    try:
        # LinkedIn opens Google in the same tab; IG sometimes opens a popup.
        for _ in range(20):
            try:
                if "accounts.google.com" in (page.url or ""):
                    google_page = page
                    break
            except Exception:
                pass
            for pg in list(context.pages):
                try:
                    if "accounts.google.com" in (pg.url or ""):
                        google_page = pg
                        break
                except Exception:
                    continue
            if "accounts.google.com" in (google_page.url or ""):
                break
            time.sleep(1)
    except Exception:
        pass

    if "accounts.google.com" not in (google_page.url or ""):
        out["blocked_reason"] = "google_page_did_not_open"
        out["screenshot"] = _snap("no_google_page")
        return out

    try:
        google_page.bring_to_front()
    except Exception:
        pass

    # 3. Try to click an existing account tile matching email.
    time.sleep(2)
    tile_selectors = [
        f"div[data-identifier='{email}']",
        f"li:has-text('{email}')",
        f"div[role='link']:has-text('{email}')",
        f"[aria-label*='{email}']",
    ]
    tile_clicked = False
    for sel in tile_selectors:
        try:
            loc = google_page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                loc.click(timeout=4000)
                tile_clicked = True
                out["google_stage"] = "account_tile_clicked"
                break
        except Exception:
            continue

    if not tile_clicked:
        # 3b. No tile -> fill the email input.
        try:
            email_input = google_page.locator("input[type='email']").first
            if email_input.count() > 0 and email_input.is_visible():
                email_input.fill(email, timeout=4000)
                out["google_stage"] = "email_filled"
                # Click Next.
                for sel in ["#identifierNext button", "button:has-text('Next')", "button:has-text('Continue')"]:
                    try:
                        b = google_page.locator(sel).first
                        if b.count() > 0 and b.is_visible():
                            b.click(timeout=4000)
                            out["google_stage"] = "email_next_clicked"
                            break
                    except Exception:
                        continue
        except Exception as e:
            notes.append(f"google_email_fill_failed:{e}")

    # 4. Wait briefly — if password / phone-approval / passkey prompt appears
    # WITHOUT auto-completing, escalate. If Google redirects back to vendor,
    # we're done here and the outer poll will confirm the cookie.
    for _ in range(30):
        try:
            u = google_page.url or ""
            if ("accounts.google.com" not in u) and any(
                v in u for v in ["linkedin.com", "instagram.com"]
            ):
                out["google_stage"] = "returned_to_vendor"
                return out
            # Password / 2SV / passkey screens.
            blockers = [
                ("input[type='password']", "google_requires_password"),
                ("text=Use your phone to sign in", "google_requires_phone_approval"),
                ("text=2-Step Verification", "google_requires_2sv"),
                ("text=Use your security key", "google_requires_security_key"),
                ("text=Verify it's you", "google_requires_owner_approval"),
            ]
            for sel, reason in blockers:
                try:
                    if google_page.locator(sel).first.count() > 0:
                        out["blocked_reason"] = reason
                        out["google_stage"] = "blocked_at_google"
                        out["screenshot"] = _snap(reason)
                        return out
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(2)

    # Timed out waiting for redirect; not necessarily blocked — outer loop will
    # decide based on vendor cookie presence.
    out["google_stage"] = "google_wait_timeout"
    out["screenshot"] = _snap("google_wait_timeout")
    return out


# --- Instagram / LinkedIn sign-in helper ------------------------------------
def _li_handle_from_page(page) -> str | None:
    """Best-effort read of the LinkedIn vanity handle the profile is signed
    in as. Returns lowercase handle without slashes, or None."""
    import re as _re
    hrefs: list[str] = []
    for sel in (
        'a.global-nav__me-photo',
        '.global-nav__me a[href*="/in/"]',
        'a[href*="/in/"].global-nav__primary-link-me-menu-trigger',
        '.feed-identity-module a[href*="/in/"]',
        '[data-view-name="identity-welcome-item"] a[href*="/in/"]',
    ):
        try:
            h = page.locator(sel).first.get_attribute("href", timeout=2500)
            if h:
                hrefs.append(h)
        except Exception:
            pass
    # Current LinkedIn UI reveals the member profile only after opening Me.
    if not hrefs:
        for trigger in (
            'button[aria-label="Me"]',
            'button[aria-label^="Me "]',
            '.global-nav__me button',
            '[data-view-name="nav-profile"]',
        ):
            try:
                node = page.locator(trigger).first
                if node.count() > 0:
                    node.click(timeout=3000)
                    time.sleep(1)
                    break
            except Exception:
                continue
        for sel in (
            '.global-nav__me-content a[href*="/in/"]',
            'a[href*="/in/"]:has-text("View Profile")',
            '[role="menu"] a[href*="/in/"]',
        ):
            try:
                h = page.locator(sel).first.get_attribute("href", timeout=2500)
                if h:
                    hrefs.append(h)
                    break
            except Exception:
                pass
    if not hrefs:
        try:
            hrefs.extend(_re.findall(r'"publicIdentifier"\s*:\s*"([A-Za-z0-9\-]+)"', page.content() or "")[:3])
        except Exception:
            pass
    # LinkedIn's current feed no longer exposes /in/... in the rendered nav.
    # Ask its authenticated same-origin identity endpoint instead; this uses
    # the existing browser session and does not require or expose credentials.
    if not hrefs:
        try:
            voyager_handle = page.evaluate("""async () => {
              try {
                const r = await fetch('/voyager/api/me', {
                  credentials: 'include',
                  headers: { 'accept': 'application/vnd.linkedin.normalized+json+2.1' }
                });
                if (!r.ok) return null;
                const data = await r.json();
                const seen = new Set();
                const walk = (value) => {
                  if (!value || typeof value !== 'object' || seen.has(value)) return null;
                  seen.add(value);
                  if (typeof value.publicIdentifier === 'string') return value.publicIdentifier;
                  if (Array.isArray(value)) {
                    for (const item of value) { const hit = walk(item); if (hit) return hit; }
                  } else {
                    for (const item of Object.values(value)) { const hit = walk(item); if (hit) return hit; }
                  }
                  return null;
                };
                return walk(data);
              } catch (_) { return null; }
            }""")
            if isinstance(voyager_handle, str) and voyager_handle:
                hrefs.append(voyager_handle)
        except Exception:
            pass
    # Final authoritative fallback: LinkedIn resolves /in/me to the currently
    # authenticated member's public profile. Preserve the original page URL so
    # the sign-in flow can continue after extracting the redirect target.
    if not hrefs:
        original_url = ""
        try:
            original_url = page.url or ""
            page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
            redirected = page.url or ""
            if "/in/" in redirected and "/in/me" not in redirected.lower():
                hrefs.append(redirected)
        except Exception:
            pass
        finally:
            if original_url:
                try:
                    page.goto(original_url, wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass
    for h in hrefs:
        m = _re.search(r"/in/([A-Za-z0-9\-_%]+)", h) if "/in/" in h else None
        handle = (m.group(1) if m else h).strip("/").lower()
        if handle and handle not in {"me", "feed"}:
            return handle
    return None


def _li_expected_profile_is_owner(page, expected_handle: str) -> bool:
    """Prove the active member owns the expected profile using controls that
    LinkedIn only renders to the profile owner. Merely reaching the public URL
    is never treated as identity proof."""
    expected = (expected_handle or "").strip().strip("/").lower()
    if not expected:
        return False
    try:
        page.goto(f"https://www.linkedin.com/in/{expected}/",
                  wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
    except Exception:
        return False
    owner_selectors = (
        'button[aria-label*="Edit intro"]',
        'button[aria-label*="Edit profile"]',
        'a[href*="/edit/intro/"]',
        '[data-view-name="profile-edit-intro"]',
    )
    for selector in owner_selectors:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def open_signin_platform(platform: str, timeout_seconds: int = 900,
                         sso_provider: str | None = None,
                         sso_email: str | None = None,
                         expected_handle: str | None = None,
                         force_logout: bool = False,
                         interactive: bool = False):


    """Open Unk's persistent Chromium profile at the platform login page,
    bring it to the foreground, poll until authenticated feed is visible,
    THEN dwell 20s, re-navigate to the home URL, read cookies, verify the
    platform auth cookie is present, close pages, close context cleanly.

    signed_in is TRUE only when the auth cookie is confirmed present.
    """
    from playwright.sync_api import sync_playwright

    slug = (platform or "").strip().lower()
    cfg = _PLATFORM_SIGNIN.get(slug)
    result: dict = {"ok": False, "signed_in": False, "platform": slug, "notes": []}
    if not cfg:
        result["error"] = f"unsupported_platform:{platform}"
        return result

    auth_name = INSTAGRAM_AUTH_COOKIE if slug == "instagram" else LINKEDIN_AUTH_COOKIE
    home_url = "https://www.instagram.com/" if slug == "instagram" else "https://www.linkedin.com/feed/"

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    receipts_dir = CONFIG_DIR / "signin_receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    poll_every = 4

    lock = profile_lock(owner=f"signin_{slug}", timeout_s=60)
    try:
        with lock:
            with sync_playwright() as p:
                _release_locked_profile(result["notes"])
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(PROFILE_DIR),
                    headless=not interactive,
                    viewport={"width": 1400, "height": 900},
                    args=_win_browser_args(UNK_CHROMIUM_ARGS, visible_required=bool(interactive)),
                )
                page = context.pages[0] if context.pages else context.new_page()
                want_handle = (expected_handle or "").strip().strip("/").lower() or None
                result["expected_handle"] = want_handle

                # ACCOUNT SWITCH — if the profile is already signed in as the
                # wrong identity, sign it out first so the login page appears.
                if slug == "linkedin" and (want_handle or force_logout):
                    try:
                        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
                        time.sleep(3)
                        current = _li_handle_from_page(page)
                        result["previous_handle"] = current
                        if force_logout or (current and want_handle and current != want_handle):
                            result["notes"].append(f"logging_out_wrong_account:{current}")
                            try:
                                page.goto("https://www.linkedin.com/m/logout/",
                                          wait_until="domcontentloaded", timeout=45000)
                                time.sleep(4)
                            except Exception as e:
                                result["notes"].append(f"logout_nav_failed:{e}")
                            try:
                                context.clear_cookies()
                            except Exception:
                                pass
                            result["logged_out"] = True
                        elif current and want_handle and current == want_handle:
                            result["notes"].append("already_correct_account")
                            try:
                                cookies = context.cookies()
                            except Exception as e:
                                cookies = []
                                result["notes"].append(f"cookies_read_failed:{e}")
                            cookie_summary = _cookie_summary(cookies, auth_name)
                            if cookie_summary[f"{auth_name}_present"]:
                                verified_url = page.url or "https://www.linkedin.com/feed/"
                                close_ts = datetime.now(timezone.utc).isoformat()
                                try:
                                    for pg in list(context.pages):
                                        try:
                                            pg.close()
                                        except Exception:
                                            pass
                                    context.close()
                                except Exception:
                                    pass
                                result.update({
                                    "ok": True,
                                    "signed_in": True,
                                    "signed_in_handle": current,
                                    "handle_matches": True,
                                    "final_url": verified_url,
                                    "profile_dir": str(PROFILE_DIR),
                                    "cookie_count": cookie_summary["cookie_count"],
                                    "cookie_names": cookie_summary["cookie_names"],
                                    f"{auth_name}_present": True,
                                    "auth_cookie_checked": auth_name,
                                    "context_close_timestamp": close_ts,
                                    "verification_mode": "silent_existing_session",
                                })
                                _log("signin_linkedin_silent_session_verified", signed_in_handle=current)
                                return result
                            result["notes"].append("matching_profile_without_auth_cookie")
                    except Exception as e:
                        result["notes"].append(f"switch_precheck_failed:{e}")

                try:
                    page.goto(cfg["url"], wait_until="domcontentloaded", timeout=45000)
                except Exception as e:
                    result["notes"].append(f"initial_goto_failed:{e}")
                try:
                    page.bring_to_front()
                except Exception:
                    pass
                _log(f"signin_opened_{slug}", url=cfg["url"], expected_handle=want_handle)

                # COOKIE ADOPTION — Jason is already signed in inside his own
                # Chrome. Import that session into Unk's profile instead of
                # asking him to log in again in a browser he never opens.
                try:
                    import chrome_cookie_import as _cci

                    domains = ["linkedin.com"] if slug == "linkedin" else ["instagram.com", "facebook.com"]
                    imported = _cci.import_into_context(context, domains)
                    # Chrome 127+ may store the login cookie with app-bound
                    # encryption (v20), which Python/DPAPI cannot decrypt. Let
                    # installed Chrome decrypt a locked snapshot of its own
                    # profile, without closing or modifying Jason's browser.
                    auth_cookie = "li_at" if slug == "linkedin" else "sessionid"
                    imported_names = {
                        str(c.get("name", "")) for c in context.cookies()
                    }
                    if auth_cookie not in imported_names:
                        assisted = _cci.import_via_chrome_clone(p, context, domains)
                        imported["chrome_assisted"] = {
                            "ok": assisted.get("ok"),
                            "injected": assisted.get("injected", 0),
                            "sources": assisted.get("sources", []),
                            "notes": assisted.get("notes", [])[:8],
                        }
                        imported["ok"] = imported.get("ok") or assisted.get("ok")
                        imported["injected"] = int(imported.get("injected", 0)) + int(assisted.get("injected", 0))
                    result["cookie_adoption"] = {
                        "ok": imported.get("ok"),
                        "injected": imported.get("injected", 0),
                        "sources": imported.get("sources", []),
                        "notes": imported.get("notes", [])[:5],
                        "chrome_assisted": imported.get("chrome_assisted"),
                    }
                    if imported.get("ok"):
                        try:
                            page.goto(home_url, wait_until="domcontentloaded", timeout=45000)
                            time.sleep(4)
                        except Exception as e:
                            result["notes"].append(f"adoption_reload_failed:{e}")
                        if slug == "linkedin":
                            adopted = _li_handle_from_page(page)
                            result["adopted_handle"] = adopted
                            if adopted and (not want_handle or adopted == want_handle):
                                result["notes"].append(f"adopted_host_browser_session:{adopted}")
                            elif adopted:
                                result["notes"].append(
                                    f"adopted_wrong_handle:{adopted} expected={want_handle}")
                except Exception as e:
                    result["notes"].append(f"cookie_adoption_failed:{e}")




                # Google-SSO click path (rules: no password typing, escalate
                # to owner-only on password/2SV/phone/CAPTCHA prompts).
                sso_receipt: dict | None = None
                if (sso_provider or "").strip().lower() == "google" and (sso_email or "").strip():
                    sso_receipt = _try_google_sso(
                        context, page, sso_email, result["notes"], receipts_dir,
                    )
                    result["sso"] = sso_receipt
                    if sso_receipt.get("blocked_reason"):
                        result.update({
                            "ok": True,
                            "signed_in": False,
                            "blocked_reason": sso_receipt["blocked_reason"],
                            "screenshot_path": sso_receipt.get("screenshot"),
                            "profile_dir": str(PROFILE_DIR),
                        })
                        try:
                            for pg in list(context.pages):
                                try: pg.close()
                                except Exception: pass
                            context.close()
                        except Exception:
                            pass
                        return result

                deadline = started + max(60, int(timeout_seconds))
                home_reached = False

                while time.time() < deadline:
                    try:
                        url_now = page.url or ""
                        login_visible = any(
                            page.locator(sel).count() > 0 for sel in cfg["login_indicators"]
                        )
                        home_signal = (
                            any(frag in url_now for frag in cfg["signed_in_url_fragments"])
                            or any(page.locator(sel).count() > 0 for sel in cfg["signed_in_indicators"])
                        )
                    except Exception:
                        login_visible, home_signal = True, False
                    if home_signal and not login_visible:
                        home_reached = True
                        break
                    time.sleep(poll_every)

                # Persistence dwell — give the cookie jar time to flush before we
                # navigate + verify.
                cookie_summary = {"cookie_names": [], "cookie_count": 0, f"{auth_name}_present": False}
                final_url = ""
                if home_reached:
                    time.sleep(20)
                    try:
                        page.goto(home_url, wait_until="domcontentloaded", timeout=30000)
                        time.sleep(3)
                    except Exception as e:
                        result["notes"].append(f"reverify_goto_failed:{e}")
                    try:
                        final_url = page.url or ""
                    except Exception:
                        pass
                    try:
                        cookies = context.cookies()
                    except Exception as e:
                        cookies = []
                        result["notes"].append(f"cookies_read_failed:{e}")
                    cookie_summary = _cookie_summary(cookies, auth_name)
                    if slug == "linkedin":
                        got_handle = _li_handle_from_page(page)
                        if not got_handle and want_handle and cookie_summary[f"{auth_name}_present"]:
                            if _li_expected_profile_is_owner(page, want_handle):
                                got_handle = want_handle
                                result["notes"].append("identity_proved_by_owner_only_profile_controls")
                        result["signed_in_handle"] = got_handle
                        if want_handle:
                            result["handle_matches"] = bool(got_handle) and got_handle == want_handle
                            if got_handle and got_handle != want_handle:
                                result["notes"].append(
                                    f"identity_mismatch expected={want_handle} signed_in={got_handle}")

                signed_in = bool(cookie_summary[f"{auth_name}_present"])
                if want_handle and result.get("handle_matches") is False:
                    signed_in = False
                elapsed = int(time.time() - started)


                # Close pages first, then context — do not leave orphan pages.
                try:
                    for pg in list(context.pages):
                        try:
                            pg.close()
                        except Exception:
                            pass
                except Exception:
                    pass
                close_ts = datetime.now(timezone.utc).isoformat()
                try:
                    context.close()
                except Exception:
                    pass

                receipt = {
                    "platform": slug,
                    "signed_in": signed_in,
                    "home_reached_before_verify": home_reached,
                    "final_url": final_url,
                    "elapsed_seconds": elapsed,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context_close_timestamp": close_ts,
                    "profile_dir": str(PROFILE_DIR),
                    "cookie_names": cookie_summary["cookie_names"],
                    "cookie_count": cookie_summary["cookie_count"],
                    f"{auth_name}_present": cookie_summary[f"{auth_name}_present"],
                    "auth_cookie_checked": auth_name,
                }
                receipt_path = receipts_dir / f"{slug}_{int(time.time())}.json"
                try:
                    receipt_path.write_text(json.dumps(receipt, indent=2))
                except Exception:
                    pass

                result.update({
                    "ok": True,
                    "signed_in": signed_in,
                    "elapsed_seconds": elapsed,
                    "final_url": final_url,
                    "receipt_path": str(receipt_path),
                    "profile_dir": str(PROFILE_DIR),
                    "cookie_count": cookie_summary["cookie_count"],
                    "cookie_names": cookie_summary["cookie_names"],
                    f"{auth_name}_present": cookie_summary[f"{auth_name}_present"],
                    "auth_cookie_checked": auth_name,
                    "context_close_timestamp": close_ts,
                })
                if not home_reached:
                    result["notes"].append("timeout_reached_without_home_signal")
                elif not cookie_summary[f"{auth_name}_present"]:
                    result["notes"].append(f"home_reached_but_{auth_name}_missing")
                elif want_handle and result.get("handle_matches") is False:
                    result["notes"].append("authenticated_but_identity_unproven")
                _log(f"signin_closed_{slug}", signed_in=signed_in, elapsed=elapsed,
                     auth_cookie_present=cookie_summary[f"{auth_name}_present"])
                return result
    except ProfileLockTimeout as e:
        result["error"] = str(e)
        result["notes"].append("profile_lock_conflict")
        return result
    except Exception as e:
        result["error"] = f"signin_failed:{e}"
        _log(f"signin_unexpected_failure_{slug}", error=str(e))
        return result


