"""Unk capability: autonomous operational secret rotation.

Rotates a rotating operational token end-to-end WITHOUT the plaintext value
ever leaving Ground Zero, being logged, printed, committed, or returned:

  1. generate 24 cryptographically random bytes (48 hex chars)
  2. publish ONLY sha256(token) to the `ops-secret-rotate` edge function
  3. push the value into the GitHub Actions repo secret via authenticated `gh`
  4. write it to the non-versioned local `.env.integration` for the test runner
  5. run the integration suite and return non-secret receipts only

Design rules (do not weaken):
  - The token exists only in process memory, the gh stdin pipe, and the local
    non-versioned env file. It is never a CLI argument (process lists leak).
  - Only ALLOWED_TOKENS may be rotated, and only ALLOWED_ENV_FILES written.
  - Every returned field is non-secret; a fingerprint prefix (first 8 hex of
    the sha256) is the only correlation handle.
  - The UNK service key is read from the local operator keyring/file; it is
    never accepted from the cloud payload and never returned.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

HOME = Path.home()
COMPANION_DIR = HOME / ".unk-companion"
OPS_KEY_FILE = COMPANION_DIR / "ops.json"
DEVICE_FILE = COMPANION_DIR / "device.json"

ALLOWED_TOKENS = {"E2E_FIXTURE_TOKEN"}
ALLOWED_ENV_FILES = {".env.integration"}
ALLOWED_TEST_SCRIPTS = {"test:integration"}
DEFAULT_REPO = "J-Fortitude-Legacy-Institute/grantflow-gateway"

# Repo checkouts Unk is permitted to touch for this operation.
ALLOWED_REPO_ROOTS = [
    HOME / "Documents" / "JFLI",
    HOME / "Documents" / "GitHub",
    HOME / "source" / "repos",
    HOME / "Projects",
]


def _ops_key(name: str = "UNK_SERVICE_KEY") -> str:
    """Read an operator key from the local keyring, then the local ops file."""
    try:
        import keyring  # type: ignore

        val = keyring.get_password("unk-companion", name)
        if val:
            return val.strip()
    except Exception:
        pass
    try:
        if OPS_KEY_FILE.exists():
            data = json.loads(OPS_KEY_FILE.read_text(encoding="utf-8"))
            val = str(data.get(name) or "").strip()
            if val:
                return val
    except Exception:
        pass
    return ""


def _device_credentials() -> tuple[str, str]:
    """Read the enrolled device identity already provisioned on Ground Zero.

    This is the zero-setup authorization path: the companion is enrolled at
    install time, so no operator has to plant an extra key on the machine.
    """
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


def _auth_headers() -> tuple[dict[str, str], str]:
    """Prefer the operator service key, fall back to the device identity."""
    key = _ops_key("UNK_SERVICE_KEY")
    if key:
        return {"x-unk-service-key": key}, "service_key"
    did, dkey = _device_credentials()
    if did and dkey:
        return {"x-device-id": did, "x-device-key": dkey}, "device_identity"
    return {}, ""


def _repo_allowed(path: Path) -> bool:
    try:
        rp = path.resolve()
    except Exception:
        return False
    if not (rp / ".git").exists():
        return False
    return any(str(rp).lower().startswith(str(root.resolve()).lower()) for root in ALLOWED_REPO_ROOTS)


def _find_repo(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser()
        return p if _repo_allowed(p) else None
    for root in ALLOWED_REPO_ROOTS:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / ".git").exists() and (child / "package.json").exists():
                try:
                    pkg = json.loads((child / "package.json").read_text(encoding="utf-8"))
                except Exception:
                    continue
                if "test:integration" in (pkg.get("scripts") or {}):
                    return child
    return None


def _which(*names: str) -> str | None:
    for n in names:
        found = shutil.which(n)
        if found:
            return found
    return None


def _write_env_var(env_path: Path, key: str, value: str) -> str:
    """Upsert KEY=value in a non-versioned env file. Returns 'created'|'updated'."""
    lines: list[str] = []
    existed = env_path.exists()
    if existed:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            out.append(f"{key}={value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key}={value}")
    env_path.write_text("\n".join(out).rstrip("\n") + "\n", encoding="utf-8")
    try:
        os.chmod(env_path, 0o600)
    except Exception:
        pass
    return "updated" if existed and replaced else ("appended" if existed else "created")


def rotate(payload: dict[str, Any]) -> dict:
    payload = dict(payload or {})
    token_name = str(payload.get("token_name") or "E2E_FIXTURE_TOKEN").strip()
    repo_slug = str(payload.get("github_repo") or DEFAULT_REPO).strip()
    env_file = str(payload.get("env_file") or ".env.integration").strip()
    test_script = str(payload.get("test_script") or "test:integration").strip()
    run_tests = bool(payload.get("run_tests", True))
    functions_base = str(payload.get("functions_base") or "").rstrip("/")

    receipt: dict[str, Any] = {
        "token_name": token_name,
        "backend_registered": False,
        "github_secret_updated": False,
        "local_env_updated": False,
        "tests_ran": False,
    }

    # Repository identity is fail-closed. The repository was transferred into
    # the organization; any payload targeting anything but the canonical slug
    # is rejected before a secret or receipt can be written.
    if repo_slug != DEFAULT_REPO:
        return {
            "ok": False,
            "error": "github_repo_not_canonical",
            "required_repo": DEFAULT_REPO,
            **receipt,
        }

    if token_name not in ALLOWED_TOKENS:
        return {"ok": False, "error": "token_name_not_allowed", **receipt}
    if env_file not in ALLOWED_ENV_FILES:
        return {"ok": False, "error": "env_file_not_allowed", **receipt}
    if test_script not in ALLOWED_TEST_SCRIPTS:
        return {"ok": False, "error": "test_script_not_allowed", **receipt}
    # Privileged secret rotation may not be redirected to the protected
    # historical source or to any noncanonical project by stale caller input.
    canonical_functions = "https://kwbegsybeyyxfmavjswv.functions.supabase.co"
    alternate_k_functions = "https://kwbegsybeyyxfmavjswv.supabase.co/functions/v1"
    if functions_base and functions_base not in (canonical_functions, alternate_k_functions):
        return {"ok": False, "error": "noncanonical_secret_rotation_destination", **receipt}
    if requests is None:
        return {"ok": False, "error": "requests_missing", **receipt}

    auth_headers, auth_mode = _auth_headers()
    if not auth_headers:
        return {
            "ok": False,
            "error": "no_local_authorization",
            "remedy": (
                "Ground Zero has neither an enrolled device identity nor UNK_SERVICE_KEY. "
                "Re-enroll the companion (it self-enrolls on start) and retry."
            ),
            **receipt,
        }
    receipt["auth_mode"] = auth_mode

    # A local repo checkout is optional. Backend registration is the
    # authoritative rotation; repo-side sync (gh secret + .env.integration +
    # tests) only runs when Ground Zero actually has a checkout.
    repo = _find_repo(payload.get("repo_path"))
    receipt["repo_available"] = repo is not None
    receipt["repo_path_allowed"] = repo is not None

    # ---- 1. generate (never logged, never a CLI arg) ----
    token = secrets.token_hex(24)  # 48 hex chars
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    receipt["fingerprint_prefix"] = digest[:8]

    # ---- 2. register the fingerprint with the backend ----
    base = functions_base or canonical_functions
    try:
        r = requests.post(
            f"{base}/ops-secret-rotate",
            headers={"Content-Type": "application/json", **auth_headers},
            json={
                "action": "rotate",
                "token_name": token_name,
                "token_sha256": digest,
                "rotated_by": f"unk:ground-zero:{auth_mode}",
                "receipt": {"source": "secret_rotate", "repo": repo_slug},
            },
            timeout=45,
        )
        receipt["backend_status"] = r.status_code
        body = r.json() if r.content else {}
        receipt["backend_registered"] = bool(body.get("rotated")) and r.ok
        if not receipt["backend_registered"]:
            receipt["backend_error"] = str(body.get("error") or "rotate_failed")
            return {"ok": False, "error": "backend_rotate_failed", **receipt}
    except Exception as exc:
        receipt["backend_error"] = type(exc).__name__
        return {"ok": False, "error": "backend_unreachable", **receipt}

    # ---- 3. GitHub Actions repo secret (value via stdin, never argv) ----
    gh = _which("gh", "gh.exe") if repo is not None else None
    if repo is None:
        receipt["github_error"] = "repo_checkout_unavailable"
    elif not gh:
        receipt["github_error"] = "gh_cli_not_found"
    else:
        try:
            p = subprocess.run(
                [gh, "secret", "set", token_name, "--repo", repo_slug, "--body-file", "-"],
                input=token,
                capture_output=True,
                text=True,
                timeout=120,
            )
            receipt["github_secret_updated"] = p.returncode == 0
            if p.returncode != 0:
                receipt["github_error"] = (p.stderr or "")[-300:].replace(token, "***")
        except Exception as exc:
            receipt["github_error"] = type(exc).__name__

    # ---- 4. local non-versioned env for the test runner ----
    try:
        if repo is None:
            raise FileNotFoundError("repo_checkout_unavailable")
        env_path = repo / env_file
        receipt["local_env_action"] = _write_env_var(env_path, token_name, token)
        receipt["local_env_updated"] = True
        receipt["local_env_file"] = env_file  # relative only; no absolute path leak
    except Exception as exc:
        receipt["local_env_error"] = type(exc).__name__

    # ---- 5. run the integration suite ----
    if run_tests and receipt["local_env_updated"]:
        runner = _which("bun", "bun.exe")
        if not runner:
            receipt["tests_error"] = "bun_not_found"
        else:
            try:
                p = subprocess.run(
                    [runner, "run", test_script],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    timeout=900,
                )
                receipt["tests_ran"] = True
                receipt["tests_exit_code"] = p.returncode
                receipt["tests_passed"] = p.returncode == 0
                tail = ((p.stdout or "") + "\n" + (p.stderr or ""))[-4000:]
                receipt["tests_output_tail"] = tail.replace(token, "***")
            except subprocess.TimeoutExpired:
                receipt["tests_error"] = "timeout"
            except Exception as exc:
                receipt["tests_error"] = type(exc).__name__

    # Scrub: token must not survive past this point in any returned structure.
    del token

    receipt["ok"] = bool(receipt["backend_registered"])
    return receipt
