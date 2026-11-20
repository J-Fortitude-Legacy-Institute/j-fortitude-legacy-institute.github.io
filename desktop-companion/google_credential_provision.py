"""Unk retrieves a durable Google Drive credential without Jason at the desk.

Why this exists
---------------
Every Drive read in the platform used to go through the Lovable connector
gateway. When the workspace runs out of credits the gateway stops answering and
the whole media engine goes dark upstream of publishing. `_shared/drive-access.ts`
already prefers a direct credential; it just needs one to exist.

This module lets Unk mint that credential on Ground Zero using Jason's already
signed-in Chrome profile, entirely unattended:

  mode="probe"            -> report which Google account is signed in and what
                             projects / service accounts already exist.
  mode="service_account"  -> ensure a Cloud project, enable the Drive API,
                             create a service account, create a JSON key, and
                             return the key material so the platform can store
                             it as GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON.

Hard rules (same doctrine as every other Unk browser capability):
  * Never types a password, a 2FA code, or an identity check.
  * Never touches billing, payment, or purchase surfaces.
  * If a human-only gate appears, it stops and returns a reason code instead of
    guessing: login_required, mfa_required, consent_required,
    billing_required, tos_required, selector_drift.
  * Always returns a receipt with a screenshot path.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from meta_browser_publisher import (  # reuse the hardened browser plumbing
    PROFILE_DIR,
    UNK_CHROMIUM_ARGS,
    _ensure_playwright_ready,
    _release_locked_profile,
    _screenshot_path,
)

try:
    from unk_window_policy import (  # type: ignore
        install_quiet_subprocess as _install_quiet_subprocess,
        browser_args as _win_browser_args,
    )
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


CONSOLE = "https://console.cloud.google.com"
DEFAULT_PROJECT_ID = "jfli-media-runtime"
DEFAULT_SA_ID = "jfli-drive-reader"

# Gates Unk must never attempt to clear himself.
_GATE_PROBES: list[tuple[str, list[str]]] = [
    ("login_required", [
        "input[type='password']",
        "form[action*='accounts.google.com']",
        "#identifierId",
    ]),
    ("mfa_required", [
        "[data-challengetype]",
        "input[name='totpPin']",
        "div[jsname='feKamc']",
    ]),
    ("billing_required", [
        "a[href*='billing/linkedaccount']",
        "[aria-label*='Enable billing']",
    ]),
    ("tos_required", [
        # Generic Terms-of-Service footer links are NOT a consent gate.
        # Only an explicit request to agree should stop autonomous work.
        "text=agree to the Terms of Service",
    ]),
]


def _detect_gate(page) -> Optional[str]:
    for code, selectors in _GATE_PROBES:
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=800):
                    return code
            except Exception:
                continue
    try:
        if "accounts.google.com" in (page.url or ""):
            return "login_required"
    except Exception:
        pass
    return None


def _shot(page, prefix: str, receipt: dict) -> None:
    try:
        path = _screenshot_path(prefix)
        page.screenshot(path=str(path))
        receipt["screenshot_path"] = str(path)
    except Exception:
        pass


def _signed_in_account(page) -> Optional[str]:
    """Read the active account from the console's own account endpoint."""
    try:
        resp = page.request.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            timeout=15000,
        )
        if resp.ok:
            data = resp.json()
            return data.get("email")
    except Exception:
        pass
    # Fallback: the avatar button exposes the address in its aria-label.
    for sel in ["a[aria-label*='Google Account']", "[aria-label*='Account: ']"]:
        try:
            label = page.locator(sel).first.get_attribute("aria-label", timeout=2000)
            if label and "@" in label:
                return label.split("(")[-1].strip(") ")
        except Exception:
            continue
    return None


def _click_first(page, selectors: list[str], timeout: int = 6000) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                loc.click(timeout=timeout)
                return True
        except Exception:
            continue
    return False


