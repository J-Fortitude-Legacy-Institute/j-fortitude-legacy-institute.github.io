"""Persistent Fixer worker for Ground Zero.

Fixer keeps one canonical repair as focus until it closes. When the server says
context is missing, Fixer first gathers safe read-only evidence, records that
evidence durably on the repair lease, and only then lets the repair loop retry.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests

HOME = Path.home()
STATE_DIR = HOME / ".unk-companion"
STATE_DIR.mkdir(exist_ok=True)
OPS_KEY_FILE = STATE_DIR / "ops.json"
DEVICE_FILE = STATE_DIR / "device.json"
RECEIPT_FILE = STATE_DIR / "fixer_worker.json"
LOG_FILE = STATE_DIR / "fixer_worker.log"
RETRIEVAL_FILE = STATE_DIR / "fixer_retrieval.json"

PROJECT_REF = "kwbegsybeyyxfmavjswv"
URL = f"https://{PROJECT_REF}.supabase.co/functions/v1/fixer-worker-control"
SUPERVISOR_REPORT_URL = f"https://{PROJECT_REF}.supabase.co/functions/v1/desktop-supervisor-report"
LOOP_SECONDS = int(os.getenv("FIXER_LOOP_SECONDS", "60"))
HTTP_TIMEOUT = 30
# Production Project K repair RPCs can run longer than ordinary read-only URL
# probes. Timeout is (connect, read), not a scheduler cycle cutoff.
CONTROL_HTTP_TIMEOUT = (10, 110)
INSTANCE_ID = uuid.uuid4().hex
MAX_EVIDENCE_CHARS = 12000

SAFE_LOCAL_ROOTS = [
    STATE_DIR.resolve(),
    (Path(os.environ.get("LOCALAPPDATA", "")) / "UnkCompanion").resolve(),
    Path(r"C:\JFortitude").resolve(),
]


def log(message: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _ops_key() -> str:
    try:
        import keyring  # type: ignore
        value = keyring.get_password("unk-companion", "UNK_SERVICE_KEY")
        if value:
            return value.strip()
    except Exception:
        pass
    try:
        if OPS_KEY_FILE.exists():
            data = json.loads(OPS_KEY_FILE.read_text(encoding="utf-8"))
            value = str(data.get("UNK_SERVICE_KEY") or "").strip()
            if value:
                return value
    except Exception:
        pass
    return ""


def _device_credentials() -> tuple[str, str]:
    try:
        import keyring  # type: ignore
        did = keyring.get_password("unk-companion", "device_id")
        dkey = keyring.get_password("unk-companion", "device_key")
        if did and dkey:
            return did.strip(), dkey.strip()
    except Exception:
        pass
    try:
        if DEVICE_FILE.exists():
            data = json.loads(DEVICE_FILE.read_text(encoding="utf-8"))
            did = str(data.get("device_id") or "").strip()
            dkey = str(data.get("device_key") or "").strip()
            if did and dkey:
                return did, dkey
    except Exception:
        pass
    return "", ""


def auth_headers() -> dict[str, str]:
    key = _ops_key()
    if key:
        return {"x-unk-service-key": key}
    did, dkey = _device_credentials()
    if did and dkey:
        return {"x-device-id": did, "x-device-key": dkey}
    return {}


def post_control(payload: dict) -> dict:
    headers = auth_headers()
    if not headers:
        return {"ok": False, "error": "no_machine_identity"}
    response = requests.post(
        URL,
        headers={**headers, "content-type": "application/json"},
        json=payload,
        timeout=CONTROL_HTTP_TIMEOUT,
    )
    try:
        body = response.json()
    except Exception:
        body = {"ok": False, "error": f"http_{response.status_code}"}
    body["http_status"] = response.status_code
    return body


def report_fallback_event(message: str, evidence: dict) -> dict:
    did, dkey = _device_credentials()
    if not did or not dkey:
        return {"ok": False, "error": "no_device_identity"}
    response = requests.post(
        SUPERVISOR_REPORT_URL,
        headers={"X-Device-Id": did, "X-Device-Key": dkey, "content-type": "application/json"},
        json={"action": "event", "event_kind": "supervisor_poll", "message": message, "evidence": evidence},
        timeout=HTTP_TIMEOUT,
    )
    try:
        payload = response.json()
    except Exception:
        payload = {"ok": False, "error": f"http_{response.status_code}"}
    payload["http_status"] = response.status_code
    return payload


def _safe_local_path(raw: str) -> Path | None:
    value = str(raw or "").replace("~", str(HOME), 1)
    try:
        path = Path(value).resolve()
    except Exception:
        return None
    for root in SAFE_LOCAL_ROOTS:
        try:
            if path == root or root in path.parents:
                return path
        except Exception:
            continue
    return None


def _read_local(raw: str) -> dict:
    path = _safe_local_path(raw)
    if not path:
        return {"source": raw, "ok": False, "error": "path_not_allowed"}
    if not path.exists() or not path.is_file():
        return {"source": str(path), "ok": False, "error": "not_found"}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return {"source": str(path), "ok": True, "text_tail": text[-MAX_EVIDENCE_CHARS:]}
    except Exception as exc:
        return {"source": str(path), "ok": False, "error": type(exc).__name__}


def _fetch_public_url(url: str) -> dict:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return {"source": url, "ok": False, "error": "invalid_url"}
        response = requests.get(
            url,
            headers={"User-Agent": "JFortitude-Fixer/1.0"},
            timeout=HTTP_TIMEOUT,
            allow_redirects=True,
        )
        ctype = str(response.headers.get("content-type") or "")
        if "text" not in ctype and "json" not in ctype and "xml" not in ctype:
            return {"source": url, "ok": response.ok, "status": response.status_code, "content_type": ctype, "body_omitted": True}
        return {
            "source": url,
            "ok": response.ok,
            "status": response.status_code,
            "content_type": ctype,
            "text": response.text[:MAX_EVIDENCE_CHARS],
        }
    except Exception as exc:
        return {"source": url, "ok": False, "error": type(exc).__name__}


def gather_retrieval(result: dict) -> dict | None:
    retrieval = result.get("retrieval") or {}
    focus = result.get("focus") or {}
    if not retrieval.get("required") or not focus.get("id"):
        return None

    evidence = {
        "fix_id": focus.get("id"),
        "objective": retrieval.get("objective"),
        "missing_signal": retrieval.get("missing_signal"),
        "retrieval_round": retrieval.get("retrieval_round") or 1,
        "database_history": retrieval.get("database_history") or {},
        "authenticated_sources": retrieval.get("authenticated_sources") or {},
        "platform_memory": retrieval.get("platform_memory") or {},
        "local": [],
        "public_urls": [],
        "collected_at": time.time(),
        "worker_instance": INSTANCE_ID,
    }
    for raw in retrieval.get("local_receipts") or []:
        evidence["local"].append(_read_local(str(raw)))
    for url in retrieval.get("explicit_urls") or []:
        evidence["public_urls"].append(_fetch_public_url(str(url)))

    auth_sources = evidence.get("authenticated_sources") or {}
    platform_memory = evidence.get("platform_memory") or {}
    memory_useful = bool(platform_memory.get("library")) or bool(platform_memory.get("opportunities"))
    useful = bool(evidence["database_history"]) or bool(auth_sources.get("useful_evidence_found")) or memory_useful or any(x.get("ok") for x in evidence["local"]) or any(x.get("ok") for x in evidence["public_urls"])
    evidence["useful_evidence_found"] = useful
    RETRIEVAL_FILE.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")

    recorded = post_control({
        "action": "record_retrieval_evidence",
        "fix_id": focus.get("id"),
        "summary": "Fixer gathered repair evidence for retrieval round " + str(evidence.get("retrieval_round") or 1) + " across database, authenticated sources, platform memory, runtime receipts, and public URLs.",
        "evidence": evidence,
        "worker_instance": INSTANCE_ID,
        "pid": os.getpid(),
    })
    return {"evidence": evidence, "recorded": recorded}


def tick() -> dict:
    payload = post_control({"action": "tick", "worker_instance": INSTANCE_ID, "pid": os.getpid()})
    if payload.get("http_status") == 404:
        prior = {}
        try:
            if RECEIPT_FILE.exists():
                prior = json.loads(RECEIPT_FILE.read_text(encoding="utf-8"))
        except Exception:
            prior = {}
        focus = prior.get("focus") if isinstance(prior.get("focus"), dict) else None
        fallback = report_fallback_event(
            "Fixer alive; primary control endpoint unavailable, preserving local focus.",
            {"worker": "fixer", "worker_instance": INSTANCE_ID, "pid": os.getpid(), "mode": "fallback_heartbeat", "primary_control_status": 404, "focus": focus},
        )
        return {"ok": bool(fallback.get("ok")), "mode": "fallback_heartbeat", "primary_control_status": 404, "fallback": fallback, "focus": focus}
    retrieval = gather_retrieval(payload)
    if retrieval:
        payload["retrieval_result"] = retrieval
    return payload


def write_receipt(payload: dict) -> None:
    safe = dict(payload)
    safe["production_project_ref"] = PROJECT_REF
    safe["control_endpoint_host"] = f"{PROJECT_REF}.supabase.co"
    safe["worker_instance"] = INSTANCE_ID
    safe["pid"] = os.getpid()
    safe["written_at"] = time.time()
    try:
        import sys
        private_root = str(HOME / "PersonalIntelligence")
        if private_root not in sys.path:
            sys.path.insert(0, private_root)
        from unk_fixer_team_memory import ingest
        safe["team_memory_bridge"] = ingest(safe)
    except Exception as e:
        safe["team_memory_bridge"] = {"recorded": False, "error_type": type(e).__name__}
    RECEIPT_FILE.write_text(json.dumps(safe, indent=2, default=str), encoding="utf-8")


def main() -> None:
    log(f"fixer_started instance={INSTANCE_ID} pid={os.getpid()}")
    while True:
        try:
            result = tick()
            write_receipt(result)
            focus = result.get("focus") or {}
            retrieval = result.get("retrieval_result") or {}
            if retrieval:
                log("retrieval_completed focus=" + str(focus.get("id") or "none") + " recorded=" + str(bool((retrieval.get("recorded") or {}).get("ok"))))
            if result.get("ok"):
                log("tick_ok focus=" + str(focus.get("id") or "none") + " severity=" + str(focus.get("severity") or "") + " awaiting_verification=" + str(bool(focus.get("awaiting_verification"))))
            else:
                log("tick_failed error=" + str(result.get("error") or result.get("heartbeat_error") or "unknown"))
        except Exception as exc:
            write_receipt({"ok": False, "error": type(exc).__name__, "detail": str(exc)[:500]})
            log(f"tick_exception type={type(exc).__name__}")
        time.sleep(max(30, LOOP_SECONDS))


if __name__ == "__main__":
    main()
