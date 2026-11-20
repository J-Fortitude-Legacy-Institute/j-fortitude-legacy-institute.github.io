#!/usr/bin/env python3
"""
Unk Supervisor
==============
Health watchdog for unk_companion.py. Enforces the rule:

  "An update is only successful if Unk comes back online and resumes work
   without Jason having to drive to the office."

What this does (every 60 seconds):
  1. Is unk_companion.py running?  If not -> launch it.
  2. Has it written a fresh heartbeat sidecar in the last 3 minutes?
     If not -> kill the PID and relaunch.
  3. Track consecutive restart failures. Exponential backoff:
     30s -> 60s -> 2m -> 5m -> 10m (cap).
     A clean 10-min uptime resets the counter.
  4. After 5 consecutive verified-failed restarts, POST an escalation to
     desktop-supervisor-report with the last 50 log lines. Keep trying,
     but stop paging.
  5. Touch a local liveness marker even during restart/backoff cycles so the
     Windows keepalive task can distinguish "supervisor dead" from "child
     being recovered" and restart only when the supervisor itself is stale.

What this does NOT do:
  - It does NOT decide whether an update was successful.  That decision is
    made server-side (desktop-update-verify) so a wedged companion can't
    lie about its own health.
  - It does NOT ship new companion code.  self_update inside unk_companion.py
    still does that.  The supervisor just enforces that the process stays up.

Run manually:   python3 unk_supervisor.py
Install (Windows, one time, at the desktop): install_supervisor.ps1
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


# --- config -----------------------------------------------------------------

HERE = Path(__file__).resolve().parent
COMPANION_SCRIPT = HERE / "unk_companion.py"
HOME = Path(os.path.expanduser("~"))
COMPANION_DIR = HOME / ".unk-companion"
COMPANION_DIR.mkdir(exist_ok=True)
HEARTBEAT_FILE = COMPANION_DIR / "heartbeat.json"      # written by unk_companion each tick
PID_FILE       = COMPANION_DIR / "supervisor_child.pid"
SUP_LOG        = COMPANION_DIR / "supervisor.log"
CRED_FILE      = COMPANION_DIR / "device.json"
LIVENESS_FILE  = COMPANION_DIR / "supervisor_alive.marker"   # touched every tick; used to detect power loss on next boot

CHECK_EVERY_SECS       = 60
HEARTBEAT_STALE_SECS   = 180        # 3 minutes = restart
ESCALATE_AFTER         = 5          # consecutive verified-failed restarts
HEALTHY_RESET_SECS     = 600        # 10-min clean run resets backoff
BACKOFF_LADDER         = [30, 60, 120, 300, 600]
POLL_REPORT_EVERY_SECS = 60         # durable proof that the supervisor task is alive

# Safe-mode phase pull: if the companion cannot stay alive long enough to drain
# its own action queue, the supervisor installs the queued self_update itself.
PHASE_PULL_AFTER_FAILURES = 2       # consecutive failed restarts before safe mode
PHASE_PULL_COOLDOWN_SECS  = 900     # never pull the same phase more than once/15min
PHASE_PULL_STATE_FILE_NAME = "supervisor_phase_pull.json"


# Infrastructure recovery doctrine (see README "Infrastructure Recovery"):
#   software failure → supervisor restarts the process
#   browser failure  → companion self-repairs Playwright/Chromium
#   power failure    → BIOS "Restore on AC Power Loss = On" boots the PC,
#                      supervisor auto-starts, and we log a power_return event
#   internet outage  → companion keeps retrying; nothing to restart locally
# Recommend a small UPS on Ground Zero so short blinks don't interrupt work.
POWER_RETURN_UPTIME_MAX_SECS = 300   # if system uptime < 5 min at start → suspected power_return

# Public creds baked into unk_companion.py — supervisor mirrors so it can call the report endpoint.
# The supervisor reports only to owner Project K, never an inherited legacy override.
SUPABASE_URL = "https://kwbegsybeyyxfmavjswv.supabase.co"
SUPABASE_ANON_KEY = os.environ.get("UNK_SUPABASE_ANON_KEY") or ""
REPORT_URL = f"{SUPABASE_URL}/functions/v1/desktop-supervisor-report"
START_REQUEST_FILE = COMPANION_DIR / "last_process_start_request.json"
KEEPALIVE_SCRIPT = HERE / "unk_keepalive.ps1"


def _claim_single_supervisor() -> bool:
    """Use a machine-local Windows mutex so task/logon/unlock triggers cannot
    create overlapping supervisors (and therefore overlapping console windows)."""
    if os.name != "nt":
        return True
    try:
        import ctypes  # type: ignore
        handle = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\JFortitudeUnkSupervisor")
        if not handle:
            return False
        # ERROR_ALREADY_EXISTS means another supervisor already owns the job.
        return ctypes.windll.kernel32.GetLastError() != 183
    except Exception:
        return True

# --- logging ----------------------------------------------------------------

def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with SUP_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _touch_liveness() -> None:
    try:
        LIVENESS_FILE.touch(exist_ok=True)
        os.utime(LIVENESS_FILE, None)
    except Exception:
        pass


def _sleep_with_liveness(seconds: float) -> None:
    deadline = time.time() + max(0.0, seconds)
    while time.time() < deadline:
        _touch_liveness()
        time.sleep(min(15.0, max(0.0, deadline - time.time())))


# --- credential loading -----------------------------------------------------

def _load_device_creds() -> tuple[str, str] | None:
    # Prefer keyring, mirror unk_companion.py behavior.
    try:
        import keyring  # type: ignore
        did = keyring.get_password("unk-companion", "device_id")
        dkey = keyring.get_password("unk-companion", "device_key")
        if did and dkey:
            return did, dkey
    except Exception:
        pass
    if CRED_FILE.exists():
        try:
            data = json.loads(CRED_FILE.read_text())
            did = data.get("device_id"); dkey = data.get("device_key")
            if did and dkey:
                return did, dkey
            # keyring-only variant: id in file, key in keyring.
            if did:
                try:
                    import keyring  # type: ignore
                    dkey = keyring.get_password("unk-companion", "device_key")
                    if dkey:
                        return did, dkey
                except Exception:
                    pass
        except Exception:
            pass
    return None


def report(action: str, body: dict) -> dict | None:
    creds = _load_device_creds()
    if not creds:
        log("report skipped: no device credentials on disk yet.")
        return None
    device_id, device_key = creds
    try:
        import urllib.request
        req = urllib.request.Request(
            REPORT_URL,
            method="POST",
            headers={
                **({"apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {SUPABASE_ANON_KEY}"}
                   if SUPABASE_ANON_KEY else {}),
                "Content-Type": "application/json",
                "X-Device-Id": device_id,
                "X-Device-Key": device_key,
            },
            data=json.dumps({"action": action, **body}).encode("utf-8"),
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw) if raw else None
            except Exception:
                return None
    except Exception as e:
        log(f"report({action}) failed: {e}")
    return None


# --- child process management ----------------------------------------------

def _child_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except Exception:
        return None


def _is_alive(pid: int) -> bool:
    if pid <= 0: return False
    if os.name == "nt":
        try:
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, timeout=5)
            return str(pid) in (out.stdout or "")
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _kill(pid: int) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], capture_output=True, timeout=10)
        else:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            try: os.kill(pid, signal.SIGKILL)
            except Exception: pass
    except Exception as e:
        log(f"_kill({pid}) failed: {e}")


def _launch_child() -> int | None:
    if not COMPANION_SCRIPT.exists():
        log(f"FATAL: {COMPANION_SCRIPT} not found")
        return None
    creation_flags = 0
    stdout = subprocess.DEVNULL
    stderr = subprocess.DEVNULL
    if os.name == "nt":
        creation_flags = 0x08000000  # CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(
            [sys.executable, str(COMPANION_SCRIPT)],
            cwd=str(HERE),
            stdout=stdout,
            stderr=stderr,
            close_fds=True,
            creationflags=creation_flags,
        )
        PID_FILE.write_text(str(proc.pid))
        log(f"launched unk_companion.py pid={proc.pid}")
        return proc.pid
    except Exception as e:
        log(f"_launch_child failed: {e}\n{traceback.format_exc()}")
        return None


# --- heartbeat check --------------------------------------------------------

def _heartbeat_age_secs() -> float | None:
    if not HEARTBEAT_FILE.exists():
        return None
    try:
        data = json.loads(HEARTBEAT_FILE.read_text())
        ts = data.get("at")
        if isinstance(ts, (int, float)):
            return max(0.0, time.time() - float(ts))
    except Exception:
        pass
    # fallback to file mtime
    try:
        return max(0.0, time.time() - HEARTBEAT_FILE.stat().st_mtime)
    except Exception:
        return None


def _log_tail(n: int = 50) -> str:
    lines: list[str] = []
    for path in (SUP_LOG, COMPANION_DIR / "companion.log"):
        if path.exists():
            try:
                with path.open("r", encoding="utf-8", errors="ignore") as f:
                    tail = f.readlines()[-n:]
                lines.append(f"--- {path.name} ---\n" + "".join(tail))
            except Exception:
                pass
    return "\n".join(lines)[-8000:]


def _heartbeat_payload() -> dict | None:
    if not HEARTBEAT_FILE.exists():
        return None
    try:
        data = json.loads(HEARTBEAT_FILE.read_text())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _fresh_heartbeat_since(started_at: float, timeout_secs: int = 90) -> tuple[bool, dict | None]:
    deadline = time.time() + timeout_secs
    latest = _heartbeat_payload()
    while time.time() < deadline:
        payload = _heartbeat_payload()
        latest = payload or latest
        ts = payload.get("at") if payload else None
        if isinstance(ts, (int, float)) and float(ts) >= started_at and payload.get("boot") is not True:
            return True, payload
        time.sleep(3)
    return False, latest


def _process_start_request(req: dict | None) -> None:
    if not req or not isinstance(req, dict):
        return
    request_id = str(req.get("id") or "")
    if not request_id:
        return
    try:
        seen = json.loads(START_REQUEST_FILE.read_text()).get("id") if START_REQUEST_FILE.exists() else None
        if seen == request_id:
            return
    except Exception:
        pass

    mode = "start" if req.get("mode") == "start" else "restart"
    before_pid = _child_pid()
    before_alive = before_pid is not None and _is_alive(before_pid)
    before_hb_age = _heartbeat_age_secs()
    started_at = time.time()
    log(f"process_start_requested id={request_id} mode={mode} before_pid={before_pid} before_alive={before_alive}")

    try:
        if mode == "restart" and before_alive and before_pid:
            log(f"manual recovery killing child pid={before_pid}")
            _kill(before_pid)
            time.sleep(2)
        pid = _launch_child()
        if not pid:
            report("event", {
                "event_kind": "process_start_failed",
                "message": "Ground Zero process start failed: companion launch returned no PID.",
                "evidence": {
                    "request_id": request_id,
                    "mode": mode,
                    "before_pid": before_pid,
                    "before_alive": before_alive,
                    "before_heartbeat_age_secs": before_hb_age,
                    "log_tail": _log_tail(50),
                },
            })
            START_REQUEST_FILE.write_text(json.dumps({"id": request_id, "at": time.time(), "ok": False}))
            return

        heartbeat_ok, heartbeat_payload = _fresh_heartbeat_since(started_at)
        event_kind = "process_start_receipt" if heartbeat_ok else "process_start_failed"
        message = (
            "Ground Zero companion process started and produced a fresh heartbeat."
            if heartbeat_ok else
            "Ground Zero companion process was launched, but no fresh heartbeat arrived before timeout. Inspect companion.log on the PC."
        )
        report("event", {
            "event_kind": event_kind,
            "message": message,
            "evidence": {
                "request_id": request_id,
                "mode": mode,
                "before_pid": before_pid,
                "before_alive": before_alive,
                "before_heartbeat_age_secs": before_hb_age,
                "started_pid": pid,
                "heartbeat_confirmed": heartbeat_ok,
                "heartbeat_payload": heartbeat_payload,
                "after_heartbeat_age_secs": _heartbeat_age_secs(),
                "log_tail": _log_tail(50),
            },
        })
        START_REQUEST_FILE.write_text(json.dumps({"id": request_id, "at": time.time(), "ok": heartbeat_ok, "pid": pid}))
    except Exception as e:
        log(f"process_start_request failed: {e}\n{traceback.format_exc()}")
        report("event", {
            "event_kind": "process_start_failed",
            "message": f"Ground Zero process start failed: {e}",
            "evidence": {"request_id": request_id, "mode": mode, "trace": traceback.format_exc(limit=4), "log_tail": _log_tail(50)},
        })
        try:
            START_REQUEST_FILE.write_text(json.dumps({"id": request_id, "at": time.time(), "ok": False}))
        except Exception:
            pass


# --- safe-mode phase pull ----------------------------------------------------

PHASE_PULL_STATE = COMPANION_DIR / PHASE_PULL_STATE_FILE_NAME


def _phase_pull_recently_tried(request_id: str) -> bool:
    try:
        state = json.loads(PHASE_PULL_STATE.read_text())
        if state.get("request_id") == request_id and (time.time() - float(state.get("at", 0))) < PHASE_PULL_COOLDOWN_SECS:
            return True
    except Exception:
        pass
    return False


def _remember_phase_pull(request_id: str, ok: bool) -> None:
    try:
        PHASE_PULL_STATE.write_text(json.dumps({"request_id": request_id, "at": time.time(), "ok": ok}))
    except Exception:
        pass


def _install_phase_zip(zip_url: str, expect_sha: str | None) -> dict:
    """Download the queued companion package and copy source files over the
    running install. Mirrors cap_self_update in unk_companion.py, but runs from
    the supervisor so a crash-looping companion can still be upgraded."""
    # A still-queued legacy release cannot overwrite the canonical K runtime.
    if "pefatniumnrxwbgnwvvh" in str(zip_url).lower():
        return {"ok": False, "error": "retired_legacy_release_source"}

    import hashlib
    import io
    import shutil
    import urllib.request
    import zipfile

    bust = zip_url + ("&" if "?" in zip_url else "?") + f"cb={int(time.time())}"
    req = urllib.request.Request(bust, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    if len(raw) > 50 * 1024 * 1024:
        return {"ok": False, "error": "zip_too_large", "bytes": len(raw)}

    sha = hashlib.sha256(raw).hexdigest()
    if expect_sha and expect_sha != sha:
        return {"ok": False, "error": "zip_hash_mismatch", "expected_sha256": expect_sha, "downloaded_sha256": sha}

    stage = COMPANION_DIR / f"supervisor-stage-{int(time.time())}"
    stage.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for name in zf.namelist():
                if name.startswith("/") or ".." in Path(name).parts:
                    return {"ok": False, "error": "bad_zip_entry", "entry": name}
            zf.extractall(stage)

        entries = list(stage.iterdir())
        src_root = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage
        if not (src_root / "unk_companion.py").exists():
            return {"ok": False, "error": "package_missing_companion"}

        backup = COMPANION_DIR / f"supervisor-backup-{int(time.time())}"
        backup.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for src in src_root.rglob("*"):
            if not src.is_file() or src.suffix.lower() not in (".py", ".bat", ".sh", ".ps1", ".md", ".vbs"):
                continue
            rel = src.relative_to(src_root)
            dest = HERE / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                bdest = backup / rel
                bdest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(dest, bdest)
                except Exception:
                    pass
            shutil.copy2(src, dest)
            copied.append(str(rel))
        return {"ok": True, "files": len(copied), "zip_sha256": sha, "backup": str(backup), "build_ref": zip_url}
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _try_phase_pull(reason: str) -> bool:
    """Ask the backend for a queued self_update and install it locally.
    Returns True if new code was installed (caller should relaunch)."""
    resp = report("pending_phase", {})
    phase = (resp or {}).get("pending_phase")
    if not phase or not phase.get("zip_url"):
        return False
    request_id = str(phase.get("request_id") or "")
    if _phase_pull_recently_tried(request_id):
        return False

    log(f"safe-mode phase pull starting ({reason}) :: {phase.get('intent_summary') or phase.get('zip_url')}")
    try:
        result = _install_phase_zip(str(phase["zip_url"]), phase.get("expect_zip_sha256"))
    except Exception as e:
        result = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    _remember_phase_pull(request_id, bool(result.get("ok")))
    report("phase_pull_result", {
        "request_id": request_id,
        "ok": bool(result.get("ok")),
        "error": result.get("error"),
        "result": {**result, "reason": reason},
    })
    if result.get("ok"):
        log(f"safe-mode phase pull installed {result.get('files')} file(s) from {phase.get('zip_url')}")
        return True
    log(f"safe-mode phase pull failed: {result.get('error')}")
    return False


# --- main loop --------------------------------------------------------------


def _system_uptime_secs() -> float | None:
    """Best-effort machine uptime. Used to distinguish 'we just booted after a
    power blip' from 'the supervisor just restarted itself'."""
    try:
        if os.name == "nt":
            import ctypes  # type: ignore
            return float(ctypes.windll.kernel32.GetTickCount64()) / 1000.0
        # POSIX
        with open("/proc/uptime", "r") as f:
            return float(f.readline().split()[0])
    except Exception:
        return None