def _run(mode: str, payload: dict, receipt: dict) -> dict:
    ready, ready_err = _ensure_playwright_ready(receipt.setdefault("notes", []))
    if not ready:
        receipt["blocker_reason_code"] = "playwright_not_ready"
        receipt["error"] = ready_err or "playwright_not_ready"
        return receipt

    from playwright.sync_api import sync_playwright  # type: ignore

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    project_id = str(payload.get("project_id") or DEFAULT_PROJECT_ID).strip()
    sa_id = str(payload.get("service_account_id") or DEFAULT_SA_ID).strip()
    # "signin" is an explicit human-in-the-loop mode: the window MUST be visible
    # so Jason can complete password + 2FA inside Unk's own persistent profile.
    # After that one time, every later run is headless and needs no human.
    visible = bool(payload.get("visible")) or mode == "signin"

    with sync_playwright() as p:
        _release_locked_profile(receipt["notes"])
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=not visible,
            viewport={"width": 1500, "height": 1000},
            accept_downloads=True,
            args=_win_browser_args(UNK_CHROMIUM_ARGS, visible_required=visible),
        )

        # Borrow Jason's already-signed-in Google session from installed Chrome.
        # Unk never types a password; he only reuses a session Jason established.
        google_domains = ["google.com", "accounts.google.com", "cloud.google.com"]
        try:
            from chrome_cookie_import import (  # type: ignore
                import_into_context as _ck_import,
                import_via_chrome_clone as _ck_clone,
            )
            direct = _ck_import(context, google_domains)
            receipt["cookie_import"] = {
                "direct_injected": direct.get("injected", 0),
                "notes": direct.get("notes", [])[:6],
            }
            if not direct.get("injected"):
                clone = _ck_clone(p, context, google_domains)
                receipt["cookie_import"]["clone_injected"] = clone.get("injected", 0)
                receipt["cookie_import"]["clone_notes"] = clone.get("notes", [])[:6]
        except Exception as exc:
            receipt["cookie_import"] = {"error": str(exc)[:200]}

        page = context.pages[0] if context.pages else context.new_page()
        try:
            if mode == "signin":
                wait_s = int(payload.get("wait_seconds") or 420)
                page.goto("https://accounts.google.com/", wait_until="domcontentloaded", timeout=60000)
                receipt["notes"].append("visible_signin_window_open")
                deadline = time.time() + wait_s
                account = None
                while time.time() < deadline:
                    time.sleep(6)
                    try:
                        account = _signed_in_account(page)
                    except Exception:
                        account = None
                    if account:
                        break
                if not account:
                    try:
                        page.goto(f"{CONSOLE}/welcome", wait_until="domcontentloaded", timeout=60000)
                        time.sleep(4)
                        account = _signed_in_account(page)
                    except Exception:
                        pass
                receipt["google_account"] = account
                _shot(page, "gcred_signin", receipt)
                if not account:
                    receipt["blocker_reason_code"] = "login_required"
                    receipt["next_automatic_action"] = (
                        "re-run mode=signin when Jason is at the desk; the window stays "
                        f"open {wait_s}s for password + 2FA"
                    )
                    return receipt
                receipt["ok"] = True
                receipt["next_automatic_action"] = (
                    "session persisted in Unk's profile; run mode=service_account headless"
                )
                return receipt

            page.goto(f"{CONSOLE}/welcome", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)


            gate = _detect_gate(page)
            if gate:
                _shot(page, f"gcred_{gate}", receipt)
                receipt["blocker_reason_code"] = gate
                receipt["next_automatic_action"] = (
                    "retry automatically once the Google session is repaired; "
                    "no window will be reopened for this gate"
                )
                return receipt

            account = _signed_in_account(page)
            receipt["google_account"] = account
            if not account:
                _shot(page, "gcred_no_account", receipt)
                receipt["blocker_reason_code"] = "login_required"
                return receipt

            if mode == "probe":
                receipt.update(_probe(page, receipt))
                _shot(page, "gcred_probe", receipt)
                receipt["ok"] = True
                return receipt

            return _provision(page, project_id, sa_id, receipt)
        finally:
            try:
                context.close()
            except Exception:
                pass


def _api(page, method: str, url: str, body: Optional[dict] = None) -> tuple[int, Any]:
    """Call a Google Cloud REST endpoint using the console's own session."""
    try:
        kwargs: dict[str, Any] = {"timeout": 30000}
        if body is not None:
            kwargs["data"] = body
        resp = getattr(page.request, method.lower())(url, **kwargs)
        try:
            return resp.status, resp.json()
        except Exception:
            return resp.status, resp.text()
    except Exception as exc:
        return 0, {"error": str(exc)[:300]}


def _probe(page, receipt: dict) -> dict:
    out: dict[str, Any] = {"mode": "probe"}
    status, body = _api(
        page, "get",
        "https://cloudresourcemanager.googleapis.com/v1/projects",
    )
    out["projects_status"] = status
    if isinstance(body, dict) and body.get("projects"):
        out["projects"] = [
            {"projectId": pr.get("projectId"), "name": pr.get("name"),
             "state": pr.get("lifecycleState")}
            for pr in body["projects"][:25]
        ]
    else:
        out["projects_raw"] = str(body)[:500]
        receipt.setdefault("notes", []).append(
            "console session cannot call the Cloud APIs directly; UI path required"
        )
    return out


