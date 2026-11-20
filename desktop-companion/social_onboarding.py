"""
Unk Social Account Onboarding (lawful, human-verified)
======================================================

Module: social_account_onboarding

Capabilities:
  - social_platform_status   : report local readiness for a platform
  - social_open_signup       : open the official signup/dev portal in browser
  - social_profile_draft     : save a profile draft locally (handle, bio, links)
  - social_key_capture       : capture API keys interactively into OS keyring
  - social_connection_test   : test a credentialed connection (read-only)
  - social_readiness_report  : roll up readiness across platforms

Hard rules (mirror the Change Gate):
  * Unk only opens official URLs and prompts the human.
  * Unk NEVER bypasses CAPTCHA, phone/email/2FA, or platform security.
  * Unk NEVER creates accounts headlessly.
  * Secrets go to the OS keyring (service per platform). NEVER to disk in
    plaintext outside a 0600 fallback file, and NEVER returned over the wire.
  * The desktop companion reports state (status, api_status, last_test_at)
    — not key material — back to the platform.
"""

from __future__ import annotations

import json
import os
import time
import webbrowser
from pathlib import Path
from typing import Optional

try:
    import keyring  # type: ignore
except Exception:  # pragma: no cover
    keyring = None  # type: ignore

import requests

CONFIG_DIR = Path.home() / ".unk_companion"
SOCIAL_DIR = CONFIG_DIR / "social"
SOCIAL_DIR.mkdir(parents=True, exist_ok=True)

# Platforms Unk can prep. Keep this list narrow — adding a platform is a
# governance decision, not a code shortcut.
PLATFORMS = {
    "instagram": {
        "signup_url": "https://www.instagram.com/accounts/emailsignup/",
        "dev_portal": "https://developers.facebook.com/apps/",
        "service": "jfortitude_social_instagram",
        "key_fields": ["IG_USER_ID", "IG_LONG_LIVED_TOKEN"],
        "test_url_tmpl": "https://graph.facebook.com/v20.0/{IG_USER_ID}?fields=username&access_token={IG_LONG_LIVED_TOKEN}",
        "needs_review_note": "Instagram Graph API requires a connected FB Page and Business/Creator account.",
    },
    "threads": {
        "signup_url": "https://www.threads.net/",
        "dev_portal": "https://developers.facebook.com/docs/threads",
        "service": "jfortitude_social_threads",
        "key_fields": ["THREADS_USER_ID", "THREADS_ACCESS_TOKEN"],
        "test_url_tmpl": "https://graph.threads.net/v1.0/{THREADS_USER_ID}?fields=username&access_token={THREADS_ACCESS_TOKEN}",
        "needs_review_note": "Threads API is on a separate review track.",
    },
    "youtube": {
        "signup_url": "https://www.youtube.com/create_channel",
        "dev_portal": "https://console.cloud.google.com/apis/library/youtube.googleapis.com",
        "service": "jfortitude_social_youtube",
        "key_fields": ["YOUTUBE_OAUTH_CLIENT_ID", "YOUTUBE_OAUTH_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"],
        "test_url_tmpl": None,  # OAuth refresh test, handled in code
        "needs_review_note": "YouTube Data API requires Google Cloud project + OAuth consent screen.",
    },
    "linkedin": {
        "signup_url": "https://www.linkedin.com/signup",
        "dev_portal": "https://www.linkedin.com/developers/apps",
        "service": "jfortitude_social_linkedin",
        "key_fields": ["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN"],
        "test_url_tmpl": "https://api.linkedin.com/v2/userinfo",
        "needs_review_note": "Marketing APIs require LinkedIn product review.",
    },
    "tiktok": {
        "signup_url": "https://www.tiktok.com/signup",
        "dev_portal": "https://developers.tiktok.com/apps",
        "service": "jfortitude_social_tiktok",
        "key_fields": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN"],
        "test_url_tmpl": "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name",
        "needs_review_note": "TikTok Content Posting API requires app review before autopilot publishing.",
    },
}


def _profile_path(platform: str) -> Path:
    return SOCIAL_DIR / f"{platform}.profile.json"


def _load_profile(platform: str) -> dict:
    p = _profile_path(platform)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_profile(platform: str, data: dict) -> None:
    p = _profile_path(platform)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass


def _save_secret(service: str, name: str, value: str) -> str:
    if keyring:
        try:
            keyring.set_password(service, name, value)
            return "system_keyring"
        except Exception:
            pass
    fb = CONFIG_DIR / f"{service}.{name}.secret"
    fb.write_text(value, encoding="utf-8")
    try:
        os.chmod(fb, 0o600)
    except Exception:
        pass
    return "local_600_file"


