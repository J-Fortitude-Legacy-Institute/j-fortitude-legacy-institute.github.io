#!/usr/bin/env python3
"""
Unk Window Policy — one place that decides whether Unk is allowed to put a
window on Jason's screen.

Problem this solves:
  Console windows (PowerShell / cmd / python helpers) and automation browser
  windows were popping up on top of whatever Jason was typing, stealing focus
  and cutting him off mid-sentence.

Doctrine:
  1. NO console window. Ever. Every child process on Windows launches with
     CREATE_NO_WINDOW + a hidden STARTUPINFO.
  2. Automation browsers still run in real (non-headless) mode — that is what
     keeps Facebook/LinkedIn/Instagram sessions working — but they open
     OFF-SCREEN and never take focus.
  3. The ONLY time a window is allowed on screen is when a human physically
     has to act (manual sign-in, CAPTCHA, certification). Those call sites
     pass visible_required=True and are the documented exception.

Override for debugging: set UNK_VISIBLE_BROWSER=1 to force every automation
browser back on screen.
"""

from __future__ import annotations

import os
import subprocess

# Windows CREATE_NO_WINDOW
CREATE_NO_WINDOW = 0x08000000

# Far off the left edge of any real monitor layout. Chromium honours this and
# the window is never composited onto a visible desktop area.
OFFSCREEN_POSITION = "--window-position=-32000,-32000"


def visible_browsers_forced() -> bool:
    return str(os.environ.get("UNK_VISIBLE_BROWSER", "")).strip() in ("1", "true", "yes")


def browser_args(base_args=None, *, visible_required: bool = False) -> list:
    """Return Chromium args with the window policy applied.

    visible_required=True is ONLY for human-gated flows (manual sign-in,
    CAPTCHA). Everything else is pushed off-screen so automation never
    interrupts what Jason is doing.
    """
    args = list(base_args or [])
    if visible_required or visible_browsers_forced():
        allow_visible_window(True, hold_seconds=900)
        # Chromium restores the LAST SAVED bounds from the persistent profile.
        # If a previous automation run parked that profile at -32000,-32000,
        # a human-gated window would relaunch off-screen and only show up as a
        # taskbar icon that cannot be clicked into view. Force on-screen bounds
        # AND run a short reverse-sweep that drags it back if Chromium wins.
        for extra in ("--window-position=120,80", "--window-size=1400,900"):
            if not any(a.startswith(extra.split("=")[0]) for a in args):
                args.append(extra)
        start_onscreen_rescue(900)
        return args
    allow_visible_window(False)
    start_offscreen_sweeper()
    for extra in (OFFSCREEN_POSITION, "--window-size=1400,900"):
        if not any(a.startswith(extra.split("=")[0]) for a in args):
            args.append(extra)
    return args


# ---------------------------------------------------------------------------
# Off-screen sweeper
#
# Chromium restores the LAST SAVED window bounds from the persistent profile,
# which silently overrides --window-position. That is why automation windows
# kept appearing on screen even after the args policy shipped. The sweeper is
# the enforcement layer: a background thread that continuously moves any
# Playwright-owned Chromium window off-screen without ever taking focus.
# ---------------------------------------------------------------------------

_SWEEPER_STARTED = False

# A *time-boxed hold* instead of a naked boolean. The boolean version caused
# the "window flashes" bug: any other automation call running in parallel hit
# browser_args(visible_required=False) -> allow_visible_window(False), which
# un-paused the sweeper. The sweeper then yanked Jason's sign-in window
# off-screen while the rescue thread dragged it back ~2x/second.
_VISIBLE_HOLD_UNTIL = 0.0

# HWNDs explicitly rescued for a human. The sweeper must NEVER touch these,
# even after the hold expires, or the window will vanish mid sign-in.
_PINNED_HWNDS: set = set()


def _visible_hold_active() -> bool:
    import time

    return time.time() < _VISIBLE_HOLD_UNTIL


def allow_visible_window(allowed: bool, hold_seconds: int = 900) -> None:
    """Pause/resume the sweeper for human-gated flows.

    allowed=True extends a time-boxed hold. allowed=False is ADVISORY: it can
    never cut an active hold short, so a background automation task cannot
    steal the screen back from a human sign-in that is still in progress.
    """
    global _VISIBLE_HOLD_UNTIL
    import time

    if allowed:
        _VISIBLE_HOLD_UNTIL = max(_VISIBLE_HOLD_UNTIL, time.time() + max(30, int(hold_seconds)))
    # allowed=False intentionally does nothing; holds expire on their own.


def restore_quiet_window_policy() -> None:
    """Re-enable off-screen enforcement after an explicit human-gated flow."""
    global _VISIBLE_HOLD_UNTIL
    _VISIBLE_HOLD_UNTIL = 0.0
    _PINNED_HWNDS.clear()
    start_offscreen_sweeper()


def _process_image_path(pid: int) -> str:
    import ctypes
    from ctypes import wintypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(4096)
        buf = ctypes.create_unicode_buffer(size.value)
        if k32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value
    finally:
        k32.CloseHandle(handle)
    return ""


def _sweep_once() -> int:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    SWP_NOSIZE = 0x0001
    SWP_NOZORDER = 0x0004
    SWP_NOACTIVATE = 0x0010

    moved = 0
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        nonlocal moved
        try:
            if int(hwnd) in _PINNED_HWNDS:
                return True  # human-gated window; never sweep it
            if not user32.IsWindowVisible(hwnd):
                return True
            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            if rect.left <= -20000:
                return True  # already parked off-screen
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            image = _process_image_path(pid.value).lower()
            if not image:
                return True
            # Only Playwright's bundled Chromium / Unk's own browser profile.
            if "ms-playwright" not in image and "unk_companion" not in image:
                return True
            user32.SetWindowPos(
                hwnd, 0, -32000, -32000, 0, 0,
                SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE,
            )
            moved += 1
        except Exception:
            pass
        return True

    user32.EnumWindows(EnumProc(callback), 0)
    return moved


