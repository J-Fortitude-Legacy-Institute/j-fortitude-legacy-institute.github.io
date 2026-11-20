@echo off
REM ================================================================
REM  Unk Supervisor Installer (one-click UAC launcher)
REM  Double-click this file. Windows will show a UAC prompt asking
REM  to allow PowerShell to make changes. Click YES.
REM  That's the only click. The installer registers UnkSupervisor,
REM  UnkSupervisorKeepAlive, and the Startup fallback, then exits.
REM ================================================================
setlocal
set "PS=%LOCALAPPDATA%\UnkCompanion\install_supervisor.ps1"

if not exist "%PS%" (
  echo.
  echo [!] Durable installer not found at:
  echo     %PS%
  echo.
  echo Extract desktop-companion.zip into %LOCALAPPDATA%\UnkCompanion
  echo and try again.
  echo.
  pause
  exit /b 1
)

echo.
echo Launching Unk supervisor installer...
echo Windows will show a UAC prompt in a moment. Click YES.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS%"
set RC=%ERRORLEVEL%

echo.
echo Installer exit code: %RC%
echo (If you saw "UnkSupervisor" and "UnkSupervisorKeepAlive" registered above, you're done.)
pause
exit /b %RC%