def _load_secret(service: str, name: str) -> Optional[str]:
    if keyring:
        try:
            v = keyring.get_password(service, name)
            if v:
                return v
        except Exception:
            pass
    fb = CONFIG_DIR / f"{service}.{name}.secret"
    if fb.exists():
        try:
            return fb.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return None


def _has_all_keys(platform: str) -> bool:
    spec = PLATFORMS[platform]
    return all(_load_secret(spec["service"], k) for k in spec["key_fields"])


# ---------------------------------------------------------------------------
# Capability handlers
# ---------------------------------------------------------------------------

def social_platform_status(payload: dict) -> dict:
    platform = (payload.get("platform") or "").lower()
    if platform not in PLATFORMS:
        return {"ok": False, "error": "unknown_platform",
                "supported": sorted(PLATFORMS.keys())}
    spec = PLATFORMS[platform]
    profile = _load_profile(platform)
    has_keys = _has_all_keys(platform)
    return {
        "ok": True,
        "platform": platform,
        "profile": profile,
        "signup_url": spec["signup_url"],
        "dev_portal": spec["dev_portal"],
        "key_store_name": spec["service"],
        "required_key_fields": spec["key_fields"],
        "has_all_keys": has_keys,
        "api_status": "keys_captured" if has_keys else "no_keys",
        "needs_review_note": spec["needs_review_note"],
    }


def social_open_signup(payload: dict) -> dict:
    platform = (payload.get("platform") or "").lower()
    target = payload.get("target", "signup")  # 'signup' | 'dev_portal'
    if platform not in PLATFORMS:
        return {"ok": False, "error": "unknown_platform"}
    spec = PLATFORMS[platform]
    url = spec["dev_portal"] if target == "dev_portal" else spec["signup_url"]
    try:
        webbrowser.open(url)
    except Exception as e:
        return {"ok": False, "error": "browser_open_failed", "detail": str(e), "url": url}
    return {"ok": True, "platform": platform, "opened_url": url, "target": target,
            "note": "Human must complete signup, phone/email, 2FA, CAPTCHA. Unk does not bypass these."}


def social_profile_draft(payload: dict) -> dict:
    platform = (payload.get("platform") or "").lower()
    if platform not in PLATFORMS:
        return {"ok": False, "error": "unknown_platform"}
    allowed = {"handle", "display_name", "bio", "website", "contact_email",
               "category", "linked_page_id", "notes"}
    draft = _load_profile(platform)
    incoming = payload.get("fields") or {}
    for k, v in incoming.items():
        if k in allowed and isinstance(v, (str, int, float, bool)):
            draft[k] = v
    draft["_updated_at"] = time.time()
    _save_profile(platform, draft)
    return {"ok": True, "platform": platform, "profile": draft,
            "saved_to": str(_profile_path(platform))}


def social_key_capture(payload: dict) -> dict:
    """
    Capture one or more keys into the OS keyring.

    payload = { platform, keys: { FIELD_NAME: "value", ... } }

    Values are stored under PLATFORMS[platform]["service"]. The response NEVER
    echoes the values back — only field names and the store used.
    """
    platform = (payload.get("platform") or "").lower()
    if platform not in PLATFORMS:
        return {"ok": False, "error": "unknown_platform"}
    spec = PLATFORMS[platform]
    keys = payload.get("keys") or {}
    if not isinstance(keys, dict) or not keys:
        return {"ok": False, "error": "missing_keys"}
    saved = []
    rejected = []
    store_used = None
    for field, value in keys.items():
        if field not in spec["key_fields"]:
            rejected.append({"field": field, "reason": "not_a_recognized_key_field"})
            continue
        if not isinstance(value, str) or len(value) < 4:
            rejected.append({"field": field, "reason": "value_too_short_or_not_string"})
            continue
        store_used = _save_secret(spec["service"], field, value)
        saved.append(field)
    return {
        "ok": bool(saved),
        "platform": platform,
        "saved_fields": saved,        # names only
        "rejected": rejected,
        "key_store_name": spec["service"],
        "store_used": store_used,
        "all_required_present": _has_all_keys(platform),
    }


