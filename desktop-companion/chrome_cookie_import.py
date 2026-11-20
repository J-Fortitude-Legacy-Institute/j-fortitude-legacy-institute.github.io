"""Import cookies from the operator's real desktop browser into Unk's profile.

Why this exists: Unk drives a dedicated Playwright Chromium profile
(``~/.unk_companion/browser_profile``). When Jason signs in to LinkedIn in his
own Chrome window, that session lives in a DIFFERENT cookie jar, so Unk still
sees a logged-out browser. Rather than asking Jason to sign in a second time
inside a browser he never opens, Unk reads the cookies he already has and
injects them into its own context.

Windows specifics: Chromium stores cookie values encrypted with an AES-256-GCM
key that is itself DPAPI-protected under the logged-in Windows user. Unk runs as
that same user, so ``CryptUnprotectData`` succeeds without any prompt.

Everything fails soft — a missing browser, a locked DB, or a missing
``cryptography`` package returns a structured reason instead of raising.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


# Chromium epoch (1601-01-01) -> unix seconds
_CHROME_EPOCH_OFFSET = 11644473600


def _candidate_user_data_dirs() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    local = os.environ.get("LOCALAPPDATA")
    appdata = os.environ.get("APPDATA")
    if local:
        base = Path(local)
        out += [
            ("chrome", base / "Google" / "Chrome" / "User Data"),
            ("edge", base / "Microsoft" / "Edge" / "User Data"),
            ("brave", base / "BraveSoftware" / "Brave-Browser" / "User Data"),
            ("chrome_beta", base / "Google" / "Chrome Beta" / "User Data"),
        ]
    if appdata:
        out.append(("opera", Path(appdata) / "Opera Software" / "Opera Stable"))
    # macOS / Linux fallbacks (values are usually unencrypted or keychain-backed)
    home = Path.home()
    out += [
        ("chrome_mac", home / "Library" / "Application Support" / "Google" / "Chrome"),
        ("chrome_linux", home / ".config" / "google-chrome"),
    ]
    return [(name, p) for name, p in out if p.exists()]


def _dpapi_unprotect(blob: bytes) -> bytes | None:
    try:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

        buf_in = DATA_BLOB(len(blob), ctypes.cast(ctypes.create_string_buffer(blob), ctypes.POINTER(ctypes.c_char)))
        buf_out = DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(buf_in), None, None, None, None, 0, ctypes.byref(buf_out)
        )
        if not ok:
            return None
        data = ctypes.string_at(buf_out.pbData, buf_out.cbData)
        ctypes.windll.kernel32.LocalFree(buf_out.pbData)
        return data
    except Exception:
        return None


def _load_master_key(user_data_dir: Path) -> bytes | None:
    local_state = user_data_dir / "Local State"
    if not local_state.exists():
        return None
    try:
        state = json.loads(local_state.read_text(encoding="utf-8", errors="ignore"))
        enc = base64.b64decode(state["os_crypt"]["encrypted_key"])
    except Exception:
        return None
    if enc[:5] != b"DPAPI":
        return None
    return _dpapi_unprotect(enc[5:])


def _load_aesgcm():
    """Import AESGCM, self-installing `cryptography` once if it is missing."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM
    except Exception:
        pass
    try:
        import subprocess
        import sys

        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet",
             "--disable-pip-version-check", "cryptography"],
            check=False, timeout=300,
        )
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM
    except Exception:
        return None


def _decrypt_value(encrypted: bytes, key: bytes | None, plaintext: str) -> str | None:

    if plaintext:
        return plaintext
    if not encrypted:
        return None
    try:
        if encrypted[:3] in (b"v10", b"v11") and key:
            AESGCM = _load_aesgcm()
            if AESGCM is None:
                return None
            nonce, payload = encrypted[3:15], encrypted[15:]
            return AESGCM(key).decrypt(nonce, payload, None).decode("utf-8", "ignore")

        # Legacy DPAPI-only value
        dec = _dpapi_unprotect(encrypted)
        return dec.decode("utf-8", "ignore") if dec else None
    except Exception:
        return None


def _profile_cookie_dbs(user_data_dir: Path) -> list[Path]:
    dbs: list[Path] = []
    for prof in ["Default"] + [p.name for p in user_data_dir.glob("Profile *") if p.is_dir()]:
        for rel in ("Network/Cookies", "Cookies"):
            candidate = user_data_dir / prof / rel
            if candidate.exists():
                dbs.append(candidate)
                break
    return dbs


