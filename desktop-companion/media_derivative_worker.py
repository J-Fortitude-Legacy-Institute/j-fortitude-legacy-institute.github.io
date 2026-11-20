"""Derivative generation for oversized masters — local-first, original-preserving.

Rules baked in (these are policy, not suggestions):

* The master is NEVER modified, moved, or deleted. Derivatives are new files.
* Deterministic naming: <asset_id>__<profile>__<masterchecksum12>.mp4
  Same master + same profile => same name => reuse instead of re-encode.
* Idempotency: if a derivative row already exists for (asset, profile) and the
  file is still on disk with a matching checksum, we return it untouched.
* Full interviews are never silently called Shorts/Reels. A derivative keeps
  `is_full_length=true` unless the profile explicitly trims, and platform
  targets are filtered by each adapter's duration policy from
  `media_platform_adapters.policy`.
* Every derivative carries size, duration, resolution, codecs, and a sha256.

Profiles
--------
platform_ready_1080p : H.264 high / AAC, <=1080p long edge, faststart,
                       bitrate budgeted to fit the tightest enabled platform cap.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import ffmpeg_bootstrap  # local playbook
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


WORKER_VERSION = "derivative-worker-v1"
DEFAULT_PROFILE = "platform_ready_1080p"

# Absolute ceiling for a "platform ready" derivative. Instagram is the tightest
# real constraint among our enabled destinations.
DEFAULT_MAX_BYTES = 950 * 1024 * 1024


def _work_dir() -> Path:
    d = ffmpeg_bootstrap.runtime_root() / "derivatives"
    d.mkdir(parents=True, exist_ok=True)
    return d


def sha256_file(path: str, limit_bytes: Optional[int] = None) -> str:
    h = hashlib.sha256()
    read = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            read += len(chunk)
            if limit_bytes and read >= limit_bytes:
                break
    return h.hexdigest()


def quick_fingerprint(path: str) -> str:
    """Cheap, stable identity for multi-GB masters: size + head/tail digest.

    Full sha256 of a 4 GB master costs minutes of disk IO on every retry. The
    head+tail+size fingerprint is deterministic, collision-safe enough for
    naming, and lets retries reuse derivatives without rereading the master.
    """
    st = os.stat(path)
    h = hashlib.sha256()
    h.update(str(st.st_size).encode())
    with open(path, "rb") as f:
        h.update(f.read(4 * 1024 * 1024))
        if st.st_size > 8 * 1024 * 1024:
            f.seek(-4 * 1024 * 1024, os.SEEK_END)
            h.update(f.read(4 * 1024 * 1024))
    return h.hexdigest()


def deterministic_name(asset_id: str, profile: str, master_fp: str) -> str:
    return f"{asset_id}__{profile}__{master_fp[:12]}.mp4"


def eligible_platforms(duration_s: float, size_bytes: int, policies: dict) -> dict:
    """Return {platform: {'eligible': bool, 'reason': str}} from adapter policy.

    This is what stops a 55-minute interview from being posted as a Reel.
    """
    out: dict = {}
    for platform, policy in (policies or {}).items():
        max_b = policy.get("max_bytes")
        max_d = policy.get("max_duration_s")
        shorts_max = policy.get("shorts_max_duration_s")
        reasons = []
        if max_b and size_bytes > max_b:
            reasons.append(f"size {size_bytes} > cap {max_b}")
        if max_d and duration_s > max_d:
            reasons.append(f"duration {duration_s:.0f}s > cap {max_d}s")
        if shorts_max and duration_s > shorts_max and platform in ("instagram_reel", "youtube_short"):
            reasons.append(f"full_length_{duration_s:.0f}s_not_a_short")
        out[platform] = {"eligible": not reasons, "reason": "; ".join(reasons) or "within policy"}
    return out


def build_derivative(
    *,
    asset_id: str,
    master_path: str,
    profile: str = DEFAULT_PROFILE,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_height: int = 1080,
    platform_policies: Optional[dict] = None,
    reuse: bool = True,
    log=print,
) -> dict:
    """Produce (or reuse) a platform-ready H.264/AAC MP4 next to the master.

    Never touches the master. Returns a full metadata envelope suitable for a
    `media_derivatives` upsert.
    """
    t0 = time.time()
    if not master_path or not Path(master_path).exists():
        return {"ok": False, "error": "master_not_found", "master_path": master_path}

    ffmpeg, ffprobe = ffmpeg_bootstrap.binaries()
    if not ffmpeg or not ffprobe:
        return {"ok": False, "error": "ffmpeg_unavailable",
                "detail": "run the ffmpeg_ensure capability on this device first"}

    master_fp = quick_fingerprint(master_path)
    name = deterministic_name(asset_id, profile, master_fp)
    out_path = _work_dir() / name

    if reuse and out_path.exists() and out_path.stat().st_size > 0:
        probed = ffmpeg_bootstrap.probe(str(out_path), ffprobe=ffprobe)
        if probed.get("ok"):
            log(f"[derivative] reuse {name}")
            return _envelope(asset_id, profile, out_path, master_path, master_fp,
                             probed, platform_policies, reused=True, seconds=0.0)

    master_probe = ffmpeg_bootstrap.probe(master_path, ffprobe=ffprobe)
    if not master_probe.get("ok"):
        return {"ok": False, "error": "master_probe_failed", "detail": master_probe.get("error")}
    duration = float(master_probe.get("duration_seconds") or 0)
    if duration <= 0:
        return {"ok": False, "error": "master_duration_unknown_refusing_blind_transcode"}

    audio_bps = 128_000
    target_total_bps = int((max_bytes * 8 * 0.92) / duration)
    video_bps = max(400_000, min(6_000_000, target_total_bps - audio_bps))

    tmp_out = out_path.with_suffix(".partial.mp4")
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", master_path,
        "-vf", f"scale=-2:'min({max_height},ih)'",
        "-c:v", "libx264", "-preset", "medium", "-profile:v", "high",
        "-b:v", str(video_bps), "-maxrate", str(int(video_bps * 1.25)),
        "-bufsize", str(video_bps * 2), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", str(audio_bps), "-ac", "2",
        "-movflags", "+faststart",
        str(tmp_out),
    ]
    log(f"[derivative] encoding {asset_id} -> {name} (video_bps={video_bps})")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60 * 60 * 6)
    except Exception as exc:
        tmp_out.unlink(missing_ok=True)
        return {"ok": False, "error": f"transcode_exception:{type(exc).__name__}", "detail": str(exc)[:400]}
    if p.returncode != 0 or not tmp_out.exists():
        detail = (p.stderr or p.stdout or "")[-1200:]
        tmp_out.unlink(missing_ok=True)
        return {"ok": False, "error": "transcode_failed", "detail": detail}

    if tmp_out.stat().st_size > max_bytes:
        size = tmp_out.stat().st_size
        tmp_out.unlink(missing_ok=True)
        return {"ok": False, "error": "derivative_exceeds_cap", "size_bytes": size, "cap": max_bytes}

    tmp_out.replace(out_path)
    probed = ffmpeg_bootstrap.probe(str(out_path), ffprobe=ffprobe)
    if not probed.get("ok"):
        return {"ok": False, "error": "derivative_probe_failed", "detail": probed.get("error")}

    return _envelope(asset_id, profile, out_path, master_path, master_fp,
                     probed, platform_policies, reused=False, seconds=round(time.time() - t0, 1))


def _envelope(asset_id, profile, out_path: Path, master_path, master_fp,
              probed: dict, platform_policies, *, reused: bool, seconds: float) -> dict:
    size_bytes = out_path.stat().st_size
    duration = float(probed.get("duration_seconds") or 0)
    return {
        "ok": True,
        "reused": reused,
        "asset_id": asset_id,
        "profile": profile,
        "deterministic_name": out_path.name,
        "local_path": str(out_path),
        "storage_key": f"derivatives/{out_path.name}",
        "sha256": sha256_file(str(out_path)),
        "size_bytes": size_bytes,
        "duration_seconds": duration,
        "width": probed.get("width"),
        "height": probed.get("height"),
        "container": probed.get("container"),
        "video_codec": probed.get("video_codec"),
        "audio_codec": probed.get("audio_codec"),
        "master_path": master_path,
        "master_fingerprint": master_fp,
        "is_full_length": True,
        "platform_eligibility": eligible_platforms(duration, size_bytes, platform_policies or {}),
        "produced_by": WORKER_VERSION,
        "encode_seconds": seconds,
        "probe": probed,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: media_derivative_worker.py <asset_id> <master_path> [profile]")
        raise SystemExit(2)
    res = build_derivative(
        asset_id=sys.argv[1],
        master_path=sys.argv[2],
        profile=sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PROFILE,
    )
    print(json.dumps(res, indent=2, default=str))
    raise SystemExit(0 if res.get("ok") else 1)
