"""FFmpeg dependency playbook for Ground Zero — no winget, no Lovable at runtime.

Doctrine (local-first): the media engine must be able to produce platform-ready
derivatives on Jason's machine without a package manager, without admin rights,
and without an operating turn in Lovable.

What this does
--------------
1. Discovery  — find an existing usable ffmpeg/ffprobe (PATH, prior install,
   common install roots). If found and healthy, do nothing.
2. Download   — pull a verified official-linked Windows build. Primary source is
   gyan.dev, the Windows build listed on https://ffmpeg.org/download.html.
3. Verify     — SHA-256 the archive. Pinned digest first; if the pinned release
   has rolled forward, fall back to the publisher's own `.sha256` sidecar
   fetched over HTTPS. NEVER install an unverified archive.
4. Install    — extract under the Unk runtime dir (%LOCALAPPDATA%\\UnkCompanion\\
   ffmpeg\\<version>) so no elevation is needed. Atomic: extract to a temp dir,
   then flip a `current` pointer.
5. Configure  — write ffmpeg_path.json that every worker reads; also prepend to
   this process's PATH.
6. Health     — run `ffmpeg -version` + `ffprobe -version` and encode a 1-second
   synthetic clip end-to-end to prove libx264/aac actually work.
7. Rollback   — the previous `current` target is kept; `rollback()` flips back.

Every step returns structured evidence so the platform can record it in
`ground_zero_dependencies` without anyone reading a log by hand.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Optional
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


PLAYBOOK_VERSION = "ffmpeg-playbook-v1"

# ---------------------------------------------------------------------------
# Where things live
# ---------------------------------------------------------------------------
def runtime_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME") or str(Path.home())
    return Path(base) / "UnkCompanion"


FFMPEG_ROOT = runtime_root() / "ffmpeg"
CURRENT_LINK = FFMPEG_ROOT / "current"
PREVIOUS_LINK = FFMPEG_ROOT / "previous"
CONFIG_FILE = runtime_root() / "ffmpeg_path.json"

# ---------------------------------------------------------------------------
# Verified sources. Ranked. Each entry MUST provide a way to authenticate bytes.
# ---------------------------------------------------------------------------
SOURCES: list[dict] = [
    {
        "id": "gyan_release_essentials_8_1_2",
        "note": "gyan.dev — the Windows build linked from ffmpeg.org/download.html",
        "url": "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-8.1.2-essentials_build.zip",
        # Pinned digest captured from the publisher's own sidecar.
        "sha256": "db580001caa24ac104c8cb856cd113a87b0a443f7bdf47d8c12b1d740584a2ec",
        "sha256_url": "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-8.1.2-essentials_build.zip.sha256",
        "version": "8.1.2",
    },
    {
        "id": "gyan_release_essentials_rolling",
        "note": "gyan.dev rolling release; digest read from the publisher sidecar",
        "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        "sha256": None,
        "sha256_url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256",
        "version": "release",
    },
]

HEALTH_TIMEOUT = 120


def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "not_found"
    except Exception as exc:  # timeout etc.
        return 1, "", str(exc)


def _exe(name: str) -> str:
    return f"{name}.exe" if platform.system() == "Windows" else name


# ---------------------------------------------------------------------------
# 1. Discovery
# ---------------------------------------------------------------------------
def _candidate_bin_dirs() -> list[Path]:
    dirs: list[Path] = []
    if CURRENT_LINK.exists():
        dirs.append(CURRENT_LINK / "bin")
    cfg = read_config()
    if cfg.get("bin_dir"):
        dirs.append(Path(cfg["bin_dir"]))
    for extra in (
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        str(Path.home() / "ffmpeg" / "bin"),
    ):
        dirs.append(Path(extra))
    return dirs


def discover() -> dict:
    """Locate a usable ffmpeg+ffprobe pair. Returns evidence, never raises."""
    tried: list[dict] = []

    def _probe(ffmpeg: str, ffprobe: str, origin: str) -> Optional[dict]:
        rc, out, err = _run([ffmpeg, "-version"], timeout=30)
        if rc != 0:
            tried.append({"origin": origin, "path": ffmpeg, "rc": rc, "err": (err or out)[:200]})
            return None
        rc2, _, err2 = _run([ffprobe, "-version"], timeout=30)
        if rc2 != 0:
            tried.append({"origin": origin, "path": ffprobe, "rc": rc2, "err": err2[:200]})
            return None
        version = out.splitlines()[0] if out else "unknown"
        return {"ffmpeg": ffmpeg, "ffprobe": ffprobe, "version": version, "origin": origin}

    # PATH first
    which_ffmpeg = shutil.which("ffmpeg")
    which_ffprobe = shutil.which("ffprobe")
    if which_ffmpeg and which_ffprobe:
        found = _probe(which_ffmpeg, which_ffprobe, "PATH")
        if found:
            return {"found": True, **found, "tried": tried}

    for d in _candidate_bin_dirs():
        f1, f2 = d / _exe("ffmpeg"), d / _exe("ffprobe")
        if f1.exists() and f2.exists():
            found = _probe(str(f1), str(f2), str(d))
            if found:
                return {"found": True, **found, "tried": tried}

    return {"found": False, "tried": tried}


# ---------------------------------------------------------------------------
# 2/3. Download + checksum verification
# ---------------------------------------------------------------------------
def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_expected_digest(source: dict) -> tuple[Optional[str], str]:
    """Pinned digest wins. Otherwise read the publisher's sidecar over HTTPS."""
    if source.get("sha256"):
        return source["sha256"].lower(), "pinned"
    url = source.get("sha256_url")
    if not url:
        return None, "none"
    try:
        import requests  # type: ignore
        r = requests.get(url, timeout=60, allow_redirects=True)
        r.raise_for_status()
        token = (r.text or "").strip().split()[0].lower()
        if len(token) == 64 and all(c in "0123456789abcdef" for c in token):
            return token, "sidecar"
    except Exception:
        pass
    return None, "unavailable"


