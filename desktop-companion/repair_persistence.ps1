param(
  [switch]$Apply,
  [switch]$RequestElevationIfNeeded,
  [string]$ActionId = "manual"
)

$ErrorActionPreference = "Continue"
$InstallRoot = $PSScriptRoot
$StateDir = Join-Path $env:USERPROFILE ".unk-companion"
$ReceiptPath = Join-Path $StateDir "persistence_repair_latest.json"
$RestoreDir = Join-Path $StateDir "power-restore"
$Now = Get-Date
New-Item -ItemType Directory -Force -Path $StateDir, $RestoreDir | Out-Null

function Is-Admin {
  try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { return $false }
}

function Run-Capture([string]$Name, [scriptblock]$Block) {
  try {
    $out = & $Block 2>&1 | Out-String
    return @{ ok = $true; name = $Name; output = $out.Trim() }
  } catch {
    return @{ ok = $false; name = $Name; error = $_.Exception.Message }
  }
}

function Run-NativeCapture([string]$Name, [string]$FilePath, [string[]]$Arguments, [int]$TimeoutSeconds = 8) {
  $stdout = Join-Path $StateDir ("{0}.stdout.txt" -f $Name)
  $stderr = Join-Path $StateDir ("{0}.stderr.txt" -f $Name)
  Remove-Item -Force -ErrorAction SilentlyContinue $stdout, $stderr
  try {
    $p = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
      try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}
      return @{ ok = $false; name = $Name; error = 'timeout'; exit_code = -1; output = ((Get-Content $stdout -Raw -ErrorAction SilentlyContinue) + (Get-Content $stderr -Raw -ErrorAction SilentlyContinue)).Trim() }
    }
    return @{ ok = ($p.ExitCode -eq 0); name = $Name; exit_code = $p.ExitCode; output = ((Get-Content $stdout -Raw -ErrorAction SilentlyContinue) + (Get-Content $stderr -Raw -ErrorAction SilentlyContinue)).Trim() }
  } catch {
    return @{ ok = $false; name = $Name; error = $_.Exception.Message; output = '' }
  }
}

function Setting([string]$Sub, [string]$Setting) {
  $cap = Run-NativeCapture "powercfg_q_${Sub}_${Setting}" 'powercfg.exe' @('/q','SCHEME_CURRENT',$Sub,$Setting) 8
  $raw = [string]($cap.output)
  $ac = $null; $dc = $null
  foreach ($line in ($raw -split "`n")) {
    if ($line -match 'Current AC Power Setting Index:\s*(0x[0-9a-fA-F]+)') { $ac = [Convert]::ToInt32($Matches[1], 16) }
    if ($line -match 'Current DC Power Setting Index:\s*(0x[0-9a-fA-F]+)') { $dc = [Convert]::ToInt32($Matches[1], 16) }
  }
  $trim = $raw.Trim()
  return @{ sub = $Sub; setting = $Setting; ac = $ac; dc = $dc; probe_ok = $cap.ok; probe_error = $cap.error; raw_tail = $trim.Substring([Math]::Max(0, $trim.Length - 1200)) }
}

function TaskSnapshot([string]$Name) {
  $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
  if (-not $task) { return @{ name = $Name; exists = $false } }
  $info = Get-ScheduledTaskInfo -TaskName $Name -ErrorAction SilentlyContinue
  $xmlText = $null
  try { $xmlText = Export-ScheduledTask -TaskName $Name } catch {}
  return @{
    name = $Name
    exists = $true
    state = [string]$task.State
    last_run_time = if ($info) { [string]$info.LastRunTime } else { $null }
    last_task_result = if ($info) { $info.LastTaskResult } else { $null }
    next_run_time = if ($info) { [string]$info.NextRunTime } else { $null }
    triggers = @($task.Triggers | ForEach-Object { $_ | Select-Object * })
    settings = $task.Settings | Select-Object *
    principal = $task.Principal | Select-Object *
    run_only_when_user_logged_on = (($task.Principal.LogonType -eq 'Interactive') -or ($task.Principal.LogonType -eq 'InteractiveToken'))
    wake_to_run = [bool]$task.Settings.WakeToRun
    start_when_available = [bool]$task.Settings.StartWhenAvailable
    restart_count = $task.Settings.RestartCount
    restart_interval = [string]$task.Settings.RestartInterval
    xml_has_unlock_trigger = if ($xmlText) { $xmlText -match 'SessionUnlock' } else { $false }
    xml_has_boot_trigger = if ($xmlText) { $xmlText -match 'BootTrigger' } else { $false }
  }
}

