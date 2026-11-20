"""Unk capability: Integration & Credential Manager (standing responsibility).

Onboards and maintains external tools end-to-end on Ground Zero:

  1. discover  - open the vendor, sign in with a stored browser profile, locate
                 the correct product/API surface
  2. acquire   - generate an API key/token through the vendor UI and capture it
                 straight into the local credential store
  3. install   - place the value into the approved destinations (Ground Zero
                 credential store, GitHub Actions secret, non-versioned env
                 file). Supabase secrets are referenced by fingerprint.
  4. connect   - install the SDK/package where a repo checkout exists
  5. test      - run a real connectivity call and return a non-secret receipt
  6. maintain  - re-verify, detect revoked/expired credentials, rotate
  7. expand    - when a vendor class is new, publish a reusable playbook back to
                 the platform instead of stopping at "I don't have permission"

WRITE/USE WITHOUT REVEAL
  Plaintext credential material never leaves this process except into an
  approved secure destination. Nothing secret is ever returned, printed,
  logged, committed, or passed as a CLI argument. Every receipt carries only a
  SHA-256 fingerprint prefix.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

from secret_rotate import (  # reuse the hardened primitives
    ALLOWED_ENV_FILES,
    DEFAULT_REPO,
    _auth_headers,
    _find_repo,
    _which,
    _write_env_var,
)

HOME = Path.home()
COMPANION_DIR = HOME / ".unk-companion"
CRED_STORE = COMPANION_DIR / "credentials.json"
FUNCTIONS_BASE = "https://kwbegsybeyyxfmavjswv.functions.supabase.co"
MANAGER_URL = f"{FUNCTIONS_BASE}/ops-integration-manager"

LIFECYCLE = ("discover", "acquire", "install", "connect", "test", "maintain", "rotate", "expand")


# --------------------------------------------------------------------------
# local credential store (write/use without reveal)
# --------------------------------------------------------------------------
def _store_load() -> dict[str, Any]:
    try:
        if CRED_STORE.exists():
            return json.loads(CRED_STORE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _store_put(name: str, value: str) -> str:
    """Persist a credential locally and return ONLY its fingerprint."""
    COMPANION_DIR.mkdir(parents=True, exist_ok=True)
    data = _store_load()
    data[name] = {
        "value": value,
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
    }
    tmp = CRED_STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(CRED_STORE)
    try:  # best-effort: owner-only on POSIX, ACL-inherited on Windows
        os.chmod(CRED_STORE, 0o600)
    except Exception:
        pass
    try:
        import keyring  # type: ignore

        keyring.set_password("unk-companion", name, value)
    except Exception:
        pass
    return data[name]["sha256"]


def store_get(name: str) -> str:
    """Read a credential for USE only. Never return this to the cloud."""
    try:
        import keyring  # type: ignore

        val = keyring.get_password("unk-companion", name)
        if val:
            return val.strip()
    except Exception:
        pass
    entry = _store_load().get(name) or {}
    return str(entry.get("value") or "")


def fingerprint(name: str) -> str:
    val = store_get(name)
    return hashlib.sha256(val.encode("utf-8")).hexdigest() if val else ""


# --------------------------------------------------------------------------
# backend control plane
# --------------------------------------------------------------------------
def _post(payload: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    if requests is None:
        return {"error": "requests_missing"}
    headers, mode = _auth_headers()
    if not headers:
        return {"error": "no_local_authorization"}
    try:
        r = requests.post(
            MANAGER_URL,
            headers={"Content-Type": "application/json", **headers},
            json=payload,
            timeout=timeout,
        )
        out = r.json() if r.content else {}
        out["_status"] = r.status_code
        out["_auth_mode"] = mode
        return out
    except Exception as exc:
        return {"error": "manager_unreachable", "detail": type(exc).__name__}


# --------------------------------------------------------------------------
# lifecycle steps
# --------------------------------------------------------------------------
def _step_discover(integ: dict, task: dict) -> dict:
    """Open the vendor console with a signed-in profile and confirm reachability."""
    receipt: dict[str, Any] = {"step": "discover"}
    url = integ.get("console_url") or integ.get("signup_url") or integ.get("docs_url")
    receipt["target_present"] = bool(url)
    if not url:
        return {"ok": False, "status": "blocked", "reason": "no_vendor_url_registered", **receipt}
    if requests is not None:
        try:
            r = requests.get(url, timeout=25, allow_redirects=True)
            receipt["vendor_reachable"] = r.status_code < 500
            receipt["vendor_status"] = r.status_code
        except Exception as exc:
            receipt["vendor_reachable"] = False
            receipt["vendor_error"] = type(exc).__name__
    try:
        from vendor_browser import open_vendor_console  # type: ignore

        receipt["console"] = open_vendor_console(url, profile=integ.get("slug"))
    except Exception as exc:
        receipt["console_error"] = type(exc).__name__
    return {"ok": bool(receipt.get("vendor_reachable")), "status": "done" if receipt.get("vendor_reachable") else "blocked", **receipt}


def _step_acquire(integ: dict, task: dict) -> dict:
    """Obtain the credential value; never return or log it."""
    receipt: dict[str, Any] = {"step": "acquire", "secrets": []}
    names = [str(n) for n in (integ.get("required_secrets") or [])]
    if not names:
        return {"ok": False, "status": "blocked", "reason": "no_required_secrets_declared", **receipt}

    playbook = (task.get("playbook") or {}) or {}
    klass = str(playbook.get("integration_class") or "api_key")

    force_reacquire = str(task.get("reason") or "").lower() in {
        "auth_rejected_credential",
        "credential_expired",
        "credential_invalid",
        "force_refresh",
    } or bool((task.get("payload") or {}).get("force_reacquire"))

    for name in names:
        existing = store_get(name)
        if existing and not force_reacquire:
            receipt["secrets"].append({"name": name, "source": "already_held", "fingerprint_prefix": fingerprint(name)[:8]})
            continue
        if existing and force_reacquire:
            receipt["secrets"].append({
                "name": name,
                "source": "held_but_rejected",
                "fingerprint_prefix": fingerprint(name)[:8],
                "reacquire_required": True,
            })
        if klass == "internal_token":
            fp = _store_put(name, secrets.token_hex(24))
            receipt["secrets"].append({"name": name, "source": "generated_locally", "fingerprint_prefix": fp[:8]})
            continue
        # Vendor-issued: attempt browser capture, otherwise report the exact gate.
        captured = ""
        try:
            from vendor_browser import capture_api_key  # type: ignore

            captured = capture_api_key(integ.get("slug"), name, integ.get("console_url")) or ""
        except Exception as exc:
            receipt.setdefault("capture_errors", []).append({"name": name, "error": type(exc).__name__})
        if captured:
            fp = _store_put(name, captured)
            receipt["secrets"].append({"name": name, "source": "vendor_ui_capture", "fingerprint_prefix": fp[:8]})
            del captured
        else:
            receipt["secrets"].append({"name": name, "source": "unavailable", "human_gate": "vendor_key_creation"})

    resolved = {
        str(item.get("name") or "")
        for item in receipt["secrets"]
        if item.get("fingerprint_prefix") and not item.get("reacquire_required")
    }
    ok = all(name in resolved for name in names)
    return {"ok": ok, "status": "done" if ok else "blocked", "reason": None if ok else "human_gate_vendor_key_creation", **receipt}


def _step_install(integ: dict, task: dict) -> dict:
    """Place held credentials into every approved destination + register fingerprints."""
    receipt: dict[str, Any] = {"step": "install", "installed": []}
    repo = _find_repo(task.get("payload", {}).get("repo_path"))
    gh = _which("gh", "gh.exe") if repo is not None else None
    env_file = ".env.integration"

    for name in [str(n) for n in (integ.get("required_secrets") or [])]:
        value = store_get(name)
        if not value:
            receipt["installed"].append({"name": name, "ground_zero": False, "reason": "not_held"})
            continue
        entry: dict[str, Any] = {"name": name, "ground_zero": True, "fingerprint_prefix": hashlib.sha256(value.encode()).hexdigest()[:8]}

        if gh:
            try:
                p = subprocess.run(
                    [gh, "secret", "set", name, "--repo", DEFAULT_REPO, "--body-file", "-"],
                    input=value, capture_output=True, text=True, timeout=120,
                )
                entry["github_actions"] = p.returncode == 0
                if p.returncode != 0:
                    entry["github_error"] = (p.stderr or "")[-200:].replace(value, "***")
            except Exception as exc:
                entry["github_error"] = type(exc).__name__
        else:
            entry["github_error"] = "repo_checkout_unavailable" if repo is None else "gh_cli_not_found"

        if repo is not None and env_file in ALLOWED_ENV_FILES:
            try:
                entry["env_file_action"] = _write_env_var(repo / env_file, name, value)
            except Exception as exc:
                entry["env_file_error"] = type(exc).__name__

        _post({
            "action": "record_credential",
            "integration_slug": integ.get("slug"),
            "secret_name": name,
            "destination": "ground_zero_store",
            "fingerprint_sha256": hashlib.sha256(value.encode()).hexdigest(),
            "status": "installed",
            "rotation_period_days": task.get("payload", {}).get("rotation_period_days") or 90,
        })
        del value
        receipt["installed"].append(entry)

    ok = any(e.get("ground_zero") for e in receipt["installed"])
    return {"ok": ok, "status": "done" if ok else "blocked", "reason": None if ok else "no_credentials_held", **receipt}


def _step_connect(integ: dict, task: dict) -> dict:
    """Install the SDK/package into the repo checkout when one exists."""
    receipt: dict[str, Any] = {"step": "connect"}
    pkg = integ.get("sdk_package")
    if not pkg:
        return {"ok": True, "status": "done", "sdk_required": False, **receipt}
    repo = _find_repo(task.get("payload", {}).get("repo_path"))
    if repo is None:
        return {"ok": True, "status": "done", "sdk_required": True, "sdk_installed": False,
                "note": "repo_checkout_unavailable_on_ground_zero", **receipt}
    runner = _which("bun", "bun.exe")
    if not runner:
        return {"ok": False, "status": "blocked", "reason": "bun_not_found", **receipt}
    try:
        p = subprocess.run([runner, "add", str(pkg)], cwd=str(repo), capture_output=True, text=True, timeout=600)
        receipt["sdk_installed"] = p.returncode == 0
        receipt["sdk_output_tail"] = ((p.stdout or "") + (p.stderr or ""))[-600:]
    except Exception as exc:
        receipt["sdk_error"] = type(exc).__name__
    ok = bool(receipt.get("sdk_installed"))
    return {"ok": ok, "status": "done" if ok else "failed", **receipt}


def _step_test(integ: dict, task: dict) -> dict:
    """Run a real connectivity call defined by the integration's health_check."""
    receipt: dict[str, Any] = {"step": "test"}
    hc = integ.get("health_check") or {}
    url = hc.get("url")
    if not url:
        return {"ok": False, "status": "blocked", "reason": "no_health_check_configured", **receipt}
    if requests is None:
        return {"ok": False, "status": "failed", "reason": "requests_missing", **receipt}

    headers = {str(k): str(v) for k, v in (hc.get("headers") or {}).items()}
    auth_secret = hc.get("auth_secret")
    if auth_secret:
        val = store_get(str(auth_secret))
        if not val:
            return {"ok": False, "status": "blocked", "reason": "credential_not_held", **receipt}
        scheme = str(hc.get("auth_scheme") or "Bearer")
        header_name = str(hc.get("auth_header") or "Authorization")
        headers[header_name] = f"{scheme} {val}".strip() if scheme else val
        del val
    try:
        r = requests.request(str(hc.get("method") or "GET"), str(url), headers=headers,
                             json=hc.get("body"), timeout=int(hc.get("timeout") or 30))
        expected = int(hc.get("expect_status") or 200)
        receipt["http_status"] = r.status_code
        receipt["expected_status"] = expected
        ok = r.status_code == expected
        receipt["ok"] = ok
        if not ok:
            receipt["code"] = f"http_{r.status_code}"
    except Exception as exc:
        receipt["ok"] = False
        receipt["code"] = type(exc).__name__

    _post({
        "action": "record_health",
        "integration_slug": integ.get("slug"),
        "check_type": "connectivity",
        "ok": bool(receipt.get("ok")),
        "code": receipt.get("code"),
        "detail": {"http_status": receipt.get("http_status")},
    })
    return {"ok": bool(receipt.get("ok")), "status": "done" if receipt.get("ok") else "failed", **receipt}


