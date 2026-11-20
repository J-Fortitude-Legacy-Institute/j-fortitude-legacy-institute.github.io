# install_supervisor.ps1 — one-time durable install for the Unk supervisor.
# Registers self-healing Scheduled Tasks:
#   - UnkSupervisor runs unk_supervisor.py under the signed-in user session.
#   - UnkSupervisorKeepAlive runs every 5 minutes and restarts/recreates
#     UnkSupervisor if Windows stops it, the task disappears, or its marker
#     goes stale.
#   - UnkSupervisorBootKeepAlive runs as SYSTEM at startup when the installer
#     has elevation; it repairs/starts the user-session supervisor as soon as
#     Windows has an interactive session available.
# Also installs a Startup-folder fallback that runs the keepalive script.
#
# Run from inside the extracted desktop-companion folder:
#   powershell -ExecutionPolicy Bypass -File .\install_supervisor.ps1
#
# Important: verification failure no longer removes the scheduled tasks. If
# network, auth, or dependencies are temporarily bad, the keepalive remains
# installed and keeps retrying instead of leaving Ground Zero permanently dead.
param(
  [switch]$Uninstall,
  [switch]$RepairOnly,
  [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# --- Self-relocate out of %TEMP% -------------------------------------------------
# Windows wipes %TEMP% on updates / Storage Sense / some sign-ins. If the installer
# was launched from an extracted zip in Temp, the resulting Scheduled Task would
# point to a folder that vanishes — which is exactly why Unk keeps "breaking every
# time I sign in." Copy the whole desktop-companion folder to a durable location
# and re-launch ourselves from there before registering anything.
$DurableRoot = Join-Path $env:LOCALAPPDATA "UnkCompanion"
$currentPath = $PSScriptRoot
$isTempPath = ($currentPath -like "*\Temp\*") -or ($currentPath -like "$env:TEMP*") -or ($currentPath -like "$env:TMP*")
if ($isTempPath -and -not $RepairOnly) {
  Write-Host "==> Detected install running from %TEMP%. Relocating to $DurableRoot so Unk survives reboots and temp cleanup." -ForegroundColor Cyan
  try {
    if (Test-Path $DurableRoot) {
      # Remove old copy so we get a clean set of files (preserves ~/.unk-companion state dir, which is elsewhere).
      Remove-Item -Path $DurableRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Force -Path $DurableRoot | Out-Null
    Copy-Item -Path (Join-Path $currentPath "*") -Destination $DurableRoot -Recurse -Force
    $durableInstaller = Join-Path $DurableRoot "install_supervisor.ps1"
    if (Test-Path $durableInstaller) {
      Write-Host "==> Re-launching installer from durable path: $durableInstaller" -ForegroundColor Cyan
      $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$durableInstaller`"")
      if ($SkipVerify) { $argList += "-SkipVerify" }
      & powershell.exe @argList
      exit $LASTEXITCODE
    }
  } catch {
    Write-Host "==> Relocate failed ($($_.Exception.Message)); continuing from current path but Unk may break again on next temp cleanup." -ForegroundColor Yellow
  }
}


# --- Self-elevate if scheduled-task registration would require admin ---------
# On some Windows configurations Register-ScheduledTask against the root task
# path is denied for non-admin users (HRESULT 0x80070005). Unk runs unelevated
# by design, so when we detect we are not already admin we re-launch this
# installer via Start-Process -Verb RunAs. That triggers a UAC prompt for the
# interactive user; after they approve, the elevated copy registers the tasks
# and returns. RepairOnly runs (invoked by unk_keepalive) do NOT self-elevate
# — they stay unelevated and simply skip if they cannot write.
if (-not $RepairOnly) {
  try {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    $isCurrentAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { $isCurrentAdmin = $false }
  if (-not $isCurrentAdmin) {
    Write-Host "==> Not running elevated. Requesting UAC approval to register scheduled tasks..." -ForegroundColor Yellow
    $selfPath = $MyInvocation.MyCommand.Path
    if (-not $selfPath) { $selfPath = Join-Path $PSScriptRoot "install_supervisor.ps1" }
    $argList = @("-NoProfile","-ExecutionPolicy","Bypass","-File","`"$selfPath`"")
    if ($SkipVerify) { $argList += "-SkipVerify" }
    try {
      $proc = Start-Process -FilePath "powershell.exe" -ArgumentList $argList -Verb RunAs -Wait -PassThru
      Write-Host "==> Elevated installer exit code: $($proc.ExitCode)" -ForegroundColor Cyan
      exit $proc.ExitCode
    } catch {
      Write-Host "==> UAC approval declined or elevation failed: $($_.Exception.Message)" -ForegroundColor Red
      exit 1223  # ERROR_CANCELLED
    }
  }
}


$TaskName = "UnkSupervisor"
$KeepAliveTaskName = "UnkSupervisorKeepAlive"
$StartupFolder = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$StartupFallback = Join-Path $StartupFolder "UnkSupervisorKeepAlive.vbs"
$StartupFallbackLegacy = Join-Path $StartupFolder "UnkSupervisorKeepAlive.cmd"
$SupervisorLauncher = Join-Path $PSScriptRoot "UnkSupervisorHidden.vbs"
$KeepAliveLauncher = Join-Path $PSScriptRoot "UnkKeepAliveHidden.vbs"
$BootKeepAliveLauncher = Join-Path $PSScriptRoot "UnkBootKeepAliveHidden.vbs"

$StateDir = Join-Path $env:USERPROFILE ".unk-companion"
$KeepAliveLog = Join-Path $StateDir "keepalive.log"

function Write-InstallLog([string]$Message, [string]$Color = "Gray") {
  Write-Host $Message -ForegroundColor $Color
  try {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    "[$(Get-Date -Format o)] $Message" | Add-Content -Path $KeepAliveLog -Encoding UTF8
  } catch {}
}

function Get-PythonExe {
  # Prefer pythonw.exe so the supervisor runs windowless (no black console flash on logon
  # or on every restart). Fall back to python.exe / py.exe if pythonw is not present.
  $pyw = (Get-Command pythonw -ErrorAction SilentlyContinue)
  if ($pyw) { return $pyw.Source }
  $python = (Get-Command python -ErrorAction SilentlyContinue)
  if ($python) {
    $pywGuess = Join-Path (Split-Path $python.Source -Parent) "pythonw.exe"
    if (Test-Path $pywGuess) { return $pywGuess }
    return $python.Source
  }
  $py = (Get-Command py -ErrorAction SilentlyContinue)
  if ($py) { return $py.Source }
  return $null
}


function Register-UnkSupervisorTask([string]$PyExe, [string]$SupervisorPath) {
  # Keep wscript alive while Python runs so Task Scheduler accurately reports
  # Running, but use window style 0 so no console can flash or remain open.
  $escapedPy = $PyExe.Replace('"', '""')
  $escapedSupervisor = $SupervisorPath.Replace('"', '""')
  @"
Set WshShell = CreateObject("WScript.Shell")
exitCode = WshShell.Run("""$escapedPy"" ""$escapedSupervisor""", 0, True)
WScript.Quit exitCode
"@ | Set-Content -Path $SupervisorLauncher -Encoding ASCII
  $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$SupervisorLauncher`"" -WorkingDirectory $PSScriptRoot
  $triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),
    (New-ScheduledTaskTrigger -AtStartup)
  )
  $settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 999 `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -WakeToRun `
    -Hidden
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers `
    -Settings $settings -Principal $principal -Force | Out-Null

  # Add workstation-unlock as an event trigger. PowerShell's ScheduledTasks
  # cmdlets do not expose unlock triggers directly, so patch the task XML.
  try {
    $xml = [xml](Export-ScheduledTask -TaskName $TaskName)
    $ns = $xml.Task.NamespaceURI
    $hasUnlock = $false
    foreach ($t in $xml.Task.Triggers.ChildNodes) {
      if ($t.Name -eq 'SessionStateChangeTrigger' -and $t.StateChange -eq 'SessionUnlock') { $hasUnlock = $true }
    }
    if (-not $hasUnlock) {
      $unlock = $xml.CreateElement('SessionStateChangeTrigger', $ns)
      $enabled = $xml.CreateElement('Enabled', $ns); $enabled.InnerText = 'true'; $unlock.AppendChild($enabled) | Out-Null
      $user = $xml.CreateElement('UserId', $ns); $user.InnerText = "$env:USERDOMAIN\$env:USERNAME"; $unlock.AppendChild($user) | Out-Null
      $state = $xml.CreateElement('StateChange', $ns); $state.InnerText = 'SessionUnlock'; $unlock.AppendChild($state) | Out-Null
      $xml.Task.Triggers.AppendChild($unlock) | Out-Null
      Register-ScheduledTask -TaskName $TaskName -Xml $xml.OuterXml -Force | Out-Null
    }
  } catch {
    Write-InstallLog "==> Unlock trigger patch warning for ${TaskName}: $($_.Exception.Message)" "Yellow"
  }
}

function Register-UnkKeepAliveTask([string]$KeepAlivePath) {
  if (-not (Test-Path $KeepAlivePath)) { return }
  $escapedKeepAlive = $KeepAlivePath.Replace('"', '""')
  @"
Set WshShell = CreateObject("WScript.Shell")
exitCode = WshShell.Run("powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$escapedKeepAlive""", 0, True)
WScript.Quit exitCode
"@ | Set-Content -Path $KeepAliveLauncher -Encoding ASCII
  $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$KeepAliveLauncher`"" -WorkingDirectory $PSScriptRoot
  $repeatTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
  $triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),
    $repeatTrigger
  )
  $settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 3) `
    -WakeToRun `
    -Hidden
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $KeepAliveTaskName -Action $action -Trigger $triggers `
    -Settings $settings -Principal $principal -Force | Out-Null

  try {
    $xml = [xml](Export-ScheduledTask -TaskName $KeepAliveTaskName)
    $ns = $xml.Task.NamespaceURI
    $unlock = $xml.CreateElement('SessionStateChangeTrigger', $ns)
    $enabled = $xml.CreateElement('Enabled', $ns); $enabled.InnerText = 'true'; $unlock.AppendChild($enabled) | Out-Null
    $user = $xml.CreateElement('UserId', $ns); $user.InnerText = "$env:USERDOMAIN\$env:USERNAME"; $unlock.AppendChild($user) | Out-Null
    $state = $xml.CreateElement('StateChange', $ns); $state.InnerText = 'SessionUnlock'; $unlock.AppendChild($state) | Out-Null
    $xml.Task.Triggers.AppendChild($unlock) | Out-Null
    Register-ScheduledTask -TaskName $KeepAliveTaskName -Xml $xml.OuterXml -Force | Out-Null
  } catch {
    Write-InstallLog "==> Unlock trigger patch warning for ${KeepAliveTaskName}: $($_.Exception.Message)" "Yellow"
  }
}

function Register-UnkSystemBootKeepAlive([string]$KeepAlivePath) {
  if (-not (Test-Path $KeepAlivePath)) { return }
  try {
    $isAdmin = $false
    try {
      $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
      $principal = New-Object Security.Principal.WindowsPrincipal($identity)
      $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {}
    if (-not $isAdmin) {
      Write-InstallLog "==> System boot keepalive skipped; rerun 'Run installer as admin' to add boot-level repair." "Yellow"
      return
    }
    $bootTaskName = "UnkSupervisorBootKeepAlive"
    $repairPath = Join-Path $PSScriptRoot "repair_persistence.ps1"
    $escapedKeepAlive = $KeepAlivePath.Replace('"', '""')
    if (Test-Path $repairPath) {
      $escapedRepair = $repairPath.Replace('"', '""')
      $bootCommand = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -Command ""& '$escapedRepair' -Apply -ActionId boot_keepalive; & '$escapedKeepAlive'"""
    } else {
      $bootCommand = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$escapedKeepAlive"""
    }
    @"
Set WshShell = CreateObject("WScript.Shell")
exitCode = WshShell.Run("$bootCommand", 0, True)
WScript.Quit exitCode
"@ | Set-Content -Path $BootKeepAliveLauncher -Encoding ASCII
    $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$BootKeepAliveLauncher`"" -WorkingDirectory $PSScriptRoot
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet `
      -AllowStartIfOnBatteries `
      -DontStopIfGoingOnBatteries `
      -StartWhenAvailable `
      -ExecutionTimeLimit (New-TimeSpan -Minutes 3) `
      -WakeToRun `
      -Hidden
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    Register-ScheduledTask -TaskName $bootTaskName -Action $action -Trigger $trigger `
      -Settings $settings -Principal $principal -Force | Out-Null
    Write-InstallLog "==> Registered SYSTEM boot keepalive $bootTaskName" "Cyan"
  } catch {
    Write-InstallLog "==> System boot keepalive install warning: $($_.Exception.Message)" "Yellow"
  }
}

function Install-StartupFallback([string]$KeepAlivePath) {
  if (-not (Test-Path $KeepAlivePath)) { return }
  New-Item -ItemType Directory -Force -Path $StartupFolder | Out-Null
  # Legacy .cmd flashed a black console window on every logon. Replace with a
  # WScript shim (Run flag 0 = hidden) so nothing appears on screen.
  try { Remove-Item -Path $StartupFallbackLegacy -Force -ErrorAction SilentlyContinue } catch {}
  $psCmd = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$KeepAlivePath"""
  @"
' UnkSupervisorKeepAlive.vbs — runs the PowerShell keepalive with no visible window.
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "$psCmd", 0, False
"@ | Set-Content -Path $StartupFallback -Encoding ASCII
}


if ($Uninstall) {
  Write-InstallLog "==> Removing scheduled tasks $TaskName / $KeepAliveTaskName" "Yellow"
  try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop } catch { Write-Host "Task not present." }
  try { Unregister-ScheduledTask -TaskName $KeepAliveTaskName -Confirm:$false -ErrorAction Stop } catch { Write-Host "Keepalive task not present." }
  try { Unregister-ScheduledTask -TaskName "UnkSupervisorBootKeepAlive" -Confirm:$false -ErrorAction Stop } catch { Write-Host "Boot keepalive task not present." }
  try { Remove-Item -Path $StartupFallback -Force -ErrorAction SilentlyContinue } catch {}
  try { Remove-Item -Path $StartupFallbackLegacy,$SupervisorLauncher,$KeepAliveLauncher,$BootKeepAliveLauncher -Force -ErrorAction SilentlyContinue } catch {}
  Write-Host "Done."; exit 0
}

# 1. Find Python
$pyExe = Get-PythonExe
if (-not $pyExe) {
  Write-Host "Python not found. Install Python 3 from https://python.org and re-run." -ForegroundColor Red
  exit 1
}
$supervisorPath = Join-Path $PSScriptRoot "unk_supervisor.py"
$keepAlivePath = Join-Path $PSScriptRoot "unk_keepalive.ps1"
if (-not (Test-Path $supervisorPath)) {
  Write-Host "unk_supervisor.py not found next to this script." -ForegroundColor Red
  exit 1
}

if (-not $RepairOnly) {
  Write-InstallLog "==> Ensuring dependencies (requests, pillow, keyring, playwright)..." "Cyan"
  & $pyExe -m pip install --quiet --disable-pip-version-check requests pillow keyring playwright | Out-Null
  try { & $pyExe -m playwright install chromium | Out-Null } catch { Write-InstallLog "Playwright browser install skipped/failed; companion will retry when needed." "Yellow" }

  # 2. Stop any competing launch_unk.bat window quietly (best-effort).
  try {
    Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | Where-Object {
      $_.CommandLine -match "launch_unk.bat"
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  } catch {}

  # Stop old foreground companion processes so the supervisor is the single owner.
  try {
    Get-CimInstance Win32_Process | Where-Object {
      $_.CommandLine -match "unk_companion\.py" -and $_.ProcessId -ne $PID
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  } catch {}
}

# Convergence cleanup: old task registrations could leave several visible
# consoles and supervisors. Stop only Unk-owned processes; never touch Chrome
# or unrelated terminals, so active Facebook publishing remains unaffected.
try {
  Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and (
      ($_.Name -match '^(cmd|powershell)\.exe$' -and $_.CommandLine -match '(launch_unk\.bat|unk_(audio|mirror)_worker|unk_(companion|supervisor|keepalive))') -or
      ($_.Name -match '^python(w)?\.exe$' -and $_.CommandLine -match 'unk_supervisor\.py')
    )
  } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
} catch {}

# Remove every known legacy Startup launcher. Shortcuts and BAT/CMD copies can
# otherwise recreate the old visible console loop at each sign-in even though
# the canonical scheduled task is already healthy.
try {
  Get-ChildItem -Path $StartupFolder -Force -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^(launch_unk|unk[_ -]?(companion|supervisor|keepalive)).*\.(bat|cmd|lnk)$'
  } | Remove-Item -Force -ErrorAction SilentlyContinue
} catch {}

# 3. Register self-healing scheduled tasks + Startup fallback.
try {
  $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if ($existing -and $existing.State -eq "Running") {
    Write-InstallLog "==> Restarting existing $TaskName before repair" "Cyan"
    Stop-ScheduledTask -TaskName $TaskName | Out-Null
    Start-Sleep -Seconds 2
  }
} catch {}
Write-InstallLog "==> Registering scheduled task $TaskName" "Cyan"
Register-UnkSupervisorTask -PyExe $pyExe -SupervisorPath $supervisorPath
Write-InstallLog "==> Registering keepalive task $KeepAliveTaskName" "Cyan"
Register-UnkKeepAliveTask -KeepAlivePath $keepAlivePath
Register-UnkSystemBootKeepAlive -KeepAlivePath $keepAlivePath
Install-StartupFallback -KeepAlivePath $keepAlivePath

try {
  Start-ScheduledTask -TaskName $TaskName | Out-Null
} catch {
  $current = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if (-not $current -or $current.State -ne "Running") { throw }
}

if ($RepairOnly -or $SkipVerify) {
  Write-InstallLog "==> Supervisor/keepalive tasks repaired. Verification skipped." "Green"
  exit 0
}

Write-InstallLog "==> Task started. Waiting up to 90s for first verified heartbeat..." "Cyan"

$heartbeatFile = Join-Path $env:USERPROFILE ".unk-companion\heartbeat.json"
$startedAt = [double]((Get-Date -UFormat %s))
$deadline = (Get-Date).AddSeconds(90)
$ok = $false
while ((Get-Date) -lt $deadline) {
  if (Test-Path $heartbeatFile) {
    try {
      $data = Get-Content $heartbeatFile -Raw | ConvertFrom-Json
      $age = [double]((Get-Date -UFormat %s)) - [double]$data.at
      $boot = $false
      try { $boot = [bool]$data.boot } catch {}
      if ($age -lt 120 -and [double]$data.at -ge $startedAt -and -not $boot) { $ok = $true; break }
    } catch {}
  }
  Start-Sleep -Seconds 3
}

if ($ok) {
  Write-Host "==> Verified heartbeat received. Unk supervisor + keepalive are installed and running." -ForegroundColor Green
  Write-Host "    Logs: $env:USERPROFILE\.unk-companion\supervisor.log"
  Write-Host "    Keepalive: $env:USERPROFILE\.unk-companion\keepalive.log"
  Write-Host "    Uninstall: powershell -File .\install_supervisor.ps1 -Uninstall"
} else {
  Write-Host "==> No verified heartbeat in 90s. Keeping supervisor + keepalive installed so they continue retrying." -ForegroundColor Yellow
  Write-Host "    Check $env:USERPROFILE\.unk-companion\supervisor.log and keepalive.log for details." -ForegroundColor Yellow
  exit 0
}
