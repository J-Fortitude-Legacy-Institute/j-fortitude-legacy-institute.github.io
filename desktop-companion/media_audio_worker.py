"""
Companion audio-extract worker.

Zero-secret design: uses only SUPABASE_ANON_KEY (already baked into the
companion). Server-side edge functions hold the Drive + Lovable keys.

Loop:
  1. POST /functions/v1/unk-media-audio-authorize -> claim an asset
  2. Byte-range download from /functions/v1/unk-media-drive-range in
     128 MB chunks until the whole video is on local disk
  3. ffmpeg -vn -ac 1 -ar 16000 -b:a 32k -> mono MP3
  4. ffmpeg -f segment -segment_time 900 -> N chunks of ~7 MB each
  5. For each chunk: POST /unk-media-audio-report {mode:'upload_url'} -> PUT
  6. POST /unk-media-audio-report {mode:'chunks_done'}
  7. On any hard error: POST /unk-media-audio-report {mode:'failed'}

Requires: python3, requests, ffmpeg on PATH.

Env:
  SUPABASE_ANON_KEY   (already set for companion)
  MEDIA_AUDIO_WORKER_ID  (default 'unk-audio-01')

Usage:
  python media_audio_worker.py            # one pass
  python media_audio_worker.py --loop 300 # every 5 min
"""

from __future__ import annotations
import argparse, json, os, re, subprocess, sys, tempfile, time
from pathlib import Path

import requests

# Resolve verified FFmpeg paths at execution, not at module import.

# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


PROJECT_REF = "kwbegsybeyyxfmavjswv"
BASE = f"https://{PROJECT_REF}.functions.supabase.co"
ANON = os.environ.get("SUPABASE_ANON_KEY", "").strip() or "sb_publishable_71YhGNn088MamieIZXBAaw_kv3w4wc9"
WORKER_ID = os.environ.get("MEDIA_AUDIO_WORKER_ID", "unk-audio-01")
RANGE_BYTES = 128 * 1024 * 1024  # 128 MB per download call
STORAGE_UPLOAD = f"https://{PROJECT_REF}.supabase.co/storage/v1/upload/sign"


def hdrs():
    # Reuse the original Unk enrollment credentials; a public API key is not
    # a machine identity (and cannot be presented as a valid Supabase user JWT).
    from unk_companion import load_credentials
    identity = load_credentials()
    if not identity or not all(identity):
        raise RuntimeError("Unk media audio worker requires an enrolled active device")
    device_id, device_key = identity
    return {
        "apikey": ANON,
        "x-device-id": device_id,
        "x-device-key": device_key,
        "Content-Type": "application/json",
    }


def post(path: str, body: dict, stream: bool = False, timeout: int = 180):
    r = requests.post(f"{BASE}{path}", headers=hdrs(), json=body, stream=stream, timeout=timeout)
    if not stream:
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, {"raw": r.text}
    return r


def download_full(asset_id: str, size_bytes: int, dst: Path) -> None:
    """Stream only independently validated, exact-size byte ranges.

    A CDN, Drive connector, or Storage route may return 200 for an ignored
    Range header, a truncated 206, or a contradictory Content-Range. Do not
    count any of those responses as a complete original-media transfer.
    """
    if size_bytes <= 0:
        raise RuntimeError("source byte size missing")
    with open(dst, "wb") as f:
        start = 0
        while start < size_bytes:
            end = min(start + RANGE_BYTES - 1, size_bytes - 1)
            expected = end - start + 1
            for attempt in range(3):
                try:
                    r = post(
                        "/unk-media-drive-range",
                        {"asset_id": asset_id, "byte_start": start, "byte_end": end},
                        stream=True, timeout=180,
                    )
                    if r.status_code == 206:
                        match = re.fullmatch(
                            r"bytes (\d+)-(\d+)/(\d+)",
                            r.headers.get("Content-Range", ""),
                        )
                        if not match or tuple(map(int, match.groups())) != (start, end, size_bytes):
                            raise RuntimeError("range identity does not match source")
                    elif r.status_code != 200 or start != 0 or end != size_bytes - 1:
                        raise RuntimeError(f"range response not complete: HTTP {r.status_code}")
                    # Retry cannot append to bytes from a previous failed attempt.
                    f.seek(start)
                    f.truncate(start)
                    copied = 0
                    for buf in r.iter_content(chunk_size=1024 * 1024):
                        if buf:
                            copied += len(buf)
                            if copied > expected:
                                raise RuntimeError("range exceeded requested bytes")
                            f.write(buf)
                    if copied != expected:
                        raise RuntimeError("range body shorter than verified source")
                    start = end + 1
                    break
                except Exception as exc:
                    f.seek(start)
                    f.truncate(start)
                    if attempt == 2:
                        raise RuntimeError(f"range {start}-{end} not verified after 3 attempts") from exc
                    time.sleep(2 * (attempt + 1))