def _detect_power_return() -> dict | None:
    """If the last alive-marker is stale AND the OS just booted, this looks
    like a power outage / hard shutdown that BIOS recovered from."""
    up = _system_uptime_secs()
    marker_age = None
    if LIVENESS_FILE.exists():
        try:
            marker_age = time.time() - LIVENESS_FILE.stat().st_mtime
        except Exception:
            marker_age = None
    if up is None or marker_age is None:
        return None
    if up < POWER_RETURN_UPTIME_MAX_SECS and marker_age > (CHECK_EVERY_SECS * 5):
        return {
            "system_uptime_secs": int(up),
            "supervisor_marker_age_secs": int(marker_age),
            "estimated_downtime_secs": int(marker_age - up),
        }
    return None


def run() -> None:
    if not _claim_single_supervisor():
        log("Supervisor already running; duplicate launch suppressed.")
        return
    log(f"Supervisor starting. companion={COMPANION_SCRIPT} heartbeat={HEARTBEAT_FILE}")
    _touch_liveness()
    report("event", {
        "event_kind": "supervisor_online",
        "message": "Unk supervisor is up.",
        "evidence": {
            "supervisor_pid": os.getpid(),
            "supervisor_script": str(Path(__file__).resolve()),
            "keepalive_script_present": KEEPALIVE_SCRIPT.exists(),
            "liveness_marker": str(LIVENESS_FILE),
        },
    })

    power_evidence = _detect_power_return()
    if power_evidence:
        log(f"power_return detected — {power_evidence}")
        report("event", {
            "event_kind": "power_return",
            "message": (
                "Machine booted after a suspected power interruption "
                f"(~{power_evidence['estimated_downtime_secs']}s downtime). "
                "Supervisor and companion auto-resumed."
            ),
            "evidence": {"failure_class": "power", **power_evidence},
        })

    consecutive_failures = 0
    last_launch_at = 0.0
    backoff_idx = 0
    last_poll_report_at = 0.0

    while True:
        try:
            _touch_liveness()
            pid = _child_pid()
            alive = pid is not None and _is_alive(pid)
            hb_age = _heartbeat_age_secs()

            needs_restart = False
            reason = ""
            if not alive:
                needs_restart = True
                reason = f"process not running (pid={pid})"
            elif hb_age is None:
                # Fresh launch – give it up to HEARTBEAT_STALE_SECS to produce the first sidecar.
                if time.time() - last_launch_at > HEARTBEAT_STALE_SECS:
                    needs_restart = True
                    reason = "no heartbeat.json ever written"
            elif hb_age > HEARTBEAT_STALE_SECS:
                needs_restart = True
                reason = f"heartbeat stale for {int(hb_age)}s"

            if needs_restart:
                # Reset failure counter if the previous run was healthy for a while.
                if last_launch_at and (time.time() - last_launch_at) > HEALTHY_RESET_SECS and hb_age is not None:
                    consecutive_failures = 0
                    backoff_idx = 0

                if alive and pid:
                    log(f"killing wedged child pid={pid} — {reason}")
                    _kill(pid)

                consecutive_failures += 1
                event_kind = "heartbeat_stale_restart" if hb_age is not None else "restarted"
                log(f"restart #{consecutive_failures} — {reason}")
                report("event", {
                    "event_kind": event_kind,
                    "message": f"Supervisor restart: {reason}",
                    "evidence": {"consecutive_failures": consecutive_failures, "heartbeat_age_secs": hb_age},
                })

                if consecutive_failures == ESCALATE_AFTER:
                    log(f"ESCALATION: {ESCALATE_AFTER} consecutive verified-failed restarts")
                    report("escalation", {
                        "alert_kind": "restart_loop_failed",
                        "severity": "critical",
                        "message": f"Unk supervisor has failed to bring companion back {ESCALATE_AFTER} times in a row. Last reason: {reason}",
                        "log_tail": _log_tail(50),
                        "consecutive_failures": consecutive_failures,
                    })

                # Safe mode: after repeated failures, the queued phase is often
                # the fix (or the cause). Pull and install it here so recovery
                # never depends on the companion draining its own queue.
                pulled = False
                if consecutive_failures >= PHASE_PULL_AFTER_FAILURES:
                    try:
                        pulled = _try_phase_pull(reason)
                    except Exception as pull_exc:
                        log(f"phase pull error: {pull_exc}")
                    if pulled:
                        # New code on disk — reset backoff and relaunch immediately.
                        backoff_idx = 0
                        consecutive_failures = 0

                _launch_child()
                last_launch_at = time.time()
                delay = 5 if pulled else BACKOFF_LADDER[min(backoff_idx, len(BACKOFF_LADDER) - 1)]
                if not pulled:
                    backoff_idx += 1
                _sleep_with_liveness(delay)
                continue


            # Healthy tick.
            if consecutive_failures and last_launch_at and (time.time() - last_launch_at) > HEALTHY_RESET_SECS:
                log("healthy for 10+ min — clearing failure counter")
                consecutive_failures = 0
                backoff_idx = 0

            # Touch the liveness marker so a hard shutdown leaves a detectable gap.
            _touch_liveness()

            # Durable polling receipt: this is the evidence the web panel needs.
            # A process-only local marker is not enough once Jason is away from the desk.
            if time.time() - last_poll_report_at >= POLL_REPORT_EVERY_SECS:
                response = report("event", {
                    "event_kind": "supervisor_poll",
                    "message": "Unk supervisor poll check passed.",
                    "evidence": {
                        "child_pid": pid,
                        "child_alive": alive,
                        "heartbeat_age_secs": hb_age,
                        "consecutive_failures": consecutive_failures,
                        "poll_interval_secs": CHECK_EVERY_SECS,
                    },
                })
                _process_start_request((response or {}).get("pending_process_start_request"))
                last_poll_report_at = time.time()

            _sleep_with_liveness(CHECK_EVERY_SECS)


        except KeyboardInterrupt:
            log("supervisor stopped by user")
            report("event", {"event_kind": "supervisor_stopped", "message": "KeyboardInterrupt"})
            return
        except Exception as loop_exc:
            log(f"supervisor loop error: {loop_exc}\n{traceback.format_exc()}")
            _sleep_with_liveness(30)


if __name__ == "__main__":
    run()
