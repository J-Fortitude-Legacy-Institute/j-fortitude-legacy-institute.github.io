"""
Unk Desktop Companion (Phase 3)
================================
Single-file Windows companion that pairs with the JFLI platform and executes
APPROVED desktop actions inside a strict permission profile.

Lifecycle:
  1. First run with no stored credentials  -> prompts for enrollment code
     (generated from /grant-engine/desktop-command) and POSTs
     action=enroll_complete to the desktop-companion edge function.
  2. Receives a one-time device_key, stores it in Windows Credential Manager
     (falls back to a 0600 file on non-Windows).
  3. Loops forever: every POLL_SECONDS sends action=heartbeat with a status
     snapshot and receives pending_actions (already approved server-side).
    4. Executes each action through a whitelisted handler. NO arbitrary shell.
      NO action without a server-approved request row. Admin elevation is only
      allowed for pre-shipped maintenance scripts under the install directory.

Hard rules baked in (mirror the platform Change Gate):
  - Runs as the logged-in user, never SYSTEM / never elevated.
  - Only capabilities in CAPABILITY_HANDLERS are executable; everything else
    is reported back as 'unsupported_capability'.
  - File ops are confined to ALLOWED_ROOTS. Path traversal is rejected.
  - Process launches are confined to ALLOWED_EXECUTABLES (basename match).
  - URLs (open_url, download_url_to_folder) must match URL_ALLOWLIST and
    must NOT match URL_HARD_BLOCKLIST (banking / brokerage / IRS / payroll).
  - open_file rejects executable / script file types regardless of folder.
  - append_to_file is append-only, never overwrite/delete.
  - Results (stdout tail, exit code, screenshot path) are posted back via
    action=action_result so the Post-Test Review loop has evidence.

Usage:
    python unk_companion.py            # normal run
    python unk_companion.py --enroll   # force re-enrollment
    python unk_companion.py --status   # one-shot heartbeat, print result, exit

Dependencies (stdlib only by default):
    pip install requests pillow    # pillow only needed for screenshots
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import uuid

# Stable per-process identity (generated once at import). Used by the
# persistence-repair-runner await_respawn phase to prove restart via a
# strictly-changed instance_id + boot_ts pair instead of a fuzzy pid+ts guess.
INSTANCE_ID = uuid.uuid4().hex
BOOT_TS = time.time()
COMPANION_VERSION = "phase71-device-vault-bridge"
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


try:
    import requests
except Exception:
    print("Missing Python dependency: requests")
    print("Run this first, then start the companion again:")
    print("  python -m pip install requests pillow keyring")
    try:
        input("\nPress Enter to close...")
    except Exception:
        pass
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPABASE_PROJECT_REF = "kwbegsybeyyxfmavjswv"
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()
FUNCTIONS_BASE = f"https://{SUPABASE_PROJECT_REF}.supabase.co/functions/v1"
COMPANION_URL = f"{FUNCTIONS_BASE}/desktop-companion"

POLL_SECONDS = 15
HTTP_TIMEOUT = 30

HOME = Path.home()
COMPANION_DIR = HOME / ".unk-companion"
COMPANION_DIR.mkdir(exist_ok=True)
CRED_FILE = COMPANION_DIR / "device.json"
LOG_FILE = COMPANION_DIR / "companion.log"
SCREENSHOT_DIR = COMPANION_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR = HOME / "Downloads" / "Unk"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
RUNNING_BUILD_FILE = COMPANION_DIR / "running_build.json"
BACKGROUND_WORKER_REGISTRY_FILE = COMPANION_DIR / "background_workers.json"

# Permission profile -- edit these to widen/narrow what Unk can touch.
# The companion's own install directory is included so read-only self-diagnosis
# (worker logs, supervisor log) is possible without a human opening the machine.
# Without it, "is the mirror worker actually running?" is unanswerable remotely.
ALLOWED_ROOTS = [
    HOME / "Documents" / "JFLI",
    HOME / "Documents" / "Bot-Fresh",
    HOME / "Documents" / "Grants",
    HOME / "Documents" / "BAMA",
    DOWNLOAD_DIR,
    COMPANION_DIR,
    Path(__file__).resolve().parent,
]

ALLOWED_EXECUTABLES = {
    "python.exe", "python", "pythonw.exe",
    "Bot-Fresh.py",       # launched via python
    "notepad.exe",
}

# --- Canonical trading-bot runtime -----------------------------------------
# The Coinbase Advanced bot runtime lives at the user-profile root and MUST
# keep the name Bot-Fresh.py. HOME itself is deliberately NOT an allowed root
# (far too broad); only this exact file, and its directory used as a working
# directory, are reachable. Nothing here touches strategy, thresholds,
# credentials, or the live-trading gate -- launch + read-only probe only.
BOT_FRESH_PATH = HOME / "Bot-Fresh.py"
BOT_FRESH_DIR = BOT_FRESH_PATH.parent
BOT_FRESH_LOG = BOT_FRESH_DIR / "bot-fresh.out.log"
ALLOWED_EXACT_FILES = {BOT_FRESH_PATH, BOT_FRESH_LOG}
ALLOWED_EXACT_CWDS = {BOT_FRESH_DIR}

# Tier-2 URL allow-list. Anything outside is refused at the companion.
URL_ALLOWLIST = {
    # Trading + market data
    "tradingview.com", "www.tradingview.com",
    "coinbase.com", "www.coinbase.com", "pro.coinbase.com",
    # JFLI / BAMA infrastructure
    "drive.google.com", "docs.google.com", "calendar.google.com",
    # Google Cloud console — service-account provisioning only. No billing,
    # no payment surfaces; Unk stops at any human-only gate.
    "console.cloud.google.com",
    "mail.google.com", "meet.google.com",
    "blackarchives.org", "www.blackarchives.org",
    "jfortitude.com", "www.jfortitude.com",
    "jfortitudelegacyinstitute.org", "www.jfortitudelegacyinstitute.org",
    # Meta/Facebook browser-assisted Page publishing. Personal profiles remain
    # human-only; Unk only opens authorized Page surfaces and never touches
    # passwords, 2FA, payments, banking, or identity checks.
    "facebook.com", "www.facebook.com", "business.facebook.com",
    "meta.com", "www.meta.com", "developers.facebook.com",
    # Funder / grant portals
    "grants.gov", "www.grants.gov",
    "ojp.gov", "www.ojp.gov", "bja.ojp.gov",
    "epa.gov", "www.epa.gov",
    "ded.mo.gov", "www.ded.mo.gov",
    "instrumentl.com", "www.instrumentl.com",
    "submittable.com", "www.submittable.com",
    "kauffman.org", "www.kauffman.org",
    "humanitiescouncil.org", "www.humanitiescouncil.org",
    "mohumanities.org", "www.mohumanities.org",
    # Lovable platform (so Unk can open his own dashboards)
    "lovable.app", "lovable.dev",
    # AI provider dashboards Unk is authorized to drive Jason to for API-key
    # creation. Unk NEVER touches the key value itself — Jason still copies from
    # OpenAI and pastes into the Lovable secret form. Unk just opens the tabs.
    "platform.openai.com",
    # LinkedIn profile build-out escort. Unk opens the authorized edit
    # surfaces for the approved identity and stages copy on the clipboard.
    # He never enters passwords, 2FA codes, or identity checks.
    "linkedin.com", "www.linkedin.com",
    # ChatGPT connector escort. Unk opens the connector settings surface so the
    # JFLI Grant Engine MCP connector can be removed and re-added after the
    # OAuth consent route shipped. No passwords, 2FA, or payment surfaces.
    "chatgpt.com", "chat.openai.com",
}

# Browser-compatible public-source headers. These contain no credentials and
# let official funder/CDN endpoints serve the same public files shown in a browser.
PUBLIC_DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JFortitude-Unk/phase69",
    "Accept": "application/pdf,text/html,application/xhtml+xml,application/octet-stream;q=0.9,*/*;q=0.8",
}

# Hard block — Unk REFUSES these even if every other check would pass.
# Banking, brokerage, IRS, payroll. Human-only, full stop.
URL_HARD_BLOCKLIST_SUBSTRINGS = [
    "irs.gov", "eftps.gov", "sam.gov",
    "chase.com", "wellsfargo.com", "bankofamerica.com", "usbank.com",
    "fidelity.com", "schwab.com", "vanguard.com", "etrade.com", "robinhood.com",
    "tdameritrade.com", "interactivebrokers.com",
    "gusto.com", "adp.com", "paychex.com", "quickbooks.intuit.com",
    "stripe.com/login", "dashboard.stripe.com",
]

# File-type deny-list for open_file (executables / scripts / installers).
OPEN_FILE_DENY_EXT = {
    ".exe", ".bat", ".cmd", ".com", ".scr", ".pif",
    ".msi", ".msp", ".ps1", ".psm1", ".vbs", ".vbe", ".js", ".wsf",
    ".jar", ".reg", ".lnk",
}

CLIPBOARD_MAX_CHARS = 8_000
DOWNLOAD_MAX_BYTES = 25 * 1024 * 1024  # 25 MB cap
APPEND_MAX_BYTES = 1 * 1024 * 1024     # 1 MB per append call

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def pause_before_exit() -> None:
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPress Enter to close...")
    except Exception:
        pass

def fatal(message: str, code: int = 1) -> None:
    log(f"FATAL: {message}")
    pause_before_exit()
    raise SystemExit(code)

# ---------------------------------------------------------------------------
# Credential storage (Windows Credential Manager preferred, file fallback)
# ---------------------------------------------------------------------------

def _try_keyring_save(device_id: str, device_key: str) -> bool:
    try:
        import keyring  # type: ignore
        keyring.set_password("unk-companion", "device_id", device_id)
        keyring.set_password("unk-companion", "device_key", device_key)
        return True
    except Exception:
        return False

def _try_keyring_load() -> tuple[str, str] | None:
    try:
        import keyring  # type: ignore
        did = keyring.get_password("unk-companion", "device_id")
        dkey = keyring.get_password("unk-companion", "device_key")
        if did and dkey:
            return did, dkey
    except Exception:
        pass
    return None

def save_credentials(device_id: str, device_key: str) -> None:
    if _try_keyring_save(device_id, device_key):
        log("Saved device credentials to OS credential store.")
        CRED_FILE.write_text(json.dumps({"device_id": device_id, "stored": "keyring"}))
        return
    CRED_FILE.write_text(json.dumps({"device_id": device_id, "device_key": device_key}))
    try:
        os.chmod(CRED_FILE, 0o600)
    except Exception:
        pass
    log(f"Saved device credentials to {CRED_FILE} (keyring unavailable).")

def load_credentials() -> tuple[str, str] | None:
    kr = _try_keyring_load()
    if kr:
        return kr
    if not CRED_FILE.exists():
        return None
    try:
        data = json.loads(CRED_FILE.read_text())
        if "device_key" in data:
            return data["device_id"], data["device_key"]
    except Exception:
        return None
    return None

# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

def enroll_interactive() -> tuple[str, str]:
    print("=== Unk Desktop Companion :: Enrollment ===")
    print("1. Open /grant-engine/desktop-command on the platform.")
    print("2. Click 'Generate enrollment code'.")
    print("3. Paste the 8-character code below.\n")
    code = (os.environ.get("UNK_ENROLL_CODE") or "").strip().upper()
    if code:
        print("Enrollment code: read from UNK_ENROLL_CODE")
    else:
        code = input("Enrollment code: ").strip().upper()
    if len(code) < 6:
        fatal("Code too short. Aborting.")

    payload = {
        "action": "enroll_complete",
        "enrollment_code": code,
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
    }
    r = requests.post(
        COMPANION_URL,
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
    if r.status_code != 200:
        fatal(f"Enrollment failed: HTTP {r.status_code} :: {r.text}")
    data = r.json()
    device_id = data["device_id"]
    device_key = data["device_key"]
    save_credentials(device_id, device_key)
    log(f"Enrolled. device_id={device_id}")
    return device_id, device_key

# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

def expand_path(p) -> Path:
    """Expand ~ and %VARS% before any allow-list decision. Previously a payload
    like "~/Documents/Bot-Fresh" was compared literally and always failed."""
    return Path(os.path.expandvars(str(p))).expanduser()


def path_is_allowed(p: Path) -> bool:
    try:
        rp = expand_path(p).resolve()
    except Exception:
        return False
    for exact in ALLOWED_EXACT_FILES:
        try:
            if rp == exact.resolve():
                return True
        except Exception:
            continue
    return any(str(rp).startswith(str(root.resolve())) for root in ALLOWED_ROOTS)


def cwd_is_allowed(p: Path) -> bool:
    """Working directories: allow-listed roots plus the exact canonical bot dir."""
    try:
        rp = expand_path(p).resolve()
    except Exception:
        return False
    for exact in ALLOWED_EXACT_CWDS:
        try:
            if rp == exact.resolve():
                return True
        except Exception:
            continue
    return path_is_allowed(rp)


def _running_processes_matching(needle: str) -> list[dict]:
    """Real process identity, no guessing. Windows uses CIM; POSIX uses ps."""
    out: list[dict] = []
    try:
        if os.name == "nt":
            ps_cmd = (
                "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "
                f"'*{needle}*' " + "} | Select-Object ProcessId,CommandLine,CreationDate "
                "| ConvertTo-Json -Compress"
            )
            r = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=60,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            raw = (r.stdout or "").strip()
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict):
                    data = [data]
                for d in data or []:
                    cl = str(d.get("CommandLine") or "")
                    if "Get-CimInstance" in cl:
                        continue  # our own probe
                    try:
                        pid = int(d.get("ProcessId"))
                    except Exception:
                        continue
                    out.append({"pid": pid, "cmdline": cl,
                                "started_at": str(d.get("CreationDate") or "")})
        else:
            r = subprocess.run(["ps", "-eo", "pid=,args="],
                               capture_output=True, text=True, timeout=30)
            for line in (r.stdout or "").splitlines():
                line = line.strip()
                if needle.lower() in line.lower() and " -eo " not in line:
                    pid_s, _, args = line.partition(" ")
                    try:
                        out.append({"pid": int(pid_s), "cmdline": args.strip()})
                    except Exception:
                        continue
    except Exception as e:
        return [{"pid": None, "cmdline": "", "probe_error": str(e)}]
    return out


_BOT_CMD_RE = re.compile(r"python[a-z0-9._-]*(\.exe)?[\"'\s].*Bot-Fresh\.py", re.I)


def bot_fresh_processes() -> list[dict]:
    """Only real `python ... Bot-Fresh.py` runtimes. Excludes this companion,
    inline `-c` probes, and anything that merely mentions the filename."""
    me = os.getpid()
    out = []
    for p in _running_processes_matching("Bot-Fresh.py"):
        pid, cmd = p.get("pid"), str(p.get("cmdline") or "")
        if not pid or pid == me:
            continue
        if " -c " in cmd or cmd.strip().endswith(" -c"):
            continue
        if not _BOT_CMD_RE.search(cmd):
            continue
        out.append(p)
    return out


def bot_fresh_paper_mode() -> dict:
    """READ-ONLY confirmation that paper/dry-run is still the active mode.
    Never edits the file, never changes strategy or the live gate."""
    try:
        text = BOT_FRESH_PATH.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return {"readable": False, "error": str(e), "path": str(BOT_FRESH_PATH)}
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if re.match(r"^(DRY_RUN|PAPER[A-Z_]*|LIVE[A-Z_]*|SIMULAT[A-Z_]*|TRADING_MODE|MODE)\s*=", s, re.I):
            lines.append(s[:200])
        if len(lines) >= 25:
            break
    live_on = any(re.match(r"^(LIVE[A-Z_]*|ENABLE_LIVE[A-Z_]*)\s*=\s*(True|1)\b", l, re.I) for l in lines)
    dry_on = any(re.match(r"^(DRY_RUN|PAPER[A-Z_]*|SIMULAT[A-Z_]*)\s*=\s*(True|1)\b", l, re.I) for l in lines)
    return {"readable": True, "path": str(BOT_FRESH_PATH), "mode_lines": lines,
            "dry_run_flag_true": dry_on, "live_flag_true": live_on}


def bot_fresh_log_evidence(tail_bytes: int = 4000) -> dict:
    try:
        if not BOT_FRESH_LOG.exists():
            return {"exists": False, "path": str(BOT_FRESH_LOG)}
        st = BOT_FRESH_LOG.stat()
        with BOT_FRESH_LOG.open("rb") as f:
            if st.st_size > tail_bytes:
                f.seek(-tail_bytes, os.SEEK_END)
            tail = f.read().decode("utf-8", errors="ignore")
        return {"exists": True, "path": str(BOT_FRESH_LOG), "size_bytes": st.st_size,
                "modified_at": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                "age_seconds": int(time.time() - st.st_mtime), "tail": tail}
    except Exception as e:
        return {"exists": None, "error": str(e), "path": str(BOT_FRESH_LOG)}


def bot_fresh_snapshot() -> dict:
    procs = bot_fresh_processes()
    return {
        "runtime_path": str(BOT_FRESH_PATH),
        "runtime_exists": BOT_FRESH_PATH.exists(),
        "running": bool(procs),
        "pids": [p["pid"] for p in procs],
        "processes": procs,
        "log": bot_fresh_log_evidence(),
        "paper_mode": bot_fresh_paper_mode(),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

def executable_is_allowed(exe: str) -> bool:
    return Path(exe).name in ALLOWED_EXECUTABLES

def url_is_allowed(url: str) -> tuple[bool, str]:
    """Returns (allowed, reason). Hard block wins over allow-list."""
    if not url or not isinstance(url, str):
        return False, "empty_url"
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, "url_parse_failed"
    if parsed.scheme not in ("http", "https"):
        return False, f"scheme_not_allowed:{parsed.scheme}"
    host = (parsed.hostname or "").lower()
    if not host:
        return False, "no_host"
    full = url.lower()
    for blocked in URL_HARD_BLOCKLIST_SUBSTRINGS:
        if blocked in full:
            return False, f"hard_blocked:{blocked}"
    # Allow if host or any parent domain is in the allow-list.
    parts = host.split(".")
    for i in range(len(parts) - 1):
        candidate = ".".join(parts[i:])
        if candidate in URL_ALLOWLIST:
            return True, "ok"
    if host in URL_ALLOWLIST:
        return True, "ok"
    return False, f"host_not_in_allowlist:{host}"

def file_open_ext_allowed(p: Path) -> bool:
    return p.suffix.lower() not in OPEN_FILE_DENY_EXT

# ---------------------------------------------------------------------------
# Capability handlers
# Each returns a dict appended to the action result.
# ---------------------------------------------------------------------------

@dataclass
class ActionContext:
    action_id: str
    capability: str
    action_type: str
    payload: dict[str, Any]
    created_at: str | None = None

def cap_capture_screenshot(ctx: ActionContext) -> dict:
    try:
        from PIL import ImageGrab  # type: ignore
    except Exception:
        return {"ok": False, "error": "pillow_not_installed"}
    out = SCREENSHOT_DIR / f"{ctx.action_id}.png"
    img = ImageGrab.grab()
    img.save(out, format="PNG")
    return {"ok": True, "screenshot_path": str(out), "size": img.size}

def cap_read_file(ctx: ActionContext) -> dict:
    p = Path(ctx.payload.get("path", ""))
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    if not p.exists():
        return {"ok": False, "error": "not_found"}
    max_bytes = int(ctx.payload.get("max_bytes", 64_000))
    data = p.read_bytes()[:max_bytes]
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        text = repr(data)
    return {"ok": True, "bytes": len(data), "text": text}

def cap_write_file(ctx: ActionContext) -> dict:
    p = Path(ctx.payload.get("path", ""))
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    content = ctx.payload.get("content", "")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "bytes": len(content)}

def cap_append_to_file(ctx: ActionContext) -> dict:
    """Append-only. Never overwrites. Cap per call: APPEND_MAX_BYTES."""
    p = Path(ctx.payload.get("path", ""))
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    content = ctx.payload.get("content", "")
    if not isinstance(content, str):
        return {"ok": False, "error": "bad_content"}
    if len(content.encode("utf-8")) > APPEND_MAX_BYTES:
        return {"ok": False, "error": "content_too_large"}
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(content)
    return {"ok": True, "appended_bytes": len(content), "path": str(p)}

def _kill_pids(pids: list[int]) -> list[dict]:
    killed = []
    for pid in pids:
        try:
            if os.name == "nt":
                r = subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                   capture_output=True, text=True, timeout=30,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                killed.append({"pid": pid, "exit_code": r.returncode,
                               "out": (r.stdout or r.stderr or "").strip()[:200]})
            else:
                os.kill(pid, 9)
                killed.append({"pid": pid, "exit_code": 0, "out": "sigkill"})
        except Exception as e:
            killed.append({"pid": pid, "error": str(e)})
    return killed


def cap_launch_process(ctx: ActionContext) -> dict:
    """Canonical desktop process launch.

    Bot-Fresh.py gets extra handling, because a trading runtime must never be
    duplicated and a launch with no receipt is worthless:
      - idempotent: an existing Bot-Fresh.py process short-circuits the launch
      - correct cwd, so logs land beside the bot
      - stdout/stderr captured to bot-fresh.out.log (never DEVNULL)
      - post-launch re-probe returns real PID + log evidence + paper-mode read
    """
    exe = ctx.payload.get("executable", "")
    args = ctx.payload.get("args", [])
    if not executable_is_allowed(exe):
        return {"ok": False, "error": "executable_not_allowed", "executable": exe}
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        return {"ok": False, "error": "bad_args"}

    is_bot = any(str(a).lower().endswith("bot-fresh.py") for a in args) or \
        bool(ctx.payload.get("bot_fresh"))
    cwd_raw = ctx.payload.get("cwd")
    stdout_target = subprocess.DEVNULL
    stderr_target = subprocess.DEVNULL
    log_handle = None
    force_restart = bool(ctx.payload.get("force_restart"))
    killed: list[dict] = []

    if is_bot:
        target = BOT_FRESH_PATH
        for a in args:
            if str(a).lower().endswith("bot-fresh.py"):
                cand = expand_path(a)
                if cand.exists():
                    target = cand
                break
        if target.name != "Bot-Fresh.py":
            return {"ok": False, "error": "bot_runtime_name_locked", "given": target.name}
        if not target.exists():
            return {"ok": False, "error": "bot_runtime_missing",
                    "expected_path": str(BOT_FRESH_PATH)}
        if not path_is_allowed(target):
            return {"ok": False, "error": "path_not_allowed", "path": str(target)}
        # -u: unbuffered stdout so bot-fresh.out.log is a real heartbeat,
        # not a file that only updates when Python flushes its buffer.
        args = ["-u", str(target)]
        cwd_raw = cwd_raw or str(target.parent)

        existing = bot_fresh_processes()
        if existing and not force_restart:
            snap = bot_fresh_snapshot()
            snap.update({"ok": True, "launched": False, "already_running": True,
                         "pid": existing[0]["pid"],
                         "note": "idempotent: live Bot-Fresh.py process found; no duplicate launched"})
            return snap
        if existing and force_restart:
            killed = _kill_pids([p["pid"] for p in existing])
            time.sleep(2)

    cwd = None
    if cwd_raw:
        cp = expand_path(cwd_raw)
        if not cwd_is_allowed(cp):
            return {"ok": False, "error": "cwd_not_allowed", "cwd": str(cp)}
        cwd = str(cp)

    try:
        if is_bot:
            BOT_FRESH_LOG.parent.mkdir(parents=True, exist_ok=True)
            log_handle = BOT_FRESH_LOG.open("a", encoding="utf-8", errors="ignore")
            log_handle.write(
                f"\n=== Unk launch {datetime.now(timezone.utc).isoformat()} "
                f"action={ctx.action_id} ===\n")
            log_handle.flush()
            stdout_target = log_handle
            stderr_target = subprocess.STDOUT
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        launch_env = None
        if is_bot:
            # Windows consoles default to cp1252; the bot prints emoji in its
            # alert lines and dies with UnicodeEncodeError -> "Retrying in 20s".
            # Force UTF-8 on the child only. No strategy/credential change.
            launch_env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        proc = subprocess.Popen(
            [exe, *args],
            cwd=cwd,
            stdout=stdout_target,
            stderr=stderr_target,
            creationflags=creation_flags,
            env=launch_env,
        )
    except Exception as e:
        if log_handle:
            try:
                log_handle.close()
            except Exception:
                pass
        return {"ok": False, "error": "launch_failed", "detail": str(e)}
    finally:
        if log_handle:
            try:
                log_handle.close()
            except Exception:
                pass

    if not is_bot:
        return {"ok": True, "pid": proc.pid, "cwd": cwd}

    # Real evidence: give it a few seconds, then re-probe the OS.
    time.sleep(6)
    snap = bot_fresh_snapshot()
    alive = proc.poll() is None
    snap.update({
        "ok": alive and snap["running"],
        "launched": True,
        "already_running": False,
        "pid": proc.pid,
        "spawn_alive": alive,
        "spawn_exit_code": proc.returncode,
        "cwd": cwd,
        "killed_stale": killed,
        "executable": exe,
    })
    if not snap["ok"]:
        snap["error"] = "bot_exited_immediately"
    return snap

def cap_elevate_powershell_script(ctx: ActionContext) -> dict:
    """Trigger a UAC prompt on the logged-in user's desktop to run an
    approved .ps1 under this companion's own install dir with admin rights.

    Guardrails:
      - Windows only.
      - Script must live under %LOCALAPPDATA%\\UnkCompanion (durable install).
      - Script must be a .ps1 that already exists.
      - Uses Start-Process -Verb RunAs so Windows displays the UAC dialog.
        Jason must click Yes; we never bypass consent.
    """
    if platform.system() != "Windows":
        return {"ok": False, "error": "windows_only"}
    install_root = Path(os.environ.get("LOCALAPPDATA", "")) / "UnkCompanion"
    script_raw = str(ctx.payload.get("script", "") or "").strip()
    script_relative = str(ctx.payload.get("script_relative", "") or "").strip()
    if script_relative:
        rel = Path(script_relative)
        if rel.is_absolute() or ".." in rel.parts:
            return {"ok": False, "error": "bad_script_relative", "script_relative": script_relative}
        script_path = install_root / rel
    elif script_raw:
        script_path = Path(script_raw)
    else:
        return {"ok": False, "error": "script_required"}
    if script_path.suffix.lower() != ".ps1":
        return {"ok": False, "error": "not_ps1"}
    try:
        script_path = script_path.resolve()
        install_root_resolved = install_root.resolve()
    except Exception as e:
        return {"ok": False, "error": "path_resolve_failed", "detail": str(e)}
    if install_root_resolved not in script_path.parents and script_path.parent != install_root_resolved:
        return {"ok": False, "error": "script_outside_install_root",
                "expected_root": str(install_root_resolved), "given": str(script_path)}
    if not script_path.exists():
        return {"ok": False, "error": "script_missing", "path": str(script_path)}
    extra_args = ctx.payload.get("args", []) or []
    if not isinstance(extra_args, list) or not all(isinstance(a, str) for a in extra_args):
        return {"ok": False, "error": "bad_args"}
    # Build a single PowerShell -Command that spawns an elevated child.
    # Start-Process from a non-elevated parent triggers the UAC dialog.
    arg_list_parts = ["'-NoProfile'", "'-ExecutionPolicy'", "'Bypass'", "'-File'", f"'{script_path}'"]
    for a in extra_args:
        safe = a.replace("'", "''")
        arg_list_parts.append(f"'{safe}'")
    inner = f"Start-Process powershell.exe -Verb RunAs -ArgumentList {','.join(arg_list_parts)}"
    try:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", inner],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"ok": True, "pid": proc.pid, "script": str(script_path),
                "note": "uac_prompt_shown_to_user"}
    except Exception as e:
        return {"ok": False, "error": "elevate_launch_failed", "detail": str(e)}


# --- run_local_script (Ground Zero signed audit runner) --------------------
GROUND_ZERO_ROOT = Path(r"C:\JFortitude\ground-zero-audit")
GROUND_ZERO_LOG_DIR = GROUND_ZERO_ROOT / "logs"
GROUND_ZERO_OUT_DIR = GROUND_ZERO_ROOT / "out"
GROUND_ZERO_MANIFEST = GROUND_ZERO_ROOT / "manifest.json"
GROUND_ZERO_MAX_TIMEOUT = 3600
GROUND_ZERO_DEFAULT_TIMEOUT = 900

_INTERPRETERS = {
    "powershell": ("powershell.exe",
                   ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]),
    "python":     ("python",       []),
    "cmd":        ("cmd.exe",      ["/c"]),
}

def _sha256_of(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_ground_zero_manifest() -> tuple[dict | None, str | None]:
    if not GROUND_ZERO_MANIFEST.exists():
        return None, "manifest_missing"
    try:
        data = json.loads(GROUND_ZERO_MANIFEST.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"manifest_unreadable:{e}"
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return None, "manifest_missing_scripts"
    return scripts, None

def cap_run_local_script(ctx: ActionContext) -> dict:
    """Execute a SIGNED script from C:\\JFortitude\\ground-zero-audit\\.

    Guardrails (all enforced):
      - Windows only.
      - Script must resolve inside GROUND_ZERO_ROOT (no traversal).
      - Script's SHA-256 must equal manifest.json entry for its relative path.
      - Interpreter is chosen from a fixed map (powershell | python | cmd) —
        picked from the manifest entry, never the caller.
      - Blocking run with a hard timeout (default 900s, cap 3600s).
      - stdout+stderr written to logs\\<action_id>.log; tails returned.
      - Any *.zip appearing under out\\ after start_ts is captured with
        {path, size, sha256}. Nothing is uploaded from here; the platform
        pulls artifacts via the existing private artifact channel.
    """
    if platform.system() != "Windows":
        return {"ok": False, "error": "windows_only"}

    rel = str(ctx.payload.get("script", "") or "").strip()
    if not rel:
        return {"ok": False, "error": "script_required"}

    # Resolve + jail.
    try:
        root = GROUND_ZERO_ROOT.resolve()
    except Exception:
        return {"ok": False, "error": "root_missing", "root": str(GROUND_ZERO_ROOT)}
    if not root.exists():
        return {"ok": False, "error": "root_missing", "root": str(root)}

    candidate = (root / rel)
    try:
        candidate = candidate.resolve()
    except Exception as e:
        return {"ok": False, "error": "path_resolve_failed", "detail": str(e)}
    if root != candidate and root not in candidate.parents:
        return {"ok": False, "error": "script_outside_root",
                "root": str(root), "given": str(candidate)}
    if not candidate.is_file():
        return {"ok": False, "error": "script_missing", "path": str(candidate)}

    # Manifest / signature check.
    scripts, err = _load_ground_zero_manifest()
    if err:
        return {"ok": False, "error": err, "manifest": str(GROUND_ZERO_MANIFEST)}
    rel_key = candidate.relative_to(root).as_posix()
    entry = scripts.get(rel_key)
    if not isinstance(entry, dict):
        return {"ok": False, "error": "script_not_signed", "script": rel_key}
    expected = str(entry.get("sha256", "")).lower().strip()
    if len(expected) != 64:
        return {"ok": False, "error": "manifest_entry_bad_hash", "script": rel_key}
    actual = _sha256_of(candidate)
    if actual.lower() != expected:
        return {"ok": False, "error": "signature_mismatch",
                "script": rel_key, "expected_sha256": expected, "actual_sha256": actual}

    interp_key = str(entry.get("interpreter", "")).lower().strip()
    interp = _INTERPRETERS.get(interp_key)
    if not interp:
        return {"ok": False, "error": "unsupported_interpreter",
                "interpreter": interp_key, "allowed": sorted(_INTERPRETERS)}
    exe, prefix_args = interp

    # Caller args (optional).
    extra_args = ctx.payload.get("args", []) or []
    if not isinstance(extra_args, list) or not all(isinstance(a, str) for a in extra_args):
        return {"ok": False, "error": "bad_args"}

    # Repository repair is doubly authorized: Project K matches an exact
    # authorization row and the signed local manifest independently matches
    # the exact argument vector. No caller text becomes a shell command.
    if rel_key == "unk_repository_repair.py":
        allowed_args = entry.get("allowed_args")
        if (not isinstance(allowed_args, list)
                or extra_args not in allowed_args):
            return {"ok": False, "error": "manifest_args_not_authorized",
                    "script": rel_key}

    # Timeout.
    try:
        timeout = int(ctx.payload.get("timeout_seconds", GROUND_ZERO_DEFAULT_TIMEOUT))
    except Exception:
        timeout = GROUND_ZERO_DEFAULT_TIMEOUT
    timeout = max(1, min(timeout, GROUND_ZERO_MAX_TIMEOUT))

    # Prepare logs + output dirs.
    GROUND_ZERO_LOG_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_ZERO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = GROUND_ZERO_LOG_DIR / f"{ctx.action_id}.log"

    cmd = [exe, *prefix_args, str(candidate), *extra_args]
    start_ts = time.time()
    timed_out = False
    try:
        r = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout, stderr, exit_code = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as te:
        timed_out = True
        stdout = te.stdout.decode(errors="replace") if isinstance(te.stdout, bytes) else (te.stdout or "")
        stderr = te.stderr.decode(errors="replace") if isinstance(te.stderr, bytes) else (te.stderr or "")
        exit_code = -1
    except Exception as e:
        return {"ok": False, "error": "run_failed", "detail": str(e), "cmd": cmd[:2]}

    duration = round(time.time() - start_ts, 2)

    # Persist full log.
    try:
        log_path.write_text(
            f"# script: {rel_key}\n"
            f"# sha256: {actual}\n"
            f"# interpreter: {interp_key}\n"
            f"# args: {json.dumps(extra_args)}\n"
            f"# exit_code: {exit_code}\n"
            f"# duration_s: {duration}\n"
            f"# timed_out: {timed_out}\n"
            f"\n===== STDOUT =====\n{stdout}\n"
            f"\n===== STDERR =====\n{stderr}\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    # Collect ZIP outputs created / modified after start.
    zips: list[dict] = []
    try:
        for z in sorted(GROUND_ZERO_OUT_DIR.rglob("*.zip")):
            try:
                st = z.stat()
                if st.st_mtime >= start_ts - 1:
                    zips.append({
                        "path": str(z),
                        "relative_path": z.relative_to(GROUND_ZERO_OUT_DIR).as_posix(),
                        "size": st.st_size,
                        "sha256": _sha256_of(z),
                        "modified_at": int(st.st_mtime),
                    })
            except Exception:
                continue
    except Exception:
        pass

    return {
        "ok": not timed_out and exit_code == 0,
        "script": rel_key,
        "sha256": actual,
        "interpreter": interp_key,
        "exit_code": exit_code,
        "duration_s": duration,
        "timed_out": timed_out,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-2000:],
        "log_path": str(log_path),
        "zip_outputs": zips,
    }



def cap_run_check(ctx: ActionContext) -> dict:
    """Short, blocking, read-only command (whitelisted exe). 30s cap."""
    _check = str((ctx.payload or {}).get("check") or "").lower().strip()
    if _check in ("bot_fresh_status", "bot_runtime_status"):
        snap = bot_fresh_snapshot()
        snap.update({"ok": True, "exit_code": 0, "check": "bot_fresh_status",
                     "companion_version": COMPANION_VERSION})
        return snap
    if _check == "bot_status":
        return {
            "ok": True,
            "exit_code": 0,
            "check": "bot_status",
            "companion_version": COMPANION_VERSION,
            "status": status_snapshot(),
            "heartbeat_sidecar_exists": HEARTBEAT_SIDECAR.exists(),
        }
    exe = ctx.payload.get("executable", "")
    args = ctx.payload.get("args", [])
    if not executable_is_allowed(exe):
        return {"ok": False, "error": "executable_not_allowed", "executable": exe}
    try:
        r = subprocess.run(
            [exe, *args],
            capture_output=True, text=True, timeout=30,
        )
        return {
            "ok": True,
            "exit_code": r.returncode,
            "stdout_tail": r.stdout[-4000:],
            "stderr_tail": r.stderr[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": "run_failed", "detail": str(e)}


_FAST_PROBE_PS = r"""
$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
$started = Get-Date
function Task-Info($name) {
  $out = [ordered]@{
    exists=$false; status=$null; last_result=$null; run_as_user=$null;
    task_to_run=$null; schedule=$null; enabled=$null;
    missed_start_enabled=$null; execution_time_limit=$null; interval_minutes=$null
  }
  try {
    $raw = & schtasks.exe /query /tn $name /v /fo LIST 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) { return $out }
    $out.exists = $true
    $map = @{}
    foreach ($line in $raw) {
      if ($line -match '^\s*([^:]+?):\s*(.*)$') { $map[$Matches[1].Trim()] = $Matches[2].Trim() }
    }
    $out.status = $map['Status']
    $out.last_result = $map['Last Result']
    $out.run_as_user = $map['Run As User']
    $out.task_to_run = $map['Task To Run']
    $out.schedule = $map['Schedule Type']
    $out.enabled = ($map['Scheduled Task State'] -eq 'Enabled')
    $out.execution_time_limit = $map['Task Time Limit']
    if ($map['Repeat: Every']) { $out.interval_minutes = $map['Repeat: Every'] }
  } catch {}
  try {
    $t = Get-ScheduledTask -TaskName ($name -replace '^\\','') -ErrorAction SilentlyContinue
    if ($t) {
      $s = $t.Settings
      if ($s) { $out.missed_start_enabled = [bool]$s.StartWhenAvailable }
    }
  } catch {}
  return $out
}
$sup  = Task-Info '\UnkSupervisor'
$keep = Task-Info '\UnkSupervisorKeepAlive'
$py = @(Get-Process python,pythonw -ErrorAction SilentlyContinue)
$companionPid = $null; $companionStart = $null
foreach ($p in $py) {
  try {
    $cl = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction SilentlyContinue).CommandLine
    if ($cl -match 'unk_companion\.py') { $companionPid = $p.Id; $companionStart = $p.StartTime.ToString('o'); break }
  } catch {}
}
$installerPath = Join-Path $env:LOCALAPPDATA 'UnkCompanion\install_supervisor.ps1'
$installerExists = Test-Path $installerPath
$installerMtime = $null
if ($installerExists) { try { $installerMtime = (Get-Item $installerPath).LastWriteTime.ToString('o') } catch {} }
$out = [ordered]@{
  supervisor_exists = $sup.exists
  supervisor_status = $sup.status
  supervisor_last_result = $sup.last_result
  supervisor_run_as_user = $sup.run_as_user
  supervisor_task_to_run = $sup.task_to_run
  supervisor_schedule = $sup.schedule
  supervisor_start_in = $null
  supervisor_enabled = $sup.enabled
  supervisor_missed_start_enabled = $sup.missed_start_enabled
  supervisor_execution_time_limit = $sup.execution_time_limit
  keepalive_exists = $keep.exists
  keepalive_status = $keep.status
  keepalive_last_result = $keep.last_result
  keepalive_run_as_user = $keep.run_as_user
  keepalive_task_to_run = $keep.task_to_run
  keepalive_schedule = $keep.schedule
  keepalive_interval_minutes = $keep.interval_minutes
  keepalive_enabled = $keep.enabled
  current_companion_pid = $companionPid
  current_companion_start_time = $companionStart
  companion_instance_count = ($py | Measure-Object).Count
  installer_exists = $installerExists
  installer_modified_at = $installerMtime
  probe_duration_ms = [int]((Get-Date) - $started).TotalMilliseconds
  probe_result = 'ok'
}
$out | ConvertTo-Json -Compress
"""


def _run_fast_probe(action_id: str) -> dict:
    started = time.time()
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", _FAST_PROBE_PS],
            capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "fast_probe_timeout", "probe_duration_ms": int((time.time() - started) * 1000)}
    except Exception as e:
        return {"ok": False, "error": "fast_probe_failed", "detail": str(e)}
    payload = None
    try:
        payload = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception as e:
        return {"ok": False, "error": "fast_probe_parse_failed", "stdout_tail": (r.stdout or "")[-2000:], "stderr_tail": (r.stderr or "")[-1000:], "detail": str(e)}
    payload["action_id"] = action_id
    payload["ok"] = True
    payload["mode"] = "fast_probe"
    payload["companion_version"] = COMPANION_VERSION
    return payload


def cap_platform_persistence_repair(ctx: ActionContext) -> dict:
    """Diagnose and repair the Ground Zero always-on worker layer.

    Modes:
      - fast_probe: bounded (<=30s) task-state snapshot. No elevation.
      - audit / apply: legacy repair_persistence.ps1 path.
    """
    if platform.system() != "Windows":
        return {"ok": False, "error": "windows_only"}

    mode = str((ctx.payload or {}).get("mode") or "audit").lower().strip()
    if mode == "fast_probe":
        return _run_fast_probe(ctx.action_id)
    if mode == "noop":
        return {"ok": True, "mode": "noop", "exit_code": 0, "companion_version": COMPANION_VERSION, "status": status_snapshot()}
    if mode == "kill_proof":
        _RESTART_REQUESTED["pending"] = True
        _RESTART_REQUESTED["reason"] = "persistence_kill_proof"
        _RESTART_REQUESTED["strategy"] = "supervisor_exit"
        return {
            "ok": True,
            "mode": "kill_proof",
            "exit_code": 0,
            "restart_scheduled": True,
            "strategy": "supervisor_exit",
            "old_instance_id": INSTANCE_ID,
            "old_boot_ts": BOOT_TS,
            "companion_version": COMPANION_VERSION,
        }

    script = _companion_script_dir() / "repair_persistence.ps1"
    if not script.exists():
        return {"ok": False, "error": "repair_script_missing", "path": str(script)}
    apply = bool((ctx.payload or {}).get("apply")) or mode in {"apply", "repair"}
    timeout = 300 if apply else 240
    args = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script), "-ActionId", ctx.action_id,
    ]
    if apply:
        args.append("-Apply")
    if bool((ctx.payload or {}).get("request_elevation_if_needed")):
        args.append("-RequestElevationIfNeeded")
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=str(_companion_script_dir()))
    except subprocess.TimeoutExpired as te:
        stdout = te.stdout.decode(errors="replace") if isinstance(te.stdout, bytes) else (te.stdout or "")
        stderr = te.stderr.decode(errors="replace") if isinstance(te.stderr, bytes) else (te.stderr or "")
        return {"ok": False, "error": "timeout", "stdout_tail": stdout[-8000:], "stderr_tail": stderr[-4000:], "exit_code": -1}
    except Exception as e:
        return {"ok": False, "error": "run_failed", "detail": str(e)}

    receipt_path = COMPANION_DIR / "persistence_repair_latest.json"
    receipt = None
    if receipt_path.exists():
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception as e:
            receipt = {"receipt_unreadable": str(e), "path": str(receipt_path)}
    return {
        "ok": r.returncode == 0,
        "mode": "apply" if apply else "audit",
        "exit_code": r.returncode,
        "stdout_tail": (r.stdout or "")[-8000:],
        "stderr_tail": (r.stderr or "")[-4000:],
        "detail": receipt,
    }

def cap_desktop_commander_repair(ctx: ActionContext) -> dict:
    """Run the bounded persistence probe for recurring desktop repair checks.

    This path is diagnostic only. It does not elevate or apply a repair, and the
    receipt says so explicitly so an automated verifier cannot mistake a probe
    for a completed repair.
    """
    result = _run_fast_probe(ctx.action_id)
    result["requested_capability"] = "desktop_commander_repair"
    result["repair_applied"] = False
    return result

# ----- Tier 2 capabilities -----

def _open_with_default_app(target: str) -> None:
    sys_name = platform.system()
    if sys_name == "Windows":
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys_name == "Darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])

def cap_open_url(ctx: ActionContext) -> dict:
    url = ctx.payload.get("url", "")
    ok, reason = url_is_allowed(url)
    if not ok:
        return {"ok": False, "error": "url_not_allowed", "reason": reason}
    try:
        _open_with_default_app(url)
        return {"ok": True, "url": url}
    except Exception as e:
        return {"ok": False, "error": "open_failed", "detail": str(e)}

def cap_connector_escort(ctx: ActionContext) -> dict:
    """Human-in-the-loop escort for Lovable workspace connectors.

    Unk cannot click through Google consent, read passwords, or bypass the
    Lovable workspace UI. What he can do safely is open the Lovable surface and
    put the exact connector checklist on Jason's clipboard so the human step is
    guided instead of remembered from chat.
    """
    payload = ctx.payload or {}
    url = str(payload.get("url") or "https://lovable.app")
    ok, reason = url_is_allowed(url)
    if not ok:
        return {"ok": False, "error": "url_not_allowed", "reason": reason}

    provider = str(payload.get("provider") or "Google Drive")
    account = str(payload.get("account_email") or "jason@blackarchives.org")
    checklist = str(payload.get("checklist") or f"""Unk Connector Escort — {provider}

