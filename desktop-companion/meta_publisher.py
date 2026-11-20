"""
Meta Publisher — end-to-end Facebook Page publishing for Unk.

Credentials are loaded by meta_credentials.load_meta_credentials() (OS keyring
or 0600 fallback files). Nothing here ever logs secret values.

Capabilities:
  - publish_text(message, link=None)
  - publish_photo(image_path, caption=None, published=True)
  - publish_video(video_path, description=None, title=None)       # standard Page video
  - publish_reel(video_path, description=None)                    # Reels API (resumable)
  - get_post_metrics(post_id)                                     # likes, comments, shares, reach
  - refresh_long_lived_token()                                    # exchange short token for ~60d token

Every call:
  - retries transient errors (HTTP 5xx, 429) with exponential backoff
  - appends a structured JSON line to ~/.unk_companion/meta_publisher.log
  - returns {ok, ...} dict; never raises through to the caller
"""

from __future__ import annotations

import json
import mimetypes
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from meta_credentials import (
    CONFIG_DIR,
    GRAPH_BASE,
    SERVICE,
    load_meta_credentials,
    _load_secret,
)

try:
    import keyring  # type: ignore
except ImportError:
    keyring = None

LOG_FILE = CONFIG_DIR / "meta_publisher.log"
MAX_RETRIES = 3
BACKOFF_BASE = 1.5  # seconds


# ---------------------------------------------------------------------------
# Logging (structured, secrets-free)
# ---------------------------------------------------------------------------

def _log(event: str, **fields) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # logging must never break publishing


def _redact(d: dict) -> dict:
    """Strip access_token / secret values from any dict before logging."""
    bad = {"access_token", "app_secret", "page_access_token", "client_secret"}
    return {k: ("***" if k in bad else v) for k, v in d.items()}


# ---------------------------------------------------------------------------
# HTTP with retries
# ---------------------------------------------------------------------------

def _request(method: str, url: str, *, retry_label: str, **kwargs) -> dict:
    attempt = 0
    last_err: dict = {}
    while attempt < MAX_RETRIES:
        attempt += 1
        try:
            r = requests.request(method, url, timeout=120, **kwargs)
            if r.status_code < 400:
                try:
                    return {"ok": True, "status": r.status_code, "body": r.json()}
                except Exception:
                    return {"ok": True, "status": r.status_code, "body": {"raw": r.text[:500]}}
            # retry 429 / 5xx
            if r.status_code == 429 or r.status_code >= 500:
                last_err = {"status": r.status_code, "body": r.text[:1000]}
                _log("retry", label=retry_label, attempt=attempt, **last_err)
                time.sleep(BACKOFF_BASE ** attempt)
                continue
            return {"ok": False, "error": "graph_api_error",
                    "status": r.status_code, "body": r.text[:1000]}
        except Exception as e:
            last_err = {"detail": str(e)}
            _log("retry_exception", label=retry_label, attempt=attempt, **last_err)
            time.sleep(BACKOFF_BASE ** attempt)
    return {"ok": False, "error": "exhausted_retries", **last_err}


# ---------------------------------------------------------------------------
# Credentials helpers
# ---------------------------------------------------------------------------

def _save_secret(name: str, value: str) -> None:
    if keyring:
        try:
            keyring.set_password(SERVICE, name, value)
            return
        except Exception:
            pass
    CONFIG_DIR.mkdir(exist_ok=True)
    fb = CONFIG_DIR / f"{name}.secret"
    fb.write_text(value, encoding="utf-8")
    try:
        os.chmod(fb, 0o600)
    except Exception:
        pass


def _require_creds() -> Optional[dict]:
    creds = load_meta_credentials()
    if not creds or not creds.get("page_access_token") or not creds.get("page_id"):
        return None
    return creds


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