function LatestLogMatch([string]$Path, [string]$Pattern) {
  if (-not (Test-Path $Path)) { return $null }
  try {
    $m = Get-Content $Path -Tail 500 | Where-Object { $_ -match $Pattern } | Select-Object -Last 1
    return $m
  } catch { return $null }
}

function ClassifyFailure($snap) {
  $classes = New-Object System.Collections.Generic.List[string]
  $standby = $snap.power_settings.STANDBYIDLE.ac
  $hibernate = $snap.power_settings.HIBERNATEIDLE.ac
  $unattend = $snap.power_settings.UNATTENDSLEEP.ac
  if ($standby -ne $null -and $standby -gt 0) { $classes.Add('machine_sleep') }
  if ($hibernate -ne $null -and $hibernate -gt 0) { $classes.Add('machine_hibernate') }
  if ($unattend -ne $null -and $unattend -gt 0) { $classes.Add('machine_sleep') }
  $sup = $snap.tasks.UnkSupervisor
  $keep = $snap.tasks.UnkSupervisorKeepAlive
  if (-not $sup.exists -or -not $keep.exists) { $classes.Add('task_not_triggered') }
  if ($sup.exists -and -not $sup.xml_has_unlock_trigger) { $classes.Add('task_not_triggered') }
  if ($keep.exists -and -not $keep.wake_to_run) { $classes.Add('keepalive_not_restarting') }
  if ($snap.heartbeat.age_seconds -ne $null -and $snap.heartbeat.age_seconds -gt 180) { $classes.Add('worker_polling_stalled') }
  if ($snap.network_power_saving_detected) { $classes.Add('network_adapter_power_suspended') }
  if ($classes.Count -eq 0) { $classes.Add('unknown_with_evidence') }
  return @($classes | Select-Object -Unique)
}