def social_connection_test(payload: dict) -> dict:
    """Read-only test that the captured credentials can authenticate."""
    platform = (payload.get("platform") or "").lower()
    if platform not in PLATFORMS:
        return {"ok": False, "error": "unknown_platform"}
    spec = PLATFORMS[platform]
    if not _has_all_keys(platform):
        return {"ok": False, "platform": platform, "api_status": "no_keys",
                "missing": [k for k in spec["key_fields"] if not _load_secret(spec["service"], k)]}

    creds = {k: _load_secret(spec["service"], k) or "" for k in spec["key_fields"]}

    # YouTube: refresh-token round trip
    if platform == "youtube":
        try:
            r = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": creds["YOUTUBE_OAUTH_CLIENT_ID"],
                    "client_secret": creds["YOUTUBE_OAUTH_CLIENT_SECRET"],
                    "refresh_token": creds["YOUTUBE_REFRESH_TOKEN"],
                    "grant_type": "refresh_token",
                },
                timeout=20,
            )
            ok = r.status_code == 200 and "access_token" in r.text
            return {"ok": ok, "platform": platform,
                    "api_status": "tested_ok" if ok else "tested_failed",
                    "status": r.status_code, "body_snippet": r.text[:300]}
        except Exception as e:
            return {"ok": False, "platform": platform, "api_status": "tested_failed",
                    "error": "request_failed", "detail": str(e)}

    url_tmpl = spec.get("test_url_tmpl")
    if not url_tmpl:
        return {"ok": False, "platform": platform, "api_status": "needs_review",
                "error": "no_test_endpoint_configured"}

    headers = {}
    if platform == "linkedin":
        headers["Authorization"] = f"Bearer {creds.get('LINKEDIN_ACCESS_TOKEN','')}"
        url = url_tmpl
    elif platform == "tiktok":
        headers["Authorization"] = f"Bearer {creds.get('TIKTOK_ACCESS_TOKEN','')}"
        url = url_tmpl
    else:
        try:
            url = url_tmpl.format(**creds)
        except KeyError as e:
            return {"ok": False, "platform": platform, "api_status": "tested_failed",
                    "error": "missing_substitution_field", "detail": str(e)}

    try:
        r = requests.get(url, headers=headers, timeout=20)
    except Exception as e:
        return {"ok": False, "platform": platform, "api_status": "tested_failed",
                "error": "request_failed", "detail": str(e)}

    ok = 200 <= r.status_code < 300
    return {
        "ok": ok,
        "platform": platform,
        "status": r.status_code,
        "api_status": "tested_ok" if ok else "tested_failed",
        "body_snippet": r.text[:400],
    }


def social_readiness_report(payload: dict) -> dict:
    """Roll up local readiness for every platform — no secrets, just state."""
    out = []
    for platform in PLATFORMS:
        s = social_platform_status({"platform": platform})
        out.append({
            "platform": platform,
            "handle": s.get("profile", {}).get("handle"),
            "profile_url": s.get("profile", {}).get("website"),
            "has_all_keys": s.get("has_all_keys"),
            "api_status": s.get("api_status"),
            "key_store_name": s.get("key_store_name"),
            "needs_review_note": s.get("needs_review_note"),
        })
    return {"ok": True, "platforms": out,
            "rule": "Unk prepares + tests. Jason completes human verification."}


# ---------------------------------------------------------------------------
# Facebook Page discovery (Page-level publishing destinations)
# ---------------------------------------------------------------------------
#
# Doctrine: Meta policy is one personal identity per person. Unk NEVER posts
# from personal profiles. We discover the Pages the user administers under
# their personal profile and treat each Page as its own publishing
# destination. Personal profile = auth only.

FB_PAGES_SERVICE = "jfortitude_fb_pages"
FB_USER_TOKEN_SERVICE = "jfortitude_meta"  # field: FB_USER_ACCESS_TOKEN
FB_USER_TOKEN_FIELD = "FB_USER_ACCESS_TOKEN"


def _fb_user_token(payload: dict) -> Optional[str]:
    return (
        payload.get("fb_user_token")
        or _load_secret(FB_USER_TOKEN_SERVICE, FB_USER_TOKEN_FIELD)
        or os.environ.get("FB_USER_ACCESS_TOKEN")
    )


def _post_pages_to_cloud(supabase_url: str, anon_key: str, body: dict) -> dict:
    """POST page metadata (no tokens) to the social-pages-sync edge function."""
    try:
        r = requests.post(
            f"{supabase_url}/functions/v1/social-pages-sync",
            headers={
                "Authorization": f"Bearer {anon_key}",
                "apikey": anon_key,
                "Content-Type": "application/json",
            },
            data=json.dumps(body),
            timeout=30,
        )
        return {"status": r.status_code, "body": r.json() if "json" in r.headers.get("content-type", "") else r.text[:400]}
    except Exception as e:
        return {"status": 0, "error": str(e)}