def refresh_long_lived_token() -> dict:
    """Exchange the current page token for a long-lived (~60d) token.
    Requires app_id + app_secret to be present in storage."""
    creds = _require_creds()
    if not creds:
        return {"ok": False, "error": "meta_not_configured"}
    if not creds.get("app_id") or not creds.get("app_secret"):
        return {"ok": False, "error": "missing_app_credentials",
                "hint": "Re-run meta_key_capture.py and provide App Secret."}
    url = f"{GRAPH_BASE}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": creds["app_id"],
        "client_secret": creds["app_secret"],
        "fb_exchange_token": creds["page_access_token"],
    }
    res = _request("GET", url, retry_label="token_refresh", params=params)
    if not res.get("ok"):
        _log("token_refresh_failed", **_redact(res))
        return res
    new_token = res["body"].get("access_token")
    if not new_token:
        return {"ok": False, "error": "no_token_in_response"}
    _save_secret("META_PAGE_ACCESS_TOKEN", new_token)
    _log("token_refreshed", expires_in=res["body"].get("expires_in"))
    return {"ok": True, "expires_in": res["body"].get("expires_in")}


# ---------------------------------------------------------------------------
# Publishers
# ---------------------------------------------------------------------------

def publish_text(message: str, link: Optional[str] = None) -> dict:
    creds = _require_creds()
    if not creds:
        return {"ok": False, "error": "meta_not_configured"}
    if not message or not message.strip():
        return {"ok": False, "error": "empty_message"}
    url = f"{GRAPH_BASE}/{creds['page_id']}/feed"
    data = {"message": message, "access_token": creds["page_access_token"]}
    if link:
        data["link"] = link
    res = _request("POST", url, retry_label="publish_text", data=data)
    _log("publish_text", ok=res.get("ok"),
         post_id=(res.get("body") or {}).get("id"),
         **({"error": res.get("error"), "status": res.get("status")} if not res.get("ok") else {}))
    if res.get("ok"):
        return {"ok": True, "post_id": res["body"].get("id")}
    return res


