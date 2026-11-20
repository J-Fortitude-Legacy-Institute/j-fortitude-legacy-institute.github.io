@echo off
REM Legacy compatibility launcher. The old implementation kept a visible CMD
REM supervisor open and spawned more CMD worker windows after every restart.
REM Hand off immediately to the canonical hidden scheduled-task supervisor.
setlocal
cd /d "%~dp0"
set "HIDDEN=%~dp0UnkLaunchHidden.vbs"
>"%HIDDEN%" echo Set sh = CreateObject("WScript.Shell")
>>"%HIDDEN%" echo sh.Run "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""%~dp0install_supervisor.ps1"" -RepairOnly -SkipVerify", 0, True
>>"%HIDDEN%" echo sh.Run "schtasks.exe /Run /TN ""UnkSupervisor""", 0, False
start "" /b wscript.exe "%HIDDEN%"
exit /b 0