def social_pages_discover(payload: dict) -> dict:
    """
    Discover Facebook Pages this user administers, capture each Page Access
    Token to the local keyring, and register the Page (metadata only) with
    the cloud.

    payload = {
      fb_user_token?: str,
      supabase_url: str,
      supabase_anon_key: str,
      account_id?: str,        # social_platform_accounts.id (the admin profile)
      mark_primary?: str,      # page_external_id to flag as the default Page
    }

    Personal profile data is never registered. Only Pages are.
    """
    token = _fb_user_token(payload)
    if not token:
        return {"ok": False, "error": "missing_fb_user_token",
                "hint": "Capture FB_USER_ACCESS_TOKEN via social_key_capture "
                        "or pass fb_user_token in payload."}
    supabase_url = payload.get("supabase_url")
    anon_key = payload.get("supabase_anon_key")
    if not supabase_url or not anon_key:
        return {"ok": False, "error": "missing_supabase_endpoint"}

    try:
        r = requests.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={"fields": "id,name,category,tasks,access_token", "access_token": token},
            timeout=30,
        )
    except Exception as e:
        return {"ok": False, "error": "graph_request_failed", "detail": str(e)}
    if r.status_code != 200:
        return {"ok": False, "error": "graph_error",
                "status": r.status_code, "body_snippet": r.text[:400]}

    data = r.json().get("data", [])
    pages_meta = []
    saved_tokens = 0
    mark_primary = (payload.get("mark_primary") or "").strip()
    for p in data:
        page_id = p.get("id")
        page_token = p.get("access_token")
        if not page_id or not page_token:
            continue
        _save_secret(FB_PAGES_SERVICE, f"PAGE_TOKEN_{page_id}", page_token)
        saved_tokens += 1
        pages_meta.append({
            "page_external_id": page_id,
            "page_name": p.get("name"),
            "page_category": p.get("category"),
            "page_url": f"https://facebook.com/{page_id}",
            "role": ",".join(p.get("tasks", []) or []),
            "is_primary": bool(mark_primary) and mark_primary == page_id,
            "api_status": "token_captured",
            "key_store_name": f"{FB_PAGES_SERVICE}:PAGE_TOKEN_{page_id}",
        })

    if not pages_meta:
        return {"ok": False, "error": "no_pages_found",
                "hint": "Personal profile has no Pages, or token is missing pages_show_list scope."}

    cloud = _post_pages_to_cloud(supabase_url, anon_key, {
        "mode": "register",
        "platform": "facebook",
        "account_id": payload.get("account_id"),
        "pages": pages_meta,
    })

    return {
        "ok": cloud.get("status") == 200,
        "discovered": len(pages_meta),
        "tokens_saved_to_keyring": saved_tokens,
        "registered_in_cloud": cloud,
        "pages": [{"page_external_id": p["page_external_id"], "page_name": p["page_name"]}
                  for p in pages_meta],
        "rule": "Personal profile is auth-only. Publishing happens at Page level.",
    }


def social_pages_test(payload: dict) -> dict:
    """
    Read-only test for one Page's stored access token.
    payload = { page_external_id, supabase_url?, supabase_anon_key? }
    """
    page_id = (payload.get("page_external_id") or "").strip()
    if not page_id:
        return {"ok": False, "error": "missing_page_external_id"}
    token = _load_secret(FB_PAGES_SERVICE, f"PAGE_TOKEN_{page_id}")
    if not token:
        return {"ok": False, "page_external_id": page_id,
                "api_status": "no_token",
                "error": "page_token_not_in_keyring"}
    try:
        r = requests.get(
            f"https://graph.facebook.com/v20.0/{page_id}",
            params={"fields": "id,name,fan_count,category", "access_token": token},
            timeout=20,
        )
    except Exception as e:
        return {"ok": False, "page_external_id": page_id,
                "api_status": "tested_failed", "error": str(e)}
    ok = r.status_code == 200
    body = r.json() if ok else r.text[:300]
    out = {
        "ok": ok,
        "page_external_id": page_id,
        "api_status": "tested_ok" if ok else "tested_failed",
        "status": r.status_code,
        "body": body,
    }
    # Echo result to cloud if endpoint provided
    supabase_url = payload.get("supabase_url")
    anon_key = payload.get("supabase_anon_key")
    if supabase_url and anon_key:
        _post_pages_to_cloud(supabase_url, anon_key, {
            "mode": "status",
            "platform": "facebook",
            "pages": [{
                "page_external_id": page_id,
                "api_status": out["api_status"],
                "last_test_result": {"status": r.status_code,
                                     "snippet": str(body)[:300]},
            }],
        })
    return out
