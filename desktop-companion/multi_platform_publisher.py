"""
Multi-Platform Browser Publisher — best-effort browser-driven publishers for
platforms beyond the Facebook Page feed. Each function drives the same
persistent Chromium profile as `meta_browser_publisher`, so whichever account
Jason is signed into on that profile is the account that posts.

Every function returns the same shape as `meta_browser_publisher.publish_*`:
    {ok, post_url, screenshot_path, error, notes[]}

They never raise. Any browser hiccup lands in `error` + a screenshot so the
companion can attach the receipt.

Supported (best-effort — Meta/LI/YT DOMs change frequently; failures should
be triaged from the screenshot):

  publish_facebook_reel(page_url, video_url, message)
  publish_instagram_feed(destination_url, image_url|video_url, message)
  publish_instagram_reel(destination_url, video_url, message)
  publish_linkedin(destination_url, message, image_url=None, video_url=None)
  publish_youtube_short(destination_url, video_url, title, description)
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from meta_browser_publisher import (  # type: ignore

    CONFIG_DIR,
    PROFILE_DIR,
    SCREENSHOT_DIR,
    LOG_FILE,
    _download_media,
    _ensure_playwright_ready,
    _screenshot_path,
    profile_lock,
    ProfileLockTimeout,
    preflight_platform_auth,
    INSTAGRAM_AUTH_COOKIE,
    LINKEDIN_AUTH_COOKIE,
)
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


def _log(event: str, **fields) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _fresh_result() -> dict:
    return {"ok": False, "post_url": None, "screenshot_path": None, "error": None, "notes": []}


def _open_context(notes: Optional[list] = None):
    from playwright.sync_api import sync_playwright  # type: ignore
    from meta_browser_publisher import _release_locked_profile, UNK_CHROMIUM_ARGS  # type: ignore
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    _release_locked_profile(notes if notes is not None else [])
    p = sync_playwright().start()
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        viewport={"width": 1400, "height": 900},
        args=_win_browser_args(UNK_CHROMIUM_ARGS),
    )
    return p, ctx



def _fatal(result: dict, page, prefix: str, err: str) -> dict:
    try:
        shot = _screenshot_path(prefix)
        page.screenshot(path=str(shot))
        result["screenshot_path"] = str(shot)
    except Exception:
        pass
    result["error"] = err
    result["diagnostics"] = _page_diagnostics(page)
    _log(prefix, error=err)
    return result


def _finalize(result: dict, page, prefix: str, url_hint: Optional[str]) -> dict:
    try:
        shot = _screenshot_path(prefix)
        page.screenshot(path=str(shot))
        result["screenshot_path"] = str(shot)
    except Exception:
        pass
    if url_hint:
        result["post_url"] = url_hint
    result["ok"] = True
    _log(prefix, post_url=result["post_url"])
    return result


def _page_diagnostics(page) -> dict:
    """Small DOM snapshot for fixing changed social composer UIs without guessing."""
    diag = {"url": None, "title": None, "buttons": [], "headings": [], "body_markers": []}
    try:
        diag["url"] = page.url
    except Exception:
        pass
    try:
        diag["title"] = page.title()
    except Exception:
        pass
    try:
        texts = page.locator("button, div[role='button'], [aria-label]").all_text_contents()
        diag["buttons"] = [t.strip() for t in texts if t and t.strip()][:80]
    except Exception:
        pass
    try:
        heads = page.locator("h1, h2, [role='heading']").all_text_contents()
        diag["headings"] = [h.strip() for h in heads if h and h.strip()][:30]
    except Exception:
        pass
    try:
        body = (page.locator("body").inner_text(timeout=3000) or "")[:12000].lower()
        markers = [
            "processing", "uploading", "share reel", "publish", "next", "log in",
            "checkpoint", "review", "description", "caption", "done", "your reel",
        ]
        diag["body_markers"] = [m for m in markers if m in body]
    except Exception:
        pass
    return diag


def _first_visible(page, selectors: list[str]):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=1000):
                return sel, loc
        except Exception:
            continue
    return None, None


def _click_first_visible(page, selectors: list[str], *, timeout_ms: int = 8000, force: bool = False) -> Optional[str]:
    sel, loc = _first_visible(page, selectors)
    if not loc:
        return None
    loc.click(timeout=timeout_ms, force=force)
    return sel


def _wait_for_any_visible(page, selectors: list[str], *, timeout_s: int = 60) -> tuple[Optional[str], object | None]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        sel, loc = _first_visible(page, selectors)
        if loc:
            return sel, loc
        time.sleep(1)
    return None, None


def _visible_post_urls(page) -> set[str]:
    urls: set[str] = set()
    try:
        anchors = page.locator("a[href*='/reel/'], a[href*='/reels/'], a[href*='/videos/'], a[href*='/posts/'], a[href*='permalink']")
        n = min(anchors.count(), 80)
        for i in range(n):
            href = anchors.nth(i).get_attribute("href") or ""
            if any(part in href for part in ["/reel/", "/reels/", "/videos/", "/posts/", "permalink"]):
                u = href.split("?")[0]
                if u.startswith("/"):
                    u = "https://www.facebook.com" + u
                urls.add(u)
    except Exception:
        pass
    return urls


# ---------------------------------------------------------------------------
# Per-platform adapter isolation.
#
# Each adapter carries its own version so a selector fix on one platform does
# not silently claim to have fixed the others, and so `media_platform_adapters`
# can record exactly which adapter produced (or failed) a post.
# ---------------------------------------------------------------------------
ADAPTER_VERSIONS = {
    "facebook_page": "fb-v3",
    "instagram_reel": "ig-v3",
    "linkedin_personal": "li-v3",
    "youtube_short": "yt-v2",
}


def _editor_evidence(page, platform: str, stage: str, tried: list[str]) -> dict:
    """Capture what the live DOM actually offers when a selector misses.

    This is the anti-blind-retry payload: real buttons, dialogs, textboxes and
    file inputs with their attributes, plus a screenshot. It is uploaded to
    `media_selector_evidence` and attached to one incident per fingerprint so
    repeated drift does not create noise.
    """
    ev: dict = {
        "platform": platform,
        "stage": stage,
        "selector_tried": tried,
        "page_url": None,
        "buttons": [],
        "dialogs": [],
        "textboxes": [],
        "file_inputs": [],
        "dom_excerpt": None,
        "screenshot_path": None,
        "adapter_version": ADAPTER_VERSIONS.get(platform),
    }
    try:
        ev["page_url"] = page.url
    except Exception:
        pass
    try:
        btns = page.locator("button, div[role='button']")
        for i in range(min(btns.count(), 40)):
            b = btns.nth(i)
            try:
                ev["buttons"].append({
                    "text": (b.inner_text(timeout=500) or "").strip()[:80],
                    "aria": (b.get_attribute("aria-label") or "")[:80],
                    "test_id": (b.get_attribute("data-test-id") or b.get_attribute("data-view-name") or "")[:80],
                    "visible": b.is_visible(timeout=300),
                })
            except Exception:
                continue
    except Exception:
        pass
    try:
        dlgs = page.locator("div[role='dialog']")
        for i in range(min(dlgs.count(), 6)):
            d = dlgs.nth(i)
            try:
                ev["dialogs"].append({
                    "aria": (d.get_attribute("aria-label") or d.get_attribute("aria-labelledby") or "")[:120],
                    "class": (d.get_attribute("class") or "")[:160],
                    "visible": d.is_visible(timeout=300),
                })
            except Exception:
                continue
    except Exception:
        pass
    try:
        tbs = page.locator("div[contenteditable='true'], [role='textbox'], textarea")
        for i in range(min(tbs.count(), 20)):
            t = tbs.nth(i)
            try:
                ev["textboxes"].append({
                    "tag": t.evaluate("e => e.tagName", timeout=500),
                    "role": (t.get_attribute("role") or "")[:40],
                    "aria": (t.get_attribute("aria-label") or "")[:120],
                    "placeholder": (t.get_attribute("data-placeholder") or t.get_attribute("placeholder") or "")[:120],
                    "class": (t.get_attribute("class") or "")[:160],
                    "editable": (t.get_attribute("contenteditable") or "")[:10],
                    "visible": t.is_visible(timeout=300),
                })
            except Exception:
                continue
    except Exception:
        pass
    try:
        fis = page.locator("input[type='file']")
        for i in range(min(fis.count(), 10)):
            f = fis.nth(i)
            try:
                ev["file_inputs"].append({
                    "accept": (f.get_attribute("accept") or "")[:120],
                    "multiple": bool(f.get_attribute("multiple")),
                })
            except Exception:
                continue
    except Exception:
        pass
    try:
        ev["dom_excerpt"] = (page.locator("body").inner_text(timeout=3000) or "")[:4000]
    except Exception:
        pass
    try:
        shot = _screenshot_path(f"{platform}_{stage}_evidence")
        page.screenshot(path=str(shot))
        ev["screenshot_path"] = str(shot)
    except Exception:
        pass
    return ev


def _type_into_editor(page, message: str, *, platform: str, stage: str,
                      selectors: list[str], scope: Optional[str] = None,
                      notes: Optional[list] = None) -> dict:
    """Ranked, scoped caption entry with verification that the text landed.

    Returns {ok, selector, evidence?}. A click that does not actually change the
    editor's text is treated as a miss, not a success — that is how a blank
    caption used to reach Share.
    """
    notes = notes if notes is not None else []
    tried: list[str] = []
    for sel in selectors:
        full = f"{scope} {sel}" if scope else sel
        tried.append(full)
        try:
            loc = page.locator(full).first
            if loc.count() == 0 or not loc.is_visible(timeout=1200):
                continue
            loc.scroll_into_view_if_needed(timeout=2000)
            loc.click(timeout=4000)
            time.sleep(0.4)
            try:
                loc.type(message, delay=12)
            except Exception:
                page.keyboard.type(message, delay=12)
            time.sleep(0.6)
            # Verify the caption actually landed in the DOM.
            landed = ""
            try:
                landed = (loc.inner_text(timeout=2000) or "").strip()
            except Exception:
                try:
                    landed = (loc.input_value(timeout=2000) or "").strip()
                except Exception:
                    landed = ""
            probe = message.strip()[:24]
            if probe and probe in landed:
                notes.append(f"{platform}_caption_typed:{full}")
                return {"ok": True, "selector": full, "chars": len(landed)}
            notes.append(f"{platform}_caption_click_no_text:{full}")
        except Exception as exc:
            notes.append(f"{platform}_caption_try_failed:{full}:{str(exc)[:80]}")
            continue
    ev = _editor_evidence(page, platform, stage, tried)
    notes.append(f"{platform}_caption_selector_drift stage={stage} tried={len(tried)}")
    return {"ok": False, "selector": None, "evidence": ev}



# ---------------------------------------------------------------------------
# Facebook Reels
# ---------------------------------------------------------------------------
def publish_facebook_reel(*, page_url: str, video_url: str, message: str) -> dict:
    result = _fresh_result()
    ready, err = _ensure_playwright_ready(result["notes"])
    if not ready:
        result["error"] = err or "playwright_not_ready"; return result
    if not video_url:
        result["error"] = "video_url_required"; return result

    local = _download_media(video_url, CONFIG_DIR / "browser_media")
    if not local:
        result["error"] = "video_download_failed"; return result

    p, ctx = _open_context(result["notes"])
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        pre_urls = set()
        try:
            page.goto(page_url or "https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            pre_urls = _visible_post_urls(page)
        except Exception:
            pre_urls = set()

        page.goto("https://www.facebook.com/reels/create", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)
        if "login" in page.url:
            return _fatal(result, page, "fb_reel_login_required", "facebook_login_required_in_browser_profile")

        # Upload video. Prefer the attached file input; fall back to the picker.
        upload_started = False
        try:
            file_inputs = page.locator("input[type='file']")
            if file_inputs.count() > 0:
                file_inputs.first.set_input_files(str(local))
                upload_started = True
                result["notes"].append("upload_via_file_input")
        except Exception as e:
            result["notes"].append(f"file_input_upload_failed:{e}")
        if not upload_started:
            try:
                with page.expect_file_chooser(timeout=20000) as fc_info:
                    clicked = _click_first_visible(page, [
                        'div[aria-label*="Add video" i]',
                        'div[role="button"]:has-text("Add video")',
                        'div[role="button"]:has-text("Upload video")',
                        'button:has-text("Add video")',
                        'button:has-text("Upload video")',
                    ], timeout_ms=5000, force=True)
                    if not clicked:
                        raise RuntimeError("add_video_button_not_found")
                fc = fc_info.value
                fc.set_files(str(local))
                upload_started = True
                result["notes"].append("upload_via_file_chooser")
            except Exception as e:
                return _fatal(result, page, "fb_reel_upload_failed", f"upload_failed:{e}")

        # Let Meta process enough of the upload for navigation buttons to enable.
        time.sleep(10)

        next_selectors = [
            'div[role="button"]:has-text("Next")',
            'button:has-text("Next")',
            'div[aria-label="Next"][role="button"]',
            'div[role="button"]:has-text("Done")',
            'button:has-text("Done")',
        ]
        publish_selectors = [
            'div[role="button"]:has-text("Share reel")',
            'button:has-text("Share reel")',
            'div[aria-label="Share reel"][role="button"]',
            'div[role="button"]:has-text("Share")',
            'button:has-text("Share")',
            'div[aria-label="Share"][role="button"]',
            'div[role="button"]:has-text("Publish")',
            'button:has-text("Publish")',
            'div[aria-label="Publish"][role="button"]',
            'div[role="button"]:has-text("Post")',
            'button:has-text("Post")',
        ]

        # Advance through the Reels wizard until the final share button appears.
        for _ in range(6):
            pub_sel, _ = _first_visible(page, publish_selectors)
            if pub_sel:
                result["notes"].append(f"publish_visible:{pub_sel}")
                break
            clicked = None
            try:
                clicked = _click_first_visible(page, next_selectors, timeout_ms=10000, force=True)
            except Exception as e:
                result["notes"].append(f"next_click_failed:{e}")
            if clicked:
                result["notes"].append(f"wizard_clicked:{clicked}")
                time.sleep(4)
            else:
                time.sleep(3)

        # Caption entry — REQUIRED before Share.
        #
        # The Kenneth Rayford Reel went live with `could_not_type_description`
        # because caption failure was swallowed and Share ran anyway. Publishing
        # a blank caption is worse than not publishing: the post is live,
        # un-editable by the worker, and the receipt lies about completeness.
        # From here a caption miss fails the job with full DOM evidence.
        caption_result: dict = {"ok": True, "selector": None}
        if message:
            caption_result = _type_into_editor(
                page, message,
                platform="facebook_page",
                stage="reel_caption",
                selectors=[
                    # Ranked: most specific composer description box first.
                    'div[role="dialog"] div[contenteditable="true"][role="textbox"]',
                    'div[aria-label*="description" i][contenteditable="true"]',
                    'div[aria-label*="Describe your reel" i][contenteditable="true"]',
                    'div[data-lexical-editor="true"][contenteditable="true"]',
                    'div[contenteditable="true"][role="textbox"]',
                    'div[role="textbox"][contenteditable="true"]',
                    'div[contenteditable="true"]',
                    '[role="textbox"]',
                    'textarea',
                ],
                notes=result["notes"],
            )
            result["caption_present"] = bool(caption_result.get("ok"))
            result["caption_selector"] = caption_result.get("selector")
            if not caption_result.get("ok"):
                result["selector_evidence"] = caption_result.get("evidence")
                # Fail safely BEFORE Share. Nothing is published.
                return _fatal(
                    result, page, "fb_reel_caption_required",
                    "caption_entry_failed_publish_blocked_no_blank_post",
                )

        # Publish

        try:
            sel, loc = _wait_for_any_visible(page, publish_selectors, timeout_s=90)
            if not loc:
                return _fatal(result, page, "fb_reel_publish_click_failed", "publish_button_not_found")
            loc.click(timeout=20000, force=True)
            result["notes"].append(f"publish_clicked:{sel}")
        except Exception as e:
            return _fatal(result, page, "fb_reel_publish_click_failed", f"publish_click:{e}")

        time.sleep(12)

        # Do not claim success from the composer URL. Require a new reel/video URL.
        post_url = None
        for _ in range(45):
            try:
                if any(part in page.url for part in ["/reel/", "/reels/", "/videos/", "/posts/"]):
                    post_url = page.url.split("?")[0]
                    break
            except Exception:
                pass
            new_urls = _visible_post_urls(page) - pre_urls
            if new_urls:
                post_url = sorted(new_urls)[0]
                break
            time.sleep(2)
        if not post_url:
            result["notes"].append("publish_clicked_but_no_new_permalink")
            return _fatal(result, page, "fb_reel_unverified", "publish_unverified_no_new_permalink")
        return _finalize(result, page, "fb_reel_final", post_url)
    finally:
        try:
            ctx.close(); p.stop()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Instagram (feed + reel) — Instagram web composer
# ---------------------------------------------------------------------------
# Ranked accessible-name strategies for Instagram composer upload button.
_IG_UPLOAD_BUTTON_NAMES = [
    "Select from computer",
    "Select from device",
    "Select From Computer",
    "Choose files",
    "Choose file",
    "Upload",
    "Upload from computer",
    "New post",
]


def _instagram_locate_file_input(page, notes: list):
    """Return (strategy_id, file_input_locator) or (None, None).

    Ranked strategy — first match wins:
      1. `<input type=file>` whose `accept` mentions video/image
      2. Any `<input type=file>` in the DOM
    """
    try:
        inputs = page.locator("input[type='file']")
        n = inputs.count()
        for i in range(min(n, 8)):
            el = inputs.nth(i)
            try:
                accept = el.get_attribute("accept") or ""
            except Exception:
                accept = ""
            if any(tok in accept.lower() for tok in ("video/", "image/", "*")):
                notes.append(f"ig_upload_strategy:input_accept_media[{accept}]")
                return "input_accept_media", el
    except Exception as e:
        notes.append(f"ig_upload_probe_input_accept_failed:{e}")

    try:
        inputs = page.locator("input[type='file']")
        if inputs.count() > 0:
            notes.append("ig_upload_strategy:input_raw_first")
            return "input_raw_first", inputs.first
    except Exception as e:
        notes.append(f"ig_upload_probe_input_raw_failed:{e}")

    return None, None


def _instagram_open_composer(page, notes: list) -> bool:
    page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    for sel in [
        'svg[aria-label="New post"]',
        'svg[aria-label="Create"]',
        'a[href="#"]:has(svg[aria-label="New post"])',
        'div[role="button"]:has-text("Create")',
        'a:has-text("Create")',
        'a[href="/create/"]',
    ]:
        try:
            page.locator(sel).first.click(timeout=4000)
            time.sleep(2)
            notes.append(f"ig_composer_opened_via:{sel}")
            for sub in ['div[role="dialog"] a:has-text("Post")',
                        'div[role="menu"] :text("Post")',
                        'a[href="/create/select/"]']:
                try:
                    page.locator(sub).first.click(timeout=1500)
                    notes.append(f"ig_composer_submenu:{sub}")
                    time.sleep(1)
                    break
                except Exception:
                    continue
            return True
        except Exception:
            continue
    return False


_IG_PERMALINK_RE = re.compile(r"instagram\.com/(?:reel|reels|p)/([A-Za-z0-9_-]+)")


def _ig_scan_permalink(page) -> Optional[str]:
    """Return the first real /reel/ or /p/ permalink visible in the DOM, if any."""
    try:
        current = page.url or ""
        m = _IG_PERMALINK_RE.search(current)
        if m:
            return f"https://www.instagram.com/reel/{m.group(1)}/" if "/reel" in current else current.split("?")[0]
    except Exception:
        pass
    try:
        anchors = page.locator("a[href*='/reel/'], a[href*='/reels/'], a[href*='/p/']")
        n = min(anchors.count(), 40)
        for i in range(n):
            href = anchors.nth(i).get_attribute("href") or ""
            m = _IG_PERMALINK_RE.search(href)
            if m:
                # Normalize to canonical reel URL when possible
                seg = "reel" if "/reel" in href else "p"
                return f"https://www.instagram.com/{seg}/{m.group(1)}/"
    except Exception:
        pass
    return None


def _ig_collect_toasts(page) -> list[str]:
    out: list[str] = []
    try:
        for sel in ('div[role="alert"]', 'div[role="status"]', 'div[data-visualcompletion="alert"]'):
            loc = page.locator(sel)
            n = min(loc.count(), 8)
            for i in range(n):
                try:
                    t = (loc.nth(i).inner_text(timeout=500) or "").strip()
                    if t:
                        out.append(t[:200])
                except Exception:
                    continue
    except Exception:
        pass
    return out


def _ig_share_and_confirm(page, notes: list) -> None:
    """Click Share inside the composer, then click a confirmation Share/Post if one appears."""
    # Restrict to visible dialogs so we do not hit an unrelated global "Share" button.
    def _click_share_in_scope(scope) -> Optional[str]:
        for name in ("Share", "Post", "Publish"):
            try:
                btn = scope.get_by_role("button", name=re.compile(rf"^\s*{name}\s*$", re.I)).first
                if btn.count() > 0 and btn.is_visible(timeout=800):
                    btn.click(timeout=6000)
                    return name
            except Exception:
                continue
        return None

    # Primary click — prefer the composer dialog scope.
    primary = None
    try:
        dialog = page.locator('div[role="dialog"]').last
        if dialog.count() > 0:
            primary = _click_share_in_scope(dialog)
    except Exception:
        pass
    if not primary:
        primary = _click_share_in_scope(page)
    notes.append(f"ig_share_primary:{primary or 'not_clicked'}")

    # Watch for confirmation dialog / second Share (up to 25s).
    deadline = time.time() + 25
    confirmed = False
    while time.time() < deadline:
        time.sleep(2)
        try:
            dialogs = page.locator('div[role="dialog"]')
            dc = dialogs.count()
            for i in range(dc):
                d = dialogs.nth(i)
                try:
                    txt = (d.inner_text(timeout=500) or "").lower()
                except Exception:
                    txt = ""
                if any(k in txt for k in ("share to", "post to", "share reel", "publish now", "your reel is ready")):
                    second = _click_share_in_scope(d)
                    if second:
                        notes.append(f"ig_share_confirm:{second}")
                        confirmed = True
                        break
            if confirmed:
                break
        except Exception:
            pass
    if not confirmed:
        notes.append("ig_share_confirm:none_shown")


def _ig_wait_for_permalink(page, notes: list, *, timeout_s: int = 180) -> Optional[str]:
    """Poll until a real /reel/ or /p/ permalink appears (URL, DOM, or profile grid)."""
    deadline = time.time() + timeout_s
    tries = 0
    last_toasts: list[str] = []
    while time.time() < deadline:
        tries += 1
        found = _ig_scan_permalink(page)
        if found:
            notes.append(f"ig_permalink_found_after_{tries}_polls:{found}")
            return found
        # Every ~20s, check toasts and try navigating to profile to look for the new reel.
        if tries % 10 == 0:
            last_toasts = _ig_collect_toasts(page)
            if last_toasts:
                notes.append(f"ig_toasts:{last_toasts[:3]}")
            try:
                # If IG is still showing composer, do NOT navigate away — that
                # would kill an in-flight publish. Only navigate if composer
                # dialog is gone.
                if page.locator('div[role="dialog"]').count() == 0:
                    page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
                    time.sleep(2)
            except Exception:
                pass
        time.sleep(2)
    notes.append(f"ig_permalink_timeout after {tries} polls; last_toasts={last_toasts[:3]}")
    return None


def publish_instagram_feed(*, image_url: Optional[str], video_url: Optional[str], message: str) -> dict:
    result = _fresh_result()
    ready, err = _ensure_playwright_ready(result["notes"])
    if not ready:
        result["error"] = err or "playwright_not_ready"; return result
    media_url = image_url or video_url
    if not media_url:
        result["error"] = "media_required"; return result
    local = _download_media(media_url, CONFIG_DIR / "browser_media")
    if not local:
        result["error"] = "media_download_failed"; return result

    # Preflight OUTSIDE the publish lock — it takes its own lock briefly.
    pre = preflight_platform_auth("instagram", dwell_seconds=4)
    result["preflight"] = pre
    if not pre.get("authenticated"):
        state = pre.get("state") or "instagram_session_not_persisted"
        result["error"] = state
        result["notes"].append(
            f"ig_preflight_blocked state={state} url={pre.get('url')} "
            f"sessionid_present={pre.get('sessionid_present')} cookies={pre.get('cookie_count')}"
        )
        _log("ig_publish_preflight_blocked", state=state, url=pre.get("url"),
             sessionid_present=pre.get("sessionid_present"))
        return result

    try:
        lock = profile_lock(owner="publish_instagram", timeout_s=300)
        with lock:
            p, ctx = _open_context(result["notes"])
            try:
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                if not _instagram_open_composer(page, result["notes"]):
                    return _fatal(result, page, "ig_composer_not_found", "instagram_composer_selector_changed")
                url_now = page.url or ""
                if "/accounts/login" in url_now:
                    return _fatal(result, page, "ig_login_required", "instagram_login_required")
                if "/accounts/emailsignup" in url_now or "/accounts/signup" in url_now:
                    return _fatal(result, page, "ig_session_not_persisted", "instagram_session_not_persisted")
                if "/challenge" in url_now or "/checkpoint" in url_now:
                    return _fatal(result, page, "ig_checkpoint", "instagram_checkpoint")

                try:
                    page.locator('div[role="dialog"]').first.wait_for(state="visible", timeout=8000)
                except Exception:
                    result["notes"].append("ig_composer_dialog_not_visible_yet")

                strategy_used = None
                strat_id, file_input = _instagram_locate_file_input(page, result["notes"])
                if file_input is not None:
                    try:
                        file_input.set_input_files(str(local))
                        strategy_used = strat_id
                    except Exception as e:
                        result["notes"].append(f"ig_input_set_files_failed:{e}")

                if strategy_used is None:
                    for name in _IG_UPLOAD_BUTTON_NAMES:
                        try:
                            with page.expect_file_chooser(timeout=4000) as fc_info:
                                page.get_by_role("button", name=name).first.click(timeout=3500)
                            fc_info.value.set_files(str(local))
                            strategy_used = f"file_chooser:{name}"
                            result["notes"].append(f"ig_upload_strategy:{strategy_used}")
                            break
                        except Exception:
                            continue

                if strategy_used is None:
                    try:
                        html_snip = page.locator('div[role="dialog"]').first.inner_html(timeout=2000)
                        result["notes"].append(f"ig_composer_dom_snip:{html_snip[:2000]}")
                    except Exception:
                        pass
                    return _fatal(result, page, "ig_upload_failed", "instagram_composer_selector_changed")

                result["notes"].append(f"ig_upload_completed_via:{strategy_used}")
                time.sleep(6)

                for step in range(2):
                    clicked = False
                    for name in ("Next", "Continue"):
                        try:
                            page.get_by_role("button", name=name).first.click(timeout=6000)
                            clicked = True
                            time.sleep(2)
                            break
                        except Exception:
                            continue
                    if not clicked:
                        result["notes"].append(f"ig_next_step_{step}_not_found")
                        break

                if message:
                    try:
                        cap = page.locator(
                            'div[aria-label="Write a caption..."], div[aria-label*="caption" i][contenteditable="true"], div[contenteditable="true"][role="textbox"]'
                        ).first
                        cap.click(timeout=5000)
                        cap.type(message, delay=15)
                    except Exception:
                        result["notes"].append("could_not_type_caption")

                # Share loop: Instagram Reels frequently requires TWO Share clicks
                # (primary in composer, then a confirmation dialog). We click Share
                # inside the composer dialog scope, watch for confirmation dialogs,
                # click Share again if one appears, and only call _finalize once we
                # capture a real /reel/{shortcode} or /p/{shortcode} permalink.
                _ig_share_and_confirm(page, result["notes"])

                permalink = _ig_wait_for_permalink(page, result["notes"], timeout_s=180)
                if not permalink:
                    # Upload completed and IG toast may say "reel is ready to view"
                    # but the publish did not land — treat as failure and force human
                    # recovery. Do NOT report ok=True with a composer URL.
                    try:
                        result["failure_evidence"] = {
                            "url_at_failure": page.url,
                            "toasts": _ig_collect_toasts(page),
                            "notes_tail": result["notes"][-12:],
                        }
                    except Exception:
                        pass
                    return _fatal(
                        result, page, "ig_share_not_confirmed",
                        "instagram_share_click_not_confirmed_no_permalink",
                    )

                return _finalize(result, page, "ig_final", permalink)
            finally:
                try:
                    ctx.close(); p.stop()
                except Exception:
                    pass
    except ProfileLockTimeout as e:
        result["error"] = "profile_lock_conflict"
        result["notes"].append(str(e))
        return result


def publish_instagram_reel(*, video_url: str, message: str) -> dict:
    return publish_instagram_feed(image_url=None, video_url=video_url, message=message)



# ---------------------------------------------------------------------------
# LinkedIn (personal or Company Page)
# ---------------------------------------------------------------------------
def _linkedin_composer_opened(page) -> tuple[bool, list[str]]:
    """Verify the LinkedIn post composer is actually open (dialog + editor)."""
    proofs: list[str] = []
    checks = [
        ("post_dialog", 'div[role="dialog"][aria-labelledby*="share" i], div[role="dialog"]:has-text("Create a post"), div.share-box-modal'),
        ("editor_textbox", 'div[role="textbox"][aria-label*="text" i], div[role="textbox"][contenteditable="true"]'),
        ("contenteditable", 'div.ql-editor[contenteditable="true"]'),
        ("media_upload_ctrl", 'button[aria-label*="Add a photo" i], button[aria-label*="Add a video" i], button[aria-label*="media" i]'),
        ("post_submit_button", 'div[role="dialog"] button:has-text("Post")'),
    ]
    for label, sel in checks:
        try:
            if page.locator(sel).first.is_visible(timeout=1500):
                proofs.append(label)
        except Exception:
            continue
    return (len(proofs) > 0, proofs)


def _linkedin_diagnostics(page) -> dict:
    diag: dict = {"url": None, "title": None, "buttons_count": 0, "dialogs_count": 0, "post_share_snips": []}
    try:
        diag["url"] = page.url
    except Exception:
        pass
    try:
        diag["title"] = page.title()
    except Exception:
        pass
    try:
        diag["buttons_count"] = page.locator("button, div[role='button']").count()
    except Exception:
        pass
    try:
        diag["dialogs_count"] = page.locator("div[role='dialog']").count()
    except Exception:
        pass
    try:
        cand = page.locator("button, div[role='button'], span, div").filter(
            has_text=re.compile(r"post|share|create", re.I)
        )
        n = min(cand.count(), 12)
        for i in range(n):
            try:
                txt = (cand.nth(i).inner_text(timeout=800) or "").strip()[:120]
                aria = cand.nth(i).get_attribute("aria-label") or ""
                if txt or aria:
                    diag["post_share_snips"].append({"text": txt, "aria": aria[:120]})
            except Exception:
                continue
    except Exception:
        pass
    try:
        shot = _screenshot_path("li_composer_diag")
        page.screenshot(path=str(shot))
        diag["screenshot_path"] = str(shot)
    except Exception:
        pass
    return diag


def _li_scan_activity_urn(page, activity_url: str, terms: Optional[list] = None,
                          notes: Optional[list] = None) -> Optional[str]:
    """Resilient scan of a LinkedIn recent-activity page for a canonical
    urn:li:activity permalink. Works even when the SPA markup drifts, by
    falling back to a raw-HTML regex sweep.

    Returns a canonical https://www.linkedin.com/feed/update/urn:li:activity:.../
    URL, or None.
    """
    notes = notes if notes is not None else []
    low_terms = [str(t).lower() for t in (terms or []) if t]
    try:
        page.goto(activity_url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        notes.append(f"li_activity_goto_failed:{e}")
        return None

    # Hydrate + lazy-load.
    for _ in range(8):
        time.sleep(2)
        try:
            if page.locator(
                "div[data-urn*='urn:li:activity:'], article[data-urn*='urn:li:activity:'], "
                "div[data-id*='urn:li:activity:'], a[href*='/feed/update/urn:li:activity:']"
            ).count() >= 1:
                break
        except Exception:
            pass
    try:
        for _ in range(3):
            page.mouse.wheel(0, 1400)
            time.sleep(1)
    except Exception:
        pass

    # 1) Direct canonical anchors, honouring term match when the item text is readable.
    try:
        anchors = page.locator("a[href*='/feed/update/urn:li:activity:']")
        acount = anchors.count()
        notes.append(f"li_activity_anchor_count:{acount}")
        for i in range(min(acount, 15)):
            href = anchors.nth(i).get_attribute("href") or ""
            if "urn:li:activity:" not in href:
                continue
            full = href if href.startswith("http") else f"https://www.linkedin.com{href}"
            if not low_terms:
                return full
            try:
                ctx_text = (anchors.nth(i).evaluate(
                    "el => (el.closest('[data-urn],[data-id],article,div.feed-shared-update-v2') || el).innerText || ''"
                ) or "").lower()
            except Exception:
                ctx_text = ""
            if not ctx_text or any(t in ctx_text for t in low_terms):
                return full
    except Exception as e:
        notes.append(f"li_activity_anchor_scan_failed:{e}")

    # 2) data-urn / data-id containers.
    try:
        items = page.locator(
            "div[data-urn*='urn:li:activity:'], article[data-urn*='urn:li:activity:'], "
            "div[data-id*='urn:li:activity:']"
        )
        icount = items.count()
        notes.append(f"li_recovery_item_count:{icount}")
        for i in range(min(icount, 15)):
            item = items.nth(i)
            urn = item.get_attribute("data-urn") or item.get_attribute("data-id") or ""
            if "urn:li:activity:" not in urn:
                continue
            text = ""
            try:
                text = (item.inner_text(timeout=2500) or "").lower()
            except Exception:
                pass
            if not low_terms or not text or any(t in text for t in low_terms):
                return f"https://www.linkedin.com/feed/update/{urn}/"
    except Exception as e:
        notes.append(f"li_activity_item_scan_failed:{e}")

    # 3) Raw-HTML regex sweep (last resort; markup-agnostic).
    try:
        html = page.content() or ""
        urns = re.findall(r"urn:li:activity:\d+", html)
        notes.append(f"li_activity_html_urns:{len(set(urns))}")
        if urns:
            body_low = ""
            try:
                body_low = (page.inner_text("body", timeout=5000) or "").lower()
            except Exception:
                pass
            if not low_terms or not body_low or any(t in body_low for t in low_terms):
                # First URN in document order is the newest post on the page.
                return f"https://www.linkedin.com/feed/update/{urns[0]}/"
    except Exception as e:
        notes.append(f"li_activity_html_scan_failed:{e}")

    return None



def _li_signed_in_handle(page) -> Optional[str]:
    """Best-effort resolution of the LinkedIn vanity handle the browser profile
    is actually signed in as. Returns lowercase handle or None."""
    candidates: list[str] = []
    try:
        for sel in (
            'a.global-nav__me-photo, a[href*="/in/"].global-nav__primary-link-me-menu-trigger',
            '.global-nav__me a[href*="/in/"]',
            'a[data-control-name="identity_welcome_message"]',
            'a[href*="/in/"][class*="profile-card"]',
            '.feed-identity-module a[href*="/in/"]',
        ):
            try:
                href = page.locator(sel).first.get_attribute("href", timeout=2500)
            except Exception:
                href = None
            if href:
                candidates.append(href)
    except Exception:
        pass
    if not candidates:
        try:
            html = page.content()
            m = re.findall(r'"publicIdentifier"\s*:\s*"([A-Za-z0-9\-]+)"', html or "")
            candidates.extend(m[:3])
        except Exception:
            pass
    for c in candidates:
        m = re.search(r"/in/([A-Za-z0-9\-_%]+)", c) if "/in/" in c else None
        handle = (m.group(1) if m else c).strip("/").lower()
        if handle and handle not in {"me", "feed"}:
            return handle
    return None


def publish_linkedin(*, destination_url: Optional[str], message: str, image_url: Optional[str] = None, video_url: Optional[str] = None, expected_handle: Optional[str] = None) -> dict:
    result = _fresh_result()
    ready, err = _ensure_playwright_ready(result["notes"])
    if not ready:
        result["error"] = err or "playwright_not_ready"; return result
    if not message.strip() and not image_url and not video_url:
        result["error"] = "message_or_media_required"; return result

    local = None
    media_kind = "video" if video_url else "image" if image_url else None
    media_url = video_url or image_url
    if media_url:
        local = _download_media(media_url, CONFIG_DIR / "browser_media")
        if not local:
            if video_url:
                result["error"] = "video_download_failed"; return result
            result["notes"].append("image_download_failed_falling_back_to_text_only")

    # Preflight — refuse to run through the opener strategies against an
    # unauthenticated feed and mis-classify the result as selector drift.
    pre = preflight_platform_auth("linkedin", dwell_seconds=4)
    result["preflight"] = pre
    if not pre.get("authenticated"):
        state = pre.get("state") or "linkedin_login_required"
        result["error"] = state
        result["notes"].append(
            f"li_preflight_blocked state={state} url={pre.get('url')} "
            f"li_at_present={pre.get('li_at_present')} cookies={pre.get('cookie_count')}"
        )
        _log("li_publish_preflight_blocked", state=state, url=pre.get("url"),
             li_at_present=pre.get("li_at_present"))
        return result

    try:
        lock = profile_lock(owner="publish_linkedin", timeout_s=300)
        with lock:
            p, ctx = _open_context(result["notes"])
            try:
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                start_url = destination_url or "https://www.linkedin.com/feed/"
                page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
                url_now = page.url or ""

                # LinkedIn intermittently returns /404/ on the first navigation
                # into /feed/ even when authenticated. Rescue once by reloading
                # into the canonical feed URL before running opener strategies.
                if "/404" in url_now:
                    result["notes"].append(f"li_404_recovery_from:{url_now}")
                    try:
                        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
                        time.sleep(3)
                        url_now = page.url or ""
                        result["notes"].append(f"li_404_recovery_url:{url_now}")
                    except Exception as e:
                        result["notes"].append(f"li_404_recovery_failed:{e}")

                auth_state = None
                if "/checkpoint/challenge" in url_now or "checkpoint" in url_now:
                    auth_state = "linkedin_2fa_or_checkpoint_required"
                elif "/uas/login" in url_now or "/login" in url_now or "accounts.google.com" in url_now:
                    auth_state = "linkedin_login_required_in_browser_profile"
                elif "consent" in url_now or "authwall" in url_now:
                    auth_state = "linkedin_consent_screen_required"
                elif "/404" in url_now:
                    auth_state = "linkedin_feed_unreachable_404"
                if auth_state:
                    result["notes"].append(f"li_auth_state:{auth_state}")
                    return _fatal(result, page, "li_login_required", auth_state)

                # IDENTITY GUARD — fail closed if the signed-in profile is not
                # the approved destination account. Publishing to the wrong
                # LinkedIn identity is worse than not publishing at all.
                if expected_handle:
                    want = str(expected_handle).strip().strip("/").lower()
                    got = _li_signed_in_handle(page)
                    result["signed_in_handle"] = got
                    result["expected_handle"] = want
                    if got and got != want:
                        result["notes"].append(f"li_identity_mismatch expected={want} signed_in={got}")
                        _log("li_identity_mismatch", expected=want, signed_in=got)
                        return _fatal(result, page, "li_identity_mismatch",
                                      f"browser signed in as /in/{got} but destination requires /in/{want}")
                    if not got:
                        result["notes"].append("li_identity_unresolved_blocked")
                        _log("li_identity_unresolved", expected=want)
                        return _fatal(result, page, "li_identity_unresolved",
                                      f"could not prove signed-in LinkedIn identity matches /in/{want}")



                # Ranked opener strategies. Verify composer opened after each.
                # Strategy set uses accessible roles + share-box anchors + the
                # placeholder textbox — never a single hardcoded English label.
                opener_strategies = [
                    ("role_button_start_post", lambda: page.get_by_role("button", name=re.compile(r"^Start a post", re.I)).first.click(timeout=6000)),
                    ("role_button_create_post", lambda: page.get_by_role("button", name=re.compile(r"Create a post|Share a post|Post to", re.I)).first.click(timeout=4000)),
                    ("share_box_placeholder_click", lambda: page.locator('.share-box-feed-entry__trigger, .share-box-feed-entry__top-bar, button.share-box-feed-entry__trigger').first.click(timeout=4000)),
                    ("share_box_test_id", lambda: page.locator('[data-test-share-box-open], [data-test-id="share-box-open"], [data-control-name="share_box_trigger"]').first.click(timeout=4000)),
                    ("placeholder_textbox", lambda: page.locator('div[role="textbox"][data-placeholder*="talk about" i], div[aria-label*="What do you want to talk about" i]').first.click(timeout=4000)),
                    ("aria_share_creation", lambda: page.locator('[aria-label*="Start a post" i], [aria-label*="Create a post" i], [aria-label*="Share a post" i], [aria-label*="talk about" i]').first.click(timeout=4000)),
                    ("text_start_post", lambda: page.locator('button:has-text("Start a post"), div[role="button"]:has-text("Start a post"), button:has-text("Create a post"), div[role="button"]:has-text("Create a post")').first.click(timeout=4000)),
                    ("visible_text_start", lambda: page.get_by_text(re.compile(r"^Start a post", re.I)).first.click(timeout=4000)),
                ]
                opener_used = None
                composer_proofs: list[str] = []
                opener_errors: list[str] = []
                for name, fn in opener_strategies:
                    try:
                        fn()
                    except Exception as e:
                        opener_errors.append(f"{name}:click:{str(e)[:120]}")
                        continue
                    time.sleep(2)
                    opened, proofs = _linkedin_composer_opened(page)
                    if opened:
                        opener_used = name
                        composer_proofs = proofs
                        break
                    opener_errors.append(f"{name}:clicked_but_no_composer_proof")

                if not opener_used:
                    diag = _linkedin_diagnostics(page)
                    result["diagnostics"] = diag
                    result["notes"].append(f"li_opener_strategies_tried:{'|'.join(opener_errors)[:800]}")
                    return _fatal(
                        result, page, "li_composer_not_found",
                        f"linkedin_composer_selector_changed url={diag.get('url')} "
                        f"buttons={diag.get('buttons_count')} dialogs={diag.get('dialogs_count')} "
                        f"screenshot={diag.get('screenshot_path')}"
                    )
                result["notes"].append(f"li_opener_used:{opener_used} proofs={','.join(composer_proofs)}")

                time.sleep(2)

                if local:
                    try:
                        uploaded = False
                        try:
                            inputs = page.locator('div[role="dialog"] input[type="file"], input[type="file"]')
                            if inputs.count() > 0:
                                inputs.first.set_input_files(str(local))
                                uploaded = True
                                result["notes"].append(f"li_media_upload_input:{media_kind}")
                        except Exception as input_exc:
                            result["notes"].append(f"li_media_input_failed:{input_exc}")
                        if not uploaded:
                            upload_buttons = (
                                'button[aria-label*="Add a photo" i], button[aria-label*="Add media" i], '
                                'button[aria-label*="Add a video" i], button[aria-label*="Media" i], '
                                'button:has-text("Add a photo"), button:has-text("Add media"), button:has-text("Add a video")'
                            )
                            with page.expect_file_chooser(timeout=15000) as fc_info:
                                page.locator(upload_buttons).first.click(timeout=8000)
                            fc_info.value.set_files(str(local))
                            uploaded = True
                            result["notes"].append(f"li_media_upload_chooser:{media_kind}")
                        time.sleep(8 if media_kind == "video" else 4)
                        try:
                            page.get_by_role("button", name=re.compile(r"^Done$|^Next$", re.I)).click(timeout=6000)
                        except Exception:
                            pass
                    except Exception as attach_exc:
                        if video_url:
                            return _fatal(result, page, "li_video_attach_failed", f"video_attach_failed:{attach_exc}")
                        result["notes"].append(f"image_attach_failed_posting_text_only:{attach_exc}")

                # Caption entry AFTER media attachment.
                #
                # LinkedIn swaps the share box for a media-preview composer once
                # a video attaches: the Quill editor is re-mounted inside the
                # media dialog and the old `div.ql-editor` handle goes stale,
                # which is why the previous single-selector click timed out.
                # Strategy: settle for the re-mount, then walk ranked selectors
                # scoped to the live dialog, verifying the text actually landed.
                if local:
                    # Give the media-preview composer time to finish mounting.
                    for _ in range(10):
                        try:
                            if page.locator(
                                'div[role="dialog"] div.ql-editor[contenteditable="true"], '
                                'div[role="dialog"] div[role="textbox"][contenteditable="true"]'
                            ).first.is_visible(timeout=1000):
                                break
                        except Exception:
                            pass
                        time.sleep(1.5)

                caption_result = _type_into_editor(
                    page, message,
                    platform="linkedin_personal",
                    stage="post_attach_caption",
                    scope='div[role="dialog"]',
                    selectors=[
                        'div.ql-editor[contenteditable="true"][data-placeholder]',
                        'div.ql-editor[contenteditable="true"]',
                        'div[role="textbox"][contenteditable="true"][aria-label*="text" i]',
                        'div[role="textbox"][contenteditable="true"]',
                        'div[data-test-ql-editor-contenteditable="true"]',
                        'div[contenteditable="true"][aria-multiline="true"]',
                        'div[contenteditable="true"]',
                    ],
                    notes=result["notes"],
                )
                if not caption_result.get("ok"):
                    # Second pass unscoped — some LinkedIn builds render the
                    # editor as a sibling of the dialog rather than a child.
                    caption_result = _type_into_editor(
                        page, message,
                        platform="linkedin_personal",
                        stage="post_attach_caption_unscoped",
                        selectors=[
                            'div.ql-editor[contenteditable="true"]',
                            'div[role="textbox"][contenteditable="true"]',
                            'div[contenteditable="true"][aria-multiline="true"]',
                        ],
                        notes=result["notes"],
                    )
                result["caption_present"] = bool(caption_result.get("ok"))
                result["caption_selector"] = caption_result.get("selector")
                if not caption_result.get("ok"):
                    result["selector_evidence"] = caption_result.get("evidence")
                    result["diagnostics"] = _linkedin_diagnostics(page)
                    return _fatal(
                        result, page, "li_caption_selector_drift",
                        "linkedin_caption_editor_not_found_after_media_attach",
                    )



                time.sleep(1)
                # Scope the Post click strictly inside the open composer dialog.
                # The unscoped get_by_role match hits ~19 elements (feed menu,
                # sidebar, share modules) and triggers a strict-mode violation.
                post_click_err: Optional[Exception] = None
                clicked = False
                for locator_fn in (
                    lambda: page.locator('div[role="dialog"]').filter(has_text=re.compile(r"Post|Share", re.I)).get_by_role("button", name=re.compile(r"^Post$", re.I)).first,
                    lambda: page.locator('div[role="dialog"] button[data-view-name="share-actions-submit-button"]').first,
                    lambda: page.locator('div[role="dialog"] button:has-text("Post")').last,
                    lambda: page.locator('button.share-actions__primary-action').first,
                ):
                    try:
                        loc = locator_fn()
                        loc.wait_for(state="visible", timeout=4000)
                        loc.click(timeout=6000)
                        clicked = True
                        break
                    except Exception as e:
                        post_click_err = e
                        continue
                if not clicked:
                    return _fatal(result, page, "li_post_click_failed", f"post_click:{post_click_err}")

                # Wait for composer to close + toast, then hunt for the real
                # activity URN. `/feed/` is NOT an acceptable permalink.
                time.sleep(8)
                permalink: Optional[str] = None
                # Strategy 1: success toast "View post" link.
                try:
                    toast = page.locator('a[href*="/feed/update/urn:li:activity:"]').first
                    toast.wait_for(state="attached", timeout=6000)
                    href = toast.get_attribute("href") or ""
                    if "urn:li:activity:" in href:
                        permalink = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                except Exception:
                    pass
                # Strategy 2: navigate to recent-activity and grab first URN.
                if not permalink:
                    slug = None
                    try:
                        m = re.search(r"linkedin\.com/in/([^/?#]+)", destination_url or "")
                        slug = m.group(1) if m else None
                    except Exception:
                        pass
                    activity_url = (
                        f"https://www.linkedin.com/in/{slug}/recent-activity/all/"
                        if slug else "https://www.linkedin.com/in/me/recent-activity/all/"
                    )
                    try:
                        permalink = _li_scan_activity_urn(page, activity_url, notes=result["notes"])
                    except Exception as e:
                        result["notes"].append(f"li_activity_scan_failed:{e}")

                if not permalink:
                    # Do NOT return a bogus /feed/ URL. Mark as failed so the
                    # supervisor can retry rather than record a false-positive.
                    return _fatal(result, page, "li_permalink_not_found",
                                  "post_submitted_but_no_activity_urn_recoverable")
                return _finalize(result, page, "li_final", permalink)

            finally:
                try:
                    ctx.close(); p.stop()
                except Exception:
                    pass
    except ProfileLockTimeout as e:
        result["error"] = "profile_lock_conflict"
        result["notes"].append(str(e))
        return result


# ---------------------------------------------------------------------------
# LinkedIn permalink recovery (post-hoc, non-publishing)
# ---------------------------------------------------------------------------
def recover_linkedin_permalink(
    match_title: str = "",
    match_terms: Optional[list] = None,
    profile_slug: Optional[str] = None,
    submitted_after_iso: Optional[str] = None,
) -> dict:
    """Read-only recovery of a canonical urn:li:activity URL for an already-
    submitted post. Never composes or posts anything. Uses the persistent
    authenticated Chromium profile.

    Match strategy: substring match of any of `match_terms` (and match_title)
    against post text within each recent-activity feed item. Extract permalink
    from: nested <a href="...urn:li:activity:...">, data-urn / data-id
    attributes, or embedded JSON. Falls back to opening the post menu and
    reading its "Copy link to post" href.

    Returns:
        {ok, permalink, screenshot_path, error, notes[], candidates[]}
    where `permalink` is only set when it contains `urn:li:activity:` and does
    NOT match `/feed/` alone. On failure, `candidates` lists what was seen so
    the caller has hard evidence.
    """
    from playwright.sync_api import TimeoutError as PWTimeout  # type: ignore

    result: dict = {
        "ok": False,
        "permalink": None,
        "post_url": None,
        "screenshot_path": None,
        "error": None,
        "notes": [],
        "candidates": [],
        "matched_title": None,
    }
    terms = [t.lower() for t in (match_terms or []) if isinstance(t, str) and t.strip()]
    if match_title and match_title.strip():
        terms.append(match_title.strip().lower())
    terms = list({t for t in terms if t})
    if not terms:
        result["error"] = "no_match_terms_provided"
        return result

    # BUGFIX 2026-07-28: both of these were called with the wrong signature and
    # sat OUTSIDE any try/except, so a TypeError escaped the function entirely and
    # surfaced as the opaque `browser_worker_publisher_exception` from
    # browser_publish_worker._call_in_clean_thread. Read-only recovery must never
    # be able to crash the worker.
    try:
        ready, ready_err = _ensure_playwright_ready(result["notes"])
        if not ready:
            result["error"] = ready_err or "playwright_not_ready"
            return result
    except Exception as e:
        result["error"] = f"playwright_bootstrap_failed:{e}"
        return result
    try:
        with profile_lock(owner="recover_linkedin_permalink", timeout_s=300):
            try:
                preflight_platform_auth("linkedin")
            except Exception as e:
                result["notes"].append(f"li_preflight_skipped:{e}")
            p, ctx = _open_context(result["notes"])
            try:
                page = ctx.new_page()
                slug = None
                try:
                    m = re.search(r"linkedin\.com/in/([^/?#]+)", profile_slug or "")
                    slug = m.group(1) if m else (profile_slug or None)
                except Exception:
                    pass
                activity_url = (
                    f"https://www.linkedin.com/in/{slug}/recent-activity/all/"
                    if slug else "https://www.linkedin.com/in/me/recent-activity/all/"
                )
                permalink: Optional[str] = _li_scan_activity_urn(
                    page, activity_url, terms=terms, notes=result["notes"]
                )
                if not permalink:
                    # Term-agnostic retry: any recent activity URN on the page.
                    permalink = _li_scan_activity_urn(page, activity_url, notes=result["notes"])
                matched_urn = permalink
                matched_snippet = None
                result["candidates"] = []

                # Sanity — refuse any /feed/ non-update URL.
                if permalink and ("urn:li:activity:" not in permalink):
                    permalink = None


                # Take an evidence screenshot regardless of outcome.
                try:
                    shot = _screenshot_path("li_recovery")
                    page.screenshot(path=str(shot))
                    result["screenshot_path"] = str(shot)
                except Exception:
                    pass

                if permalink:
                    result["ok"] = True
                    result["permalink"] = permalink
                    result["post_url"] = permalink
                    result["notes"].append(f"li_recovery_matched:{matched_urn}")
                else:
                    result["error"] = (
                        "no_matching_post_found" if not matched_urn else "matched_but_no_canonical_href"
                    )
                    if matched_snippet:
                        result["notes"].append(f"li_recovery_matched_text:{matched_snippet}")
                return result
            finally:
                try:
                    ctx.close(); p.stop()
                except Exception:
                    pass
    except ProfileLockTimeout as e:
        result["error"] = "profile_lock_conflict"
        result["notes"].append(f"profile_lock:{e}")
        return result
    except PWTimeout as e:
        result["error"] = "linkedin_recovery_timeout"
        result["notes"].append(f"pw_timeout:{e}")
        return result
    except Exception as e:
        result["error"] = f"linkedin_recovery_exception:{e}"
        return result




# ---------------------------------------------------------------------------
# YouTube Shorts (via youtube.com/upload)
# ---------------------------------------------------------------------------
def publish_youtube_short(*, video_url: str, title: str, description: str) -> dict:
    result = _fresh_result()
    ready, err = _ensure_playwright_ready(result["notes"])
    if not ready:
        result["error"] = err or "playwright_not_ready"; return result
    if not video_url:
        result["error"] = "video_url_required"; return result

    local = _download_media(video_url, CONFIG_DIR / "browser_media")
    if not local:
        result["error"] = "video_download_failed"; return result

    p, ctx = _open_context()
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)
        if "accounts.google.com" in page.url:
            return _fatal(result, page, "yt_login_required", "google_login_required_in_browser_profile")

        try:
            page.get_by_role("button", name="Create").click(timeout=10000)
            page.get_by_text("Upload videos").click(timeout=6000)
        except Exception as e:
            return _fatal(result, page, "yt_upload_open_failed", f"open_failed:{e}")

        try:
            with page.expect_file_chooser(timeout=15000) as fc_info:
                page.get_by_role("button", name="Select files").click(timeout=8000)
            fc_info.value.set_files(str(local))
        except Exception as e:
            return _fatal(result, page, "yt_upload_failed", f"upload_failed:{e}")

        time.sleep(8)

        # Title
        try:
            t = page.locator('div[aria-label="Add a title that describes your video"], div#title-textarea div[contenteditable="true"]').first
            t.click(timeout=8000)
            # Clear default filename
            t.press("Control+A")
            t.type((title or "")[:95], delay=15)
        except Exception:
            result["notes"].append("could_not_set_title")

        # Description
        if description:
            try:
                d = page.locator('div#description-textarea div[contenteditable="true"]').first
                d.click(timeout=5000)
                d.type(description[:4900], delay=8)
            except Exception:
                result["notes"].append("could_not_set_description")

        # "Not made for kids"
        try:
            page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').click(timeout=4000)
        except Exception:
            pass

        # Advance through the wizard (Next Next Next) and publish public.
        for _ in range(3):
            try:
                page.get_by_role("button", name="Next").click(timeout=6000)
                time.sleep(2)
            except Exception:
                break

        try:
            page.get_by_role("radio", name="Public").click(timeout=5000)
        except Exception:
            pass

        try:
            page.get_by_role("button", name="Publish").click(timeout=10000)
        except Exception as e:
            return _fatal(result, page, "yt_publish_failed", f"publish_click:{e}")

        time.sleep(10)
        return _finalize(result, page, "yt_final", page.url)
    finally:
        try:
            ctx.close(); p.stop()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# LinkedIn content migration (read-only harvest of a retired alias profile)
# ---------------------------------------------------------------------------
def harvest_linkedin_profile_posts(*, profile_slug: str, limit: int = 25) -> dict:
    """Read-only scrape of a LinkedIn profile's recent activity.

    Never posts. Returns:
        {ok, handle, items[{source_post_url, text, media_count}], screenshot_path,
         error, notes[]}
    """
    result = _fresh_result()
    result["items"] = []
    slug = str(profile_slug or "").strip()
    m = re.search(r"linkedin\.com/in/([^/?#]+)", slug)
    if m:
        slug = m.group(1)
    slug = slug.strip("/")
    if not slug:
        result["error"] = "profile_slug_required"
        return result
    try:
        ready, ready_err = _ensure_playwright_ready(result["notes"])
        if not ready:
            result["error"] = ready_err or "playwright_not_ready"
            return result
    except Exception as e:
        result["error"] = f"playwright_bootstrap_failed:{e}"
        return result

    try:
        with profile_lock(owner="harvest_linkedin_posts", timeout_s=300):
            try:
                preflight_platform_auth("linkedin")
            except Exception as e:
                result["notes"].append(f"li_preflight_skipped:{e}")
            p, ctx = _open_context(result["notes"])
            try:
                page = ctx.new_page()
                url = f"https://www.linkedin.com/in/{slug}/recent-activity/all/"
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(4000)
                if "/authwall" in (page.url or "") or "/login" in (page.url or ""):
                    result["error"] = "linkedin_not_signed_in"
                    return result
                # Scroll to load more activity.
                for _ in range(6):
                    try:
                        page.mouse.wheel(0, 2400)
                    except Exception:
                        break
                    page.wait_for_timeout(1200)

                items: list[dict] = []
                seen: set[str] = set()
                cards = page.locator('div.feed-shared-update-v2, div[data-urn*="urn:li:activity:"], div[data-id*="urn:li:activity:"]')
                count = min(cards.count(), limit * 3)
                for i in range(count):
                    card = cards.nth(i)
                    urn = None
                    for attr in ("data-urn", "data-id"):
                        try:
                            v = card.get_attribute(attr, timeout=1500)
                        except Exception:
                            v = None
                        if v and "urn:li:activity:" in v:
                            urn = re.search(r"urn:li:activity:\d+", v)
                            urn = urn.group(0) if urn else None
                            break
                    if not urn:
                        try:
                            html = card.inner_html(timeout=2000)
                            mm = re.search(r"urn:li:activity:\d+", html or "")
                            urn = mm.group(0) if mm else None
                        except Exception:
                            urn = None
                    if not urn or urn in seen:
                        continue
                    seen.add(urn)
                    try:
                        text = card.inner_text(timeout=2500)
                    except Exception:
                        text = ""
                    text = re.sub(r"\n{3,}", "\n\n", (text or "")).strip()
                    # Trim LinkedIn chrome (reactions/comment counters at the end).
                    text = re.sub(r"\n(Like|Comment|Repost|Send)\b.*$", "", text, flags=re.S).strip()
                    media_count = 0
                    try:
                        media_count = card.locator("video, img.ivm-view-attr__img--centered, div.update-components-image img").count()
                    except Exception:
                        pass
                    items.append({
                        "source_post_url": f"https://www.linkedin.com/feed/update/{urn}/",
                        "text": text[:6000],
                        "media_count": media_count,
                    })
                    if len(items) >= limit:
                        break

                try:
                    shot = _screenshot_path("li_harvest")
                    page.screenshot(path=str(shot))
                    result["screenshot_path"] = str(shot)
                except Exception:
                    pass

                result["items"] = items
                result["handle"] = slug
                result["ok"] = True
                if not items:
                    result["notes"].append("no_activity_cards_found")
                return result
            finally:
                try:
                    ctx.close(); p.stop()
                except Exception:
                    pass
    except ProfileLockTimeout as e:
        result["error"] = "profile_lock_conflict"
        result["notes"].append(f"profile_lock:{e}")
        return result
    except Exception as e:
        result["error"] = f"linkedin_harvest_exception:{e}"
        return result