def start_offscreen_sweeper() -> bool:
    """Start the background off-screen enforcement thread (idempotent)."""
    global _SWEEPER_STARTED
    if _SWEEPER_STARTED or os.name != "nt" or visible_browsers_forced():
        return False
    import threading
    import time

    def loop():
        while True:
            try:
                if not _visible_hold_active():
                    _sweep_once()
            except Exception:
                pass
            time.sleep(0.35)

    t = threading.Thread(target=loop, name="unk-offscreen-sweeper", daemon=True)
    t.start()
    _SWEEPER_STARTED = True
    return True


# ---------------------------------------------------------------------------
# On-screen rescue (reverse sweeper)
#
# Failure mode this fixes: a human-gated sign-in window launches but Chromium
# restores off-screen bounds from the persistent profile, so Jason sees a
# taskbar icon that "doesn't open" when clicked. This drags any parked
# Playwright/Unk Chromium window back to a visible position and restores it.
# ---------------------------------------------------------------------------


def rescue_offscreen_windows(*, focus: bool = True) -> int:
    """Move every off-screen Playwright/Unk Chromium window back on screen."""
    if os.name != "nt":
        return 0
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    SWP_NOSIZE = 0x0001
    SWP_NOZORDER = 0x0004
    SW_RESTORE = 9

    moved = 0
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        nonlocal moved
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            offscreen = rect.left <= -20000 or rect.top <= -20000
            too_small = width < 500 or height < 400
            minimized = bool(user32.IsIconic(hwnd))
            needs_fix = offscreen or too_small or minimized
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            image = _process_image_path(pid.value).lower()
            if "ms-playwright" not in image and "unk_companion" not in image:
                return True
            already_pinned = int(hwnd) in _PINNED_HWNDS
            _PINNED_HWNDS.add(int(hwnd))
            if not needs_fix:
                return True  # healthy and now pinned; leave it alone
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetWindowPos(hwnd, 0, 120, 80, 1400, 900, SWP_NOZORDER)
            # Focus exactly once per window, on first rescue only.
            if focus and not already_pinned:
                user32.SetForegroundWindow(hwnd)
            moved += 1
        except Exception:
            pass
        return True


    user32.EnumWindows(EnumProc(callback), 0)
    return moved


_RESCUE_RUNNING = False


def start_onscreen_rescue(duration_seconds: int = 180) -> bool:
    """Keep pulling human-gated windows on screen for a short window of time.

    Only ONE rescue thread ever runs (stacked threads were part of the flash),
    and each window is repositioned only while it is actually off-screen.
    """
    global _RESCUE_RUNNING
    if os.name != "nt" or _RESCUE_RUNNING:
        return False
    import threading
    import time

    allow_visible_window(True, hold_seconds=max(60, int(duration_seconds)))

    def loop():
        global _RESCUE_RUNNING
        deadline = time.time() + max(10, int(duration_seconds))
        try:
            while time.time() < deadline:
                try:
                    if _visible_hold_active():
                        rescue_offscreen_windows(focus=False)
                except Exception:
                    pass
                time.sleep(1.5)
        finally:
            _RESCUE_RUNNING = False

    _RESCUE_RUNNING = True
    threading.Thread(target=loop, name="unk-onscreen-rescue", daemon=True).start()
    return True



def quiet_startupinfo():
    """Hidden STARTUPINFO for Windows child processes."""
    if os.name != "nt":
        return None
    try:
        si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
        si.wShowWindow = 0  # SW_HIDE
        return si
    except Exception:
        return None


def quiet_kwargs(kwargs: dict) -> dict:
    """Inject no-window flags into subprocess kwargs (idempotent)."""
    if os.name != "nt":
        return kwargs
    try:
        kwargs["creationflags"] = int(kwargs.get("creationflags") or 0) | CREATE_NO_WINDOW
        if kwargs.get("startupinfo") is None:
            si = quiet_startupinfo()
            if si is not None:
                kwargs["startupinfo"] = si
    except Exception:
        pass
    return kwargs


_INSTALLED = False


def install_quiet_subprocess() -> bool:
    """Globally wrap subprocess.run/Popen/call/check_output so no child process
    can flash a console window. Safe to call from every entrypoint; only the
    first call patches."""
    global _INSTALLED
    if _INSTALLED or os.name != "nt":
        _INSTALLED = True
        return False

    # Enforcement layer for automation browser windows.
    start_offscreen_sweeper()

    orig_run = subprocess.run
    orig_call = subprocess.call
    orig_check_output = subprocess.check_output
    orig_popen = subprocess.Popen


    def run(*args, **kwargs):
        return orig_run(*args, **quiet_kwargs(kwargs))

    def call(*args, **kwargs):
        return orig_call(*args, **quiet_kwargs(kwargs))

    def check_output(*args, **kwargs):
        return orig_check_output(*args, **quiet_kwargs(kwargs))

    class QuietPopen(orig_popen):  # type: ignore[misc,valid-type]
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **quiet_kwargs(kwargs))

    subprocess.run = run  # type: ignore[assignment]
    subprocess.call = call  # type: ignore[assignment]
    subprocess.check_output = check_output  # type: ignore[assignment]
    subprocess.Popen = QuietPopen  # type: ignore[assignment]
    _INSTALLED = True
    return True