def _copy_locked_file(source: Path, destination: Path, notes: list[str], label: str) -> bool:
    """Copy a Chromium SQLite file without stopping the operator's browser.

    Windows can deny CopyFile while Chrome has the cookie database open.
    esentutl's raw-copy mode uses backup semantics and can snapshot that file
    without closing Chrome. This remains read-only against the host profile.
    """
    try:
        shutil.copy2(source, destination)
        return True
    except Exception as exc:
        notes.append(f"copy_failed:{label}:{exc}")

    if os.name != "nt":
        return False
    try:
        completed = subprocess.run(
            ["esentutl.exe", "/y", str(source), "/d", str(destination), "/o"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode == 0 and destination.exists():
            notes.append(f"locked_copy_ok:{label}:esentutl")
            return True
        detail = (completed.stderr or completed.stdout or "unknown").strip().replace("\n", " ")[:240]
        notes.append(f"locked_copy_failed:{label}:{completed.returncode}:{detail}")
    except Exception as exc:
        notes.append(f"locked_copy_failed:{label}:{exc}")
    return False


def _snapshot_cookie_db(db_path: Path, snapshot: Path, notes: list[str], browser: str) -> bool:
    """Create a consistent SQLite snapshot, including Chrome's WAL sidecars."""
    if not _copy_locked_file(db_path, snapshot, notes, f"{browser}:db"):
        return False
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists():
            _copy_locked_file(sidecar, Path(f"{snapshot}{suffix}"), notes, f"{browser}:{suffix[1:]}")
    return True


def _remove_snapshot(snapshot: Path) -> None:
    for suffix in ("", "-wal", "-shm", "-journal"):
        try:
            Path(f"{snapshot}{suffix}").unlink(missing_ok=True)
        except Exception:
            pass


def collect_cookies(domain_substrings: list[str]) -> dict:
    """Return {ok, cookies:[playwright cookie dicts], sources:[...], notes:[...]}"""
    wanted = [d.lower().lstrip(".") for d in domain_substrings if d]
    result: dict = {"ok": False, "cookies": [], "sources": [], "notes": []}
    seen: set[tuple[str, str, str]] = set()

    for browser, udd in _candidate_user_data_dirs():
        key = _load_master_key(udd)
        for db_path in _profile_cookie_dbs(udd):
            rows = None
            tmp = Path(tempfile.gettempdir()) / f"unk_cookies_{browser}_{abs(hash(str(db_path)))}.db"
            SQL = ("SELECT host_key, name, value, encrypted_value, path, expires_utc, "
                   "is_secure, is_httponly FROM cookies")
            # Snapshot the database plus WAL before reading it. This preserves
            # the operator's open Chrome session and does not interrupt any
            # publishing lane.
            try:
                if _snapshot_cookie_db(db_path, tmp, result["notes"], browser):
                    con = sqlite3.connect(f"file:{tmp.as_posix()}?mode=ro", uri=True)
                    try:
                        rows = con.execute(SQL).fetchall()
                    finally:
                        con.close()
            except Exception as e:
                result["notes"].append(f"snapshot_read_failed:{browser}:{e}")
            finally:
                _remove_snapshot(tmp)
            if rows is None:
                for uri in (f"file:{db_path.as_posix()}?immutable=1",
                            f"file:{db_path.as_posix()}?mode=ro&nolock=1"):
                    try:
                        con = sqlite3.connect(uri, uri=True)
                        rows = con.execute(SQL).fetchall()
                        con.close()
                        result["notes"].append(f"locked_db_read_ok:{browser}")
                        break
                    except Exception as e:
                        result["notes"].append(f"read_failed:{browser}:{e}")
            if rows is None:
                continue


            found_here = 0
            for host, name, value, enc, path, expires, secure, httponly in rows:
                h = (host or "").lower()
                if not any(w in h for w in wanted):
                    continue
                plain = _decrypt_value(enc or b"", key, value or "")
                if not plain:
                    continue
                dedupe = (h, name, path or "/")
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                cookie = {
                    "name": name,
                    "value": plain,
                    "domain": host,
                    "path": path or "/",
                    "secure": bool(secure),
                    "httpOnly": bool(httponly),
                    "sameSite": "Lax",
                }
                if expires:
                    exp = int(expires) / 1_000_000 - _CHROME_EPOCH_OFFSET
                    if exp > 0:
                        cookie["expires"] = exp
                result["cookies"].append(cookie)
                found_here += 1
            if found_here:
                result["sources"].append({"browser": browser, "db": str(db_path), "cookies": found_here})

    result["ok"] = bool(result["cookies"])
    if not result["ok"] and not result["notes"]:
        result["notes"].append("no_matching_cookies_found")
    return result


def import_into_context(context, domain_substrings: list[str]) -> dict:
    """Collect host-browser cookies and add them to a Playwright context."""
    collected = collect_cookies(domain_substrings)
    if not collected["ok"]:
        return collected
    try:
        context.add_cookies(collected["cookies"])
        collected["injected"] = len(collected["cookies"])
    except Exception as e:
        # Retry one-by-one: a single malformed cookie must not kill the import.
        injected = 0
        for c in collected["cookies"]:
            try:
                context.add_cookies([c])
                injected += 1
            except Exception:
                continue
        collected["injected"] = injected
        collected["notes"].append(f"bulk_add_failed:{e}")
        collected["ok"] = injected > 0
    return collected


def import_via_chrome_clone(playwright, target_context, domain_substrings: list[str]) -> dict:
    """Let installed Chrome decrypt its own app-bound (``v20``) cookies.

    Current Chrome releases intentionally prevent non-Chrome processes from
    decrypting these values.  We therefore create a small, read-only working
    clone of each host profile, launch the installed Chrome binary against the
    clone, ask Chrome for the decrypted cookie jar through Playwright, and add
    only the requested domains to Unk's persistent context.  The operator's
    live browser is never closed or modified.
    """
    wanted = [d.lower().lstrip(".") for d in domain_substrings if d]
    result: dict = {"ok": False, "injected": 0, "sources": [], "notes": []}
    if not wanted:
        result["notes"].append("no_domains_requested")
        return result

    for browser, user_data_dir in _candidate_user_data_dirs():
        if browser not in {"chrome", "chrome_beta", "edge", "brave"}:
            continue
        local_state = user_data_dir / "Local State"
        if not local_state.exists():
            continue

        for db_path in _profile_cookie_dbs(user_data_dir):
            try:
                profile_dir = db_path.parent.parent if db_path.parent.name == "Network" else db_path.parent
                profile_name = profile_dir.name
                clone_root = Path(tempfile.mkdtemp(prefix=f"unk_{browser}_cookie_clone_"))
                clone_profile = clone_root / profile_name
                (clone_profile / "Network").mkdir(parents=True, exist_ok=True)
                shutil.copy2(local_state, clone_root / "Local State")
                for name in ("Preferences", "Secure Preferences"):
                    source = profile_dir / name
                    if source.exists():
                        try:
                            shutil.copy2(source, clone_profile / name)
                        except Exception as exc:
                            result["notes"].append(f"profile_file_copy_failed:{browser}:{profile_name}:{name}:{exc}")

                clone_db = clone_profile / "Network" / "Cookies"
                if not _snapshot_cookie_db(db_path, clone_db, result["notes"], f"{browser}:{profile_name}"):
                    shutil.rmtree(clone_root, ignore_errors=True)
                    continue

                channel = "msedge" if browser == "edge" else "chrome"
                browser_context = None
                try:
                    browser_context = playwright.chromium.launch_persistent_context(
                        user_data_dir=str(clone_root),
                        channel=channel,
                        headless=True,
                        args=_win_browser_args([f"--profile-directory={profile_name}", "--disable-extensions"]),
                    )
                    page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
                    home = "https://www.linkedin.com/feed/" if any("linkedin.com" in d for d in wanted) else "https://www.instagram.com/"
                    try:
                        page.goto(home, wait_until="domcontentloaded", timeout=45000)
                        time.sleep(3)
                    except Exception as exc:
                        result["notes"].append(f"chrome_clone_goto_failed:{browser}:{profile_name}:{exc}")
                    cookies = browser_context.cookies()
                    matching = [
                        c for c in cookies
                        if any(w in str(c.get("domain", "")).lower().lstrip(".") for w in wanted)
                    ]
                    if matching:
                        target_context.add_cookies(matching)
                        result["injected"] += len(matching)
                        names = {str(c.get("name", "")) for c in matching}
                        result["sources"].append({
                            "browser": browser,
                            "profile": profile_name,
                            "cookies": len(matching),
                            "auth_cookie_present": "li_at" in names or "sessionid" in names,
                        })
                except Exception as exc:
                    result["notes"].append(f"chrome_clone_failed:{browser}:{profile_name}:{exc}")
                finally:
                    if browser_context is not None:
                        try:
                            browser_context.close()
                        except Exception:
                            pass
                    shutil.rmtree(clone_root, ignore_errors=True)
            except Exception as exc:
                result["notes"].append(f"chrome_clone_setup_failed:{browser}:{exc}")

    result["ok"] = result["injected"] > 0
    if not result["ok"] and not result["notes"]:
        result["notes"].append("chrome_clone_no_matching_cookies")
    return result