def _step_maintain(integ: dict, task: dict) -> dict:
    """Re-verify and repair: a failed test escalates to rotation automatically."""
    out = _step_test(integ, task)
    out["step"] = "maintain"
    if not out.get("ok") and str(out.get("code") or "").startswith(("http_401", "http_403")):
        _post({"action": "enqueue_task", "integration_slug": integ.get("slug"), "step": "rotate",
               "reason": "auth_rejected_credential"})
        out["rotation_queued"] = True
        out["status"] = "done"
    return out


def _step_rotate(integ: dict, task: dict) -> dict:
    """Rotate an internally-generated credential; vendor keys re-enter acquire."""
    receipt: dict[str, Any] = {"step": "rotate"}
    playbook = (task.get("playbook") or {}) or {}
    klass = str(playbook.get("integration_class") or "api_key")
    name = str(task.get("payload", {}).get("secret_name") or (integ.get("required_secrets") or [""])[0])
    if not name:
        return {"ok": False, "status": "blocked", "reason": "no_secret_name", **receipt}

    if klass == "internal_token":
        try:
            from secret_rotate import ALLOWED_TOKENS as _ROTATABLE  # type: ignore
            from secret_rotate import rotate as _rotate  # type: ignore
        except Exception as exc:
            return {"ok": False, "status": "failed", "reason": type(exc).__name__, **receipt}
        if name in _ROTATABLE:
            # Legacy allow-listed operational token: full repo/CI sync path.
            out = _rotate({"secret_name": name, "token_name": name, "run_tests": False})
            receipt.update({k: v for k, v in out.items() if k != "ok"})
            ok = bool(out.get("ok"))
        else:
            # Registry-driven token: generate locally, install everywhere approved.
            _store_put(name, secrets.token_hex(24))
            inst = _step_install({**integ, "required_secrets": [name]}, task)
            receipt["reinstalled"] = inst.get("installed")
            ok = bool(inst.get("ok"))
    else:
        acq = _step_acquire({**integ, "required_secrets": [name]}, task)
        if not acq.get("ok"):
            return {"ok": False, "status": "blocked", "reason": acq.get("reason") or "vendor_rotation_gate", **receipt}
        inst = _step_install({**integ, "required_secrets": [name]}, task)
        receipt["reinstalled"] = inst.get("installed")
        ok = bool(inst.get("ok"))

    if ok:
        _post({"action": "record_credential", "integration_slug": integ.get("slug"), "secret_name": name,
               "destination": "ground_zero_store", "fingerprint_sha256": fingerprint(name) or None,
               "status": "verified", "rotated": True, "rotation_period_days": 90})
        _post({"action": "enqueue_task", "integration_slug": integ.get("slug"), "step": "test",
               "reason": "post_rotation_verification"})
    receipt["fingerprint_prefix"] = (fingerprint(name) or "")[:8]
    return {"ok": ok, "status": "done" if ok else "failed", **receipt}