def publish_photo(image_path: str, caption: Optional[str] = None,
                  published: bool = True) -> dict:
    creds = _require_creds()
    if not creds:
        return {"ok": False, "error": "meta_not_configured"}
    p = Path(image_path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": "file_not_found", "path": str(p)}
    url = f"{GRAPH_BASE}/{creds['page_id']}/photos"
    data = {
        "access_token": creds["page_access_token"],
        "published": "true" if published else "false",
    }
    if caption:
        data["caption"] = caption
    mime, _ = mimetypes.guess_type(str(p))
    with p.open("rb") as f:
        files = {"source": (p.name, f, mime or "image/jpeg")}
        res = _request("POST", url, retry_label="publish_photo",
                       data=data, files=files)
    _log("publish_photo", ok=res.get("ok"),
         post_id=(res.get("body") or {}).get("post_id") or (res.get("body") or {}).get("id"),
         path=str(p))
    if res.get("ok"):
        b = res["body"]
        return {"ok": True, "post_id": b.get("post_id") or b.get("id"),
                "photo_id": b.get("id")}
    return res


def publish_video(video_path: str, description: Optional[str] = None,
                  title: Optional[str] = None) -> dict:
    """Standard Page video upload (single-request; for ≤1GB the Graph API
    accepts non-resumable POST to /{page-id}/videos)."""
    creds = _require_creds()
    if not creds:
        return {"ok": False, "error": "meta_not_configured"}
    p = Path(video_path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": "file_not_found", "path": str(p)}
    url = f"{GRAPH_BASE}/{creds['page_id']}/videos"
    data = {"access_token": creds["page_access_token"]}
    if description:
        data["description"] = description
    if title:
        data["title"] = title
    mime, _ = mimetypes.guess_type(str(p))
    with p.open("rb") as f:
        files = {"source": (p.name, f, mime or "video/mp4")}
        res = _request("POST", url, retry_label="publish_video",
                       data=data, files=files)
    _log("publish_video", ok=res.get("ok"),
         video_id=(res.get("body") or {}).get("id"), path=str(p))
    if res.get("ok"):
        return {"ok": True, "video_id": res["body"].get("id")}
    return res


def publish_reel(video_path: str, description: Optional[str] = None) -> dict:
    """Reels API — resumable upload in 3 phases: start → upload → finish."""
    creds = _require_creds()
    if not creds:
        return {"ok": False, "error": "meta_not_configured"}
    p = Path(video_path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": "file_not_found", "path": str(p)}
    page_id = creds["page_id"]
    token = creds["page_access_token"]

    # Phase 1: start
    start = _request(
        "POST", f"{GRAPH_BASE}/{page_id}/video_reels",
        retry_label="reel_start",
        data={"upload_phase": "start", "access_token": token},
    )
    if not start.get("ok"):
        _log("publish_reel_start_failed", **_redact(start))
        return start
    video_id = start["body"].get("video_id")
    upload_url = start["body"].get("upload_url")
    if not video_id or not upload_url:
        return {"ok": False, "error": "reel_start_missing_fields", "body": start["body"]}

    # Phase 2: upload via rupload.facebook.com (different host)
    file_size = p.stat().st_size
    with p.open("rb") as f:
        up = _request(
            "POST", upload_url,
            retry_label="reel_upload",
            headers={
                "Authorization": f"OAuth {token}",
                "offset": "0",
                "file_size": str(file_size),
            },
            data=f.read(),
        )
    if not up.get("ok"):
        _log("publish_reel_upload_failed", video_id=video_id, **_redact(up))
        return up

    # Phase 3: finish + publish
    finish = _request(
        "POST", f"{GRAPH_BASE}/{page_id}/video_reels",
        retry_label="reel_finish",
        params={
            "access_token": token,
            "video_id": video_id,
            "upload_phase": "finish",
            "video_state": "PUBLISHED",
            **({"description": description} if description else {}),
        },
    )
    _log("publish_reel", ok=finish.get("ok"), video_id=video_id, path=str(p))
    if finish.get("ok"):
        return {"ok": True, "video_id": video_id, "result": finish["body"]}
    return finish


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def get_post_metrics(post_id: str) -> dict:
    creds = _require_creds()
    if not creds:
        return {"ok": False, "error": "meta_not_configured"}
    token = creds["page_access_token"]
    # Native Reel/video objects reject the Page-post shares field. Do not
    # let unsupported metrics erase otherwise verifiable engagement data.
    summary = _request(
        "GET", f"{GRAPH_BASE}/{post_id}",
        retry_label="post_summary",
        params={
            "access_token": token,
            "fields": "id,created_time,permalink_url,"
                      "likes.summary(true).limit(0),"
                      "comments.summary(true).limit(0)",
        },
    )
    if not summary.get("ok"):
        return summary
    body = summary["body"]
    likes = (body.get("likes") or {}).get("summary", {}).get("total_count", 0)
    comments = (body.get("comments") or {}).get("summary", {}).get("total_count", 0)

    # Query shares separately: Page posts may support it while Reels may
    # return HTTP 400. An unavailable field is UNKNOWN, never a made-up 0.
    shares_res = _request(
        "GET", f"{GRAPH_BASE}/{post_id}",
        retry_label="post_shares_optional",
        params={"access_token": token, "fields": "shares"},
    )
    shares = None
    if shares_res.get("ok"):
        share_count = (shares_res.get("body") or {}).get("shares")
        if isinstance(share_count, dict):
            value = share_count.get("count")
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                shares = value

    # Insights (reach + impressions). Some post types don't expose all metrics;
    # missing metrics return 400 — we soft-fail here.
    insights_res = _request(
        "GET", f"{GRAPH_BASE}/{post_id}/insights",
        retry_label="post_insights",
        params={
            "access_token": token,
            "metric": "post_impressions,post_impressions_unique",
        },
    )
    reach = impressions = None
    if insights_res.get("ok"):
        for item in (insights_res["body"].get("data") or []):
            name = item.get("name")
            values = item.get("values") or [{}]
            v = values[0].get("value")
            if name == "post_impressions":
                impressions = v
            elif name == "post_impressions_unique":
                reach = v

    out = {
        "ok": True,
        "post_id": body.get("id"),
        "permalink_url": body.get("permalink_url"),
        "created_time": body.get("created_time"),
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "reach": reach,
        "impressions": impressions,
    }
    _log("post_metrics", post_id=post_id, likes=likes, comments=comments,
         shares=shares, reach=reach, impressions=impressions)
    return out


# ---------------------------------------------------------------------------
# Recent log tail (for Media Engine dashboard pull)
# ---------------------------------------------------------------------------

def recent_log(limit: int = 50) -> dict:
    if not LOG_FILE.exists():
        return {"ok": True, "entries": []}
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()[-limit:]
        entries = []
        for ln in lines:
            try:
                entries.append(json.loads(ln))
            except Exception:
                continue
        return {"ok": True, "entries": entries}
    except Exception as e:
        return {"ok": False, "error": "log_read_failed", "detail": str(e)}