def _download(url: str, dest: Path, log=print) -> int:
    import requests  # type: ignore
    total = 0
    with requests.get(url, stream=True, timeout=(30, 900), allow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
    log(f"[ffmpeg] downloaded {total} bytes from {url}")
    return total


# ---------------------------------------------------------------------------
# 4/5. Install + configure
# ---------------------------------------------------------------------------
def _extract_and_place(archive: Path, version: str, log=print) -> Path:
    """Extract to a versioned dir and return its root (the dir containing bin/)."""
    staging = Path(tempfile.mkdtemp(prefix="ffmpeg_stage_"))
    with zipfile.ZipFile(archive) as z:
        z.extractall(staging)
    # Archives contain a single top-level folder like ffmpeg-8.1.2-essentials_build/
    roots = [p for p in staging.iterdir() if p.is_dir()]
    src_root = roots[0] if len(roots) == 1 else staging
    if not (src_root / "bin" / _exe("ffmpeg")).exists():
        # Some layouts nest one level deeper.
        for cand in src_root.rglob("bin"):
            if (cand / _exe("ffmpeg")).exists():
                src_root = cand.parent
                break
    if not (src_root / "bin" / _exe("ffmpeg")).exists():
        shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError("archive_did_not_contain_bin_ffmpeg")

    FFMPEG_ROOT.mkdir(parents=True, exist_ok=True)
    target = FFMPEG_ROOT / f"v{version}-{int(time.time())}"
    shutil.move(str(src_root), str(target))
    shutil.rmtree(staging, ignore_errors=True)
    log(f"[ffmpeg] installed to {target}")
    return target


def _point_current_at(target: Path) -> None:
    """Rollback-safe pointer flip. Uses a JSON pointer file (no symlink rights needed)."""
    FFMPEG_ROOT.mkdir(parents=True, exist_ok=True)
    prev = None
    if CURRENT_LINK.exists():
        try:
            prev = json.loads(CURRENT_LINK.read_text()).get("target")
        except Exception:
            prev = None
    if prev:
        PREVIOUS_LINK.write_text(json.dumps({"target": prev}))
    CURRENT_LINK.write_text(json.dumps({"target": str(target)}))


def _current_target() -> Optional[Path]:
    try:
        if CURRENT_LINK.is_file():
            t = json.loads(CURRENT_LINK.read_text()).get("target")
            return Path(t) if t else None
    except Exception:
        pass
    return None


def read_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def write_config(ffmpeg: str, ffprobe: str, version: str, origin: str) -> dict:
    cfg = {
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "bin_dir": str(Path(ffmpeg).parent),
        "version": version,
        "origin": origin,
        "playbook_version": PLAYBOOK_VERSION,
        "configured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    _prepend_path(cfg["bin_dir"])
    return cfg


def _prepend_path(bin_dir: str) -> None:
    cur = os.environ.get("PATH", "")
    if bin_dir not in cur.split(os.pathsep):
        os.environ["PATH"] = bin_dir + os.pathsep + cur


def binaries() -> tuple[Optional[str], Optional[str]]:
    """Public accessor every worker should use instead of bare 'ffmpeg'."""
    cfg = read_config()
    f1, f2 = cfg.get("ffmpeg"), cfg.get("ffprobe")
    if f1 and f2 and Path(f1).exists() and Path(f2).exists():
        _prepend_path(str(Path(f1).parent))
        return f1, f2
    d = discover()
    if d.get("found"):
        write_config(d["ffmpeg"], d["ffprobe"], d.get("version", "unknown"), d.get("origin", "discovered"))
        return d["ffmpeg"], d["ffprobe"]
    return None, None


# ---------------------------------------------------------------------------
# 6. Health check — prove the codecs actually work, not just that a file exists
# ---------------------------------------------------------------------------
def health_check(ffmpeg: Optional[str] = None, ffprobe: Optional[str] = None) -> dict:
    if not ffmpeg or not ffprobe:
        ffmpeg, ffprobe = binaries()
    if not ffmpeg or not ffprobe:
        return {"ok": False, "error": "ffmpeg_not_installed", "playbook_version": PLAYBOOK_VERSION}

    rc, out, err = _run([ffmpeg, "-version"], timeout=30)
    if rc != 0:
        return {"ok": False, "error": "ffmpeg_version_failed", "detail": (err or out)[:300]}
    version_line = out.splitlines()[0] if out else "unknown"

    rc, pout, perr = _run([ffprobe, "-version"], timeout=30)
    if rc != 0:
        return {"ok": False, "error": "ffprobe_version_failed", "detail": (perr or pout)[:300]}

    # End-to-end encode proof: 1s synthetic clip through libx264 + aac.
    with tempfile.TemporaryDirectory(prefix="ffmpeg_health_") as td:
        sample = str(Path(td) / "health.mp4")
        rc, _, eerr = _run([
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=size=320x240:rate=15:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", "-movflags", "+faststart", sample,
        ], timeout=HEALTH_TIMEOUT)
        if rc != 0 or not Path(sample).exists():
            return {"ok": False, "error": "encode_proof_failed", "detail": eerr[:400],
                    "ffmpeg_version": version_line}
        probed = probe(sample, ffprobe=ffprobe)
        if not probed.get("ok"):
            return {"ok": False, "error": "probe_proof_failed", "detail": probed.get("error"),
                    "ffmpeg_version": version_line}

    return {
        "ok": True,
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "ffmpeg_version": version_line,
        "encode_proof": "libx264+aac ok",
        "playbook_version": PLAYBOOK_VERSION,
    }


def probe(path: str, ffprobe: Optional[str] = None) -> dict:
    if not ffprobe:
        _, ffprobe = binaries()
    if not ffprobe:
        return {"ok": False, "error": "ffprobe_not_installed"}
    rc, out, err = _run([
        ffprobe, "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", path,
    ], timeout=180)
    if rc != 0:
        return {"ok": False, "error": (err or out)[:400]}
    try:
        data = json.loads(out)
    except Exception as exc:
        return {"ok": False, "error": f"probe_parse_failed:{exc}"}
    fmt = data.get("format") or {}
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    return {
        "ok": True,
        "duration_seconds": float(fmt.get("duration") or 0) or None,
        "size_bytes": int(fmt.get("size") or 0) or None,
        "container": fmt.get("format_name"),
        "width": v.get("width"),
        "height": v.get("height"),
        "video_codec": v.get("codec_name"),
        "audio_codec": a.get("codec_name"),
        "bit_rate": int(fmt.get("bit_rate") or 0) or None,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def ensure(force: bool = False, log=print) -> dict:
    """Idempotent: make ffmpeg+ffprobe available and healthy. Returns evidence."""
    evidence: dict = {"playbook_version": PLAYBOOK_VERSION, "steps": [], "forced": force}

    if not force:
        found = discover()
        evidence["steps"].append({"step": "discover", **found})
        if found.get("found"):
            cfg = write_config(found["ffmpeg"], found["ffprobe"], found.get("version", "unknown"), found.get("origin", "discovered"))
            hc = health_check(found["ffmpeg"], found["ffprobe"])
            evidence["steps"].append({"step": "health", **hc})
            if hc.get("ok"):
                return {"ok": True, "action": "already_installed", "config": cfg,
                        "health": hc, "evidence": evidence}
            evidence["steps"].append({"step": "existing_unhealthy_reinstalling"})

    if platform.system() != "Windows":
        # Non-Windows Ground Zero variants get a clear, non-guessing answer.
        return {"ok": False, "error": "auto_install_supported_on_windows_only",
                "detail": f"platform={platform.system()}; install ffmpeg via the OS package manager",
                "evidence": evidence}

    last_error = None
    for source in SOURCES:
        step: dict = {"step": "install", "source": source["id"], "url": source["url"]}
        try:
            expected, digest_origin = _fetch_expected_digest(source)
            step["digest_origin"] = digest_origin
            if not expected:
                step["error"] = "no_verifiable_checksum_refusing_install"
                evidence["steps"].append(step)
                last_error = step["error"]
                continue
            with tempfile.TemporaryDirectory(prefix="ffmpeg_dl_") as td:
                archive = Path(td) / "ffmpeg.zip"
                step["bytes"] = _download(source["url"], archive, log=log)
                actual = _sha256_file(archive)
                step["checksum_expected"] = expected
                step["checksum_actual"] = actual
                if actual != expected:
                    step["error"] = "checksum_mismatch_install_aborted"
                    evidence["steps"].append(step)
                    last_error = step["error"]
                    continue
                step["checksum_verified"] = True
                target = _extract_and_place(archive, source.get("version", "unknown"), log=log)
            ffmpeg = str(target / "bin" / _exe("ffmpeg"))
            ffprobe = str(target / "bin" / _exe("ffprobe"))
            hc = health_check(ffmpeg, ffprobe)
            step["health"] = hc
            if not hc.get("ok"):
                step["error"] = "installed_but_unhealthy"
                evidence["steps"].append(step)
                last_error = step["error"]
                continue
            _point_current_at(target)
            cfg = write_config(ffmpeg, ffprobe, source.get("version", "unknown"), source["id"])
            step["installed_to"] = str(target)
            evidence["steps"].append(step)
            return {
                "ok": True,
                "action": "installed",
                "config": cfg,
                "health": hc,
                "checksum_expected": expected,
                "checksum_actual": actual,
                "checksum_verified": True,
                "install_source": source["id"],
                "install_path": str(target),
                "evidence": evidence,
            }
        except Exception as exc:
            step["error"] = f"{type(exc).__name__}:{exc}"
            evidence["steps"].append(step)
            last_error = step["error"]
            continue

    return {"ok": False, "error": last_error or "all_sources_failed", "evidence": evidence}


def rollback(log=print) -> dict:
    """Flip back to the previous verified install."""
    try:
        if not PREVIOUS_LINK.is_file():
            return {"ok": False, "error": "no_previous_install"}
        prev = json.loads(PREVIOUS_LINK.read_text()).get("target")
        if not prev or not Path(prev).exists():
            return {"ok": False, "error": "previous_install_missing_on_disk", "target": prev}
        target = Path(prev)
        ffmpeg = str(target / "bin" / _exe("ffmpeg"))
        ffprobe = str(target / "bin" / _exe("ffprobe"))
        hc = health_check(ffmpeg, ffprobe)
        if not hc.get("ok"):
            return {"ok": False, "error": "previous_install_unhealthy", "health": hc}
        CURRENT_LINK.write_text(json.dumps({"target": str(target)}))
        cfg = write_config(ffmpeg, ffprobe, "rolled_back", "rollback")
        log(f"[ffmpeg] rolled back to {target}")
        return {"ok": True, "config": cfg, "health": hc}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}"}


def status() -> dict:
    cfg = read_config()
    cur = _current_target()
    hc = health_check()
    return {
        "playbook_version": PLAYBOOK_VERSION,
        "config": cfg,
        "current_install": str(cur) if cur else None,
        "has_previous": PREVIOUS_LINK.is_file(),
        "health": hc,
        "healthy": bool(hc.get("ok")),
    }


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ensure"
    if cmd == "status":
        print(json.dumps(status(), indent=2, default=str))
    elif cmd == "rollback":
        print(json.dumps(rollback(), indent=2, default=str))
    elif cmd == "health":
        print(json.dumps(health_check(), indent=2, default=str))
    else:
        print(json.dumps(ensure(force="--force" in sys.argv), indent=2, default=str))