$isAdmin = Is-Admin
if ($Apply -and $RequestElevationIfNeeded -and -not $isAdmin) {
  $args = @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"",'-Apply','-ActionId',"`"$ActionId`"")
  try {
    $p = Start-Process powershell.exe -Verb RunAs -ArgumentList $args -Wait -PassThru
    $receipt = @{ ok = $true; action_id = $ActionId; elevated_relaunch_requested = $true; elevated_pid = $p.Id; note = 'UAC prompt shown; elevated child will write persistence_repair_latest.json if approved.'; at = (Get-Date).ToString('o') }
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -Path $ReceiptPath -Encoding UTF8
    Write-Output ($receipt | ConvertTo-Json -Depth 8)
    exit 0
  } catch {
    $receipt = @{ ok = $false; action_id = $ActionId; error = 'elevation_launch_failed'; detail = $_.Exception.Message; at = (Get-Date).ToString('o') }
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -Path $ReceiptPath -Encoding UTF8
    Write-Output ($receipt | ConvertTo-Json -Depth 8)
    exit 1
  }
}

$heartbeatPath = Join-Path $StateDir "heartbeat.json"
$heartbeat = @{ exists = (Test-Path $heartbeatPath); path = $heartbeatPath; age_seconds = $null; content = $null }
if (Test-Path $heartbeatPath) {
  try {
    $hb = Get-Content $heartbeatPath -Raw | ConvertFrom-Json
    $heartbeat.content = $hb
    if ($hb.at) { $heartbeat.age_seconds = [int](([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) - [double]$hb.at) }
  } catch { $heartbeat['error'] = $_.Exception.Message }
}

$networkAdapters = @(@{ skipped = $true; reason = 'bounded_audit_skips_slow_adapter_probe' })
$networkPowerSavingDetected = $false

$snap = @{
  action_id = $ActionId
  apply_requested = [bool]$Apply
  is_admin = $isAdmin
  captured_at = $Now.ToString('o')
  power_scheme = (Run-NativeCapture 'powercfg_getactivescheme' 'powercfg.exe' @('/getactivescheme') 8).output
  available_sleep_states = (Run-NativeCapture 'powercfg_a' 'powercfg.exe' @('/a') 8).output
  power_settings = @{
    STANDBYIDLE = Setting 'SUB_SLEEP' 'STANDBYIDLE'
    HIBERNATEIDLE = Setting 'SUB_SLEEP' 'HIBERNATEIDLE'
    UNATTENDSLEEP = Setting 'SUB_SLEEP' 'UNATTENDSLEEP'
    HYBRIDSLEEP = Setting 'SUB_SLEEP' 'HYBRIDSLEEP'
    RTCWAKE = Setting 'SUB_SLEEP' 'RTCWAKE'
    VIDEOIDLE = Setting 'SUB_VIDEO' 'VIDEOIDLE'
    USBSELECTIVE = Setting 'SUB_USB' 'USBSELECTIVE'
  }
  current_user = (Run-Capture 'whoami' { whoami }).output
  lock_and_session_state = (Run-NativeCapture 'quser' 'quser.exe' @() 5).output
  last_boot_time = $null
  last_sign_in_time = $null
  heartbeat = $heartbeat
  last_successful_work_poll = LatestLogMatch (Join-Path $StateDir 'companion.log') 'heartbeat ok|pending action'
  last_completed_desktop_action = LatestLogMatch (Join-Path $StateDir 'companion.log') 'result:'
  companion_processes = (Run-Capture 'companion_processes' { Get-Process python,python3,py -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime | ConvertTo-Json -Depth 4 }).output
  tasks = @{
    UnkSupervisor = TaskSnapshot 'UnkSupervisor'
    UnkSupervisorKeepAlive = TaskSnapshot 'UnkSupervisorKeepAlive'
    UnkSupervisorBootKeepAlive = TaskSnapshot 'UnkSupervisorBootKeepAlive'
  }
  network_adapters = $networkAdapters
  network_power_saving_detected = $networkPowerSavingDetected
  companion_exits_when_desktop_locks = 'unknown_with_evidence_no_lock_transition_observed_in_this_run'
  playwright_fails_only_after_lock_or_sleep = 'unknown_with_evidence_no_browser_action_executed_in_this_run'
  standby_mode_classification_basis = 'powercfg /a + configured timeouts + task state + heartbeat age'
}

try { $snap['last_boot_time'] = [string](Get-CimInstance Win32_OperatingSystem).LastBootUpTime } catch {}
$snap['last_sign_in_time'] = 'skipped_bounded_audit_no_security_log_scan'

$previousPath = Join-Path $RestoreDir ("power-settings-before-{0}.json" -f (Get-Date -Format 'yyyyMMddTHHmmss'))
$changes = New-Object System.Collections.Generic.List[object]

if ($Apply) {
  $snap | ConvertTo-Json -Depth 18 | Set-Content -Path $previousPath -Encoding UTF8
  $commands = @(
    @{ name='sleep_timeout_ac_never'; cmd=@('powercfg','/setacvalueindex','SCHEME_CURRENT','SUB_SLEEP','STANDBYIDLE','0') },
    @{ name='hibernate_timeout_ac_never'; cmd=@('powercfg','/setacvalueindex','SCHEME_CURRENT','SUB_SLEEP','HIBERNATEIDLE','0') },
    @{ name='unattended_sleep_ac_never'; cmd=@('powercfg','/setacvalueindex','SCHEME_CURRENT','SUB_SLEEP','UNATTENDSLEEP','0') },
    @{ name='hybrid_sleep_ac_off'; cmd=@('powercfg','/setacvalueindex','SCHEME_CURRENT','SUB_SLEEP','HYBRIDSLEEP','0') },
    @{ name='wake_timers_ac_enable'; cmd=@('powercfg','/setacvalueindex','SCHEME_CURRENT','SUB_SLEEP','RTCWAKE','1') },
    @{ name='usb_selective_suspend_ac_off'; cmd=@('powercfg','/setacvalueindex','SCHEME_CURRENT','SUB_USB','USBSELECTIVE','0') },
    @{ name='monitor_timeout_ac_15'; cmd=@('powercfg','/setacvalueindex','SCHEME_CURRENT','SUB_VIDEO','VIDEOIDLE','900') },
    @{ name='set_active_scheme'; cmd=@('powercfg','/setactive','SCHEME_CURRENT') },
    @{ name='hibernate_off_best_effort'; cmd=@('powercfg','/hibernate','off') }
  )
  foreach ($c in $commands) {
    try {
      $p = Start-Process -FilePath $c.cmd[0] -ArgumentList ($c.cmd[1..($c.cmd.Count-1)]) -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$StateDir\$($c.name).out" -RedirectStandardError "$StateDir\$($c.name).err"
      $changes.Add(@{ name=$c.name; exit_code=$p.ExitCode; stdout=(Get-Content "$StateDir\$($c.name).out" -Raw -ErrorAction SilentlyContinue); stderr=(Get-Content "$StateDir\$($c.name).err" -Raw -ErrorAction SilentlyContinue) }) | Out-Null
    } catch { $changes.Add(@{ name=$c.name; ok=$false; error=$_.Exception.Message }) | Out-Null }
  }
  $changes.Add(@{ name='network_adapter_power_disable'; ok=$true; skipped=$true; reason='bounded_repair_avoids_slow_adapter_cmdlet' }) | Out-Null
  try {
    $installer = Join-Path $InstallRoot 'install_supervisor.ps1'
    if (Test-Path $installer) {
      $repair = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -RepairOnly -SkipVerify 2>&1 | Out-String
      $changes.Add(@{ name='supervisor_task_repair'; ok=$true; output_tail=$repair.Substring([Math]::Max(0, $repair.Length - 4000)) }) | Out-Null
    }
  } catch { $changes.Add(@{ name='supervisor_task_repair'; ok=$false; error=$_.Exception.Message }) | Out-Null }
}

# Re-snapshot after repairs so verification uses current state.
$afterTasks = @{
  UnkSupervisor = TaskSnapshot 'UnkSupervisor'
  UnkSupervisorKeepAlive = TaskSnapshot 'UnkSupervisorKeepAlive'
  UnkSupervisorBootKeepAlive = TaskSnapshot 'UnkSupervisorBootKeepAlive'
}
$afterPower = @{
  STANDBYIDLE = Setting 'SUB_SLEEP' 'STANDBYIDLE'
  HIBERNATEIDLE = Setting 'SUB_SLEEP' 'HIBERNATEIDLE'
  UNATTENDSLEEP = Setting 'SUB_SLEEP' 'UNATTENDSLEEP'
  HYBRIDSLEEP = Setting 'SUB_SLEEP' 'HYBRIDSLEEP'
  RTCWAKE = Setting 'SUB_SLEEP' 'RTCWAKE'
  VIDEOIDLE = Setting 'SUB_VIDEO' 'VIDEOIDLE'
  USBSELECTIVE = Setting 'SUB_USB' 'USBSELECTIVE'
}

$snap['failure_classification'] = ClassifyFailure $snap
$previousSettingsPathForReceipt = $null
if ($Apply) { $previousSettingsPathForReceipt = $previousPath }
$remainingBlockers = New-Object System.Collections.Generic.List[string]

$verification = @{}
$verification['ac_sleep_never'] = [bool]($afterPower['STANDBYIDLE']['ac'] -eq 0)
$verification['ac_hibernate_never'] = [bool]($afterPower['HIBERNATEIDLE']['ac'] -eq 0)
$verification['unattended_sleep_disabled'] = [bool]($afterPower['UNATTENDSLEEP']['ac'] -eq 0)
$verification['hybrid_sleep_disabled'] = [bool]($afterPower['HYBRIDSLEEP']['ac'] -eq 0)
$verification['wake_timers_enabled'] = [bool]($afterPower['RTCWAKE']['ac'] -eq 1)
$verification['usb_selective_suspend_disabled'] = [bool]($afterPower['USBSELECTIVE']['ac'] -eq 0)
$verification['display_can_turn_off'] = [bool]($afterPower['VIDEOIDLE']['ac'] -gt 0)
$verification['supervisor_task_exists'] = [bool]$afterTasks['UnkSupervisor']['exists']
$verification['keepalive_task_exists'] = [bool]$afterTasks['UnkSupervisorKeepAlive']['exists']
$verification['supervisor_start_when_available'] = [bool]$afterTasks['UnkSupervisor']['start_when_available']
$verification['keepalive_start_when_available'] = [bool]$afterTasks['UnkSupervisorKeepAlive']['start_when_available']
$verification['supervisor_wake_to_run'] = [bool]$afterTasks['UnkSupervisor']['wake_to_run']
$verification['keepalive_wake_to_run'] = [bool]$afterTasks['UnkSupervisorKeepAlive']['wake_to_run']
$verification['supervisor_unlock_trigger'] = [bool]$afterTasks['UnkSupervisor']['xml_has_unlock_trigger']
$verification['keepalive_unlock_trigger'] = [bool]$afterTasks['UnkSupervisorKeepAlive']['xml_has_unlock_trigger']

$after = @{}
$after['power_settings'] = $afterPower
$after['tasks'] = $afterTasks
$after['heartbeat'] = $heartbeat

# Materialize changes as a plain object[] to avoid OrderedDictionary/List type mismatch.
$changesArray = @()
foreach ($ch in $changes) { $changesArray += ,([hashtable]$ch) }

$receipt = @{}
$receipt['ok'] = $true
$receipt['action_id'] = $ActionId
$receipt['applied'] = [bool]$Apply
$receipt['is_admin'] = $isAdmin
$receipt['previous_settings_path'] = $previousSettingsPathForReceipt
$receipt['before'] = $snap
$receipt['changes'] = $changesArray
$receipt['after'] = $after
$receipt['verification'] = $verification
$receipt['remaining_blockers'] = @()
$receipt['completed_at'] = (Get-Date).ToString('o')

if ($Apply -and -not $isAdmin) {
  $adminFailures = @($changes | Where-Object { $_.exit_code -ne $null -and $_.exit_code -ne 0 })
  if ($adminFailures.Count -gt 0) { $remainingBlockers.Add('some_power_or_adapter_changes_failed_without_elevation') | Out-Null }
}
if (-not $verification['supervisor_task_exists'] -or -not $verification['keepalive_task_exists']) { $remainingBlockers.Add('scheduled_task_repair_incomplete') | Out-Null }
if (-not $verification['ac_sleep_never']) { $remainingBlockers.Add('ac_sleep_timeout_not_never') | Out-Null }

$receipt['remaining_blockers'] = @($remainingBlockers)
$receipt['ok'] = ($remainingBlockers.Count -eq 0)
$receipt | ConvertTo-Json -Depth 24 | Set-Content -Path $ReceiptPath -Encoding UTF8
Write-Output ($receipt | ConvertTo-Json -Depth 24)
if ($receipt['ok']) { exit 0 } else { exit 2 }