Goal: add/link a SECOND {provider} connection for {account}.

1. In Lovable, open the workspace-level Connectors area.
2. Search/select {provider}.
3. Choose + Add connection / Connect another account.
4. On Google, choose Use another account and sign in as {account}.
5. Keep Drive read permission selected and approve.
6. Return to Lovable and finish linking the new connection to this project.
7. Tell Lovable chat: "I did it" so the agent can verify list_connections shows another google_drive row.

If you only see Gmail or Calendar afterward, that was the wrong Google connector; repeat under Google Drive.
""")

    clipboard_ok = _clipboard_set(checklist[:CLIPBOARD_MAX_CHARS])
    try:
        _open_with_default_app(url)
    except Exception as e:
        return {
            "ok": False,
            "error": "open_failed",
            "detail": str(e),
            "clipboard_ok": clipboard_ok,
            "checklist": checklist,
        }
    return {
        "ok": True,
        "url": url,
        "provider": provider,
        "account_email": account,
        "clipboard_ok": clipboard_ok,
        "next_human_step": "Use the copied checklist in Lovable's Connectors UI; Google consent remains human-only.",
    }

def cap_open_file(ctx: ActionContext) -> dict:
    p = Path(ctx.payload.get("path", ""))
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    if not p.exists():
        return {"ok": False, "error": "not_found"}
    if not file_open_ext_allowed(p):
        return {"ok": False, "error": "extension_blocked", "ext": p.suffix.lower()}
    try:
        _open_with_default_app(str(p))
        return {"ok": True, "path": str(p)}
    except Exception as e:
        return {"ok": False, "error": "open_failed", "detail": str(e)}

def cap_reveal_in_explorer(ctx: ActionContext) -> dict:
    p = Path(ctx.payload.get("path", ""))
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    if not p.exists():
        return {"ok": False, "error": "not_found"}
    sys_name = platform.system()
    try:
        if sys_name == "Windows":
            subprocess.Popen(["explorer", "/select,", str(p)])
        elif sys_name == "Darwin":
            subprocess.Popen(["open", "-R", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])
        return {"ok": True, "path": str(p)}
    except Exception as e:
        return {"ok": False, "error": "reveal_failed", "detail": str(e)}

def _clipboard_get() -> str | None:
    sys_name = platform.system()
    try:
        if sys_name == "Windows":
            r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                               capture_output=True, text=True, timeout=5)
            return r.stdout if r.returncode == 0 else None
        if sys_name == "Darwin":
            r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
            return r.stdout if r.returncode == 0 else None
        r = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None

def _clipboard_set(text: str) -> bool:
    sys_name = platform.system()
    try:
        if sys_name == "Windows":
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-16le"))
            return p.returncode == 0
        if sys_name == "Darwin":
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode("utf-8"))
        return p.returncode == 0
    except Exception:
        return False

def cap_read_clipboard(ctx: ActionContext) -> dict:
    text = _clipboard_get()
    if text is None:
        return {"ok": False, "error": "clipboard_unavailable"}
    if len(text) > CLIPBOARD_MAX_CHARS:
        text = text[:CLIPBOARD_MAX_CHARS]
    return {"ok": True, "text": text, "chars": len(text)}

def cap_write_clipboard(ctx: ActionContext) -> dict:
    text = ctx.payload.get("text", "")
    if not isinstance(text, str):
        return {"ok": False, "error": "bad_text"}
    if len(text) > CLIPBOARD_MAX_CHARS:
        return {"ok": False, "error": "text_too_large"}
    ok = _clipboard_set(text)
    return {"ok": ok, "chars": len(text)} if ok else {"ok": False, "error": "clipboard_write_failed"}

def cap_download_url_to_folder(ctx: ActionContext) -> dict:
    url = ctx.payload.get("url", "")
    ok, reason = url_is_allowed(url)
    if not ok:
        return {"ok": False, "error": "url_not_allowed", "reason": reason}
    folder_raw = ctx.payload.get("folder") or str(DOWNLOAD_DIR)
    folder = Path(folder_raw)
    if not path_is_allowed(folder):
        return {"ok": False, "error": "folder_not_allowed"}
    folder.mkdir(parents=True, exist_ok=True)
    filename = ctx.payload.get("filename")
    if not filename:
        parsed = urllib.parse.urlparse(url)
        filename = Path(parsed.path).name or f"download_{ctx.action_id}.bin"
    # sanitize
    filename = re.sub(r"[^A-Za-z0-9._\-]", "_", filename)[:200]
    out = folder / filename
    try:
        with requests.get(url, stream=True, timeout=HTTP_TIMEOUT, headers=PUBLIC_DOWNLOAD_HEADERS, allow_redirects=True) as r:
            r.raise_for_status()
            total = 0
            with out.open("wb") as f:
                for chunk in r.iter_content(chunk_size=65_536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > DOWNLOAD_MAX_BYTES:
                        f.close()
                        out.unlink(missing_ok=True)
                        return {"ok": False, "error": "size_cap_exceeded"}
                    f.write(chunk)
        return {"ok": True, "path": str(out), "bytes": total}
    except Exception as e:
        return {"ok": False, "error": "download_failed", "detail": str(e)}

try:
    from meta_credentials import meta_status  # type: ignore
except Exception:  # pragma: no cover
    meta_status = None  # type: ignore

try:
    from meta_publisher import (  # type: ignore
        publish_text as _meta_publish_text,
        publish_photo as _meta_publish_photo,
        publish_video as _meta_publish_video,
        publish_reel as _meta_publish_reel,
        get_post_metrics as _meta_get_post_metrics,
        refresh_long_lived_token as _meta_refresh_token,
        recent_log as _meta_recent_log,
    )
except Exception:  # pragma: no cover
    _meta_publish_text = None  # type: ignore
    _meta_publish_photo = None  # type: ignore
    _meta_publish_video = None  # type: ignore
    _meta_publish_reel = None  # type: ignore
    _meta_get_post_metrics = None  # type: ignore
    _meta_refresh_token = None  # type: ignore
    _meta_recent_log = None  # type: ignore


def _meta_guard(fn) -> dict | None:
    if fn is None:
        return {"ok": False, "error": "meta_publisher_missing"}
    return None


def cap_meta_status(ctx: ActionContext) -> dict:
    if meta_status is None:
        return {"ok": False, "error": "meta_helper_missing"}
    return meta_status()


def cap_meta_publish(ctx: ActionContext) -> dict:
    guard = _meta_guard(_meta_publish_text)
    if guard:
        return guard
    message = (ctx.payload.get("message") or "").strip()
    if not message:
        return {"ok": False, "error": "empty_message"}
    if len(message) > 8000:
        return {"ok": False, "error": "message_too_long"}
    return _meta_publish_text(message, link=ctx.payload.get("link"))


def cap_meta_publish_photo(ctx: ActionContext) -> dict:
    guard = _meta_guard(_meta_publish_photo)
    if guard:
        return guard
    path = ctx.payload.get("image_path") or ctx.payload.get("path")
    if not path:
        return {"ok": False, "error": "missing_image_path"}
    p = Path(path)
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    return _meta_publish_photo(
        str(p),
        caption=ctx.payload.get("caption"),
        published=bool(ctx.payload.get("published", True)),
    )


def cap_meta_publish_video(ctx: ActionContext) -> dict:
    guard = _meta_guard(_meta_publish_video)
    if guard:
        return guard
    path = ctx.payload.get("video_path") or ctx.payload.get("path")
    if not path:
        return {"ok": False, "error": "missing_video_path"}
    p = Path(path)
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    return _meta_publish_video(
        str(p),
        description=ctx.payload.get("description"),
        title=ctx.payload.get("title"),
    )


def cap_meta_publish_reel(ctx: ActionContext) -> dict:
    guard = _meta_guard(_meta_publish_reel)
    if guard:
        return guard
    path = ctx.payload.get("video_path") or ctx.payload.get("path")
    if not path:
        return {"ok": False, "error": "missing_video_path"}
    p = Path(path)
    if not path_is_allowed(p):
        return {"ok": False, "error": "path_not_allowed"}
    return _meta_publish_reel(str(p), description=ctx.payload.get("description"))


def cap_meta_post_metrics(ctx: ActionContext) -> dict:
    guard = _meta_guard(_meta_get_post_metrics)
    if guard:
        return guard
    post_id = ctx.payload.get("post_id")
    if not post_id:
        return {"ok": False, "error": "missing_post_id"}
    return _meta_get_post_metrics(post_id)


def cap_meta_refresh_token(ctx: ActionContext) -> dict:
    guard = _meta_guard(_meta_refresh_token)
    if guard:
        return guard
    return _meta_refresh_token()


def cap_meta_recent_log(ctx: ActionContext) -> dict:
    guard = _meta_guard(_meta_recent_log)
    if guard:
        return guard
    try:
        limit = int(ctx.payload.get("limit", 50))
    except Exception:
        limit = 50
    limit = max(1, min(limit, 500))
    return _meta_recent_log(limit=limit)


try:
    from meta_autopilot import (  # type: ignore
        autopilot_publish as _meta_autopilot_publish,
        list_holds as _meta_list_holds,
        list_alerts as _meta_list_alerts,
        list_history as _meta_list_history,
        release_hold as _meta_release_hold,
        classify as _meta_classify,
    )
except Exception:  # pragma: no cover
    _meta_autopilot_publish = None  # type: ignore
    _meta_list_holds = None  # type: ignore
    _meta_list_alerts = None  # type: ignore
    _meta_list_history = None  # type: ignore
    _meta_release_hold = None  # type: ignore
    _meta_classify = None  # type: ignore


def cap_meta_autopilot_publish(ctx: ActionContext) -> dict:
    if _meta_autopilot_publish is None:
        return {"ok": False, "error": "meta_autopilot_missing"}
    payload = ctx.payload
    message = (payload.get("message") or "").strip()
    if not message and payload.get("format", "text") == "text":
        return {"ok": False, "error": "empty_message"}
    if len(message) > 8000:
        return {"ok": False, "error": "message_too_long"}
    # Validate any paths through the existing allow-list
    for key in ("image_path", "video_path"):
        v = payload.get(key)
        if v and not path_is_allowed(Path(v)):
            return {"ok": False, "error": f"{key}_not_allowed"}
    return _meta_autopilot_publish(
        message=message,
        format=payload.get("format", "text"),
        image_path=payload.get("image_path"),
        video_path=payload.get("video_path"),
        link=payload.get("link"),
        title=payload.get("title"),
        source_id=payload.get("source_id"),
        force=bool(payload.get("force", False)),
    )


def cap_meta_autopilot_holds(ctx: ActionContext) -> dict:
    if _meta_list_holds is None:
        return {"ok": False, "error": "meta_autopilot_missing"}
    return _meta_list_holds(limit=int(ctx.payload.get("limit", 50)))


def cap_meta_autopilot_alerts(ctx: ActionContext) -> dict:
    if _meta_list_alerts is None:
        return {"ok": False, "error": "meta_autopilot_missing"}
    return _meta_list_alerts(limit=int(ctx.payload.get("limit", 50)))


def cap_meta_autopilot_history(ctx: ActionContext) -> dict:
    if _meta_list_history is None:
        return {"ok": False, "error": "meta_autopilot_missing"}
    return _meta_list_history(limit=int(ctx.payload.get("limit", 100)))


def cap_meta_autopilot_release(ctx: ActionContext) -> dict:
    if _meta_release_hold is None:
        return {"ok": False, "error": "meta_autopilot_missing"}
    hold_id = ctx.payload.get("hold_id")
    if not hold_id:
        return {"ok": False, "error": "missing_hold_id"}
    return _meta_release_hold(hold_id)


def cap_meta_autopilot_classify(ctx: ActionContext) -> dict:
    """Dry-run sensitivity classifier — does not publish."""
    if _meta_classify is None:
        return {"ok": False, "error": "meta_autopilot_missing"}
    text = (ctx.payload.get("text") or "").strip()
    if not text:
        return {"ok": False, "error": "empty_text"}
    return {"ok": True, **_meta_classify(text)}


# Social account onboarding (lawful, human-verified — see social_onboarding.py)
try:
    from social_onboarding import (  # type: ignore
        social_platform_status as _social_platform_status,
        social_open_signup as _social_open_signup,
        social_profile_draft as _social_profile_draft,
        social_key_capture as _social_key_capture,
        social_connection_test as _social_connection_test,
        social_readiness_report as _social_readiness_report,
        social_pages_discover as _social_pages_discover,
        social_pages_test as _social_pages_test,
    )
except Exception:  # pragma: no cover
    _social_platform_status = None  # type: ignore
    _social_open_signup = None  # type: ignore
    _social_profile_draft = None  # type: ignore
    _social_key_capture = None  # type: ignore
    _social_connection_test = None  # type: ignore
    _social_readiness_report = None  # type: ignore
    _social_pages_discover = None  # type: ignore
    _social_pages_test = None  # type: ignore


def _social_guard(fn):
    if fn is None:
        return {"ok": False, "error": "social_onboarding_missing"}
    return None


def cap_social_platform_status(ctx: ActionContext) -> dict:
    g = _social_guard(_social_platform_status)
    return g or _social_platform_status(ctx.payload)


def cap_social_open_signup(ctx: ActionContext) -> dict:
    g = _social_guard(_social_open_signup)
    return g or _social_open_signup(ctx.payload)


def cap_social_profile_draft(ctx: ActionContext) -> dict:
    g = _social_guard(_social_profile_draft)
    return g or _social_profile_draft(ctx.payload)


def cap_social_key_capture(ctx: ActionContext) -> dict:
    g = _social_guard(_social_key_capture)
    return g or _social_key_capture(ctx.payload)


def cap_social_connection_test(ctx: ActionContext) -> dict:
    g = _social_guard(_social_connection_test)
    return g or _social_connection_test(ctx.payload)


def cap_social_readiness_report(ctx: ActionContext) -> dict:
    g = _social_guard(_social_readiness_report)
    return g or _social_readiness_report(ctx.payload)


def cap_social_pages_discover(ctx: ActionContext) -> dict:
    g = _social_guard(_social_pages_discover)
    return g or _social_pages_discover(ctx.payload)


def cap_social_pages_test(ctx: ActionContext) -> dict:
    g = _social_guard(_social_pages_test)
    return g or _social_pages_test(ctx.payload)


# Meta Autofix (browser_session + invoke_edge_function) — dry-run scaffold
try:
    from meta_autofix_handlers import (  # type: ignore
        dispatch_browser_session as _autofix_browser,
        dispatch_invoke_edge_function as _autofix_invoke_edge,
        recent_autofix_history as _autofix_history,
    )
except Exception:  # pragma: no cover
    _autofix_browser = None  # type: ignore
    _autofix_invoke_edge = None  # type: ignore
    _autofix_history = None  # type: ignore


def cap_browser_session(ctx: ActionContext) -> dict:
    if _autofix_browser is None:
        return {"ok": False, "error": "meta_autofix_handlers_missing"}
    payload = dict(ctx.payload or {})
    payload.setdefault("action_type", ctx.action_type)
    return _autofix_browser(payload, action_type=ctx.action_type)


def cap_invoke_edge_function(ctx: ActionContext) -> dict:
    if _autofix_invoke_edge is None:
        return {"ok": False, "error": "meta_autofix_handlers_missing"}
    return _autofix_invoke_edge(ctx.payload)


def cap_secret_rotate(ctx: ActionContext) -> dict:
    """Rotate an allow-listed operational token end-to-end on Ground Zero.

    Generates the value locally, publishes only its SHA-256 fingerprint to the
    backend, pushes it to the GitHub Actions repo secret via authenticated gh
    (stdin, never argv), writes the non-versioned local test env file, runs the
    integration suite, and returns NON-SECRET receipts only.
    """
    try:
        from secret_rotate import rotate as _rotate  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": "secret_rotate_module_missing", "detail": str(exc)}
    out = _rotate(dict(ctx.payload or {}))
    out["companion_version"] = COMPANION_VERSION
    return out


def cap_integration_onboard(ctx: ActionContext) -> dict:
    """Standing Integration & Credential Manager pass.

    Claims due integration tasks (discover / acquire / install / connect /
    test / maintain / rotate / expand) and executes them end-to-end. Plaintext
    credentials never leave Ground Zero; only fingerprints are published.
    """
    try:
        from integration_manager import run as _run  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": "integration_manager_module_missing", "detail": str(exc)}
    out = _run(dict(ctx.payload or {}))
    out["companion_version"] = COMPANION_VERSION
    return out




# --- Google Drive credential provisioning (credit-independent media engine) --
def cap_google_credential_provision(ctx: ActionContext) -> dict:
    """Mint a direct Google Drive credential using Jason's signed-in profile.

    Removes the last Lovable-credit dependency in the media engine: the
    platform's drive-access layer prefers a direct service-account credential
    and only falls back to the connector gateway. Runs headless; stops at any
    human-only gate (login, MFA, billing, ToS) with a reason code.
    """
    try:
        from google_credential_provision import provision as _provision  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": "google_credential_module_missing", "detail": str(exc)}
    payload = dict(ctx.payload or {})
    mode = str(payload.get("mode") or "service_account").strip()
    if mode != "service_account":
        # Probe and interactive sign-in never carry a private-key payload.
        out = _provision(payload)
        out.pop("credential_json", None)
        return out

    # The native capability must never return raw provision() results into the
    # desktop_action_requests queue. Install directly in Project K and return
    # only a nonsecret, server-acknowledged result.
    try:
        from google_credential_install import install_provisioned as _install  # type: ignore
    except Exception:
        return {"ok": False, "stage": "install", "blocker_reason_code": "credential_installer_unavailable"}
    return _install(_provision(payload))


# --- Paperwork autofill (Unk fills forms; Jason only clears real gates) ----
def cap_browser_portal_login(ctx: ActionContext) -> dict:
    """Create, sign in to, or resume a funder-portal account/session.

    Delegates to portal_login_worker.py, which fetches credentials one-time from
    the vault and never accepts legal terms, signs/certifies, pays, or submits.
    """
    mode_by_action = {
        "portal_register_account": "register",
        "portal_session_login": "login",
        "portal_session_resume": "resume",
    }
    mode = mode_by_action.get(ctx.action_type)
    if not mode:
        return {"ok": False, "error": "unsupported_action_type", "action_type": ctx.action_type}

    worker = Path(__file__).with_name("portal_login_worker.py")
    if not worker.exists():
        return {"ok": False, "error": "portal_login_worker_missing"}

    payload = dict(ctx.payload or {})
    if mode == "register" and not payload.get("registration_receipt_id"):
        return {"ok": False, "error": "registration_receipt_id_required"}
    if mode in ("login", "resume") and not payload.get("portal_session_id"):
        return {"ok": False, "error": "portal_session_id_required"}

    # Pass the already-enrolled Ground Zero identity to the child in memory
    # only. It never appears in the action payload, command line, result, or log.
    device_credentials = load_credentials()
    if not device_credentials:
        return {"ok": False, "error": "device_credentials_unavailable"}
    device_id, device_key = device_credentials
    child_env = os.environ.copy()
    child_env["UNK_DEVICE_ID"] = device_id
    child_env["UNK_DEVICE_KEY"] = device_key
    child_env["SUPABASE_ANON_KEY"] = SUPABASE_ANON_KEY

    tmp = Path(tempfile.gettempdir()) / f"portal_login_{ctx.action_id}.json"
    try:
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        cmd = [sys.executable, str(worker), "--mode", mode, "--payload-file", str(tmp)]
        if os.name == "nt":
            cmd.append("--headed")
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, env=child_env)
        try:
            result = json.loads((proc.stdout or "").strip() or "{}")
        except Exception:
            result = {}
        if not result:
            return {
                "ok": False,
                "error": "worker_no_result",
                "exit_code": proc.returncode,
                "stderr": (proc.stderr or "")[-2000:],
            }
        result["exit_code"] = proc.returncode
        result["companion_version"] = COMPANION_VERSION
        return result
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "portal_login_timeout", "mode": mode}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:400], "mode": mode}
    finally:
        # Remove the device key from the child environment copy immediately.
        child_env.pop("UNK_DEVICE_KEY", None)
        device_key = None
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

def cap_form_autofill(ctx: ActionContext) -> dict:
    """Fill a paperwork form autonomously and return a structured receipt.

    Runs HEADLESSLY unless the cloud explicitly sets allow_human_gate=true,
    which it only does once per gate. That is what stops partially completed
    forms from reopening on Jason's desktop over and over.
    """
    try:
        from form_autofill import autofill as _autofill, dry_run as _autofill_dry  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": "form_autofill_module_missing", "detail": str(exc)}

    payload = dict(ctx.payload or {})
    url = str(payload.get("url") or "").strip()
    if not url:
        return {"ok": False, "error": "missing_url"}
    allowed, reason = url_is_allowed(url)
    if not allowed:
        return {"ok": False, "error": f"url_not_allowed:{reason}", "url": url}

    kwargs = {
        "url": url,
        "fields": payload.get("fields") or [],
        "attachments": payload.get("attachments") or [],
        "save_selectors": payload.get("save_selectors") or [],
        "allow_human_gate": bool(payload.get("allow_human_gate")),
        "task_id": payload.get("task_id"),
    }
    result = _autofill_dry(url=url, fields=kwargs["fields"]) if payload.get("dry_run") \
        else _autofill(**kwargs)
    result["companion_version"] = COMPANION_VERSION
    return result


def cap_meta_autofix_history(ctx: ActionContext) -> dict:
    if _autofix_history is None:
        return {"ok": False, "error": "meta_autofix_handlers_missing"}
    return _autofix_history(limit=int(ctx.payload.get("limit", 50)))


# --- Browser-driven Facebook Page publisher (Option 1 launch path) ---------
try:
    from meta_browser_publisher import (  # type: ignore
        publish_facebook_page as _browser_publish_fb,
        PAGE_URLS as _FB_PAGE_URLS,
        open_signin as _browser_open_signin,
        open_signin_platform as _browser_open_signin_platform,
        preflight_platform_auth as _browser_preflight_platform,
    )
except Exception:  # pragma: no cover
    _browser_publish_fb = None  # type: ignore
    _FB_PAGE_URLS = {}  # type: ignore
    _browser_open_signin = None  # type: ignore
    _browser_open_signin_platform = None  # type: ignore
    _browser_preflight_platform = None  # type: ignore



try:
    from multi_platform_publisher import (  # type: ignore
        publish_facebook_reel as _publish_fb_reel,
        publish_instagram_feed as _publish_ig_feed,
        publish_instagram_reel as _publish_ig_reel,
        publish_linkedin as _publish_linkedin,
        publish_youtube_short as _publish_yt_short,
        recover_linkedin_permalink as _recover_linkedin_permalink,
        harvest_linkedin_profile_posts as _harvest_linkedin_posts,
    )
except Exception:  # pragma: no cover
    _publish_fb_reel = None  # type: ignore
    _publish_ig_feed = None  # type: ignore
    _publish_ig_reel = None  # type: ignore
    _publish_linkedin = None  # type: ignore
    _publish_yt_short = None  # type: ignore
    _recover_linkedin_permalink = None  # type: ignore
    _harvest_linkedin_posts = None  # type: ignore




def _post_browser_publish_receipt(job_id: str, outcome: str, res: dict) -> None:
    """POST the receipt back to the browser-publish-result edge function."""
    try:
        creds = load_credentials()
        if not creds:
            return
        device_id, device_key = creds

        body = {
            "job_id": job_id,
            "outcome": outcome,
            "published_post_url": res.get("post_url"),
            "screenshot_path": res.get("screenshot_path"),
            "error": res.get("error"),
            "receipt": {
                "notes": res.get("notes", []),
                "diagnostics": res.get("diagnostics"),
                "detail": res.get("detail"),
                "trace": res.get("trace"),
                "stderr_tail": res.get("stderr_tail"),
                "exit_code": res.get("exit_code"),
            },
        }
        requests.post(
            f"{FUNCTIONS_BASE}/browser-publish-result",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
                "x-device-id": device_id,
                "x-device-key": device_key,
            },
            json=body,
            timeout=20,
        )
    except Exception as e:  # pragma: no cover
        log(f"[browser_publish] receipt post failed: {e}")


def _return_publish(ctx: ActionContext, res: dict) -> dict:
    job_id = str((ctx.payload or {}).get("job_id") or "")
    if job_id:
        _post_browser_publish_receipt(job_id, "published" if res.get("ok") else "failed", res)
    detail = res.get("detail")
    if detail is None:
        detail = res.get("trace")
    return {
        "ok": bool(res.get("ok")),
        "post_url": res.get("post_url"),
        "screenshot_path": res.get("screenshot_path"),
        "error": res.get("error"),
        "detail": detail,
        "trace": res.get("trace"),
        "stdout_tail": res.get("stdout_tail"),
        "stderr_tail": res.get("stderr_tail"),
        "exit_code": res.get("exit_code"),
        "notes": res.get("notes", []),
        "diagnostics": res.get("diagnostics"),
    }


def cap_browser_publish_facebook(ctx: ActionContext) -> dict:
    if _browser_publish_fb is None:
        return {"ok": False, "error": "meta_browser_publisher_missing"}
    payload = ctx.payload or {}
    if not payload.get("job_id"):
        return {"ok": False, "error": "missing_job_id"}

    direct_failure = str(payload.get("direct_publish_failure") or "")
    credential_failure_needles = (
        "pages_read_engagement",
        "pages_manage_posts",
        "Missing Meta Page credential",
        "Error validating access token",
        "Session has expired",
        "OAuthException",
    )
    if any(needle in direct_failure for needle in credential_failure_needles):
        repair_notes: list[str] = [f"direct_publish_failed_repairing_token:{direct_failure[:240]}"]
        repaired = False
        if _configure_meta is not None:
            try:
                repair = _configure_meta(
                    preferred_page_name=str(payload.get("destination_label") or "J. Fortitude"),
                    app_id=payload.get("meta_app_id"),
                )
                if not isinstance(repair, dict):
                    repair = {"ok": False, "error": "meta_configure_returned_non_object", "detail": repr(repair)}
                repaired = bool(repair.get("ok"))
                repair_notes.append(f"meta_configure_ok={repaired}")
                repair_notes.extend([f"meta_configure:{n}" for n in repair.get("notes", [])[:8]])
                repair_notes.extend(_sync_configured_meta_token_to_backend(repair))
                missing = repair.get("missing_permissions") or []
                if missing:
                    return _return_publish(ctx, {
                        "ok": False,
                        "error": "meta_token_missing_required_permissions",
                        "notes": repair_notes + [f"missing_permissions:{','.join(map(str, missing))}", "blocked_browser_fallback_until_token_is_publishable"],
                        "diagnostics": {"missing_permissions": missing, "repair_error": repair.get("error")},
                    })
            except Exception as repair_exc:
                repair_notes.append(f"meta_configure_exception:{repair_exc}")
        else:
            repair_notes.append("meta_configure_unavailable")

        if repaired and _meta_publish_text is not None:
            try:
                msg = str(payload.get("message") or payload.get("title") or "").strip()
                if msg:
                    api_res = _meta_publish_text(msg, link=payload.get("link_url"))
                    if not isinstance(api_res, dict):
                        api_res = {"ok": False, "error": "meta_publish_returned_non_object", "detail": repr(api_res)}
                    if api_res.get("ok"):
                        post_id = api_res.get("post_id")
                        res = {
                            "ok": True,
                            "post_url": f"https://www.facebook.com/{post_id}" if post_id else None,
                            "notes": repair_notes + ["published_after_meta_token_repair", f"post_id={post_id}"],
                        }
                        return _return_publish(ctx, res)
                    repair_notes.append(f"post_repair_api_failed:{api_res.get('error') or api_res.get('body') or api_res.get('status')}")
            except Exception as api_exc:
                repair_notes.append(f"post_repair_api_exception:{api_exc}")
        return _return_publish(ctx, {
            "ok": False,
            "error": "meta_token_repair_required",
            "notes": repair_notes + ["blocked_browser_fallback_for_meta_credential_failure"],
            "diagnostics": {"direct_publish_failure": direct_failure[:500]},
        })

    res = _run_browser_publisher_isolated(
        _browser_publish_fb,
        page_slug=str(payload.get("page_slug") or "j-fortitude"),
        message=str(payload.get("message") or ""),
        link_url=payload.get("link_url"),
        image_url=payload.get("image_url"),
        video_url=payload.get("video_url"),
        page_url_override=payload.get("destination_url"),
    )
    if direct_failure:
        res.setdefault("notes", [])
        res["notes"] = repair_notes + res.get("notes", []) if 'repair_notes' in locals() else [f"direct_publish_failure:{direct_failure[:240]}"] + res.get("notes", [])
    return _return_publish(ctx, res)


def cap_browser_signin_facebook(ctx: ActionContext) -> dict:
    """Open the persistent Chrome profile at Business Suite so Jason can sign
    in. Never posts; used to unblock composer_not_found / login_required."""
    if _browser_open_signin is None:
        return {"ok": False, "error": "meta_browser_publisher_missing"}
    p = ctx.payload or {}
    url = str(p.get("url") or "https://business.facebook.com/")
    if not (url.startswith("https://business.facebook.com") or url.startswith("https://www.facebook.com")):
        return {"ok": False, "error": "url_not_allowed", "url": url}
    timeout_seconds = int(p.get("timeout_seconds") or 600)
    return _browser_open_signin(url=url, timeout_seconds=timeout_seconds)


def _cap_browser_signin_generic(ctx: ActionContext, platform: str) -> dict:
    """Shared wrapper for Instagram / LinkedIn sign-in via Unk's persistent
    Playwright profile (the same PROFILE_DIR used by the publisher).
    Supports payload {sso_provider:'google', sso_email:'...'} to auto-click
    Continue-with-Google without typing passwords.
    """
    if _browser_open_signin_platform is None:
        return {"ok": False, "error": "meta_browser_publisher_missing"}
    p = ctx.payload or {}
    timeout_seconds = int(p.get("timeout_seconds") or p.get("timeout") or 900)
    sso_provider = p.get("sso_provider") or None
    sso_email = p.get("sso_email") or None
    expected_handle = p.get("expected_handle") or p.get("page_slug") or None
    force_logout = bool(p.get("force_logout"))
    # Visible browser windows are exceptional and must be explicitly requested
    # by a current human-gated action. Legacy/stale sign-in jobs stay silent.
    interactive = p.get("interactive") is True
    if not interactive:
        # An unattended sign-in cannot complete a human login. Keep it as a
        # bounded session diagnostic so it never monopolizes the single device
        # queue and starves grant coordination work.
        unattended_limit = int(p.get("unattended_timeout_seconds") or 30)
        timeout_seconds = min(timeout_seconds, max(5, unattended_limit))
    return _browser_open_signin_platform(
        platform=platform, timeout_seconds=timeout_seconds,
        sso_provider=sso_provider, sso_email=sso_email,
        expected_handle=expected_handle, force_logout=force_logout,
        interactive=interactive,
    )




def cap_browser_signin_instagram(ctx: ActionContext) -> dict:
    """Open the persistent Chromium profile at instagram.com/accounts/login/
    so Jason can sign in once. Cookies persist for the publisher."""
    return _cap_browser_signin_generic(ctx, "instagram")


def cap_browser_signin_linkedin(ctx: ActionContext) -> dict:
    """Open the persistent Chromium profile at linkedin.com/login so Jason
    can sign in once. Cookies persist for the publisher."""
    return _cap_browser_signin_generic(ctx, "linkedin")


def cap_rescue_windows(ctx: ActionContext) -> dict:
    """Drag every off-screen automation browser window back onto the visible
    desktop. Fixes 'the taskbar icon is there but clicking does nothing' —
    the window was parked at -32000,-32000 by the quiet-window sweeper."""
    try:
        from unk_window_policy import (
            allow_visible_window as _allow,
            rescue_offscreen_windows as _rescue,
            start_onscreen_rescue as _keep,
        )
    except Exception as exc:
        return {"ok": False, "error": f"window_policy_missing:{exc}"}
    hold = int((ctx.payload or {}).get("hold_seconds") or 900)
    _allow(True, hold)    # time-boxed hold; background tasks can't cancel it
    moved = _rescue(focus=True)
    _keep(hold)           # keep them on screen while Jason signs in
    return {"ok": True, "windows_restored": moved, "hold_seconds": hold}



def cap_browser_preflight_platform(ctx: ActionContext) -> dict:
    """Prove that Unk's persistent profile is authenticated on a platform by
    launching a *fresh* persistent context and reading its cookies. Returns
    {ok, platform, authenticated, state, url, cookie_names[], cookie_count,
     sessionid_present|li_at_present, notes[]}. Never posts."""
    if _browser_preflight_platform is None:
        return {"ok": False, "error": "meta_browser_publisher_missing"}
    p = ctx.payload or {}
    platform = str(p.get("platform") or "").strip().lower()
    if platform not in ("instagram", "linkedin"):
        return {"ok": False, "error": "unsupported_platform", "platform": platform}
    dwell = int(p.get("dwell_seconds") or 4)
    return _browser_preflight_platform(platform=platform, dwell_seconds=dwell)






def _resolve_fb_page_url(payload: dict) -> str:
    return (
        payload.get("destination_url")
        or _FB_PAGE_URLS.get(str(payload.get("page_slug") or ""), "")
        or "https://www.facebook.com/"
    )


def _run_browser_publisher_isolated(fn: Callable[..., dict], **kwargs) -> dict:
    """Run Playwright sync publishers in a separate Python process.

    The desktop companion can run under supervisors that keep asyncio state on
    the process. Playwright's sync API can still detect that state even when a
    handler is moved to a thread, so browser posting gets a clean interpreter.
    """
    worker = Path(__file__).resolve().parent / "browser_publish_worker.py"
    if not worker.exists():
        return {"ok": False, "error": "browser_worker_missing", "path": str(worker)}
    payload = {
        "module": getattr(fn, "__module__", ""),
        "function": getattr(fn, "__name__", ""),
        "kwargs": kwargs,
    }
    try:
        proc = subprocess.run(
            [sys.executable, str(worker)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=45 * 60,
            cwd=str(worker.parent),
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        result: dict[str, Any]
        try:
            # Use the last JSON-looking line so incidental browser/process noise
            # does not destroy the result envelope.
            line = next((ln for ln in reversed(stdout.splitlines()) if ln.strip().startswith("{")), "")
            result = json.loads(line) if line else {}
        except Exception:
            result = {}
        if not result:
            result = {"ok": False, "error": "browser_worker_no_json_result"}
        result.setdefault("exit_code", proc.returncode)
        if stdout:
            result.setdefault("stdout_tail", stdout[-4000:])
        if stderr:
            result.setdefault("stderr_tail", stderr[-4000:])
        if proc.returncode not in (0, 2) and result.get("ok") is not True:
            result.setdefault("error", "browser_worker_failed")
        return result
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": "browser_worker_timeout",
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else None,
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else None,
        }
    except Exception as exc:
        return {"ok": False, "error": "browser_worker_launch_exception", "detail": str(exc), "trace": traceback.format_exc(limit=6)}


def cap_browser_publish_facebook_reel(ctx: ActionContext) -> dict:
    if _publish_fb_reel is None:
        return {"ok": False, "error": "multi_platform_publisher_missing"}
    p = ctx.payload or {}
    if not p.get("video_url"):
        return {"ok": False, "error": "video_url_required"}
    res = _run_browser_publisher_isolated(
        _publish_fb_reel,
        page_url=_resolve_fb_page_url(p),
        video_url=str(p.get("video_url")),
        message=str(p.get("message") or p.get("title") or ""),
    )
    return _return_publish(ctx, res)


def cap_browser_publish_instagram(ctx: ActionContext) -> dict:
    if _publish_ig_feed is None:
        return {"ok": False, "error": "multi_platform_publisher_missing"}
    p = ctx.payload or {}
    res = _run_browser_publisher_isolated(
        _publish_ig_feed,
        image_url=p.get("image_url"),
        video_url=p.get("video_url"),
        message=str(p.get("message") or p.get("title") or ""),
    )
    return _return_publish(ctx, res)


def cap_browser_publish_instagram_reel(ctx: ActionContext) -> dict:
    if _publish_ig_reel is None:
        return {"ok": False, "error": "multi_platform_publisher_missing"}
    p = ctx.payload or {}
    if not p.get("video_url"):
        return {"ok": False, "error": "video_url_required"}
    res = _run_browser_publisher_isolated(
        _publish_ig_reel,
        video_url=str(p.get("video_url")),
        message=str(p.get("message") or p.get("title") or ""),
    )
    return _return_publish(ctx, res)


def cap_browser_publish_linkedin(ctx: ActionContext) -> dict:
    if _publish_linkedin is None:
        return {"ok": False, "error": "multi_platform_publisher_missing"}
    p = ctx.payload or {}
    res = _run_browser_publisher_isolated(
        _publish_linkedin,
        destination_url=p.get("destination_url"),
        message=str(p.get("message") or p.get("title") or ""),
        image_url=p.get("image_url"),
        video_url=p.get("video_url"),
        expected_handle=p.get("expected_handle") or p.get("page_slug"),
    )
    return _return_publish(ctx, res)


def cap_recover_linkedin_permalink(ctx: ActionContext) -> dict:
    """Post-hoc LinkedIn permalink recovery for an already-submitted post.
    Never publishes. Only writes a canonical urn:li:activity URL + screenshot
    back to the target browser_publish_jobs row when it can be proven.
    """
    if _recover_linkedin_permalink is None:
        return {"ok": False, "error": "multi_platform_publisher_missing"}
    p = ctx.payload or {}
    job_id = str(p.get("job_id") or "").strip()
    if not job_id:
        return {"ok": False, "error": "job_id_required"}
    match_terms = p.get("match_terms") if isinstance(p.get("match_terms"), list) else None
    res = _run_browser_publisher_isolated(
        _recover_linkedin_permalink,
        match_title=str(p.get("match_title") or ""),
        match_terms=match_terms,
        profile_slug=p.get("profile_slug"),
        submitted_after_iso=p.get("submitted_after_iso"),
    )
    permalink = res.get("permalink") or res.get("post_url")
    # Post evidence-only or verified receipt back to the shared receipt endpoint.
    outcome = "verified_permalink" if (res.get("ok") and permalink and "urn:li:activity:" in str(permalink)) else "evidence_only"
    try:
        creds = load_credentials()
        if creds:
            device_id, device_key = creds
            body = {
                "job_id": job_id,
                "outcome": outcome,
                "published_post_url": permalink if outcome == "verified_permalink" else None,
                "screenshot_path": res.get("screenshot_path"),
                "error": res.get("error"),
                "receipt": {
                    "kind": "linkedin_permalink_recovery",
                    "notes": res.get("notes", []),
                    "candidates": res.get("candidates", []),
                    "matched_title": res.get("matched_title"),
                },
            }
            requests.post(
                f"{FUNCTIONS_BASE}/browser-publish-result",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json",
                    "x-device-id": device_id,
                    "x-device-key": device_key,
                },
                json=body,
                timeout=20,
            )
    except Exception as e:  # pragma: no cover
        log(f"[recover_linkedin_permalink] receipt post failed: {e}")
    return {
        "ok": bool(res.get("ok")),
        "outcome": outcome,
        "permalink": permalink,
        "screenshot_path": res.get("screenshot_path"),
        "error": res.get("error"),
        "notes": res.get("notes", []),
        "candidates": res.get("candidates", []),
        "matched_title": res.get("matched_title"),
    }



def cap_browser_publish_youtube_short(ctx: ActionContext) -> dict:
    if _publish_yt_short is None:
        return {"ok": False, "error": "multi_platform_publisher_missing"}
    p = ctx.payload or {}
    if not p.get("video_url"):
        return {"ok": False, "error": "video_url_required"}
    res = _run_browser_publisher_isolated(
        _publish_yt_short,
        video_url=str(p.get("video_url")),
        title=str(p.get("title") or (p.get("message") or "")[:80] or "Untitled Short"),
        description=str(p.get("message") or ""),
    )
    return _return_publish(ctx, res)


# --- Browser-driven Meta credential configurator ---------------------------
try:
    from meta_browser_configurator import configure_meta_via_browser as _configure_meta  # type: ignore
except Exception:  # pragma: no cover
    _configure_meta = None  # type: ignore


def _sync_configured_meta_token_to_backend(res: dict) -> list[str]:
    notes: list[str] = []
    if not res.get("ok"):
        return notes
    try:
        from meta_credentials import load_meta_credentials  # type: ignore
        creds = load_meta_credentials() or {}
        page_id = str(creds.get("page_id") or res.get("page_id") or "")
        token = str(creds.get("page_access_token") or "")
        loaded = load_credentials()
        if page_id and token and loaded:
            device_id, device_key = loaded
            sync = requests.post(
                f"{FUNCTIONS_BASE}/meta-token-sync",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json",
                    "X-Device-Id": device_id,
                    "X-Device-Key": device_key,
                },
                json={
                    "fb_page_id": page_id,
                    "page_name": res.get("page_name") or "J. Fortitude",
                    "page_access_token": token,
                    "token_scopes": res.get("token_scopes") or [],
                    "trusted_source": "me_accounts",
                },
                timeout=30,
            )
            notes.append(f"backend_token_sync_http:{sync.status_code}")
            if sync.status_code >= 400:
                notes.append(f"backend_token_sync_failed:{sync.text[:300]}")
    except Exception as sync_exc:
        notes.append(f"backend_token_sync_exception:{sync_exc}")
    return notes


def cap_meta_app_dashboard_configure(ctx: ActionContext) -> dict:
    """Configure the Facebook Login for Business Settings for a given app_id.
    Toggles Client OAuth Login + Web OAuth Login ON and adds the redirect URI
    so subsequent meta_configure_via_browser calls can actually receive a
    token in the URL fragment. Runs in the persistent Unk browser profile."""
    payload = ctx.payload or {}
    app_id = (payload.get("meta_app_id") or "").strip()
    if not app_id:
        return {"ok": False, "error": "meta_app_id_required"}
    try:
        from meta_app_dashboard_configurator import configure_app_dashboard  # type: ignore
    except Exception as e:
        return {"ok": False, "error": f"module_missing:{e}"}
    redirect_uri = (payload.get("redirect_uri") or "").strip() or None
    return configure_app_dashboard(app_id=app_id, redirect_uri=redirect_uri)


def cap_meta_configure_via_browser(ctx: ActionContext) -> dict:

    if _configure_meta is None:
        return {"ok": False, "error": "meta_browser_configurator_missing"}
    payload = ctx.payload or {}
    # Doctrine: auto-fix locally. If cloud pushed the app secret, persist it
    # into the same store meta_credentials reads from — no Jason .env edits.
    pushed_secret = (payload.get("meta_app_secret") or "").strip()
    if pushed_secret:
        try:
            from meta_key_capture import save_secret as _save_meta_secret  # type: ignore
            _save_meta_secret("META_APP_SECRET", pushed_secret)
        except Exception as _e:
            log(f"meta_app_secret_save_failed: %s" % _e)
    # Solve-first shortcut: if cloud pushed a Page token + Page ID AND that
    # token actually works against Graph API right now, persist it locally and
    # skip OAuth. If the token is dead (e.g. the Meta app was rebuilt and the
    # server-side secret is stale), fall through to real OAuth instead of
    # falsely reporting success.
    pushed_token = (payload.get("meta_page_access_token") or "").strip()
    pushed_page_id = (payload.get("meta_page_id") or "").strip()
    if pushed_token and pushed_page_id and pushed_page_id.isdecimal() and len(pushed_page_id) <= 40:
        try:
            import requests as _rq
            probe = _rq.get(
                f"https://graph.facebook.com/v25.0/{pushed_page_id}",
                params={"fields": "id,name"},
                headers={"Authorization": f"Bearer {pushed_token}"},
                timeout=15,
                allow_redirects=False,
            )
            probe_ok = probe.status_code == 200 and str((probe.json() or {}).get("id")) == pushed_page_id
        except Exception as pe:
            probe_ok = False
            log(f"meta_pushed_token_probe_failed: %s" % pe)
        if probe_ok:
            try:
                from meta_browser_configurator import _save_meta_credentials  # type: ignore
                save_info = _save_meta_credentials(
                    app_id=(payload.get("meta_app_id") or "").strip() or None,
                    configuration_id=(payload.get("meta_configuration_id") or "").strip() or None,
                    page_id=pushed_page_id,
                    page_access_token=pushed_token,
                )
                res = {
                    "ok": True,
                    "steps": [{"step": "seeded_from_cloud_secrets_after_probe", "ok": True}],
                    "notes": ["skipped_oauth_using_verified_cloud_credentials"],
                    "app_id": (payload.get("meta_app_id") or "").strip() or None,
                    "configuration_id": (payload.get("meta_configuration_id") or "").strip() or None,
                    "page_id": pushed_page_id,
                    "page_name": payload.get("preferred_page_name") or "J. Fortitude",
                    "page_access_token_preview": (pushed_token[:6] + "…" + pushed_token[-4:]) if len(pushed_token) > 12 else "***",
                    "save_info": save_info,
                    "app_secret_missing": not pushed_secret,
                }
                res["notes"].extend(_sync_configured_meta_token_to_backend(res))
                return res
            except Exception as e:
                log(f"meta_seed_from_cloud_failed: %s" % e)
                # Fall through to normal OAuth path below.
        else:
            log("meta_pushed_token_dead_falling_through_to_oauth")

    # Preferred deterministic path: Facebook Login for Business code flow.
    # Opens the OAuth dialog, captures ?code=, and posts it to the
    # meta-oauth-exchange edge function which trades it (with META_APP_SECRET)
    # for a long-lived user token, discovers Pages, and writes the Page
    # access tokens directly into meta_page_credentials. This replaces the
    # fragile implicit-token + dashboard-scraping path.
    app_id_for_code = (payload.get("meta_app_id") or "").strip()
    if not app_id_for_code:
        try:
            from meta_browser_configurator import _load_existing_app_id  # type: ignore
            app_id_for_code = _load_existing_app_id() or ""
        except Exception:
            pass
    config_id_for_code = (payload.get("meta_configuration_id") or "").strip() or None
    if app_id_for_code:
        try:
            from meta_browser_configurator import oauth_capture_code  # type: ignore
            cap = oauth_capture_code(
                app_id=app_id_for_code,
                configuration_id=config_id_for_code,
            )
        except Exception as ce:
            cap = {"ok": False, "error": f"oauth_capture_code_exception:{ce}"}
        if cap.get("ok") and cap.get("code"):
            loaded = load_credentials()
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            }
            if loaded:
                device_id, device_key = loaded
                headers["X-Device-Id"] = device_id
                headers["X-Device-Key"] = device_key
            try:
                exch = requests.post(
                    f"{FUNCTIONS_BASE}/meta-oauth-exchange",
                    headers=headers,
                    json={
                        "code": cap["code"],
                        "redirect_uri": cap.get("redirect_uri"),
                        "app_id": app_id_for_code,
                    },
                    timeout=60,
                )
                exch_body = {}
                try: exch_body = exch.json()
                except Exception: exch_body = {"raw": exch.text[:400]}
                return {
                    "ok": bool(exch_body.get("ok")),
                    "flow": "login_for_business_code_exchange",
                    "http_status": exch.status_code,
                    "app_id": app_id_for_code,
                    "configuration_id": config_id_for_code,
                    "exchange_result": exch_body,
                    "capture_notes": cap.get("notes"),
                    "capture_steps": cap.get("steps"),
                    "screenshot_path": cap.get("screenshot_path"),
                }
            except Exception as ee:
                return {
                    "ok": False,
                    "flow": "login_for_business_code_exchange",
                    "error": f"exchange_call_failed:{ee}",
                    "capture_notes": cap.get("notes"),
                }
        else:
            # Code capture failed — fall through to legacy path as backup.
            log(f"oauth_code_capture_failed:{cap.get('error')}")

    res = _configure_meta(
        preferred_page_name=payload.get("preferred_page_name") or "J. Fortitude",
        app_id=payload.get("meta_app_id"),
        configuration_id=payload.get("meta_configuration_id"),
    )
    res.setdefault("notes", []).extend(_sync_configured_meta_token_to_backend(res))
    return res



# ---------------------------------------------------------------------------
# Self-update + restart (Ground Zero remote maintenance)
# ---------------------------------------------------------------------------

_RESTART_REQUESTED: dict[str, Any] = {"pending": False, "reason": "", "strategy": "execv"}

def _companion_script_dir() -> Path:
    return Path(__file__).resolve().parent

def cap_self_update(ctx: ActionContext) -> dict:
    """Download the latest desktop-companion ZIP and swap the source files.

    Payload: { zip_url: str }. Backs up replaced files to ~/.unk-companion/backup-<ts>/
    and copies .py/.bat/.sh/.ps1/.md from the ZIP into the running install dir.
    A `restart_companion` action should follow to load the new code.
    """
    import io
    import shutil
    import zipfile

    # Restart requests are routed through the self_update capability for
    # historical queue reasons; delegate them to the dedicated handler.
    if ctx.action_type == "restart_companion":
        return cap_restart_companion(ctx)

    zip_url = (ctx.payload or {}).get("zip_url", "")
    if not isinstance(zip_url, str) or not zip_url.startswith(("http://", "https://")):
        return {"ok": False, "error": "bad_zip_url"}

    if "pefatniumnrxwbgnwvvh" in zip_url.lower():
        return {"ok": False, "error": "retired_legacy_release_source"}

    script_dir = _companion_script_dir()
    if not (script_dir / "unk_companion.py").exists():
        return {"ok": False, "error": "cannot_locate_install_dir", "dir": str(script_dir)}

    try:
        # Cache-bust: some CDNs serve a stale object for the same path.
        bust_url = zip_url + ("&" if "?" in zip_url else "?") + f"cb={int(time.time())}"
        r = requests.get(bust_url, timeout=60, headers={"Cache-Control": "no-cache"})
        if r.status_code != 200:
            return {"ok": False, "error": "download_failed", "http": r.status_code}
        raw = r.content
        if len(raw) > 50 * 1024 * 1024:
            return {"ok": False, "error": "zip_too_large", "bytes": len(raw)}

        import hashlib
        zip_sha256 = hashlib.sha256(raw).hexdigest()
        expect = (ctx.payload or {}).get("expect_zip_sha256")
        if expect and expect != zip_sha256:
            # Fail closed: we downloaded a different package than the one built.
            return {
                "ok": False,
                "error": "zip_hash_mismatch",
                "expected_sha256": expect,
                "downloaded_sha256": zip_sha256,
                "bytes": len(raw),
                "url": bust_url,
            }


        stage = COMPANION_DIR / f"update-stage-{int(time.time())}"
        stage.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for name in zf.namelist():
                if name.startswith("/") or ".." in Path(name).parts:
                    shutil.rmtree(stage, ignore_errors=True)
                    return {"ok": False, "error": "bad_zip_entry", "entry": name}
            zf.extractall(stage)

        entries = [p for p in stage.iterdir()]
        src_root = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage

        previous_build_ref = None
        try:
            if RUNNING_BUILD_FILE.exists():
                previous_build_ref = json.loads(RUNNING_BUILD_FILE.read_text()).get("build_ref")
        except Exception:
            previous_build_ref = None

        backup = COMPANION_DIR / f"backup-{int(time.time())}"
        backup.mkdir(parents=True, exist_ok=True)
        swap_exts = {".py", ".bat", ".cmd", ".vbs", ".sh", ".ps1", ".md"}
        swapped: list[str] = []
        for src in src_root.rglob("*"):
            if not src.is_file() or src.suffix.lower() not in swap_exts:
                continue
            rel = src.relative_to(src_root)
            dst = script_dir / rel
            if dst.exists():
                bkp = backup / rel
                bkp.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, bkp)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            swapped.append(str(rel))

        # Converge legacy visible launchers before attempting scheduled-task
        # repair. Task registration may require elevation on older installs,
        # but the signed-in user can always stop their own stale CMD wrappers
        # and remove obsolete Startup shortcuts. Never stop Python workers or
        # Chrome here, so active Facebook publishing remains untouched.
        popup_cleanup_notes: list[str] = []
        if os.name == "nt":
            try:
                cleanup_script = r"""
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
try {
  Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and $_.Name -match '^(cmd|powershell)\.exe$' -and
    $_.CommandLine -match '(launch_unk\.bat|unk_(audio|mirror)_worker)'
  } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
} catch {}
try {
  Get-ChildItem -Path $startup -Force -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^(launch_unk|unk[_ -]?(companion|supervisor|keepalive)).*\.(bat|cmd|lnk)$'
  } | Remove-Item -Force -ErrorAction SilentlyContinue
} catch {}
"""
                cleanup = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", cleanup_script],
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                popup_cleanup_notes.append(f"legacy_popup_cleanup_exit:{cleanup.returncode}")
                if cleanup.stderr:
                    popup_cleanup_notes.append(f"legacy_popup_cleanup_stderr:{cleanup.stderr[-500:]}")
            except Exception as cleanup_exc:
                popup_cleanup_notes.append(f"legacy_popup_cleanup_warning:{cleanup_exc}")

        dependency_notes: list[str] = []
        try:
            dep = subprocess.run(
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
            dependency_notes.append(f"pip_exit:{dep.returncode}")
            browser = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            dependency_notes.append(f"chromium_exit:{browser.returncode}")
        except Exception as dep_exc:
            dependency_notes.append(f"dependency_repair_warning:{dep_exc}")

        supervisor_repair_notes: list[str] = []
        try:
            installer = script_dir / "install_supervisor.ps1"
            if os.name == "nt" and installer.exists():
                repair = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(installer),
                        "-RepairOnly",
                        "-SkipVerify",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                supervisor_repair_notes.append(f"install_supervisor_repair_exit:{repair.returncode}")
                if repair.stderr:
                    supervisor_repair_notes.append(f"install_supervisor_repair_stderr:{repair.stderr[-500:]}")
            elif os.name == "nt":
                supervisor_repair_notes.append("install_supervisor_missing")
        except Exception as repair_exc:
            supervisor_repair_notes.append(f"install_supervisor_repair_warning:{repair_exc}")

        shutil.rmtree(stage, ignore_errors=True)

        # Two-phase update: if the enqueuer supplied an update_verification_token,
        # persist it so the NEXT run of unk_companion (after restart_companion)
        # can POST an ack. Also stash the backup dir so cap_rollback_last_update
        # knows where to revert to if the platform decides the update failed.
        token = (ctx.payload or {}).get("update_verification_token")
        if token:
            try:
                PENDING_UPDATE_TOKEN_FILE.write_text(json.dumps({
                    "token": token,
                    "staged_at": time.time(),
                    "backup_dir": str(backup),
                    "new_build_ref": zip_url,
                    "previous_build_ref": previous_build_ref,
                }))
            except Exception as tok_exc:
                log(f"pending update token write failed: {tok_exc}")
        try:
            (COMPANION_DIR / "last_backup.json").write_text(json.dumps({
                "backup_dir": str(backup),
                "at": time.time(),
                "new_build_ref": zip_url,
                "previous_build_ref": previous_build_ref,
            }))
        except Exception:
            pass
        try:
            RUNNING_BUILD_FILE.write_text(json.dumps({
                "build_ref": zip_url,
                "installed_at": time.time(),
                "swapped": swapped,
            }))
        except Exception as build_exc:
            log(f"running build receipt write failed: {build_exc}")

        installed_sha = {}
        try:
            for fname in ("unk_companion.py", "media_mirror_worker.py", "multi_platform_publisher.py"):
                fp = script_dir / fname
                if fp.exists():
                    installed_sha[fname] = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]
        except Exception:
            pass

        return {
            "ok": True,
            "swapped": swapped,
            "swapped_count": len(swapped),
            "zip_sha256": zip_sha256,
            "zip_bytes": len(raw),
            "installed_sha256_prefix": installed_sha,
            "backup_dir": str(backup),
            "install_dir": str(script_dir),
            "dependency_notes": dependency_notes,
            "supervisor_repair_notes": supervisor_repair_notes,
            "popup_cleanup_notes": popup_cleanup_notes,
            "update_verification_token": token if token else None,
        }

    except Exception as e:
        return {"ok": False, "error": "update_failed", "detail": str(e),
                "trace": traceback.format_exc(limit=4)}


def cap_rollback_last_update(ctx: ActionContext) -> dict:
    """Restore files from the most recent self_update backup. Meant to be
    called by the recovery loop after desktop-update-verify rolls back."""
    import shutil
    try:
        pointer = COMPANION_DIR / "last_backup.json"
        if not pointer.exists():
            return {"ok": False, "error": "no_previous_backup"}
        pointer_payload = json.loads(pointer.read_text())
        backup_dir = Path(pointer_payload.get("backup_dir", ""))
        if not backup_dir.exists() or not backup_dir.is_dir():
            return {"ok": False, "error": "backup_dir_missing", "path": str(backup_dir)}
        script_dir = _companion_script_dir()
        restored: list[str] = []
        for src in backup_dir.rglob("*"):
            if not src.is_file(): continue
            rel = src.relative_to(backup_dir)
            dst = script_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(str(rel))
        try:
            previous_build_ref = pointer_payload.get("previous_build_ref")
            if previous_build_ref:
                RUNNING_BUILD_FILE.write_text(json.dumps({
                    "build_ref": previous_build_ref,
                    "restored_at": time.time(),
                    "rollback_from": pointer_payload.get("new_build_ref"),
                }))
            elif RUNNING_BUILD_FILE.exists():
                RUNNING_BUILD_FILE.unlink()
        except Exception as build_restore_exc:
            log(f"running build rollback receipt failed: {build_restore_exc}")
        # Schedule an immediate restart so the reverted script runs.
        _RESTART_REQUESTED["pending"] = True
        _RESTART_REQUESTED["reason"] = "rollback_last_update"
        return {"ok": True, "restored": restored, "restored_count": len(restored), "from": str(backup_dir)}
    except Exception as e:
        return {"ok": False, "error": "rollback_failed", "detail": str(e),
                "trace": traceback.format_exc(limit=4)}


def _restart_already_satisfied(created_at, boot_ts, *, expected_build_ref=None, current_build_ref=None):
    """A previously approved restart is already met by a later real boot.

    Keep the original action-result and device authentication; never skip a
    newer restart, a missing timestamp, or a mismatched required build.
    """
    from datetime import datetime as _datetime
    if not isinstance(created_at, str) or not created_at:
        return False
    if type(boot_ts) not in (int, float) or boot_ts <= 0:
        return False
    if expected_build_ref and (not isinstance(expected_build_ref, str)
                               or expected_build_ref != current_build_ref):
        return False
    try:
        observed = _datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return bool(observed.tzinfo and float(boot_ts) > observed.timestamp())
    except (TypeError, ValueError, OverflowError):
        return False


def cap_restart_companion(ctx: ActionContext) -> dict:
    from_source = ctx.payload if isinstance(ctx.payload, dict) else {}
    if _restart_already_satisfied(
        ctx.created_at, BOOT_TS,
        expected_build_ref=from_source.get("expected_build_ref"),
        current_build_ref=_runtime_routing_and_build_evidence().get("companion_build_ref"),
    ):
        return {"ok": True, "restart_scheduled": False,
                "already_satisfied_by_current_boot": True,
                "completion_claimed": False}
    _RESTART_REQUESTED["pending"] = True
    _RESTART_REQUESTED["reason"] = str((ctx.payload or {}).get("reason") or "manual")
    strategy = str((ctx.payload or {}).get("strategy") or "execv").lower().strip()
    if strategy not in {"execv", "supervisor_exit"}:
        strategy = "execv"
    _RESTART_REQUESTED["strategy"] = strategy
    return {"ok": True, "restart_scheduled": True, "reason": _RESTART_REQUESTED["reason"], "strategy": strategy}


def cap_browser_release_locks(ctx: ActionContext) -> dict:
    """Force-close all Unk/Playwright Chromium windows using the saved browser profile.

    Use this before retrying publish jobs when the browser profile is wedged
    (leftover Playwright Chromium holding SingletonLock; publishes fail with
    composer_not_found / profile_locked). No-op on non-Windows hosts.
    """
    notes: list[str] = []
    released_via_publisher = False
    try:
        from meta_browser_publisher import _release_locked_profile  # type: ignore
        _release_locked_profile(notes)
        released_via_publisher = True
    except Exception as e:
        notes.append(f"publisher_release_unavailable:{e}")

    killed_extra = 0
    if os.name == "nt":
        try:
            proc = subprocess.run(
                ["wmic", "process", "where",
                 "Name='chrome.exe' or Name='chromium.exe'",
                 "get", "ProcessId,CommandLine", "/FORMAT:CSV"],
                capture_output=True, text=True, timeout=10,
            )
            for line in (proc.stdout or "").splitlines():
                if ".unk_companion" not in line and "browser_profile" not in line:
                    continue
                pid = line.strip().split(",")[-1]
                if not pid.isdigit():
                    continue
                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, timeout=5)
                killed_extra += 1
            if killed_extra:
                notes.append(f"broad_sweep_killed:{killed_extra}")
                time.sleep(1.0)
        except Exception as e:
            notes.append(f"broad_sweep_warning:{e}")

    cleared_locks: list[str] = []
    try:
        from meta_browser_publisher import PROFILE_DIR as _PROFILE_DIR  # type: ignore
        for lock_name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            p = Path(_PROFILE_DIR) / lock_name
            if p.exists():
                try:
                    p.unlink()
                    cleared_locks.append(lock_name)
                except Exception as e:
                    notes.append(f"lock_unlink_warning:{lock_name}:{e}")
    except Exception as e:
        notes.append(f"profile_dir_unavailable:{e}")

    return {
        "ok": True,
        "released_via_publisher": released_via_publisher,
        "extra_processes_killed": killed_extra,
        "cleared_locks": cleared_locks,
        "notes": notes,
    }





VENDOR_VAULT_URL = f"{FUNCTIONS_BASE}/vendor-vault"


def _fetch_vendor_credential(device_id: str, device_key: str, credential_id: str, reason: str) -> dict:
    """Call vendor-vault edge function with device auth to fetch decrypted creds."""
    try:
        r = requests.post(
            VENDOR_VAULT_URL,
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
                "X-Device-Id": device_id,
                "X-Device-Key": device_key,
            },
            json={"action": "fetch_decrypted", "credential_id": credential_id, "reason": reason},
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code >= 400:
            return {"ok": False, "error": f"http_{r.status_code}", "detail": r.text[:400]}
        data = r.json()
        if not data.get("ok"):
            return {"ok": False, "error": data.get("error") or "unknown_vault_error", "detail": data}
        return {"ok": True, "credential": data["credential"]}
    except Exception as e:
        return {"ok": False, "error": "fetch_exception", "detail": str(e)}


EMAIL_VERIFICATION_URL = f"{FUNCTIONS_BASE}/email-verification-fetch-code"


def _email_verify_call(device_id: str, device_key: str, payload: dict) -> dict:
    """POST to email-verification-fetch-code with device auth. Returns raw JSON."""
    try:
        r = requests.post(
            EMAIL_VERIFICATION_URL,
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
                "X-Device-Id": device_id,
                "X-Device-Key": device_key,
            },
            json=payload,
            timeout=HTTP_TIMEOUT,
        )
        try:
            data = r.json()
        except Exception:
            data = {"ok": False, "error": f"http_{r.status_code}", "detail": r.text[:400]}
        return data
    except Exception as e:
        return {"ok": False, "error": "http_exception", "detail": str(e)}


def cap_email_fetch_verification_code(ctx: ActionContext) -> dict:
    """Fetch the newest one-time code from Gmail matching a service hint."""
    creds = load_credentials()
    if not creds:
        return {"ok": False, "error": "companion_not_enrolled"}
    device_id, device_key = creds
    payload = dict(ctx.payload or {})
    payload.setdefault("action", "fetch")
    if not payload.get("service_hint"):
        return {"ok": False, "error": "service_hint_required"}
    return _email_verify_call(device_id, device_key, payload)


def cap_vendor_login(ctx: ActionContext) -> dict:
    """Attempt an automated vendor login using a credential from the vault.
    On email-based 2FA, Unk auto-fetches the code from Gmail and enters it.
    On app-approval / SMS / CAPTCHA challenges, escalates via needs_human.
    """
    credential_id = str((ctx.payload or {}).get("credential_id") or "")
    if not credential_id:
        return {"ok": False, "error": "credential_id_required"}
    creds = load_credentials()
    if not creds:
        return {"ok": False, "error": "companion_not_enrolled"}
    device_id, device_key = creds

    fetched = _fetch_vendor_credential(device_id, device_key, credential_id, "vendor_login_action")
    if not fetched.get("ok"):
        return fetched

    try:
        from vendor_browser import login as _vendor_login  # type: ignore
    except Exception as e:
        return {"ok": False, "error": "vendor_browser_unavailable", "detail": str(e)}

    def _fetch_email_code(service_hint: str, sender_hint: str | None = None,
                          subject_hint: str | None = None) -> dict:
        return _email_verify_call(device_id, device_key, {
            "action": "fetch",
            "service_hint": service_hint,
            "sender_hint": sender_hint,
            "subject_hint": subject_hint,
            "context": {"credential_id": credential_id},
        })

    def _report_event(event_id: str, status: str, escalation_reason: str | None = None,
                      screenshot_path: str | None = None) -> None:
        _email_verify_call(device_id, device_key, {
            "action": "update",
            "event_id": event_id,
            "status": status,
            "escalation_reason": escalation_reason,
            "screenshot_path": screenshot_path,
        })

    result = _vendor_login(
        credential=fetched["credential"],
        fetch_email_code=_fetch_email_code,
        report_event=_report_event,
    )
    return result




def cap_vendor_signup(ctx: ActionContext) -> dict:
    """Placeholder for vendor account creation. Requires per-site scaffolding."""
    payload = ctx.payload or {}
    return {
        "ok": False,
        "error": "not_implemented",
        "detail": "vendor_signup requires per-site logic. Add the target site's signup steps to vendor_browser.py.",
        "requested": {
            "service_name": payload.get("service_name"),
            "service_url": payload.get("service_url"),
        },
    }


def cap_vendor_action(ctx: ActionContext) -> dict:
    """Placeholder for arbitrary post-login vendor actions (add to cart, checkout, etc.)."""
    return {
        "ok": False,
        "error": "not_implemented",
        "detail": "vendor_action requires per-site logic. Add steps to vendor_browser.py.",
    }


# ---------------------------------------------------------------------------
# Media engine — local FFmpeg dependency playbook + derivative generation.
#
# These run entirely on Ground Zero. No winget, no elevation, no Lovable turn.
# ---------------------------------------------------------------------------
def _ffmpeg_module():
    import importlib
    import ffmpeg_bootstrap  # type: ignore
    return importlib.reload(ffmpeg_bootstrap)


def cap_ffmpeg_ensure(ctx: ActionContext) -> dict:
    """Install/verify FFmpeg under the Unk runtime from a checksum-verified build."""
    payload = ctx.payload or {}
    try:
        mod = _ffmpeg_module()
        res = mod.ensure(force=bool(payload.get("force")), log=log)
        res["companion_version"] = COMPANION_VERSION
        return res
    except Exception as e:
        return {"ok": False, "error": "ffmpeg_ensure_failed", "detail": str(e)}


def cap_ffmpeg_health(ctx: ActionContext) -> dict:
    """Report install path, version, checksum origin and a live encode proof."""
    try:
        mod = _ffmpeg_module()
        st = mod.status()
        st["ok"] = bool(st.get("healthy"))
        st["companion_version"] = COMPANION_VERSION
        return st
    except Exception as e:
        return {"ok": False, "error": "ffmpeg_health_failed", "detail": str(e)}


def cap_ffmpeg_rollback(ctx: ActionContext) -> dict:
    """Flip back to the previously verified FFmpeg install."""
    try:
        mod = _ffmpeg_module()
        return mod.rollback(log=log)
    except Exception as e:
        return {"ok": False, "error": "ffmpeg_rollback_failed", "detail": str(e)}


def cap_media_generate_derivative(ctx: ActionContext) -> dict:
    """Produce (or reuse) a platform-ready H.264/AAC derivative from a local master.

    payload: {asset_id, master_path, profile?, max_bytes?, max_height?,
              platform_policies?, reuse?}
    The master is never modified. Returns full derivative metadata for upsert
    into `media_derivatives`, including per-platform eligibility so a full
    interview is never mislabelled as a Reel/Short.
    """
    payload = ctx.payload or {}
    asset_id = str(payload.get("asset_id") or "").strip()
    master_path = str(payload.get("master_path") or "").strip()
    if not asset_id or not master_path:
        return {"ok": False, "error": "asset_id_and_master_path_required"}
    try:
        import importlib
        import media_derivative_worker as mdw  # type: ignore
        mdw = importlib.reload(mdw)
        res = mdw.build_derivative(
            asset_id=asset_id,
            master_path=master_path,
            profile=payload.get("profile") or mdw.DEFAULT_PROFILE,
            max_bytes=int(payload.get("max_bytes") or mdw.DEFAULT_MAX_BYTES),
            max_height=int(payload.get("max_height") or 1080),
            platform_policies=payload.get("platform_policies") or {},
            reuse=payload.get("reuse", True),
            log=log,
        )
        res["companion_version"] = COMPANION_VERSION
        return res
    except Exception as e:
        return {"ok": False, "error": "derivative_generation_failed", "detail": str(e)}


def cap_media_make_reel(ctx: ActionContext) -> dict:
    """Cut one vertical reel + poster frame from a mirrored master and upload it.

    payload: {plan_id, source_asset_id, source_url, start_seconds,
              duration_seconds, upload_video_url, upload_thumb_url}
    Pure local FFmpeg — no model calls, no Lovable credits. The master is
    range-read over HTTPS, never fully downloaded, and never modified.
    """
    payload = ctx.payload or {}
    required = ("plan_id", "source_asset_id", "source_url",
                "upload_video_url", "upload_thumb_url")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return {"ok": False, "error": "missing_payload_fields", "fields": missing}
    try:
        import importlib
        import media_reel_worker as mrw  # type: ignore
        mrw = importlib.reload(mrw)
        res = mrw.make_reel(
            plan_id=str(payload["plan_id"]),
            source_asset_id=str(payload["source_asset_id"]),
            source_url=str(payload["source_url"]),
            start_seconds=float(payload.get("start_seconds") or 0),
            duration_seconds=float(payload.get("duration_seconds") or 30),
            upload_video_url=str(payload["upload_video_url"]),
            upload_thumb_url=str(payload["upload_thumb_url"]),
            log=log,
        )
        res["companion_version"] = COMPANION_VERSION
        return res
    except Exception as e:
        return {"ok": False, "error": "reel_generation_failed", "detail": str(e)}





def cap_media_local_inventory(ctx: ActionContext) -> dict:
    """Map local master files on Ground Zero: path, size, mtime, probe metadata.

    payload: {roots: [path,...], patterns?: [".mp4",".mov"], probe?: bool,
              name_contains?: str, limit?: int}
    Used to build the Carl Boyd readiness inventory from verified local truth
    instead of guessing, and to avoid re-downloading multi-GB masters.
    """
    payload = ctx.payload or {}
    roots = payload.get("roots") or []
    if isinstance(roots, str):
        roots = [roots]
    exts = [e.lower() for e in (payload.get("patterns") or [".mp4", ".mov", ".m4v", ".mkv", ".avi"])]
    needle = str(payload.get("name_contains") or "").lower().strip()
    do_probe = bool(payload.get("probe", True))
    limit = int(payload.get("limit") or 400)

    items: list[dict] = []
    scanned_roots: list[dict] = []
    try:
        mod = _ffmpeg_module()
    except Exception:
        mod = None
    for root in roots:
        p = Path(str(root))
        info = {"root": str(p), "exists": p.exists(), "files": 0}
        if not p.exists():
            scanned_roots.append(info)
            continue
        try:
            for f in p.rglob("*"):
                if len(items) >= limit:
                    break
                if not f.is_file() or f.suffix.lower() not in exts:
                    continue
                if needle and needle not in f.name.lower():
                    continue
                try:
                    st = f.stat()
                except Exception:
                    continue
                rec = {
                    "path": str(f),
                    "file_name": f.name,
                    "size_bytes": st.st_size,
                    "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                }
                if do_probe and mod:
                    pr = mod.probe(str(f))
                    if pr.get("ok"):
                        rec.update({
                            "duration_seconds": pr.get("duration_seconds"),
                            "width": pr.get("width"),
                            "height": pr.get("height"),
                            "container": pr.get("container"),
                            "video_codec": pr.get("video_codec"),
                            "audio_codec": pr.get("audio_codec"),
                        })
                    else:
                        rec["probe_error"] = pr.get("error")
                items.append(rec)
                info["files"] += 1
        except Exception as e:
            info["error"] = str(e)
        scanned_roots.append(info)

    return {
        "ok": True,
        "roots": scanned_roots,
        "count": len(items),
        "items": items,
        "ffmpeg_available": bool(mod and mod.read_config().get("ffprobe")),
        "companion_version": COMPANION_VERSION,
    }


def _detect_local_drives(include_system: bool = False) -> list[dict]:
    """Enumerate attached drives (external/USB first). Windows + POSIX."""
    drives: list[dict] = []
    if os.name == "nt":
        import ctypes
        import string
        kernel = ctypes.windll.kernel32
        mask = kernel.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if not (mask >> i) & 1:
                continue
            root = f"{letter}:\\"
            try:
                dtype = kernel.GetDriveTypeW(ctypes.c_wchar_p(root))
            except Exception:
                dtype = 0
            # 2 = removable, 3 = fixed, 4 = network, 5 = cdrom
            if dtype not in (2, 3):
                continue
            is_system = letter.upper() == "C"
            if is_system and not include_system:
                continue
            label = ""
            try:
                buf = ctypes.create_unicode_buffer(1024)
                fsbuf = ctypes.create_unicode_buffer(1024)
                kernel.GetVolumeInformationW(
                    ctypes.c_wchar_p(root), buf, 1024, None, None, None, fsbuf, 1024)
                label = buf.value
            except Exception:
                pass
            drives.append({
                "root": root,
                "volume_label": label,
                "kind": "removable" if dtype == 2 else "fixed",
                "is_system": is_system,
            })
        # Removable/external drives are what Jason means by "my external drive".
        drives.sort(key=lambda d: (d["kind"] != "removable", d["root"]))
    else:
        for base in ("/Volumes", "/media", "/mnt"):
            p = Path(base)
            if not p.exists():
                continue
            try:
                for child in p.iterdir():
                    if child.is_dir():
                        drives.append({"root": str(child), "volume_label": child.name,
                                       "kind": "removable", "is_system": False})
            except Exception:
                continue
    return drives


def _classify_media_local_ingest_receipt(body: object, scanned: int) -> dict:
    """Require a durable K ingest event and one verifiable outcome per source file.

    A transport 200 is not a completed ingest. Unknown writes must not be
    automatically replayed because asset changes may already have committed.
    """
    unverified = {"ok": False, "error": "ingest_receipt_unverified",
                  "retry_prohibited": True}
    if not isinstance(body, dict) or body.get("ok") is not True:
        return unverified
    receipt_id = body.get("audit_receipt_id")
    matched, created = body.get("matched"), body.get("created")
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        return unverified
    if (not isinstance(scanned, int) or scanned < 1
            or type(matched) is not int or type(created) is not int
            or matched < 0 or created < 0 or matched + created > scanned):
        return unverified

    rows = body.get("results")
    if not isinstance(rows, list) or len(rows) != scanned:
        return unverified
    accepted_rows = [row for row in rows
                     if isinstance(row, dict) and row.get("status")
                     in ("linked_local_master", "registered_local_master")]
    if (len(accepted_rows) != matched + created
            or sum(row["status"] == "linked_local_master" for row in accepted_rows) != matched
            or sum(row["status"] == "registered_local_master" for row in accepted_rows) != created
            or any(not isinstance(row.get("asset_id"), str)
                   or not row["asset_id"].strip() for row in accepted_rows)):
        return unverified

    accepted = matched + created
    result = {"ok": accepted == scanned, "audit_receipt_id": receipt_id,
              "matched": matched, "created": created, "accepted": accepted,
              "rejected": scanned - accepted}
    if accepted != scanned:
        result.update(error="ingest_manifest_incomplete", retry_prohibited=True)
    return result


def cap_media_local_ingest(ctx: ActionContext) -> dict:
    """Open attached drives, find master video files, and register them upstream.

    payload: {roots?: [path,...], include_system?: bool, name_contains?: str,
              series_tag?: str, owning_org?: str, owning_program?: str,
              approve?: bool, limit?: int, probe?: bool, min_size_mb?: int}

    Auto-detects external drives when no roots are given, walks them for video
    masters, probes duration locally with ffprobe, then POSTs the manifest to
    the media-local-ingest edge function. Existing library rows are relinked by
    file name so the multi-gigabyte masters never have to be re-downloaded.
    """
    payload = ctx.payload or {}
    roots = payload.get("roots") or []
    if isinstance(roots, str):
        roots = [roots]

    detected = _detect_local_drives(include_system=bool(payload.get("include_system")))
    if not roots:
        roots = [d["root"] for d in detected]
    if not roots:
        return {"ok": False, "error": "no_attached_drives_found",
                "hint": "plug the external drive in, or pass roots explicitly"}

    label_by_root = {d["root"]: d.get("volume_label") for d in detected}
    exts = [e.lower() for e in (payload.get("patterns") or [".mp4", ".mov", ".m4v", ".mkv", ".avi"])]
    needle = str(payload.get("name_contains") or "").lower().strip()
    limit = int(payload.get("limit") or 400)
    min_bytes = int(payload.get("min_size_mb") or 20) * 1024 * 1024
    do_probe = bool(payload.get("probe", True))
    skip_dirs = {"$recycle.bin", "system volume information", "windows",
                 "program files", "program files (x86)", "node_modules", "appdata"}

    try:
        mod = _ffmpeg_module()
    except Exception:
        mod = None

    items: list[dict] = []
    scanned: list[dict] = []
    for root in roots:
        p = Path(str(root))
        info = {"root": str(p), "exists": p.exists(), "files": 0,
                "volume_label": label_by_root.get(str(p))}
        if not p.exists():
            scanned.append(info)
            continue
        try:
            for f in p.rglob("*"):
                if len(items) >= limit:
                    break
                try:
                    if any(part.lower() in skip_dirs for part in f.parts):
                        continue
                    if not f.is_file() or f.suffix.lower() not in exts:
                        continue
                    st = f.stat()
                except Exception:
                    continue
                if st.st_size < min_bytes:
                    continue
                if needle and needle not in f.name.lower():
                    continue
                rec = {
                    "path": str(f),
                    "file_name": f.name,
                    "parent_path": str(f.parent),
                    "volume_label": info.get("volume_label"),
                    "size_bytes": st.st_size,
                    "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                }
                if do_probe and mod:
                    pr = mod.probe(str(f))
                    if pr.get("ok"):
                        rec.update({
                            "duration_seconds": pr.get("duration_seconds"),
                            "width": pr.get("width"),
                            "height": pr.get("height"),
                        })
                    else:
                        rec["probe_error"] = pr.get("error")
                items.append(rec)
                info["files"] += 1
        except Exception as e:
            info["error"] = str(e)
        scanned.append(info)

    if not items:
        return {"ok": False, "error": "no_master_files_found", "roots": scanned,
                "detected_drives": detected, "companion_version": COMPANION_VERSION}

    creds = load_credentials()
    if not creds:
        return {"ok": False, "error": "device_not_enrolled"}
    device_id, device_key = creds

    try:
        r = requests.post(
            f"{FUNCTIONS_BASE}/media-local-ingest",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
                "x-device-id": device_id,
                "x-device-key": device_key,
            },
            json={
                "items": items,
                "series_tag": payload.get("series_tag"),
                "owning_org": payload.get("owning_org"),
                "owning_program": payload.get("owning_program"),
                "approve": bool(payload.get("approve")),
                "device_label": payload.get("device_label"),
            },
            timeout=180,
        )
        body = r.json() if r.content else {}
    except Exception as e:
        return {"ok": False, "error": "ingest_post_failed", "detail": str(e),
                "scanned": len(items), "roots": scanned,
                "retry_prohibited": True}

    if r.status_code >= 400:
        return {"ok": False, "error": "ingest_rejected", "status": r.status_code,
                "body": body, "scanned": len(items),
                "retry_prohibited": bool(body.get("retry_prohibited")) if isinstance(body, dict) else True}

    outcome = _classify_media_local_ingest_receipt(body, len(items))
    return {
        **outcome,
        "detected_drives": detected,
        "roots": scanned,
        "scanned": len(items),
        "results": body.get("results", []) if isinstance(body, dict) else [],
        "companion_version": COMPANION_VERSION,
    }




def cap_linkedin_content_migrate(ctx: ActionContext) -> dict:
    """Move content off a RETIRED LinkedIn alias profile onto the canonical one.

    Read-only on the source profile: harvests recent activity text + permalinks,
    then posts the manifest to the linkedin-content-migrate edge function which
    records the ledger row and enqueues the repost through the normal publish
    rail (identity guard still applies). Never posts directly from here.
    """
    if _harvest_linkedin_posts is None:
        return {"ok": False, "error": "multi_platform_publisher_missing"}
    p = ctx.payload or {}
    sources = p.get("source_handles")
    if isinstance(sources, str):
        sources = [sources]
    if not sources:
        one = p.get("source_handle")
        sources = [one] if one else []
    if not sources:
        return {"ok": False, "error": "source_handles_required"}
    limit = int(p.get("limit") or 25)
    max_repost = int(p.get("max_repost") or 10)
    auto_repost = bool(p.get("auto_repost", True))

    creds = load_credentials()
    if not creds:
        return {"ok": False, "error": "device_not_enrolled"}
    device_id, device_key = creds

    out = []
    for src in sources:
        harvest = _run_browser_publisher_isolated(
            _harvest_linkedin_posts,
            profile_slug=str(src),
            limit=limit,
        )
        entry = {
            "source_handle": src,
            "harvest_ok": bool(harvest.get("ok")),
            "harvest_error": harvest.get("error"),
            "items_found": len(harvest.get("items") or []),
            "screenshot_path": harvest.get("screenshot_path"),
            "notes": (harvest.get("notes") or [])[:10],
        }
        items = harvest.get("items") or []
        if harvest.get("ok") and items:
            try:
                r = requests.post(
                    f"{FUNCTIONS_BASE}/linkedin-content-migrate",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Content-Type": "application/json",
                        "x-device-id": device_id,
                        "x-device-key": device_key,
                    },
                    json={
                        "source_handle": src,
                        "items": items,
                        "auto_repost": auto_repost,
                        "max_repost": max_repost,
                    },
                    timeout=180,
                )
                body = r.json() if r.content else {}
                entry["ingest_status"] = r.status_code
                entry["queued"] = body.get("queued")
                entry["target_handle"] = body.get("target_handle")
                entry["ingest_error"] = body.get("error")
            except Exception as e:
                entry["ingest_error"] = f"ingest_post_failed:{e}"
        out.append(entry)

    return {
        "ok": any(e.get("harvest_ok") for e in out),
        "sources": out,
        "companion_version": COMPANION_VERSION,
    }


def _sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for a downloaded evidence artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _portal_source_filename(url: str, index: int) -> str:
    """Deterministic safe filename for a verified source URL."""
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name or f"official-source-{index}.html"
    return re.sub(r"[^A-Za-z0-9._\\-]", "_", name)[:180]


def cap_portal_traverse(ctx: ActionContext) -> dict:
    """Capture official sources, then walk a funder portal read-only.

    The broker may supply a source-locked work_plan. Every official source is
    downloaded through the existing allowlisted downloader before traversal,
    so Ground Zero returns durable artifacts instead of silently ignoring the
    evidence packet. Traversal itself remains structurally unable to submit.
    """
    run_id = str(ctx.payload.get("run_id", "") or "").strip()
    url = str(ctx.payload.get("portal_url", "") or "").strip()
    if not run_id or not url:
        return {"ok": False, "error": "run_id_and_portal_url_required"}

    work_plan = ctx.payload.get("work_plan") or {}
    if not isinstance(work_plan, dict):
        work_plan = {}
    official_sources = work_plan.get("official_sources") or []
    if not isinstance(official_sources, list):
        official_sources = []

    source_dir = DOWNLOAD_DIR / "grant-sources" / run_id
    source_downloads: list[dict] = []
    for index, source_url in enumerate(official_sources, start=1):
        if not isinstance(source_url, str) or not source_url.startswith("https://"):
            source_downloads.append({
                "url": str(source_url)[:300],
                "ok": False,
                "error": "invalid_official_source_url",
            })
            continue
        source_ctx = ActionContext(
            action_id=f"{ctx.action_id}-source-{index}",
            capability="download_url_to_folder",
            action_type="download_url_to_folder",
            payload={
                "url": source_url,
                "folder": str(source_dir),
                "filename": _portal_source_filename(source_url, index),
            },
        )
        outcome = cap_download_url_to_folder(source_ctx)
        if outcome.get("ok") is True and outcome.get("path"):
            try:
                artifact_path = Path(str(outcome["path"]))
                outcome["sha256"] = _sha256_file(artifact_path)
                outcome["downloaded_at"] = datetime.now(timezone.utc).isoformat()
            except Exception as exc:  # noqa: BLE001
                outcome["ok"] = False
                outcome["error"] = f"source_hash_failed:{str(exc)[:240]}"
        source_downloads.append({"url": source_url, **outcome})

    worker = Path(__file__).with_name("portal_traversal_worker.py")
    if not worker.exists():
        return {
            "ok": False,
            "error": "portal_traversal_worker_missing",
            "official_source_downloads": source_downloads,
        }
    try:
        proc = subprocess.run(
            [sys.executable, str(worker), "--run-id", run_id, "--url", url],
            capture_output=True, text=True, timeout=900,
        )
        return {
            "ok": proc.returncode == 0,
            "run_id": run_id,
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-2000:],
            "task_instructions_present": bool(ctx.payload.get("instructions")),
            "acceptance_tests": work_plan.get("acceptance_tests") or [],
            "expected_artifacts": work_plan.get("expected_artifacts") or [],
            "official_source_downloads": source_downloads,
            "official_sources_requested": len(official_sources),
            "official_sources_downloaded": sum(
                1 for item in source_downloads if item.get("ok") is True
            ),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "traversal_timeout",
            "run_id": run_id,
            "official_source_downloads": source_downloads,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc)[:400],
            "run_id": run_id,
            "official_source_downloads": source_downloads,
        }


CAPABILITY_HANDLERS: dict[str, Callable[[ActionContext], dict]] = {

    # Tier 1
    "capture_screenshot": cap_capture_screenshot,
    "read_file": cap_read_file,
    "write_file": cap_write_file,
    "launch_process": cap_launch_process,
    "elevate_powershell_script": cap_elevate_powershell_script,
    "run_check": cap_run_check,
    "run_local_script": cap_run_local_script,
    "platform_persistence_repair": cap_platform_persistence_repair,
    # Production repair requests use this equivalent capability name. Keep it
    # on the same allowlisted handler; no arbitrary command path is introduced.
    "desktop_commander_repair": cap_desktop_commander_repair,

    # Tier 2
    "open_url": cap_open_url,
    "connector_escort": cap_connector_escort,
    "portal_traverse_via_browser": cap_portal_traverse,
    "open_file": cap_open_file,
    "reveal_in_explorer": cap_reveal_in_explorer,
    "read_clipboard": cap_read_clipboard,
    "write_clipboard": cap_write_clipboard,
    # Tier 3 (desktop side)
    "append_to_file": cap_append_to_file,
    "download_url_to_folder": cap_download_url_to_folder,
    # Tier 3 — Meta Graph API publishing (creds loaded from local keyring)
    "meta_status": cap_meta_status,
    "meta_publish": cap_meta_publish,
    "meta_publish_photo": cap_meta_publish_photo,
    "meta_publish_video": cap_meta_publish_video,
    "meta_publish_reel": cap_meta_publish_reel,
    "meta_post_metrics": cap_meta_post_metrics,
    "meta_refresh_token": cap_meta_refresh_token,
    "meta_recent_log": cap_meta_recent_log,
    # Tier 3 — Meta Autopilot (auto-publish w/ guardrail holds + alerts)
    "meta_autopilot_publish": cap_meta_autopilot_publish,
    "meta_autopilot_holds": cap_meta_autopilot_holds,
    "meta_autopilot_alerts": cap_meta_autopilot_alerts,
    "meta_autopilot_history": cap_meta_autopilot_history,
    "meta_autopilot_release": cap_meta_autopilot_release,
    "meta_autopilot_classify": cap_meta_autopilot_classify,
    # Social account onboarding (Instagram, Threads, YouTube, LinkedIn, TikTok)
    "social_platform_status": cap_social_platform_status,
    "social_open_signup": cap_social_open_signup,
    "social_profile_draft": cap_social_profile_draft,
    "social_key_capture": cap_social_key_capture,
    "social_connection_test": cap_social_connection_test,
    "social_readiness_report": cap_social_readiness_report,
    # Page-level publishing destinations (Facebook Pages discovered under the
    # admin's personal profile; personal profile is auth-only and never posted from).
    "social_pages_discover": cap_social_pages_discover,
    "social_pages_test": cap_social_pages_test,
    # Meta Autofix (dry-run until META_AUTOPILOT_ENABLED=true)
    "browser_session": cap_browser_session,
    "browser_portal_login": cap_browser_portal_login,
    # Paperwork queue — autonomous non-signature form filling
    "form_autofill": cap_form_autofill,
    # Credit-independent Google Drive credential provisioning
    "google_credential_provision": cap_google_credential_provision,
    "invoke_edge_function": cap_invoke_edge_function,
    # Autonomous operational secret rotation (token never leaves Ground Zero)
    "secret_rotate": cap_secret_rotate,
    # Standing Integration & Credential Manager (onboard + maintain every tool)
    "integration_onboard": cap_integration_onboard,

    "meta_autofix_history": cap_meta_autofix_history,
    # Option 1 — browser-driven Page publishing via Jason's logged-in Chrome
    "browser_publish_facebook": cap_browser_publish_facebook,
    "browser_signin_facebook": cap_browser_signin_facebook,
    "browser_signin_instagram": cap_browser_signin_instagram,
    "browser_signin_linkedin": cap_browser_signin_linkedin,
    "browser_preflight_platform": cap_browser_preflight_platform,
    "rescue_windows": cap_rescue_windows,



    "browser_publish_facebook_reel": cap_browser_publish_facebook_reel,
    "browser_publish_instagram": cap_browser_publish_instagram,
    "browser_publish_instagram_reel": cap_browser_publish_instagram_reel,
    "browser_publish_linkedin": cap_browser_publish_linkedin,
    "recover_linkedin_permalink": cap_recover_linkedin_permalink,
    "linkedin_content_migrate": cap_linkedin_content_migrate,
    "browser_publish_youtube_short": cap_browser_publish_youtube_short,

    # Browser-driven Meta credential configurator (Graph Explorer → keyring)
    "meta_configure_via_browser": cap_meta_configure_via_browser,
    "meta_app_dashboard_configure": cap_meta_app_dashboard_configure,

    # Remote maintenance — download latest ZIP + re-exec (Ground Zero button)
    "self_update": cap_self_update,
    "rollback_last_update": cap_rollback_last_update,

    # Media engine — local FFmpeg playbook + derivative generation
    "ffmpeg_ensure": cap_ffmpeg_ensure,
    "ffmpeg_health": cap_ffmpeg_health,
    "ffmpeg_rollback": cap_ffmpeg_rollback,
    "media_generate_derivative": cap_media_generate_derivative,
    "media_make_reel": cap_media_make_reel,
    "media_local_inventory": cap_media_local_inventory,
    "media_local_ingest": cap_media_local_ingest,

    "restart_companion": cap_restart_companion,
    "browser_release_locks": cap_browser_release_locks,
    # Vendor credential vault (operational accounts — Home Depot Pro, suppliers, etc.)
    "vendor_login": cap_vendor_login,
    "email_fetch_verification_code": cap_email_fetch_verification_code,

    "vendor_signup": cap_vendor_signup,
    "vendor_action": cap_vendor_action,
}








# ---------------------------------------------------------------------------
# Action execution + result reporting
# ---------------------------------------------------------------------------

def report_result(device_id: str, device_key: str, action_id: str, result: dict) -> None:
    try:
        r = requests.post(
            COMPANION_URL,
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
                "X-Device-Id": device_id,
                "X-Device-Key": device_key,
            },
            json={"action": "action_result", "action_id": action_id, "result": result},
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code >= 400:
            log(f"  result POST -> HTTP {r.status_code} {r.text[:200]}")
    except Exception as e:
        log(f"  result POST failed: {e}")

def execute_action(device_id: str, device_key: str, action: dict) -> None:
    ctx = ActionContext(
        action_id=action["id"],
        capability=action.get("capability", ""),
        action_type=action.get("action_type", ""),
        payload=action.get("payload") or {},
        created_at=action.get("created_at"),
    )
    log(f"-> action {ctx.action_id} :: {ctx.capability} / {ctx.action_type}" +
        (f" created_at={ctx.created_at} boot_ts={BOOT_TS:.1f}" if ctx.action_type=="restart_companion" else ""))
    handler = CAPABILITY_HANDLERS.get(ctx.capability)
    if not handler:
        result = {"ok": False, "error": "unsupported_capability", "capability": ctx.capability}
    else:
        try:
            result = handler(ctx)
        except Exception as e:
            result = {"ok": False, "error": "handler_exception", "detail": str(e),
                      "trace": traceback.format_exc(limit=4)}
    log(f"   result: {json.dumps(result)[:300]}")
    report_result(device_id, device_key, ctx.action_id, result)

# ---------------------------------------------------------------------------
# Heartbeat loop
# ---------------------------------------------------------------------------

def _background_worker_report() -> dict:
    """Real process evidence for the always-on sibling workers.

    Advertising a capability is not proof of a running worker. Report both
    children started by this process and healthy workers reused from the durable
    registry so a companion restart never multiplies worker processes.
    """
    report: dict = {}
    for name, script_name, log_name, _loop in _BACKGROUND_WORKERS:
        entry: dict = {"script": script_name, "pid": None, "alive": False}
        proc = _BACKGROUND_WORKER_PROCS.get(name)
        if proc is not None:
            entry["pid"] = proc.pid
            entry["alive"] = proc.poll() is None
            entry["exit_code"] = proc.returncode
            entry["reused"] = False
        else:
            reused_pid = int(_BACKGROUND_WORKER_REUSED.get(name) or 0)
            if reused_pid:
                entry["pid"] = reused_pid
                entry["alive"] = _pid_alive(reused_pid)
                entry["reused"] = True
        try:
            log_path = Path(__file__).parent / log_name
            if log_path.exists():
                st = log_path.stat()
                entry["log"] = log_name
                entry["log_bytes"] = st.st_size
                entry["log_mtime"] = st.st_mtime
        except Exception:
            pass
        report[name] = entry
    return report


def _runtime_routing_and_build_evidence() -> dict:
    """Report Project K as live destination, without rewriting an old install.
    The legacy build URL remains in the local running_build.json audit record.
    """
    source = ""
    try:
        if RUNNING_BUILD_FILE.exists():
            raw = json.loads(RUNNING_BUILD_FILE.read_text(encoding="utf-8"))
            source = str(raw.get("build_ref") or "")
    except (OSError, ValueError, TypeError):
        source = ""
    is_legacy = "pefatniumnrxwbgnwvvh" in source
    return {
        "production_project_ref": SUPABASE_PROJECT_REF,
        "production_companion_url": COMPANION_URL,
        "companion_build_ref": source if source and not is_legacy else None,
        "installed_build_source_class": "historical_legacy_release" if is_legacy else ("recorded_current_release" if source else "source_unrecorded"),
        "historical_build_ref_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest() if is_legacy else None,
    }


def status_snapshot() -> dict:
    return {
        **_runtime_routing_and_build_evidence(),
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "python": sys.version.split()[0],
        "cwd": str(Path.cwd()),
        "ts": time.time(),
        "pid": os.getpid(),
        "instance_id": INSTANCE_ID,
        "boot_ts": BOOT_TS,
        "companion_version": COMPANION_VERSION,
        "keepalive_script_present": (_companion_script_dir() / "unk_keepalive.ps1").exists(),
        "background_workers": _background_worker_report(),
        "singleton_owner": _read_singleton_lock(),
        "capabilities": sorted(CAPABILITY_HANDLERS.keys()),
    }


def heartbeat(device_id: str, device_key: str) -> dict:
    r = requests.post(
        COMPANION_URL,
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
            "X-Device-Id": device_id,
            "X-Device-Key": device_key,
        },
        json={"action": "heartbeat", "status": status_snapshot()},
        timeout=HTTP_TIMEOUT,
    )
    if r.status_code == 401:
        fatal("Device unauthorized. Re-run with --enroll.")
    if r.status_code != 200:
        raise RuntimeError(f"heartbeat HTTP {r.status_code}: {r.text[:300]}")
    return r.json()

def _windows_prevent_sleep(enable: bool) -> None:
    """Keep Windows awake (screen + system) while the companion is running.
    ES_CONTINUOUS=0x80000000, ES_SYSTEM_REQUIRED=0x00000001, ES_AWAYMODE_REQUIRED=0x00000040.
    Passing ES_CONTINUOUS alone re-enables normal sleep. No-op on non-Windows."""
    if os.name != "nt":
        return
    try:
        import ctypes
        if enable:
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_AWAYMODE_REQUIRED = 0x00000040
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
            )
            log("sleep guard: Windows sleep + away-mode DISABLED while companion is running.")
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    except Exception as e:
        log(f"sleep guard: could not set execution state ({e})")


HEARTBEAT_SIDECAR = COMPANION_DIR / "heartbeat.json"
PENDING_UPDATE_TOKEN_FILE = COMPANION_DIR / "pending_update_token.json"


def _write_heartbeat_sidecar(extra: dict | None = None) -> None:
    """Atomic write of a small heartbeat sidecar file that the on-device
    unk_supervisor.py reads to decide health. No network required."""
    try:
        payload = {
            "at": time.time(),
            "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "companion_version": COMPANION_VERSION,
            "pid": os.getpid(),
            "instance_id": INSTANCE_ID,
            "boot_ts": BOOT_TS,
            "local_process_alive": True,
        }
        payload.update(_runtime_routing_and_build_evidence())
        if extra: payload.update(extra)
        # Windows readers (supervisor, antivirus, health collectors) can
        # briefly lock the destination. Use a unique temp file and bounded
        # retries so one transient sharing violation cannot erase the signal.
        tmp = HEARTBEAT_SIDECAR.with_name(
            f".{HEARTBEAT_SIDECAR.name}.{os.getpid()}.{time.time_ns()}.tmp"
        )
        try:
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            for attempt in range(5):
                try:
                    os.replace(tmp, HEARTBEAT_SIDECAR)
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
    except Exception as e:
        log(f"heartbeat sidecar write failed: {e}")


def _cloud_backoff_with_local_liveness(seconds: float, consecutive_errors: int) -> None:
    """Keep the native watchdog informed during a Project K/cloud outage.

    This is a LOCAL process heartbeat only, never a claim that remote Auth,
    the Data API, or a platform write worked. Bound each sleep to 20 seconds
    (well below the supervisor's 180-second stale threshold) while preserving
    the original total retry delay, single-instance owner and cloud failure.
    """
    remaining = max(0.0, float(seconds))
    while remaining > 0:
        interval = min(20.0, remaining)
        time.sleep(interval)
        remaining -= interval
        _write_heartbeat_sidecar({
            "cloud_ok": False,
            "cloud_state": "retry_wait",
            "consecutive_cloud_errors": consecutive_errors,
        })


def _ack_pending_update_token_if_any() -> bool:
    """If self_update+restart_companion left us a token, POST an ack to the
    platform's desktop-supervisor-report so the two-phase update verifier
    can move from 'staged' -> 'verifying'. Delete the token file after."""
    if not PENDING_UPDATE_TOKEN_FILE.exists():
        return True
    try:
        payload = json.loads(PENDING_UPDATE_TOKEN_FILE.read_text())
        token = payload.get("token")
        creds = load_credentials()
        if not token or not creds:
            return False
        did, dkey = creds
        r = requests.post(
            f"{FUNCTIONS_BASE}/desktop-supervisor-report",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Content-Type": "application/json",
                "X-Device-Id": did,
                "X-Device-Key": dkey,
            },
            json={"action": "ack_update_token", "token": token},
            timeout=HTTP_TIMEOUT,
        )
        log(f"post-update token ack -> HTTP {r.status_code} {r.text[:200]}")
        if r.status_code == 200:
            try:
                body = r.json()
            except Exception:
                body = {}
            if body.get("ok") is True or body.get("reason") == "token_not_active":
                try: PENDING_UPDATE_TOKEN_FILE.unlink()
                except Exception: pass
                return True
        return False
    except Exception as e:
        log(f"post-update token ack failed: {e}")
        return False


SINGLETON_LOCK_FILE = COMPANION_DIR / "companion.lock"
INSTANCE_REGISTRY_FILE = COMPANION_DIR / "companion_instances.json"


def _pid_alive(pid: int) -> bool:
    if not pid or pid == os.getpid():
        return pid == os.getpid()
    try:
        if sys.platform == "win32":
            r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, timeout=15)
            return str(pid) in (r.stdout or "")
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _terminate_pid(pid: int) -> bool:
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True, timeout=20)
        else:
            os.kill(pid, 9)
        return True
    except Exception:
        return False


def _read_singleton_lock() -> dict:
    try:
        return json.loads(SINGLETON_LOCK_FILE.read_text())
    except Exception:
        return {}


def _write_singleton_lock() -> None:
    try:
        SINGLETON_LOCK_FILE.write_text(json.dumps({
            "pid": os.getpid(),
            "instance_id": INSTANCE_ID,
            "companion_version": COMPANION_VERSION,
            "boot_ts": BOOT_TS,
        }))
    except Exception as e:
        log(f"singleton lock write failed: {e}")


def acquire_singleton() -> None:
    """Exactly one companion process may own this device.

    Duplicate companions (often stale builds left over from restarts) each
    claim device actions, so a job can be picked up by an OLD build that no
    longer supports the requested capability. Newest boot wins: this process
    terminates any older live holder, and refuses to start if a NEWER one is
    already running.
    """
    prior = _read_singleton_lock()
    pid = int(prior.get("pid") or 0)
    if pid and pid != os.getpid() and _pid_alive(pid):
        if float(prior.get("boot_ts") or 0) > BOOT_TS:
            log(f"Newer companion already running (pid={pid}, {prior.get('companion_version')}). Exiting.")
            raise SystemExit(0)
        log(f"Terminating stale companion pid={pid} version={prior.get('companion_version')}")
        _terminate_pid(pid)
        time.sleep(2)

    # Sweep every previously-seen companion PID. The lock only tracks the last
    # writer; older builds started before the lock existed are invisible to it
    # and would keep claiming device actions with outdated capabilities.
    try:
        seen = json.loads(INSTANCE_REGISTRY_FILE.read_text()) if INSTANCE_REGISTRY_FILE.exists() else []
    except Exception:
        seen = []
    for other in seen:
        try:
            opid = int(other)
        except Exception:
            continue
        if opid != os.getpid() and _pid_alive(opid):
            log(f"Terminating duplicate companion pid={opid}")
            _terminate_pid(opid)
    try:
        INSTANCE_REGISTRY_FILE.write_text(json.dumps([os.getpid()]))
    except Exception:
        pass

    _write_singleton_lock()



def _singleton_still_ours() -> bool:
    cur = _read_singleton_lock()
    if not cur:
        _write_singleton_lock()
        return True
    return str(cur.get("instance_id")) == INSTANCE_ID


def run_loop(device_id: str, device_key: str) -> None:
    _windows_prevent_sleep(True)
    log(f"Companion online. device_id={device_id} polling every {POLL_SECONDS}s.")
    log(f"Capabilities: {sorted(CAPABILITY_HANDLERS.keys())}")
    _ack_pending_update_token_if_any()
    _write_heartbeat_sidecar({"boot": True})
    consecutive_errors = 0
    last_cloud_ok = None
    while True:
        try:
            if not _singleton_still_ours():
                log("Another companion instance took ownership of this device. Exiting cleanly.")
                raise SystemExit(0)

            # Local liveness must not depend on the cloud heartbeat. During an
            # internet outage the process is still healthy, so write the
            # sidecar before the network call to stop supervisor restart loops.
            _write_heartbeat_sidecar({"cloud_ok": last_cloud_ok, "cloud_state": "checking",
                                      "consecutive_cloud_errors": consecutive_errors})
            _ack_pending_update_token_if_any()
            data = heartbeat(device_id, device_key)
            consecutive_errors = 0  # healthy tick
            last_cloud_ok = True
            _write_heartbeat_sidecar({"cloud_ok": True, "cloud_state": "connected",
                                      "consecutive_cloud_errors": 0})

            pending = data.get("pending_actions") or []
            if pending:
                log(f"heartbeat ok :: {len(pending)} pending action(s)")
                for action in pending:
                    # Browser publishing can legitimately run longer than the
                    # supervisor's stale-heartbeat threshold. Keep local
                    # liveness current while an action is executing so the
                    # supervisor never kills and replays the same browser job.
                    action_done = threading.Event()
                    action_id = str(action.get("id") or "unknown")

                    def _action_liveness_tick() -> None:
                        while not action_done.wait(20):
                            _write_heartbeat_sidecar({
                                "cloud_ok": True,
                                "action_in_progress": action_id,
                                "consecutive_cloud_errors": 0,
                            })

                    liveness_thread = threading.Thread(
                        target=_action_liveness_tick,
                        name=f"unk-action-liveness-{action_id[:8]}",
                        daemon=True,
                    )
                    liveness_thread.start()
                    try:
                        execute_action(device_id, device_key, action)
                    except Exception as ae:
                        log(f"action execution error (continuing): {ae}")
                    finally:
                        action_done.set()
                        liveness_thread.join(timeout=1)
                        _write_heartbeat_sidecar({
                            "cloud_ok": True,
                            "action_in_progress": None,
                            "consecutive_cloud_errors": 0,
                        })
            # Honor a restart_companion request AFTER results are posted.
            if _RESTART_REQUESTED.get("pending"):
                log(f"Restart requested ({_RESTART_REQUESTED.get('reason')}, strategy={_RESTART_REQUESTED.get('strategy')}).")
                if _RESTART_REQUESTED.get("strategy") == "supervisor_exit":
                    log("Exiting intentionally so UnkSupervisor proves relaunch.")
                    raise SystemExit(0)
                log("Re-executing current Python process…")
                try:
                    time.sleep(1)
                    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), *[a for a in sys.argv[1:] if a not in ("--enroll",)]])
                except Exception as re_exc:
                    log(f"os.execv failed ({re_exc}); exiting so supervisor can relaunch.")
                    raise SystemExit(0)

        except KeyboardInterrupt:
            log("Stopped by user.")
            return
        except SystemExit:
            # heartbeat() calls fatal() on 401 -> SystemExit. Let the supervisor
            # restart us; do NOT die silently.
            log("Fatal auth/system exit — asking supervisor for a fresh process.")
            raise
        except Exception as e:
            consecutive_errors += 1
            last_cloud_ok = False
            _write_heartbeat_sidecar({"cloud_ok": False, "cloud_state": "error",
                "consecutive_cloud_errors": consecutive_errors, "last_cloud_error": str(e)[:300]})
            backoff = min(POLL_SECONDS * (2 ** min(consecutive_errors, 4)), 300)
            log(f"heartbeat error #{consecutive_errors} ({e}); sleeping {backoff}s before retry")
            _cloud_backoff_with_local_liveness(backoff, consecutive_errors)
            continue
        time.sleep(POLL_SECONDS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_BACKGROUND_WORKER_PROCS: dict = {}
_BACKGROUND_WORKER_REUSED: dict[str, int] = {}

# Background workers that must always be alive alongside the companion.
# Doctrine: no operator ever launches these by hand. If a worker is missing,
# the corresponding rail silently stops.
_BACKGROUND_WORKERS = (
    ("audio-worker", "media_audio_worker.py", "unk_audio_worker.log", "300"),
    ("mirror-worker", "media_mirror_worker.py", "unk_mirror_worker.log", "300"),
)


def _registered_background_worker_pids() -> dict[str, int]:
    try:
        raw = json.loads(BACKGROUND_WORKER_REGISTRY_FILE.read_text())
        if not isinstance(raw, dict):
            return {}
        return {
            str(name): int(pid)
            for name, pid in raw.items()
            if str(pid).isdigit() and int(pid) > 0
        }
    except Exception:
        return {}


def _discover_background_worker_pids(script_name: str) -> list[int]:
    """Find existing Windows workers by exact script basename.

    The registry is the fast path. CIM discovery repairs old installations that
    predate the registry and lets startup collapse historical duplicates.
    """
    found: list[int] = []
    for name, pid in _registered_background_worker_pids().items():
        if name.endswith(script_name) and _pid_alive(pid):
            found.append(pid)
    if sys.platform != "win32":
        return sorted(set(found))
    safe = script_name.replace("'", "''")
    command = (
        "Get-CimInstance Win32_Process -Filter \"Name LIKE 'python%'\" | "
        f"Where-Object {{ $_.CommandLine -like '*{safe}*' }} | "
        "Select-Object -ExpandProperty ProcessId"
    )
    try:
        run = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for line in (run.stdout or "").splitlines():
            value = line.strip()
            if value.isdigit() and int(value) != os.getpid():
                found.append(int(value))
    except Exception:
        pass
    return sorted(set(pid for pid in found if _pid_alive(pid)))


def _write_background_worker_registry() -> None:
    """Atomically update OUR media workers without erasing other owners' PIDs.

    The registry is a name->PID mapping, not an array. Another supervisor may
    register its own workers (for example ai-worker). Never normalize the
    registry on module import or silently discard unknown worker owners.
    """
    managed = {f"{name}:{script}" for name, script, _log, _loop in _BACKGROUND_WORKERS}
    payload: dict[str, int] = {}
    try:
        if BACKGROUND_WORKER_REGISTRY_FILE.exists():
            existing = json.loads(BACKGROUND_WORKER_REGISTRY_FILE.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                raise ValueError("background_worker_registry_not_mapping")
            for key, pid in existing.items():
                if (isinstance(key, str) and key not in managed
                        and not isinstance(pid, bool) and str(pid).isdigit()
                        and int(pid) > 0):
                    payload[key] = int(pid)
    except (OSError, ValueError, TypeError) as exc:
        # A malformed/unreadable registry must remain intact for repair;
        # overwriting it would erase other workers' recovery evidence.
        print(f"[background-workers] registry read failed: {type(exc).__name__}")
        return
    for name, script_name, _log_name, _loop in _BACKGROUND_WORKERS:
        proc = _BACKGROUND_WORKER_PROCS.get(name)
        if proc is not None and proc.poll() is None:
            payload[f"{name}:{script_name}"] = proc.pid
            continue
        reused = int(_BACKGROUND_WORKER_REUSED.get(name) or 0)
        if reused and _pid_alive(reused):
            payload[f"{name}:{script_name}"] = reused
    try:
        tmp = BACKGROUND_WORKER_REGISTRY_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload))
        os.replace(tmp, BACKGROUND_WORKER_REGISTRY_FILE)
    except Exception as exc:
        print(f"[background-workers] registry write failed: {exc}")

def _spawn_background_worker(name: str, script_name: str, log_name: str, loop_seconds: str) -> None:
    """Reuse one healthy worker and terminate historical duplicates before spawn."""
    try:
        existing = _discover_background_worker_pids(script_name)
        if existing:
            keep = existing[-1]
            for duplicate in existing[:-1]:
                _terminate_pid(duplicate)
            _BACKGROUND_WORKER_REUSED[name] = keep
            _write_background_worker_registry()
            print(
                f"[{name}] reused pid={keep}; "
                f"removed_duplicates={max(0, len(existing) - 1)}"
            )
            return

        worker = Path(__file__).parent / script_name
        if not worker.exists():
            print(f"[{name}] script not found at {worker}, skipping")
            return
        log_path = Path(__file__).parent / log_name
        log_fh = open(log_path, "ab")
        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.Popen(
            [sys.executable, str(worker), "--loop", loop_seconds],
            stdout=log_fh, stderr=log_fh,
            cwd=str(worker.parent),
            creationflags=creationflags,
        )
        _BACKGROUND_WORKER_PROCS[name] = proc
        _write_background_worker_registry()
        print(f"[{name}] spawned pid={proc.pid} log={log_path}")
    except Exception as exc:
        print(f"[{name}] failed to spawn: {exc}")


def _spawn_background_workers() -> None:
    for name, script_name, log_name, loop_seconds in _BACKGROUND_WORKERS:
        _spawn_background_worker(name, script_name, log_name, loop_seconds)


def main() -> None:

    ap = argparse.ArgumentParser(description="Unk Desktop Companion")
    ap.add_argument("--enroll", action="store_true", help="Force re-enrollment")
    ap.add_argument("--status", action="store_true", help="One-shot heartbeat then exit")
    args = ap.parse_args()

    creds = None if args.enroll else load_credentials()
    if creds is None:
        creds = enroll_interactive()
    device_id, device_key = creds

    if args.status:
        data = heartbeat(device_id, device_key)
        print(json.dumps(data, indent=2))
        return

    acquire_singleton()
    _spawn_background_workers()
    run_loop(device_id, device_key)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Stopped by user.")
    except SystemExit:
        raise
    except Exception as exc:
        log(f"FATAL: {exc}")
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(traceback.format_exc() + "\n")
        except Exception:
            pass
        pause_before_exit()
        raise SystemExit(1)
