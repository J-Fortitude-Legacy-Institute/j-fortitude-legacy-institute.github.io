"""
Oversized-video mirror worker (companion-side).

Pulls one asset at a time from `unk-media-mirror-dispatch`, streams the bytes
from Google Drive through this machine into the Supabase Storage
`media-archive` bucket using TUS resumable upload, verifies MD5 against the
Drive-reported md5Checksum, and reports the result back via
`unk-media-mirror-complete`.

Environment required on the companion machine:
    SUPABASE_URL                      optional; canonical production is the safe default
    SUPABASE_SERVICE_ROLE_KEY         service-role JWT (server-side only)
    GOOGLE_DRIVE_OAUTH_TOKEN          access token with drive.readonly
    MEDIA_MIRROR_WORKER_ID            unique per machine, e.g. "unk-companion-01"
    MEDIA_MIRROR_ENABLED              "true" to actually run

Usage:
    python -m desktop_companion.media_mirror_worker            # one pass
    python -m desktop_companion.media_mirror_worker --loop 300 # every 5 min
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime
import sys
import threading
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

try:
    import requests
except ImportError:  # pragma: no cover
    print("requests is required: pip install requests", file=sys.stderr)
    raise

import ffmpeg_bootstrap  # local-first discovery/install
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])




CHUNK_SIZE = 6 * 1024 * 1024  # 6 MiB — TUS minimum for Supabase resumable
CANONICAL_SUPABASE_HOST = "kwbegsybeyyxfmavjswv.supabase.co"
TUS_ENDPOINT_PATH = "/storage/v1/upload/resumable"
HEARTBEAT_INTERVAL_SECONDS = 120  # keep a 30-minute server lease alive during long transcodes
MEDIA_MIRROR_WORKER_PROTOCOL = "2026-11-01-lease-ack-v1"

class MirrorUploadIndeterminate(RuntimeError):
    """Bytes may have reached Project K but Storage's final ACK is missing.

    Preserve the current lease/Storage pointer for independent reconciliation.
    Never mark this upload failed or start a second transfer to the same target.
    """



def env(name: str, required: bool = True) -> str:
    v = os.environ.get(name, "").strip()
    if required and not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v



def require_https_supabase_origin(supabase_url: str) -> str:
    """Never send service-role credentials to an insecure or non-root API origin."""
    parsed = urlparse(supabase_url)
    if (parsed.scheme != "https" or
            parsed.hostname != CANONICAL_SUPABASE_HOST or
            parsed.port not in (None, 443) or
            parsed.username or parsed.password or
            parsed.query or parsed.fragment or
            parsed.path not in ("", "/")):
        raise RuntimeError("mirror service origin must match canonical HTTPS production")
    return f"https://{CANONICAL_SUPABASE_HOST}"


def configured_supabase_origin() -> str:
    """Use the fixed canonical public origin when the optional URL is unset.

    An explicitly configured alternate project or insecure URL is still
    rejected before any private credential or media can be transmitted.
    """
    configured = env("SUPABASE_URL", required=False)
    return require_https_supabase_origin(configured or f"https://{CANONICAL_SUPABASE_HOST}")


def validate_claim_storage_target(job: dict[str, Any]) -> str:
    """Constrain a claimed upload to the server's exact asset/lease Storage path.

    A dispatcher HTTP 200 is not authority to send private media or the
    service-role key to another bucket, asset, or stale lease object. Mirror
    the server's pure mirrorLeaseTargetPath contract before any TUS upload.
    """
    import re
    from datetime import datetime

    asset_id = job.get("asset_id")
    lease_token = job.get("mirror_claimed_at")
    file_name = job.get("file_name")
    derivative_required = job.get("transcode_required")
    if not isinstance(asset_id, str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", asset_id
    ):
        raise RuntimeError("mirror claim has invalid asset identity")
    if not isinstance(lease_token, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", lease_token
    ):
        raise RuntimeError("mirror claim has invalid lease identity")
    try:
        datetime.strptime(lease_token, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise RuntimeError("mirror claim lease timestamp invalid") from exc
    if not isinstance(file_name, str) or not file_name.strip():
        raise RuntimeError("mirror claim filename missing")
    if type(derivative_required) is not bool:
        raise RuntimeError("mirror claim transcode requirement unverified")
    if job.get("target_bucket") != "media-archive":
        raise RuntimeError("mirror claim Storage bucket unexpected")

    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", file_name)
    safe_name = re.sub(r"^\.+", "_", safe_name) or "media"
    leaf = (
        "derivative_h264_" + re.sub(r"\.[^.]+$", "", safe_name) + ".mp4"
        if derivative_required else safe_name
    )
    lease_part = re.sub(r"\D", "", lease_token)
    expected_path = f"{asset_id}/{lease_part}/{leaf}"
    if job.get("target_path") != expected_path:
        raise RuntimeError("mirror claim Storage path mismatches asset/lease")
    return expected_path

def claim_batch(supabase_url: str, service_key: str, worker_id: str, batch_size: int) -> list[dict]:
    supabase_url = require_https_supabase_origin(supabase_url)
    r = requests.post(
        f"{supabase_url}/functions/v1/unk-media-mirror-dispatch",
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
        },
        json={"worker_id": worker_id, "batch_size": batch_size},
        timeout=30,
        allow_redirects=False,
    )
    if r.status_code != 200:
        raise RuntimeError(f"mirror dispatch unexpected HTTP status: {r.status_code}")
    r.raise_for_status()
    # HTTP 200 is not proof that the dispatcher returned a valid job list.
    # A missing or malformed claims field must not look like an idle queue.
    try:
        payload = r.json()
    except (ValueError, TypeError) as exc:
        raise RuntimeError("mirror dispatch claims receipt invalid") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("claimed"), list):
        raise RuntimeError("mirror dispatch claims receipt invalid")
    claimed = payload["claimed"]
    if any(
        not isinstance(job, dict)
        or not isinstance(job.get("asset_id"), str)
        or not job["asset_id"].strip()
        or not isinstance(job.get("mirror_claimed_at"), str)
        or not job["mirror_claimed_at"].strip()
        for job in claimed
    ):
        raise RuntimeError("mirror dispatch claimed job malformed")
    for job in claimed:
        validate_claim_storage_target(job)
    return claimed


def renew_claim(
    supabase_url: str,
    service_key: str,
    worker_id: str,
    asset_id: str,
    lease_token: str,
) -> dict:
    """Renew only this worker's still-current immutable lease, with DB readback.

    The server advances mirror_tick_at, never mirror_claimed_at: the latter
    remains the exact completion fence and per-lease Storage path identity.
    """
    supabase_url = require_https_supabase_origin(supabase_url)
    r = requests.post(
        f"{supabase_url}/functions/v1/unk-media-mirror-dispatch",
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
        },
        json={
            "action": "heartbeat",
            "worker_id": worker_id,
            "asset_id": asset_id,
            "mirror_claimed_at": lease_token,
        },
        timeout=(10, 30),
        allow_redirects=False,
    )
    if r.status_code != 200:
        raise RuntimeError(f"mirror heartbeat unexpected HTTP status: {r.status_code}")
    r.raise_for_status()
    receipt = r.json()
    if (receipt.get("renewed") is not True or
            receipt.get("asset_id") != asset_id or
            receipt.get("mirror_claimed_at") != lease_token or
            not isinstance(receipt.get("mirror_tick_at"), str)):
        raise RuntimeError("mirror lease heartbeat receipt unverified")
    return receipt


class LeaseHeartbeat:
    """Keep a long-running upload lease active without changing its token."""

    def __init__(self, supabase_url: str, service_key: str,
                 worker_id: str, asset_id: str, lease_token: str):
        self.args = (supabase_url, service_key, worker_id, asset_id, lease_token)
        self._stop = threading.Event()
        self._failure: str | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.wait(HEARTBEAT_INTERVAL_SECONDS):
            try:
                renew_claim(*self.args)
            except Exception as exc:  # noqa: BLE001
                self._failure = type(exc).__name__
                self._stop.set()
                return

    def start(self) -> None:
        # Confirm the exact claim before reading any original or starting ffmpeg.
        renew_claim(*self.args)
        self._thread.start()

    def verify(self) -> None:
        # The final synchronous receipt must not race a background renewal:
        # two valid writes could otherwise cross and make each readback look
        # unverified. Stop and join the heartbeat before the final CAS/receipt.
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=35)
            if self._thread.is_alive():
                raise RuntimeError("mirror heartbeat thread still in flight")
        if self._failure is not None:
            raise RuntimeError(f"mirror lease heartbeat lost: {self._failure}")
        # Final independent lease readback before reporting either outcome.
        renew_claim(*self.args)
        if self._failure is not None:
            raise RuntimeError(f"mirror lease heartbeat lost: {self._failure}")

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=35)


def report_result(
    supabase_url: str,
    service_key: str,
    worker_id: str,
    asset_id: str,
    outcome: str,
    *,
    mirror_claimed_at: str,
    bytes_transferred: int | None = None,
    storage_bucket: str | None = None,
    storage_path: str | None = None,
    md5_ok: bool | None = None,
    source_md5_verified: bool | None = None,
    claimed_source: dict | None = None,
    error_message: str | None = None,
    archive_collection: str | None = None,
) -> dict:
    body = {
        "worker_id": worker_id,
        "asset_id": asset_id,
        "outcome": outcome,
        "mirror_claimed_at": mirror_claimed_at,
        "bytes_transferred": bytes_transferred,
        "storage_bucket": storage_bucket,
        "storage_path": storage_path,
        "md5_ok": md5_ok,
        "source_md5_verified": source_md5_verified,
        "claimed_source": claimed_source,
        "error_message": error_message,
    }
    if archive_collection:
        body["archive_collection"] = archive_collection
    supabase_url = require_https_supabase_origin(supabase_url)
    r = requests.post(
        f"{supabase_url}/functions/v1/unk-media-mirror-complete",
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
        allow_redirects=False,
    )
    if r.status_code != 200:
        raise RuntimeError(f"mirror completion unexpected HTTP status: {r.status_code}")
    r.raise_for_status()
    ack = r.json()
    if (not isinstance(ack, dict) or
            ack.get("ok") is not True or
            ack.get("asset_id") != asset_id or
            ack.get("outcome") != outcome or
            ack.get("mirror_claimed_at") != mirror_claimed_at or
            ack.get("worker_id") != worker_id):
        raise RuntimeError("mirror completion receipt unverified")
    return ack


def open_drive_stream(
    drive_file_id: str, oauth_token: str, offset: int = 0,
) -> requests.Response:
    """Request exact original Drive bytes, optionally at a verified resume offset."""
    if not isinstance(drive_file_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", drive_file_id):
        raise RuntimeError("invalid Drive media identifier")
    if not isinstance(offset, int) or offset < 0:
        raise RuntimeError("invalid Drive resume offset")
    url = f"https://www.googleapis.com/drive/v3/files/{drive_file_id}?alt=media"
    headers = {"Authorization": f"Bearer {oauth_token}", "Accept-Encoding": "identity"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    resp = requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=(30, 600),
    )
    resp.raise_for_status()
    return resp


def iter_verified_drive_stream(
    drive_file_id: str,
    oauth_token: str,
    expected_bytes: int,
    initial_response: requests.Response,
    chunk_size: int = 1024 * 1024,
    max_resume_attempts: int = 4,
):
    """Stream Drive master with bounded exact-byte Range recovery.

    Retain one existing K claim/TUS upload and one running MD5 across stream
    interruptions. A provider ignoring Range or reporting a different source
    total must FAIL, never silently duplicate bytes or acknowledge a mirror.
    """
    if expected_bytes <= 0 or chunk_size <= 0 or max_resume_attempts < 0:
        raise ValueError("invalid Drive source length or resume budget")
    offset = 0
    attempts = 0
    response = initial_response
    while offset < expected_bytes:
        try:
            if response.headers.get("Content-Encoding", "identity").lower() not in ("identity", ""):
                raise RuntimeError("drive range cannot validate encoded media bytes")
            range_end = expected_bytes - 1
            if response.status_code == 206:
                header = response.headers.get("Content-Range", "")
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", header.strip())
                if not match:
                    raise RuntimeError("drive range header missing or invalid")
                start, end, total = (int(x) for x in match.groups())
                if start != offset or total != expected_bytes or end < start or end >= total:
                    raise RuntimeError("drive range offset or catalog size mismatch")
                range_end = end
            elif response.status_code != 200 or offset != 0:
                raise RuntimeError("drive range resume rejected: provider ignored Range")
            try:
                for raw in response.iter_content(chunk_size=chunk_size):
                    if not raw:
                        continue
                    if offset + len(raw) > expected_bytes or offset + len(raw) - 1 > range_end:
                        raise RuntimeError("drive range returned more bytes than authorized")
                    offset += len(raw)
                    yield raw
            except (requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout):
                # A broken multi-GB HTTP stream does not invalidate the existing
                # K claim; resume exactly after the final consumed byte instead.
                pass
            if offset == expected_bytes:
                return
            if attempts >= max_resume_attempts:
                raise RuntimeError("drive resume attempts exhausted before verified length")
        finally:
            response.close()
        attempts += 1
        response = open_drive_stream(drive_file_id, oauth_token, offset=offset)


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()



def validate_tus_location(endpoint: str, location: str) -> str:
    """Keep a privileged TUS PATCH on this exact Storage origin and upload route.

    A Location header is data, not permission to forward the service-role key
    to another host, a redirect, or a different Supabase API route.
    """
    if not isinstance(location, str) or not location.strip():
        raise RuntimeError("TUS upload Location missing")
    expected = urlparse(endpoint)
    target = urlparse(urljoin(endpoint.rstrip("/") + "/", location.strip()))
    if target.scheme != expected.scheme or target.netloc != expected.netloc:
        raise RuntimeError("TUS upload Location crossed trusted Storage origin")
    if not target.path.startswith(TUS_ENDPOINT_PATH + "/"):
        raise RuntimeError("TUS upload Location escaped resumable Storage route")
    if any(part in (".", "..") for part in target.path.split("/")):
        raise RuntimeError("TUS upload Location contains path traversal")
    decoded_path = unquote(target.path)
    if (not decoded_path.startswith(TUS_ENDPOINT_PATH + "/") or
            any(part in (".", "..") for part in decoded_path.split("/")) or
            "\\" in decoded_path or target.fragment or
            target.username or target.password):
        raise RuntimeError("TUS upload Location is not a safe Storage upload URL")
    return target.geturl()

def tus_create(
    supabase_url: str,
    service_key: str,
    bucket: str,
    object_path: str,
    total_bytes: int,
    content_type: str,
) -> str:
    """Create a TUS upload and return the upload URL to PATCH into."""
    supabase_url = require_https_supabase_origin(supabase_url)
    endpoint = f"{supabase_url}{TUS_ENDPOINT_PATH}"
    metadata = ",".join([
        f"bucketName {_b64(bucket)}",
        f"objectName {_b64(object_path)}",
        f"contentType {_b64(content_type)}",
        f"cacheControl {_b64('3600')}",
    ])
    r = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Tus-Resumable": "1.0.0",
            "Upload-Length": str(total_bytes),
            "Upload-Metadata": metadata,
        },
        timeout=30,
        allow_redirects=False,
    )
    if r.status_code not in (201, 200):
        raise RuntimeError(f"TUS create failed: HTTP {r.status_code}")
    location = r.headers.get("Location")
    if not location:
        raise RuntimeError("TUS create returned no Location header")
    return validate_tus_location(endpoint, location)


def tus_patch_chunk(
    upload_url: str,
    service_key: str,
    offset: int,
    chunk: bytes,
) -> int:
    try:
        r = requests.patch(
            upload_url,
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "Tus-Resumable": "1.0.0",
                "Upload-Offset": str(offset),
                "Content-Type": "application/offset+octet-stream",
            },
            data=chunk,
            timeout=(30, 600),
            allow_redirects=False,
        )
    except requests.exceptions.RequestException:
        # The server may have committed this PATCH before the response was lost.
        # Keep the lease and TUS pointer for an authoritative HEAD reconciliation.
        raise MirrorUploadIndeterminate("TUS PATCH response uncertain") from None
    if r.status_code != 204:
        raise RuntimeError(f"TUS PATCH failed at offset {offset}: HTTP {r.status_code}")
    ack = r.headers.get("Upload-Offset")
    if ack is None:
        raise MirrorUploadIndeterminate("TUS PATCH offset acknowledgement missing")
    try:
        acknowledged_offset = int(ack)
    except (TypeError, ValueError):
        raise MirrorUploadIndeterminate("TUS PATCH offset acknowledgement invalid") from None
    expected_offset = offset + len(chunk)
    if acknowledged_offset != expected_offset:
        raise MirrorUploadIndeterminate("TUS PATCH offset acknowledgement mismatched")
    return acknowledged_offset


def _run_ffmpeg_transcode(src_path: str, dst_path: str, max_bytes: int) -> None:
    """H.264/AAC MP4 derivative sized to fit under `max_bytes`.

    Two-pass: probe duration, compute a video bitrate budget that keeps the
    output under max_bytes, and cap at 6 Mbps for quality safety.
    """
    # Only transcoded derivatives need this dependency. The normal direct
    # mirror path remains available without installing external media tools.
    ffmpeg, ffprobe = ffmpeg_bootstrap.binaries()
    if not ffmpeg or not ffprobe:
        bootstrap = ffmpeg_bootstrap.ensure()
        if not bootstrap.get("ok"):
            raise RuntimeError("ffmpeg/ffprobe unavailable for derivative transcode")
        ffmpeg, ffprobe = ffmpeg_bootstrap.binaries()
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg/ffprobe unavailable for derivative transcode")
    probe = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", src_path],
        capture_output=True, text=True, timeout=120,
    )
    duration_s = float((probe.stdout or "0").strip() or 0)
    if duration_s <= 0:
        raise RuntimeError("ffprobe could not determine duration; refusing blind transcode")
    audio_bps = 128_000
    # 92% of ceiling for muxing overhead
    target_total_bps = int((max_bytes * 8 * 0.92) / duration_s)
    video_bps = max(400_000, min(6_000_000, target_total_bps - audio_bps))
    subprocess.run(
        [ffmpeg, "-y", "-i", src_path,
         # CPU-only Jwoffice runs concurrent multi-GB transcodes. Keep the
         # exact bitrate/size/MD5 and lease checks, but avoid the hours-long
         # x264 medium preset so the existing workers can finish more jobs.
         "-c:v", "libx264", "-preset", "veryfast", "-b:v", str(video_bps),
         "-maxrate", str(int(video_bps * 1.25)), "-bufsize", str(video_bps * 2),
         "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", str(audio_bps), "-ac", "2",
         dst_path],
        check=True, timeout=60 * 60 * 4,
    )




def validate_signed_upload_url(supabase_url: str, signed_url: str, bucket: str, object_path: str) -> str:
    """Never send private media bytes to a signed URL outside the exact trusted object.

    The server mints an upload capability, but a URL received over the wire is
    still input: require HTTPS, the same Storage origin, exact bucket/object,
    and the signed token before streaming a master or derivative.
    """
    if not isinstance(signed_url, str) or not signed_url.strip():
        raise RuntimeError("signed upload URL missing")
    expected = urlparse(supabase_url.rstrip("/"))
    target = urlparse(urljoin(supabase_url.rstrip("/") + "/", signed_url.strip()))
    if (expected.scheme != "https" or target.scheme != "https" or
            target.netloc != expected.netloc or
            target.username or target.password or target.fragment):
        raise RuntimeError("signed upload URL crossed trusted Storage origin")
    expected_path = f"/storage/v1/object/upload/sign/{bucket}/{object_path}"
    if unquote(target.path) != expected_path:
        raise RuntimeError("signed upload URL does not match claimed Storage object")
    if not parse_qs(target.query).get("token"):
        raise RuntimeError("signed upload URL has no upload capability token")
    return target.geturl()


def _signed_put_file(signed_url: str, file_path: str, content_type: str):
    """Upload a local file through a Supabase signed upload URL.

    Keeps the desktop worker credential-free: the platform mints the URL, so a
    rotated service-role key can never silently break mirroring again.
    """
    md5 = hashlib.md5()
    total = os.path.getsize(file_path)
    observed_bytes = 0
    if total <= 0:
        raise RuntimeError("signed PUT file length must be positive")

    def _gen():
        nonlocal observed_bytes
        with open(file_path, "rb") as fh:  # noqa: PTH123
            while True:
                blk = fh.read(CHUNK_SIZE)
                if not blk:
                    return
                md5.update(blk)
                observed_bytes += len(blk)
                yield blk

    try:
        r = requests.put(
            signed_url,
            data=_gen(),
            headers={
                "Content-Type": content_type,
                "Content-Length": str(total),
            },
            timeout=(30, 3600),
            allow_redirects=False,
        )
    except requests.exceptions.RequestException:
        if observed_bytes:
            # Request generator delivered bytes, but server commit is unknown.
            # A fresh TUS fallback could duplicate or overwrite a completed PUT.
            raise MirrorUploadIndeterminate("signed PUT response uncertain after streaming") from None
        raise
    if r.status_code not in (200, 201, 204):
        if observed_bytes:
            raise MirrorUploadIndeterminate("signed PUT rejected after streaming; commit uncertain")
        raise RuntimeError(f"signed upload acknowledgement unverified: HTTP {r.status_code}")
    if observed_bytes != total:
        raise MirrorUploadIndeterminate(
            f"signed PUT transferred {observed_bytes} of {total} bytes; refusing completion"
        )
    return md5, total


def _upload_local_resilient(
    signed_url: str | None,
    file_path: str,
    content_type: str,
    supabase_url: str,
    service_key: str,
    bucket: str,
    object_path: str,
):
    """Upload a local file without letting one broken transport stop the rail.

    Use signed PUT for <=6 MiB objects only. Send larger verified local media
    directly via 6 MiB TUS chunks: a long signed PUT can end without a trusted
    acknowledgment and indefinitely hold the original lease. Small signed PUT
    may fall back to TUS only on explicit pre-commit transport failure.
    """
    total = os.path.getsize(file_path)
    if total <= 0:
        raise RuntimeError("mirror upload file length must be positive")
    if signed_url:
        # Validate even when choosing TUS. An untrusted capability must not
        # turn into privileged upload permission to a different object/host.
        safe_signed_url = validate_signed_upload_url(supabase_url, signed_url, bucket, object_path)
        if total <= CHUNK_SIZE:
            try:
                return _signed_put_file(safe_signed_url, file_path, content_type)
            except requests.exceptions.RequestException as exc:
                # Only small signed PUT transport faults may try TUS next.
                # The exact target must remain unchanged; never retry an
                # ambiguous post-stream HTTP rejection that might have committed.
                print(f"[mirror] small signed PUT transport failed ({type(exc).__name__}); using TUS", flush=True)

    # Large local masters and derivatives go straight to 6 MiB resumable TUS.
    # A single enormous signed PUT used to finish streaming without a trusted
    # Storage ACK, marooning the original lease with no durable byte checkpoint.
    # TUS makes individual offsets independently acknowledged and keeps the
    # existing claim, exact Storage target and source checksum guards unchanged.
    upload_url = tus_create(supabase_url, service_key, bucket, object_path, total, content_type)
    md5 = hashlib.md5()
    offset = 0
    with open(file_path, "rb") as fh:  # noqa: PTH123
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break
            md5.update(chunk)
            offset = tus_patch_chunk(upload_url, service_key, offset, chunk)
    return md5, offset


def verify_local_master_md5(local_path: str, expected_md5: str | None) -> bool | None:
    """Confirm the local source bytes match independent catalog MD5 before upload.

    A matching byte count does not prove source identity. If the catalog has
    no comparable checksum, do not invent a successful checksum receipt.
    """
    if not expected_md5:
        return None
    import re
    if not re.fullmatch(r"[0-9a-fA-F]{32}", expected_md5):
        raise RuntimeError("local master catalog MD5 invalid")
    digest = hashlib.md5()
    with open(local_path, "rb") as source:  # noqa: PTH123
        while True:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    if digest.hexdigest().lower() != expected_md5.lower():
        raise RuntimeError("local master catalog checksum mismatch; refusing mirror")
    return True


def verified_drive_md5(expected_md5: str | None, computed_md5: str) -> bool | None:
    """Refuse publication when a Drive stream disagrees with its source checksum.

    Local masters without a comparable Drive checksum remain unverified, never
    falsely reported as checksum-matched.
    """
    if not expected_md5:
        return None
    if computed_md5.lower() != expected_md5.lower():
        raise RuntimeError("Drive source checksum mismatch; refusing mirrored completion")
    return True


def require_complete_upload(expected_bytes: int, uploaded_bytes: int) -> None:
    """A partial or short resumable transfer cannot be reported as mirrored.

    This is a transfer-length guard, not a full object digest/playback receipt.
    """
    if expected_bytes <= 0 or uploaded_bytes != expected_bytes:
        raise RuntimeError(
            f"incomplete mirror upload: expected {expected_bytes} bytes, acknowledged {uploaded_bytes}"
        )

def claim_receipt(job: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Validate the dispatch lease and immutable source identity before upload."""
    lease = job.get("mirror_claimed_at")
    if not isinstance(lease, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", lease
    ):
        raise ValueError("dispatch omitted valid mirror_claimed_at; upload refused")
    try:
        datetime.strptime(lease, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ValueError("dispatch supplied invalid lease timestamp; upload refused") from exc
    fields = ("file_name", "drive_file_id", "size_bytes", "drive_md5", "local_path")
    if not all(key in job for key in fields):
        raise ValueError("dispatch omitted source identity fields; upload refused")
    source = {key: job[key] for key in fields}
    if (not isinstance(source["file_name"], str) or not source["file_name"] or
        not isinstance(source["drive_file_id"], str) or not source["drive_file_id"] or
        not (source["size_bytes"] is None or
             (type(source["size_bytes"]) is int and source["size_bytes"] > 0)) or
        not (source["drive_md5"] is None or isinstance(source["drive_md5"], str)) or
        not (source["local_path"] is None or isinstance(source["local_path"], str))):
        raise ValueError("dispatch supplied invalid source identity; upload refused")
    return lease, source


def file_md5(path: str) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def mirror_one(job: dict[str, Any], supabase_url: str, service_key: str, oauth: str) -> dict:
    import tempfile
    asset_id = job["asset_id"]
    drive_id = job.get("drive_file_id")
    total_bytes = int(job.get("size_bytes") or 0)
    bucket = job.get("target_bucket") or "media-archive"
    path = job["target_path"]
    expected_md5 = (job.get("drive_md5") or "").lower() or None
    if expected_md5 and not re.fullmatch(r"[0-9a-f]{32}", expected_md5):
        raise ValueError("invalid catalog MD5")
    source_verified = None
    transcode_required = bool(job.get("transcode_required"))
    derivative_max_bytes = int(job.get("derivative_max_bytes") or (950 * 1024 * 1024))
    signed_upload_url = (job.get("upload_url") or "").strip() or None

    # Local master on an attached drive beats Google Drive every time: no quota,
    # no 404s, no broken streams. Drive is only the fallback now.
    local_path = (job.get("local_path") or "").strip() or None
    use_local = bool(local_path) and os.path.isfile(local_path)
    if local_path and not use_local:
        print(f"[mirror] local master missing on disk: {local_path}", flush=True)

    print(
        f"[mirror] start {asset_id} {job['file_name']} ({total_bytes} bytes) "
        f"source={'local' if use_local else 'drive'} transcode={transcode_required}",
        flush=True,
    )

    stream = None
    source_md5_verified: bool | None = None
    if use_local:
        content_type = "video/mp4" if local_path.lower().endswith(".mp4") else "application/octet-stream"
        # The catalog's independent original length must match this local
        # master before FFmpeg can derive a valid-looking video from wrong bytes.
        # Never silently replace the claimed source length with disk metadata.
        observed_local_bytes = os.path.getsize(local_path)
        if total_bytes <= 0 or observed_local_bytes != total_bytes:
            raise RuntimeError(
                f"local master size mismatch: catalog expected {total_bytes} bytes, "
                f"observed {observed_local_bytes}; refusing mirror"
            )
        # Compare the independent catalog MD5 before FFmpeg or any upload.
        # A same-length but different local source must never be mirrored.
        source_md5_verified = verify_local_master_md5(local_path, expected_md5)

        def _iter_source(chunk_size: int = 1024 * 1024):
            with open(local_path, "rb") as fh:  # noqa: PTH123
                while True:
                    blk = fh.read(chunk_size)
                    if not blk:
                        return
                    yield blk
    else:
        if not drive_id:
            raise RuntimeError("no local_path on disk and no drive_file_id; nothing to mirror")
        # A response's Content-Length is not an independent source manifest:
        # a truncated Drive object can advertise its own shorter length and
        # otherwise pass our transfer-length and checksum-optional checks.
        if total_bytes <= 0:
            raise RuntimeError("Drive catalog source length missing; refusing unverified mirror")
        stream = open_drive_stream(drive_id, oauth)
        content_type = stream.headers.get("Content-Type", "application/octet-stream")

        def _iter_source(chunk_size: int = 1024 * 1024):
            yield from iter_verified_drive_stream(
                drive_id, oauth, total_bytes, stream, chunk_size=chunk_size,
            )

    if not total_bytes:
        raise RuntimeError("cannot determine total bytes; refusing to upload")


    if transcode_required:
        # Preserve the original master on Drive (never delete); write a local scratch
        # copy, transcode to platform-safe H.264/AAC, then mirror the derivative.
        # Windows/AV can hold derivative.mp4 during scratch cleanup; do not
        # convert a fully acknowledged upload into a false failed transfer.
        # TemporaryDirectory still removes every file it can safely remove.
        with tempfile.TemporaryDirectory(prefix=f"mirror_{asset_id}_", ignore_cleanup_errors=True) as tmpd:
            dst_local = f"{tmpd}/derivative.mp4"
            if use_local:
                # Transcode straight off the external drive — no scratch copy.
                src_local = local_path
            else:
                src_local = f"{tmpd}/master.bin"
                # A truncated Drive stream can still produce a decodable MP4,
                # so validate the complete original before encoding a derivative.
                source_md5 = hashlib.md5()
                source_bytes = 0
                with open(src_local, "wb") as f:
                    for raw in _iter_source():
                        if raw:
                            f.write(raw)
                            source_bytes += len(raw)
                            source_md5.update(raw)
                require_complete_upload(total_bytes, source_bytes)
                source_md5_verified = verified_drive_md5(expected_md5, source_md5.hexdigest())
            _run_ffmpeg_transcode(src_local, dst_local, derivative_max_bytes)
            if use_local:
                # The source can change while FFmpeg reads a large original.
                # Recheck the exact catalog size and digest before granting
                # a derivative upload success receipt for stale source bytes.
                post_encode_source_bytes = os.path.getsize(local_path)
                if post_encode_source_bytes != total_bytes:
                    raise RuntimeError("local master changed during transcode; refusing derivative upload")
                source_md5_verified = verify_local_master_md5(local_path, expected_md5)

            import os as _os
            derivative_bytes = _os.path.getsize(dst_local)
            if derivative_bytes > derivative_max_bytes:
                raise RuntimeError(
                    f"derivative {derivative_bytes} still exceeds max {derivative_max_bytes}"
                )
            content_type = "video/mp4"
            md5, offset = _upload_local_resilient(
                signed_upload_url, dst_local, content_type,
                supabase_url, service_key, bucket, path,
            )

            require_complete_upload(derivative_bytes, offset)
            print(f"[mirror] transcoded+uploaded {asset_id} derivative_bytes={offset}", flush=True)
            return {
                "asset_id": asset_id,
                "bytes_transferred": offset,
                "storage_bucket": bucket,
                "storage_path": path,
                "computed_md5": md5.hexdigest(),
                # MD5 will not match Drive master after transcode; caller should ignore.
                "md5_ok": None,
                "source_md5_verified": source_md5_verified,
            }

    if use_local:
        md5obj, offset = _upload_local_resilient(
            signed_upload_url, local_path, content_type,
            supabase_url, service_key, bucket, path,
        )
        require_complete_upload(total_bytes, offset)
        computed_md5 = md5obj.hexdigest()
        md5_ok = verified_drive_md5(expected_md5, computed_md5)
    else:
        upload_url = tus_create(supabase_url, service_key, bucket, path, total_bytes, content_type)

        md5 = hashlib.md5()
        offset = 0
        buf = bytearray()

        for raw in _iter_source():
            if not raw:
                continue
            md5.update(raw)
            buf.extend(raw)
            while len(buf) >= CHUNK_SIZE:
                chunk = bytes(buf[:CHUNK_SIZE])
                del buf[:CHUNK_SIZE]
                offset = tus_patch_chunk(upload_url, service_key, offset, chunk)
        if buf:
            offset = tus_patch_chunk(upload_url, service_key, offset, bytes(buf))
            buf.clear()

        require_complete_upload(total_bytes, offset)
        computed_md5 = md5.hexdigest()
        md5_ok = verified_drive_md5(expected_md5, computed_md5)

    if md5_ok is False:
        raise RuntimeError("source master MD5 mismatch; mirror refused")

    print(
        f"[mirror] done  {asset_id} bytes={offset} md5={computed_md5} "
        f"expected={expected_md5} ok={md5_ok}",
        flush=True,
    )

    return {
        "asset_id": asset_id,
        "bytes_transferred": offset,
        "storage_bucket": bucket,
        "storage_path": path,
        "computed_md5": computed_md5,
        "md5_ok": md5_ok,
        "source_md5_verified": md5_ok,
    }



def run_once(batch_size: int = 1) -> int:
    # An explicitly disabled mirror must not read protected credentials or
    # install FFmpeg. Plain direct uploads do not need FFmpeg at all.
    enabled = env("MEDIA_MIRROR_ENABLED", required=False).lower() == "true"
    if not enabled:
        print("[mirror] MEDIA_MIRROR_ENABLED != true; refusing to run", flush=True)
        return 0

    supabase_url = configured_supabase_origin()
    service_key = env("SUPABASE_SERVICE_ROLE_KEY")
    # Optional: local-drive masters mirror fine with no Drive credential at all.
    oauth = env("GOOGLE_DRIVE_OAUTH_TOKEN", required=False)
    worker_id = env("MEDIA_MIRROR_WORKER_ID")


    mirrored = 0
    # A single worker processes assets sequentially. Do not preclaim up to
    # five long videos at once: later leases could expire while the first
    # transcode or upload is still running. Obtain each lease just in time.
    for _ in range(max(1, min(batch_size, 5))):
        jobs = claim_batch(supabase_url, service_key, worker_id, 1)
        if not jobs:
            if mirrored == 0:
                print("[mirror] no pending assets", flush=True)
            break
        job = jobs[0]
        try:
            lease_token, claimed_source = claim_receipt(job)
        except (ValueError, TypeError) as invalid_claim:
            print(f"[mirror] refusing incomplete claim for {job.get('asset_id')}: {type(invalid_claim).__name__}", flush=True)
            continue

        # A 4-hour transcode cannot rely on a fixed 30-minute lease. Start
        # an authenticated, exact-token heartbeat before the operation, and
        # independently verify the lease once more before any completion ACK.
        lease_guard = LeaseHeartbeat(
            supabase_url, service_key, worker_id, job["asset_id"], lease_token,
        )
        try:
            lease_guard.start()
        except Exception as e:  # noqa: BLE001
            print(f"[mirror] refusing work without verified current lease for {job['asset_id']}: {type(e).__name__}", flush=True)
            continue
        try:
            try:
                result = mirror_one(job, supabase_url, service_key, oauth)
            except MirrorUploadIndeterminate:
                # Do not convert an ACK loss into a failed terminal callback:
                # Storage may already contain bytes and a successor must reconcile.
                print("[mirror] upload acknowledgement uncertain; retain claim for reconciliation", flush=True)
                continue
            except Exception as e:  # noqa: BLE001
                print(f"[mirror] FAILED {job.get('asset_id')}: {type(e).__name__}", flush=True)
                try:
                    lease_guard.verify()
                except Exception as lease_error:  # noqa: BLE001
                    # Do not report a failure for a lease that may have been
                    # reassigned. Server expiry/recovery handles uncertainty.
                    print(f"[mirror] failure receipt withheld; lease unverified: {type(lease_error).__name__}", flush=True)
                    continue
                try:
                    report_result(
                        supabase_url, service_key, worker_id, job["asset_id"],
                        outcome="failed",
                        mirror_claimed_at=lease_token,
                        claimed_source=claimed_source,
                        # Dispatch fixed this exact target to the lease. Carry it on
                        # failed outcomes too: K must close the original CLAIMED
                        # audit row, never leave an orphan beside a FAILED receipt.
                        storage_bucket=job.get("target_bucket") or "media-archive",
                        storage_path=job.get("target_path"),
                        error_message=f"worker_{type(e).__name__}",
                    )
                except Exception as inner:  # noqa: BLE001
                    print(f"[mirror] could not report failure: {type(inner).__name__}", flush=True)
                continue

            # Bytes may already exist when a heartbeat or completion ACK is
            # ambiguous. Never send a second 'failed' outcome after uploaded
            # bytes, or falsely report success. Exact lease CAS is authoritative.
            try:
                lease_guard.verify()
            except Exception as lease_error:  # noqa: BLE001
                print(f"[mirror] upload finished but lease unverified for {job['asset_id']}: {type(lease_error).__name__}", flush=True)
                continue
            try:
                # The above upload has returned successfully. An ambiguous
                # completion ACK is handled by the enclosing exception branch,
                # preserving this exact lease without a second terminal callback.
                report_result(
                    supabase_url, service_key, worker_id, job["asset_id"],
                    outcome="mirrored",
                    mirror_claimed_at=lease_token,
                    bytes_transferred=result["bytes_transferred"],
                    storage_bucket=result["storage_bucket"],
                    storage_path=result["storage_path"],
                    md5_ok=result["md5_ok"],
                    source_md5_verified=result["source_md5_verified"],
                    claimed_source=claimed_source,
                )
            except Exception as e:  # noqa: BLE001
                print(f"[mirror] upload completed but receipt unverified for {job['asset_id']}: {type(e).__name__}", flush=True)
                continue
            mirrored += 1
        finally:
            lease_guard.stop()
    return mirrored


def safe_mirror_loop_error(exc: BaseException) -> str:
    """Expose only whitelisted recovery hints, never exception URLs or credentials."""
    kind = type(exc).__name__
    if type(exc) is not RuntimeError:
        return kind
    message = str(exc)
    allowed = {
        "Missing env var: SUPABASE_SERVICE_ROLE_KEY",
        "Missing env var: MEDIA_MIRROR_WORKER_ID",
        "mirror dispatch claims receipt invalid",
        "mirror dispatch claimed job malformed",
        "mirror service origin must match canonical HTTPS production",
    }
    if message in allowed:
        return f"{kind}: {message}"
    prefix = "mirror dispatch unexpected HTTP status: "
    if message.startswith(prefix):
        code = message[len(prefix):]
        if len(code) == 3 and code.isascii() and code.isdecimal():
            return f"{kind}: mirror dispatch HTTP {code}"
    return kind


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--loop", type=int, default=0,
                    help="If > 0, run continuously and sleep this many seconds between passes.")
    args = ap.parse_args()

    if args.loop <= 0:
        run_once(args.batch)
        return
    while True:
        try:
            run_once(args.batch)
        except Exception as e:  # noqa: BLE001
            print(f"[mirror] top-level error: {safe_mirror_loop_error(e)}", flush=True)
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
