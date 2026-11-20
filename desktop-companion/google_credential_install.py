"""Safely mint and install a Google Drive credential into Project K.

The private key exists only in memory and the HTTPS request body. Never print
provider responses, private key values, or a plaintext backup file. The
installer requires an explicit acknowledgment from the authenticated Edge API.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests  # type: ignore

from google_credential_provision import provision  # type: ignore
from unk_companion import (  # type: ignore
    FUNCTIONS_BASE,
    SUPABASE_ANON_KEY,
    load_credentials,
)

PROJECT_ID = "jfli-media-runtime"
SERVICE_ACCOUNT_ID = "jfli-drive-reader"
CREDENTIAL_KEY = "GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON"
SAFE_BLOCKERS = {
    "login_required", "mfa_required", "consent_required", "billing_required",
    "tos_required", "selector_drift", "playwright_not_ready", "project_create_failed",
    "service_account_create_failed", "key_create_failed", "key_decode_failed",
    "console_api_unavailable", "unauthorized", "invalid_json",
    "credential_key_not_allowed", "value_missing_or_too_short",
    "service_account_json_missing_fields", "service_account_json_invalid",
}


def install_provisioned(receipt: dict) -> dict:
    """Install once, returning only a nonsecret receipt suitable for Unk's queue."""
    credential = receipt.pop("credential_json", None)
    summary = receipt.get("credential_summary") or {}
    if not isinstance(summary, dict):
        summary = {}
    base = {
        "ok": False,
        "stage": "install",
        "client_email": summary.get("client_email"),
        "project_id": summary.get("project_id"),
        "server_receipt_confirmed": False,
        "human_followup": receipt.get("human_followup"),
    }
    if not receipt.get("ok") or not isinstance(credential, str) or not credential:
        reason = receipt.get("blocker_reason_code")
        return {
            **base, "stage": "mint",
            "blocker_reason_code": reason if isinstance(reason, str) and reason in SAFE_BLOCKERS else "credential_not_minted",
        }

    creds = load_credentials()
    if not creds:
        return {**base, "stage": "auth", "blocker_reason_code": "no_device_credentials"}
    device_id, device_key = creds

    try:
        response = requests.post(
            f"{FUNCTIONS_BASE}/unk-credential-install",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
                "x-device-id": device_id,
                "x-device-key": device_key,
            },
            json={
                "action": "install",
                "credential_key": CREDENTIAL_KEY,
                "value": credential,
            },
            timeout=60,
        )
    except Exception:
        # Never print provider/HTTP exception strings; they might embed headers.
        return {**base, "blocker_reason_code": "install_transport_failed"}
    finally:
        credential = None

    try:
        payload = response.json()
    except Exception:
        payload = None

    acknowledged = (
        response.status_code == 200
        and isinstance(payload, dict)
        and payload.get("ok") is True
        and payload.get("credential_key") == CREDENTIAL_KEY
        and (
            not summary.get("client_email")
            or payload.get("client_email") == summary.get("client_email")
        )
    )
    result = {
        **base,
        "ok": acknowledged,
        "http_status": response.status_code,
        "server_receipt_confirmed": acknowledged,
    }
    if not acknowledged:
        raw = payload.get("error") if isinstance(payload, dict) else None
        result["blocker_reason_code"] = raw if isinstance(raw, str) and raw in SAFE_BLOCKERS else "install_not_acknowledged"
    return result


def main() -> int:
    receipt = provision({
        "mode": "service_account",
        "visible": "--headless" not in sys.argv,
        "project_id": PROJECT_ID,
        "service_account_id": SERVICE_ACCOUNT_ID,
    })
    result = install_provisioned(receipt)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
