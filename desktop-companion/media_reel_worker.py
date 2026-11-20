"""Local reel cutter — deterministic vertical clips, zero cloud AI.

Given a signed read URL for a mirrored master and a start offset, FFmpeg cuts a
single vertical (1080x1920) clip plus a poster frame and PUTs both to the signed
upload URLs handed down by the reel factory. The master is never downloaded in
full: `-ss` before `-i` makes FFmpeg range-request only the bytes it needs.

Everything here runs on Ground Zero. No API keys, no model calls, no credits.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests

import ffmpeg_bootstrap  # local playbook
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


WORKER_VERSION = "reel-worker-v1"
REEL_WIDTH = 1080
REEL_HEIGHT = 1920


def _work_dir() -> Path:
    d = ffmpeg_bootstrap.runtime_root() / "reels"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _put(url: str, path: Path, content_type: str) -> dict:
    with open(path, "rb") as fh:
        r = requests.put(
            url,
            data=fh,
            headers={"Content-Type": content_type, "x-upsert": "true"},
            timeout=(30, 900),
        )
    if r.status_code >= 400:
        return {"ok": False, "error": "upload_failed", "status": r.status_code, "body": r.text[:500]}
    return {"ok": True, "status": r.status_code}


def make_reel(
    *,
    plan_id: str,
    source_asset_id: str,
    source_url: str,
    start_seconds: float,
    duration_seconds: float,
    upload_video_url: str,
    upload_thumb_url: str,
    log=print,
    **_ignored,
) -> dict:
    t0 = time.time()
    ffmpeg, ffprobe = ffmpeg_bootstrap.binaries()
    if not ffmpeg or not ffprobe:
        return {"ok": False, "error": "ffmpeg_unavailable",
                "detail": "run the ffmpeg_ensure capability on this device first"}

    out_dir = _work_dir()
    clip = out_dir / f"{source_asset_id}__{plan_id}.mp4"
    thumb = out_dir / f"{source_asset_id}__{plan_id}.jpg"

    vf = (
        f"scale={REEL_WIDTH}:{REEL_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={REEL_WIDTH}:{REEL_HEIGHT}"
    )

    cut = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", str(float(start_seconds)),
        "-i", source_url,
        "-t", str(float(duration_seconds)),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high",
        "-b:v", "4500k", "-maxrate", "5000k", "-bufsize", "9000k",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-movflags", "+faststart",
        str(clip),
    ]
    log(f"[reel] cutting {source_asset_id} @ {start_seconds}s -> {clip.name}")
    p = subprocess.run(cut, capture_output=True, text=True, timeout=60 * 45)
    if p.returncode != 0 or not clip.exists() or clip.stat().st_size == 0:
        return {"ok": False, "error": "reel_cut_failed",
                "detail": (p.stderr or p.stdout or "")[-1200:]}

    poster = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", str(max(0.0, float(duration_seconds) / 2)),
        "-i", str(clip), "-frames:v", "1", "-q:v", "3", str(thumb),
    ]
    tp = subprocess.run(poster, capture_output=True, text=True, timeout=300)
    if tp.returncode != 0 or not thumb.exists():
        return {"ok": False, "error": "thumbnail_failed",
                "detail": (tp.stderr or tp.stdout or "")[-800:]}

    probed = ffmpeg_bootstrap.probe(str(clip), ffprobe=ffprobe)

    up1 = _put(upload_video_url, clip, "video/mp4")
    if not up1["ok"]:
        return {"ok": False, "error": "video_upload_failed", "detail": up1}
    up2 = _put(upload_thumb_url, thumb, "image/jpeg")
    if not up2["ok"]:
        return {"ok": False, "error": "thumb_upload_failed", "detail": up2}

    clip_size = clip.stat().st_size
    # Local scratch is disposable; the mirrored copy is now the record.
    clip.unlink(missing_ok=True)
    thumb.unlink(missing_ok=True)

    return {
        "ok": True,
        "plan_id": plan_id,
        "source_asset_id": source_asset_id,
        "start_seconds": float(start_seconds),
        "duration_seconds": float(probed.get("duration_seconds") or duration_seconds),
        "width": probed.get("width") or REEL_WIDTH,
        "height": probed.get("height") or REEL_HEIGHT,
        "size_bytes": clip_size,
        "produced_by": WORKER_VERSION,
        "seconds": round(time.time() - t0, 1),
    }


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    res = make_reel(**payload)
    print(json.dumps(res, indent=2, default=str))
    raise SystemExit(0 if res.get("ok") else 1)