def _media_binaries() -> tuple[str, str]:
    """Resolve local verified FFmpeg paths before holding a media claim."""
    from ffmpeg_bootstrap import binaries, ensure
    ffmpeg, ffprobe = binaries()
    if not ffmpeg or not ffprobe:
        result = ensure(log=lambda _message: None)
        if not result.get("ok"):
            raise RuntimeError("verified FFmpeg setup failed: " + str(result.get("error", "unknown")))
        ffmpeg, ffprobe = binaries()
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg/ffprobe still unavailable after verified setup")
    return ffmpeg, ffprobe


def ffmpeg_extract(src: Path, out_dir: Path) -> list[Path]:
    """Extract mono 16k mp3, split into 900s segments. Returns segment paths."""
    ffmpeg, _ = _media_binaries()
    audio = out_dir / "audio.mp3"
    subprocess.check_call([
        ffmpeg, "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
        "-b:a", "32k", "-f", "mp3", str(audio),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pattern = out_dir / "seg_%03d.mp3"
    subprocess.check_call([
        ffmpeg, "-y", "-i", str(audio), "-f", "segment", "-segment_time", "900",
        "-c", "copy", str(pattern),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    audio.unlink(missing_ok=True)
    return sorted(out_dir.glob("seg_*.mp3"))


def upload_chunk(asset_id: str, idx: int, path: Path) -> None:
    status, resp = post(
        "/unk-media-audio-report",
        {"asset_id": asset_id, "mode": "upload_url", "chunk_index": idx},
    )
    signed = resp.get("signedUrl") or resp.get("signed_url")
    if status != 200 or not signed:
        raise RuntimeError(f"upload_url failed: {status} {resp}")
    # Signed URL may be relative — prefix with the storage host if so.
    if signed.startswith("/"):
        signed = f"https://{PROJECT_REF}.supabase.co{signed}"
    with open(path, "rb") as f:
        r = requests.put(signed, headers={
            "Content-Type": "audio/mpeg",
            "x-upsert": "true",
        }, data=f, timeout=300)
    if r.status_code >= 300:
        raise RuntimeError(f"chunk {idx} upload {r.status_code}: {r.text[:200]}")


def probe_duration(path: Path) -> float:
    try:
        _, ffprobe = _media_binaries()
        out = subprocess.check_output([
            ffprobe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ])
        return float(out.strip())
    except Exception:
        return 900.0


def process_one() -> bool:
    try:
        # Fail before claiming work if the local media toolchain is unavailable.
        _media_binaries()
    except Exception as exc:
        print(f"[audio] verified codec preflight failed: {exc}", flush=True)
        return False
    status, job = post("/unk-media-audio-authorize", {"worker_id": WORKER_ID})
    if status != 200:
        print(f"[audio] authorize {status}: {job}", flush=True)
        return False
    if job.get("empty"):
        return False
    asset_id = job["asset_id"]
    size_bytes = int(job.get("size_bytes") or 0)
    if not size_bytes:
        post("/unk-media-audio-report", {"asset_id": asset_id, "mode": "failed", "error": "size_bytes unknown"})
        return True

    print(f"[audio] claimed {asset_id} ({job.get('file_name')}, {size_bytes/1e9:.2f} GB)", flush=True)
    with tempfile.TemporaryDirectory(prefix=f"unk_audio_{asset_id[:8]}_") as tmp:
        tmpd = Path(tmp)
        src = tmpd / "source.bin"
        try:
            print("[audio]  downloading...", flush=True)
            download_full(asset_id, size_bytes, src)
            print("[audio]  extracting audio...", flush=True)
            segs = ffmpeg_extract(src, tmpd)
            src.unlink(missing_ok=True)
            print(f"[audio]  uploading {len(segs)} chunks...", flush=True)
            chunk_meta = []
            for i, p in enumerate(segs):
                upload_chunk(asset_id, i, p)
                chunk_meta.append({
                    "index": i,
                    "byte_size": p.stat().st_size,
                    "duration_seconds": int(probe_duration(p)),
                })
            code, resp = post("/unk-media-audio-report", {
                "asset_id": asset_id, "mode": "chunks_done", "chunks": chunk_meta,
            })
            if code != 200:
                raise RuntimeError(f"chunks_done failed: {code} {resp}")
            print(f"[audio]  done: {len(segs)} chunks staged for transcription", flush=True)
        except Exception as e:
            print(f"[audio]  FAILED {asset_id}: {e}", flush=True)
            post("/unk-media-audio-report", {
                "asset_id": asset_id, "mode": "failed", "error": str(e)[:400],
            })
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, default=0,
                    help="Loop forever, sleeping N seconds when idle. 0 = one pass.")
    args = ap.parse_args()

    while True:
        try:
            processed_any = process_one()
        except Exception as e:
            print(f"[audio] pass error: {e}", flush=True)
            processed_any = False
        if not args.loop:
            return
        if not processed_any:
            time.sleep(args.loop)


if __name__ == "__main__":
    main()