def _step_expand(integ: dict, task: dict) -> dict:
    """Turn an unsupported vendor class into a reusable playbook."""
    receipt: dict[str, Any] = {"step": "expand"}
    slug = f"{str(integ.get('category') or 'api_key')}-{str(integ.get('vendor') or 'vendor')}".lower().replace(" ", "-")
    res = _post({
        "action": "learn_playbook",
        "slug": slug,
        "title": f"{integ.get('vendor')} ({integ.get('category')}) onboarding",
        "integration_class": str(integ.get("category") or "api_key"),
        "vendor_pattern": integ.get("vendor"),
        "automation_level": "assisted",
        "steps": list(LIFECYCLE[:6]),
        "human_gates": ["vendor_key_creation", "billing"],
        "notes": f"Auto-drafted from live onboarding of {integ.get('slug')}. Refine after first successful run.",
    })
    receipt["playbook_slug"] = slug
    receipt["published"] = bool(res.get("learned"))
    return {"ok": receipt["published"], "status": "done" if receipt["published"] else "failed", **receipt}


STEP_HANDLERS = {
    "discover": _step_discover,
    "acquire": _step_acquire,
    "install": _step_install,
    "connect": _step_connect,
    "test": _step_test,
    "maintain": _step_maintain,
    "rotate": _step_rotate,
    "expand": _step_expand,
}


