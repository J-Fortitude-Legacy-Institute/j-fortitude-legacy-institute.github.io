@echo off
REM ============================================================
REM Diagnostic launcher — keeps the window open so you can SEE
REM what went wrong. Double-click this instead of launch_unk.bat
REM when Unk closes instantly.
REM ============================================================
cd /d "%~dp0"

echo ============================================================
echo  Unk Diagnostic Launcher
echo  Folder: %cd%
echo ============================================================
echo.

echo [1/3] Checking Python...
where python
if errorlevel 1 (
  echo.
  echo  ^>^>^> PROBLEM: Python is not installed or not on PATH.
  echo  ^>^>^> Fix: install Python 3.11+ from https://python.org
  echo       During install, TICK "Add Python to PATH".
  echo.
  goto end
)
python --version
echo.

echo [2/3] Checking unk_companion.py exists...
if not exist unk_companion.py (
  echo  ^>^>^> PROBLEM: unk_companion.py is missing from this folder.
  goto end
)
echo  OK
echo.

echo [3/3] Starting unk_companion.py (errors will show below)...
echo ------------------------------------------------------------
python unk_companion.py
echo ------------------------------------------------------------
echo.
echo Companion exited with code %errorlevel%.

:end
echo.
echo ============================================================
echo  Window will stay open. Press any key to close.
echo ============================================================
pause >nul
