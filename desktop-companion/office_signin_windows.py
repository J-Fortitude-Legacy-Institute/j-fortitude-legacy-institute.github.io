"""office_signin_windows.py — park two visible, signed-out browser tabs in
Unk's persistent Chromium profile so Jason can clear both remaining human
gates in one sitting at the office machine:

  1. Google Cloud Console  -> unblocks the Drive service-account mint
  2. ChatGPT               -> restores the ChatGPT session for plan checks

The script NEVER types a password, never reads one, and never logs page
content. It only opens the tabs, waits for the session cookies to appear, and
writes a small receipt with booleans + timestamps.

Usage:
    python office_signin_windows.py [--hold-hours 8]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CONFIG_DIR = Path.home() / ".unk_companion"
PROFILE_DIR = CONFIG_DIR / "browser_profile"
RECEIPT = CONFIG_DIR / "office_signin_receipt.json"

TARGETS = [
    ("google_cloud", "https://console.cloud.google.com/", ("SID", "__Secure-1PSID")),
    ("chatgpt", "https://chatgpt.com/", ("__Secure-next-auth.session-token", "__Session")),
]


def hold_hours() -> float:
    if "--hold-hours" in sys.argv:
        try:
            return float(sys.argv[sys.argv.index("--hold-hours") + 1])
        except Exception:
            pass
    return 8.0


def emit(receipt: dict) -> None:
    receipt["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(receipt, indent=2)[:4000])


def signed_in(cookies: list, names: tuple) -> bool:
    have = {c.get("name") for c in cookies}
    return any(n in have for n in names)


def main() -> int:
    receipt: dict = {"ok": False, "stage": "start", "targets": {}}

    try:
        from meta_browser_publisher import _ensure_playwright_ready, profile_lock  # type: ignore
    except Exception as exc:
        receipt["error"] = f"publisher_import_failed:{exc}"
        emit(receipt)
        return 2

    notes: list[str] = []
    ok, err = _ensure_playwright_ready(notes)
    if not ok:
        receipt["error"] = f"playwright_not_ready:{err}"
        receipt["notes"] = notes
        emit(receipt)
        return 3

    from playwright.sync_api import sync_playwright  # type: ignore

    deadline = time.time() + hold_hours() * 3600

    try:
        with profile_lock(owner="office_signin", timeout_s=120):
            try:
                from unk_window_policy import allow_visible_window, start_onscreen_rescue  # type: ignore

                allow_visible_window(True, int(hold_hours() * 3600))
                start_onscreen_rescue(int(hold_hours() * 3600))
            except Exception:
                pass

            with sync_playwright() as pw:
                ctx = pw.chromium.launch_persistent_context(
                    str(PROFILE_DIR),
                    headless=False,
                    args=["--start-maximized", "--no-first-run"],
                    viewport=None,
                )
                pages = []
                for key, url, _names in TARGETS:
                    page = ctx.pages[0] if (not pages and ctx.pages) else ctx.new_page()
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    except Exception as exc:
                        notes.append(f"{key}_nav_warning:{str(exc)[:120]}")
                    pages.append((key, page))

                receipt["stage"] = "waiting_for_human"
                receipt["profile_dir"] = str(PROFILE_DIR)
                receipt["notes"] = notes
                emit(receipt)

                done: dict[str, bool] = {k: False for k, _u, _n in TARGETS}
                while time.time() < deadline:
                    cookies = ctx.cookies()
                    for key, _url, names in TARGETS:
                        if not done[key] and signed_in(cookies, names):
                            done[key] = True
                            receipt["targets"][key] = {
                                "signed_in": True,
                                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            }
                            emit(receipt)
                    if all(done.values()):
                        break
                    time.sleep(10)

                for key in done:
                    receipt["targets"].setdefault(key, {"signed_in": done[key]})
                receipt["ok"] = all(done.values())
                receipt["stage"] = "done" if receipt["ok"] else "timed_out"
                emit(receipt)

                try:
                    ctx.close()
                except Exception:
                    pass
    except Exception as exc:
        receipt["error"] = f"signin_window_failed:{str(exc)[:200]}"
        receipt["stage"] = "error"
        emit(receipt)
        return 4

    return 0 if receipt.get("ok") else 5


if __name__ == "__main__":
    raise SystemExit(main())