def run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Claim and execute due integration tasks. Returns NON-SECRET receipts."""
    payload = dict(payload or {})
    limit = int(payload.get("limit") or 3)

    if payload.get("register"):
        reg = _post({"action": "register_integration", **payload["register"]})
        if payload.get("register_only"):
            return {"ok": bool(reg.get("registered")), "registered": reg.get("slug"), "receipts": []}

    claim = _post({"action": "claim_task", "limit": limit})
    if claim.get("error"):
        return {"ok": False, "error": claim.get("error"), "detail": claim.get("detail")}

    receipts: list[dict[str, Any]] = []
    for task in claim.get("tasks") or []:
        integ = task.get("integration") or {}
        step = str(task.get("step"))
        handler = STEP_HANDLERS.get(step)
        if handler is None:
            _post({"action": "complete_task", "task_id": task["id"], "status": "skipped",
                   "reason": "unknown_step", "receipt": {}})
            receipts.append({"slug": integ.get("slug"), "step": step, "ok": False, "reason": "unknown_step"})
            continue
        try:
            out = handler(integ, task)
        except Exception as exc:
            out = {"ok": False, "status": "failed", "reason": type(exc).__name__}
        status = str(out.get("status") or ("done" if out.get("ok") else "failed"))
        safe = {k: v for k, v in out.items() if k not in ("ok", "status")}
        _post({
            "action": "complete_task",
            "task_id": task["id"],
            "status": status,
            "reason": out.get("reason"),
            "receipt": safe,
            "retry_in_minutes": 30 if status == "failed" else 0,
        })
        receipts.append({"slug": integ.get("slug"), "step": step, "ok": bool(out.get("ok")), "status": status,
                         "reason": out.get("reason")})

    return {"ok": True, "claimed": len(receipts), "receipts": receipts}