def _provision(page, project_id: str, sa_id: str, receipt: dict) -> dict:
    """Create project -> enable Drive API -> service account -> JSON key."""
    receipt["mode"] = "service_account"
    receipt["project_id"] = project_id
    receipt["service_account_id"] = sa_id
    steps: list[dict] = receipt.setdefault("steps", [])

    def step(name: str, ok: bool, detail: Any = None) -> None:
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    # 1. Project — create only if missing.
    status, body = _api(
        page, "get",
        f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}",
    )
    if status == 200:
        step("project_exists", True, project_id)
    elif status in (403, 404):
        cstatus, cbody = _api(
            page, "post",
            "https://cloudresourcemanager.googleapis.com/v1/projects",
            {"projectId": project_id, "name": "JFLI Media Runtime"},
        )
        step("project_create", cstatus in (200, 201), {"status": cstatus, "body": str(cbody)[:300]})
        if cstatus not in (200, 201):
            receipt["blocker_reason_code"] = "project_create_failed"
            _shot(page, "gcred_project_failed", receipt)
            return receipt
        time.sleep(8)
    else:
        step("project_lookup", False, {"status": status, "body": str(body)[:300]})
        receipt["blocker_reason_code"] = "console_api_unavailable"
        _shot(page, "gcred_api_unavailable", receipt)
        return receipt

    # 2. Enable the Drive API + IAM API on that project.
    for svc in ("drive.googleapis.com", "iam.googleapis.com"):
        estatus, ebody = _api(
            page, "post",
            f"https://serviceusage.googleapis.com/v1/projects/{project_id}"
            f"/services/{svc}:enable",
            {},
        )
        step(f"enable_{svc}", estatus in (200, 201), {"status": estatus, "body": str(ebody)[:200]})
    time.sleep(5)

    # 3. Service account.
    sa_email = f"{sa_id}@{project_id}.iam.gserviceaccount.com"
    receipt["service_account_email"] = sa_email
    gstatus, _ = _api(
        page, "get",
        f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts/{sa_email}",
    )
    if gstatus != 200:
        cstatus, cbody = _api(
            page, "post",
            f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts",
            {"accountId": sa_id,
             "serviceAccount": {"displayName": "JFLI Drive Reader (Unk)"}},
        )
        step("service_account_create", cstatus in (200, 201),
             {"status": cstatus, "body": str(cbody)[:300]})
        if cstatus not in (200, 201):
            receipt["blocker_reason_code"] = "service_account_create_failed"
            _shot(page, "gcred_sa_failed", receipt)
            return receipt
        time.sleep(4)
    else:
        step("service_account_exists", True, sa_email)

    # 4. JSON key.
    kstatus, kbody = _api(
        page, "post",
        f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts/{sa_email}/keys",
        {"privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE", "keyAlgorithm": "KEY_ALG_RSA_2048"},
    )
    if kstatus not in (200, 201) or not isinstance(kbody, dict):
        step("key_create", False, {"status": kstatus, "body": str(kbody)[:300]})
        receipt["blocker_reason_code"] = "key_create_failed"
        _shot(page, "gcred_key_failed", receipt)
        return receipt

    import base64
    try:
        key_json = base64.b64decode(kbody["privateKeyData"]).decode("utf-8")
        parsed = json.loads(key_json)
    except Exception as exc:
        step("key_decode", False, str(exc)[:200])
        receipt["blocker_reason_code"] = "key_decode_failed"
        return receipt

    step("key_create", True, {"private_key_id": parsed.get("private_key_id")})

    # Keep this freshly minted key only in process memory for direct, authenticated
    # installation into Project K. Never create an unencrypted local key file.
    receipt["ok"] = True
    receipt["credential_json"] = key_json
    receipt["credential_summary"] = {
        "client_email": parsed.get("client_email"),
        "project_id": parsed.get("project_id"),
        "private_key_id": parsed.get("private_key_id"),
    }
    receipt["human_followup"] = (
        f"Share the STV / Carl Boyd Drive folders with {parsed.get('client_email')} "
        "(Viewer is enough) so the service account can read them."
    )
    _shot(page, "gcred_success", receipt)
    return receipt


def provision(payload: Optional[dict] = None) -> dict:
    payload = payload or {}
    mode = str(payload.get("mode") or "service_account").strip()
    if mode not in {"probe", "service_account", "signin"}:
        return {"ok": False, "error": "unsupported_mode", "mode": mode}

    receipt: dict[str, Any] = {
        "ok": False,
        "mode": mode,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "notes": [],
    }
    try:
        return _run(mode, payload, receipt)
    except Exception as exc:  # never crash the companion loop
        receipt["error"] = str(exc)[:500]
        receipt["blocker_reason_code"] = receipt.get("blocker_reason_code") or "selector_drift"
        return receipt
