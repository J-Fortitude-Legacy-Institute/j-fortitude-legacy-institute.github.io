"""
Shared loader for Meta Graph API credentials captured by meta_key_capture.py.

Reads:
  - ~/.unk_companion/meta_media_engine.json  (public config: app_id, page_id)
  - OS keyring under service 'jfortitude_meta_media_engine', OR fallback
    0600 files at ~/.unk_companion/META_*.secret

Public API:
  load_meta_credentials() -> dict | None
  publish_meta_feed(message, link=None) -> dict
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

try:
    import keyring  # type: ignore
except ImportError:
    keyring = None

import requests

SERVICE = "jfortitude_meta_media_engine"
CONFIG_DIR = Path.home() / ".unk_companion"
CONFIG_FILE = CONFIG_DIR / "meta_media_engine.json"
GRAPH_BASE = "https://graph.facebook.com/v20.0"


def _load_secret(name: str) -> Optional[str]:
    if keyring:
        try:
            v = keyring.get_password(SERVICE, name)
            if v:
                return v
        except Exception:
            pass
    fallback = CONFIG_DIR / f"{name}.secret"
    if fallback.exists():
        try:
            return fallback.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return None


def load_meta_credentials() -> Optional[dict]:
    """Return {app_id, page_id, app_secret, page_access_token} or None if
    capture has not been run on this machine."""
    if not CONFIG_FILE.exists():
        return None
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    app_secret = _load_secret("META_APP_SECRET")
    page_token = _load_secret("META_PAGE_ACCESS_TOKEN")
    if not page_token:
        return None
    return {
        "app_id": cfg.get("app_id"),
        "page_id": cfg.get("page_id"),
        "app_secret": app_secret,
        "page_access_token": page_token,
        "secret_store": cfg.get("secret_store"),
    }


def meta_status() -> dict:
    creds = load_meta_credentials()
    if not creds:
        return {"ok": False, "configured": False,
                "error": "meta_not_configured",
                "hint": "Run meta_key_capture.py on this machine first."}
    return {
        "ok": True,
        "configured": True,
        "app_id": creds["app_id"],
        "page_id": creds["page_id"],
        "secret_store": creds["secret_store"],
        "has_app_secret": bool(creds["app_secret"]),
        "has_page_access_token": bool(creds["page_access_token"]),
    }


def publish_meta_feed(message: str, link: Optional[str] = None) -> dict:
    """Publish a text (optionally with link) post to the configured Facebook
    Page via Graph API. Returns {ok, post_id?, error?}."""
    creds = load_meta_credentials()
    if not creds:
        return {"ok": False, "error": "meta_not_configured"}
    page_id = creds["page_id"]
    token = creds["page_access_token"]
    if not page_id or not token:
        return {"ok": False, "error": "missing_page_id_or_token"}
    if not message or not message.strip():
        return {"ok": False, "error": "empty_message"}

    url = f"{GRAPH_BASE}/{page_id}/feed"
    data = {"message": message, "access_token": token}
    if link:
        data["link"] = link
    try:
        r = requests.post(url, data=data, timeout=30)
    except Exception as e:
        return {"ok": False, "error": "request_failed", "detail": str(e)}
    if r.status_code >= 400:
        return {"ok": False, "error": "graph_api_error",
                "status": r.status_code, "body": r.text[:1000]}
    try:
        body = r.json()
    except Exception:
        return {"ok": False, "error": "bad_response", "body": r.text[:1000]}
    return {"ok": True, "post_id": body.get("id"), "raw": body}
