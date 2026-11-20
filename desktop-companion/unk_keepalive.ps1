# unk_keepalive.ps1 — Windows Scheduled Task self-healer for UnkSupervisor.
# Runs every 5 minutes plus at logon. It repairs/starts the supervisor, keeps
# the durable Unk <-> OpenAI bridge alive, and restores the independent Remote
# Desktop Commander relay when its user-session agent is absent.

$ErrorActionPreference = "SilentlyContinue"
Set-Location -Path $PSScriptRoot

$TaskName = "UnkSupervisor"
$StateDir = Join-Path $env:USERPROFILE ".unk-companion"
$LogFile = Join-Path $StateDir "keepalive.log"
$MarkerFile = Join-Path $StateDir "supervisor_alive.marker"
$Installer = Join-Path $PSScriptRoot "install_supervisor.ps1"
$PersistenceRepair = Join-Path $PSScriptRoot "repair_persistence.ps1"
$PowerReceiptFile = Join-Path $StateDir "persistence_repair_latest.json"
$PowerRepairCadenceSeconds = 3600
$BridgeWorker = Join-Path $PSScriptRoot "unk_ai_bridge.py"
$BridgeFallbackWorker = Join-Path $PSScriptRoot "unk_ai_bridge_daemon.py"
$FixerWorker = Join-Path $PSScriptRoot "unk_fixer_worker.py"
$MirrorWorker = Join-Path $PSScriptRoot "media_mirror_worker.py"
$MirrorWorkerProtocol = "2026-11-01-lease-ack-v1"
$MirrorWorkerStdout = Join-Path $StateDir "media_mirror_worker.stdout.log"
$MirrorWorkerStderr = Join-Path $StateDir "media_mirror_worker.stderr.log"
$MirrorHealthReceipt = Join-Path $StateDir "media_mirror_worker_health.json"
$CanonicalMirrorOrigin = "https://kwbegsybeyyxfmavjswv.supabase.co"
$RemoteRelayReceipt = Join-Path $StateDir "remote_desktop_commander_watchdog.json"
$RemoteRelayRunnerReceipt = Join-Path $StateDir "remote_desktop_commander_relay_latest.json"
$RemoteDesktopCommanderPackage = '@wonderwhy-er/desktop-commander@latest'
$RemoteRelayScript = Join-Path $PSScriptRoot "remote_desktop_commander_relay.ps1"
$RemoteRelayTaskName = "UnkRemoteDesktopCommanderRelay"
$RemoteRelayTaskSpecVersion = "2026-11-07-v7-redacted-device-log-signals"

function Log([string]$Message) {
  try {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    "[$(Get-Date -Format o)] $Message" | Add-Content -Path $LogFile -Encoding UTF8
  } catch {}
}

function Write-MediaMirrorHealthReceipt([string]$State, [int]$WorkerProcessId = 0) {
  # An observed process or a successful Scheduled Task tick never proves that
  # Storage bytes were transferred. Keep a separate redacted health snapshot.
  try {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    @{
      checked_at = (Get-Date).ToString('o')
      state = $State
      process_visible = ($WorkerProcessId -gt 0)
      process_id = $WorkerProcessId
      transfer_verified = $false
      canonical_origin = $CanonicalMirrorOrigin
    } | ConvertTo-Json -Depth 3 | Set-Content -Path $MirrorHealthReceipt -Encoding UTF8
  } catch {
    Log "Media mirror health receipt unavailable; error_class=$($_.Exception.GetType().Name)"
  }
}

function Write-RemoteRelayReceipt([hashtable]$Receipt) {
  try {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    $Receipt['checked_at'] = (Get-Date).ToString('o')
    $Receipt['package'] = $RemoteDesktopCommanderPackage
    $Receipt['task_name'] = $RemoteRelayTaskName
    $Receipt['task_spec_version'] = $RemoteRelayTaskSpecVersion
    $Receipt | ConvertTo-Json -Depth 6 | Set-Content -Path $RemoteRelayReceipt -Encoding UTF8
  } catch {}
}

function MarkerAgeSeconds {
  if (-not (Test-Path $MarkerFile)) { return $null }
  try { return [int]((Get-Date) - (Get-Item $MarkerFile).LastWriteTime).TotalSeconds } catch { return $null }
}

function ReceiptAgeSeconds([string]$Path) {
  if (-not (Test-Path $Path)) { return $null }
  try { return [int]((Get-Date) - (Get-Item $Path).LastWriteTime).TotalSeconds } catch { return $null }
}

function Get-RemoteDesktopCommanderProcesses {
  try {
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
      $cmd = [string]$_.CommandLine
      $cmd -and
      ($cmd -match '(?i)desktop-commander') -and
      ($cmd -match '(?i)(^|\s)remote(\s|$)')
    })
  } catch { return @() }
}

function Find-RemoteDesktopCommanderProcess {
  return Get-RemoteDesktopCommanderProcesses | Select-Object -First 1
}

function Find-TaskOwnedRemoteDesktopCommanderProcess {
  try {
    $processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    if ($processes.Count -eq 0) { return $null }

    $runnerPattern = [regex]::Escape($RemoteRelayScript)
    $runners = @($processes | Where-Object {
      $cmd = [string]$_.CommandLine
      $cmd -and
      ($cmd -match '(?i)powershell(?:\.exe)?') -and
      ($cmd -match $runnerPattern)
    })
    if ($runners.Count -eq 0) { return $null }

    $byPid = @{}
    foreach ($process in $processes) {
      $byPid[[int]$process.ProcessId] = $process
    }

    foreach ($relay in @($processes | Where-Object {
      $cmd = [string]$_.CommandLine
      $cmd -and
      ($cmd -match '(?i)desktop-commander') -and
      ($cmd -match '(?i)(^|\s)remote(\s|$)')
    })) {
      $cursor = $relay
      $visited = @{}
      for ($depth = 0; $depth -lt 16; $depth++) {
        $parentPid = [int]$cursor.ParentProcessId
        if ($parentPid -le 0 -or $visited.ContainsKey($parentPid)) { break }
        $visited[$parentPid] = $true

        $runner = $runners | Where-Object { [int]$_.ProcessId -eq $parentPid } | Select-Object -First 1
        if ($runner) {
          return [pscustomobject]@{ Relay = $relay; Runner = $runner }
        }

        if (-not $byPid.ContainsKey($parentPid)) { break }
        $cursor = $byPid[$parentPid]
      }
    }
  } catch {}
  return $null
}

function Ensure-AIBridge {
  $worker = if (Test-Path $BridgeWorker) { $BridgeWorker } elseif (Test-Path $BridgeFallbackWorker) { $BridgeFallbackWorker } else { $null }
  if (-not $worker) {
    Log "AI bridge ensure skipped; bridge worker not installed."
    return
  }
  try {
    $leaf = [IO.Path]::GetFileName($worker)
    $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
      $_.CommandLine -and $_.CommandLine -like "*$leaf*"
    } | Select-Object -First 1
    if ($running) { return }

    $py = Get-Command pythonw -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if (-not $py) {
      Log "AI bridge ensure failed; Python not found."
      return
    }
    $arg = if ($leaf -eq "unk_ai_bridge.py") { "--worker" } else { "" }
    if ($arg) {
      Start-Process -FilePath $py.Source -ArgumentList @("-u", $worker, $arg) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null
    } else {
      Start-Process -FilePath $py.Source -ArgumentList @("-u", $worker) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null
    }
    Log "AI bridge start requested. worker=$leaf"
  } catch {
    Log "AI bridge ensure failed: $($_.Exception.Message)"
  }
}


function Ensure-FixerWorker {
  if (-not (Test-Path $FixerWorker)) {
    Log "Fixer ensure skipped; worker not installed."
    return
  }
  try {
    $leaf = [IO.Path]::GetFileName($FixerWorker)
    $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
      $_.CommandLine -and $_.CommandLine -like "*$leaf*"
    } | Select-Object -First 1
    if ($running) { return }

    $py = Get-Command pythonw -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if (-not $py) {
      Log "Fixer ensure failed; Python not found."
      return
    }
    Start-Process -FilePath $py.Source -ArgumentList @("-u", $FixerWorker) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null
    Log "Fixer start requested. worker=$leaf"
  } catch {
    Log "Fixer ensure failed: $($_.Exception.Message)"
  }
}

function Ensure-MediaMirrorWorker {
  # The existing Unk keepalive is the sole startup owner. SYSTEM never launches
  # private-media processes under a different identity or credential store.
  if ($env:USERNAME -eq "SYSTEM") { return }
  if (-not (Test-Path $MirrorWorker)) {
    Log "Media mirror worker is not installed; no process started."
    Write-MediaMirrorHealthReceipt 'worker_not_installed'
    return
  }

  # An older installed worker lacks exact lease fencing and completion ACK rules.
  # Read source metadata only: never execute, replace, or fetch worker credentials.
  try {
    $workerHeader = @(Get-Content -LiteralPath $MirrorWorker -TotalCount 90 -ErrorAction Stop)
    if ($workerHeader -cnotcontains ('MEDIA_MIRROR_WORKER_PROTOCOL = "' + $MirrorWorkerProtocol + '"')) {
      Log "Media mirror startup rejected: local worker protocol drift."
      Write-MediaMirrorHealthReceipt 'worker_protocol_mismatch'
      return
    }
  } catch {
    Log "Media mirror startup rejected: worker protocol could not be inspected."
    Write-MediaMirrorHealthReceipt 'worker_protocol_unavailable'
    return
  }
  if (([string]$env:MEDIA_MIRROR_ENABLED).Trim().ToLowerInvariant() -ne "true") {
    Write-MediaMirrorHealthReceipt 'mirror_disabled'
    return
  }
  $configuredMirrorOrigin = ([string]$env:SUPABASE_URL).TrimEnd("/")
  if ([string]::IsNullOrWhiteSpace($configuredMirrorOrigin)) {
    # SUPABASE_URL is optional: the worker itself defaults to the fixed owner K
    # root. Never infer or accept an explicitly configured alternate host.
    $configuredMirrorOrigin = $CanonicalMirrorOrigin
  }
  if ($configuredMirrorOrigin -cne $CanonicalMirrorOrigin) {
    Log "Media mirror startup rejected: non-canonical Supabase origin."
    Write-MediaMirrorHealthReceipt 'noncanonical_origin'
    return
  }
  # Check presence only. Never log/retrieve/provision or pass a private key as
  # a command-line argument. The child inherits its already-authorized environment.
  if ([string]::IsNullOrWhiteSpace([string]$env:SUPABASE_SERVICE_ROLE_KEY) -or
      [string]::IsNullOrWhiteSpace([string]$env:MEDIA_MIRROR_WORKER_ID)) {
    Log "Media mirror startup unavailable: required runtime configuration absent."
    Write-MediaMirrorHealthReceipt 'missing_runtime_configuration'
    return
  }
  # Match this keepalive's exact installed worker, not another installation's
  # same-named Python process with different credentials or destination.
  $expectedWorkerPattern = '(?i)(^|[\s"])' + [regex]::Escape([string]$MirrorWorker) + '(?=$|[\s"])'
  try {
    $running = Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
      ([string]$_.Name -match '^pythonw?(?:[0-9]+(?:\.[0-9]+)?)?\.exe(?=$)') -and
      ([string]$_.CommandLine -match $expectedWorkerPattern)
    } | Select-Object -First 1
    if ($running) {
      Write-MediaMirrorHealthReceipt 'running_unverified' ([int]$running.ProcessId)
      return
    }
  } catch {
    Log "Media mirror process visibility unavailable; no duplicate launch attempted."
    Write-MediaMirrorHealthReceipt 'process_visibility_unavailable'
    return
  }
  $python = Get-Command pythonw -ErrorAction SilentlyContinue
  if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
  if (-not $python) {
    Log "Media mirror runtime unavailable: Python not found."
    Write-MediaMirrorHealthReceipt 'python_unavailable'
    return
  }
  try {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    $proc = Start-Process -FilePath $python.Source -ArgumentList @("-u", ('"{0}"' -f $MirrorWorker), "--loop", "300") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $MirrorWorkerStdout -RedirectStandardError $MirrorWorkerStderr -PassThru
    Start-Sleep -Seconds 2
    if (-not $proc -or -not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) {
      Log "Media mirror worker exited during startup; inspect local redacted worker logs."
      Write-MediaMirrorHealthReceipt 'startup_exited'
      return
    }
    Log "Media mirror worker process started pid=$($proc.Id); transfer and durable receipts not yet verified."
    Write-MediaMirrorHealthReceipt 'started_unverified' ([int]$proc.Id)
  } catch {
    Log "Media mirror worker start failed; error_class=$($_.Exception.GetType().Name)"
    Write-MediaMirrorHealthReceipt 'startup_error'
  }
}

function Ensure-RemoteDesktopCommanderTask {
  if ($env:USERNAME -eq "SYSTEM") { return $false }
  if (-not (Test-Path $RemoteRelayScript)) {
    Log "Remote Desktop Commander scheduled runner unavailable; relay script missing."
    return $false
  }

  try {
    $relayArgs = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$RemoteRelayScript`""
    $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue
    $drift = New-Object System.Collections.Generic.List[string]
    $unmanagedRelayMigrated = $false

    if (-not $task) {
      $drift.Add('task_missing') | Out-Null
    } else {
      $existingAction = $task.Actions | Select-Object -First 1
      if (-not $existingAction) {
        $drift.Add('action_missing') | Out-Null
      } else {
        $execute = [string]$existingAction.Execute
        $arguments = [string]$existingAction.Arguments
        $workingDirectory = [string]$existingAction.WorkingDirectory
        if ($execute -notmatch '(?i)(^|\\)powershell\.exe$') { $drift.Add('action_execute_mismatch') | Out-Null }
        if ($arguments -ne $relayArgs) { $drift.Add('action_arguments_mismatch') | Out-Null }
        if ($workingDirectory -and ($workingDirectory.TrimEnd('\\') -ne $PSScriptRoot.TrimEnd('\\'))) { $drift.Add('working_directory_mismatch') | Out-Null }
      }

      $settings = $task.Settings
      if (-not $settings) {
        $drift.Add('settings_missing') | Out-Null
      } else {
        if ([int]$settings.RestartCount -lt 999) { $drift.Add('restart_count_mismatch') | Out-Null }
        $restartInterval = [string]$settings.RestartInterval
        if ($restartInterval -notin @('PT1M','00:01:00')) { $drift.Add('restart_interval_mismatch') | Out-Null }
        $executionLimit = [string]$settings.ExecutionTimeLimit
        if ($executionLimit -notin @('PT0S','00:00:00')) { $drift.Add('execution_time_limit_mismatch') | Out-Null }
        if (-not [bool]$settings.StartWhenAvailable) { $drift.Add('start_when_available_disabled') | Out-Null }
      }

      $hasLogonTrigger = @($task.Triggers | Where-Object {
        $_.CimClass -and ([string]$_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger')
      }).Count -gt 0
      if (-not $hasLogonTrigger) { $drift.Add('logon_trigger_missing') | Out-Null }

      $logonType = [string]$task.Principal.LogonType
      if ($logonType -notin @('Interactive','InteractiveToken')) { $drift.Add('principal_not_interactive') | Out-Null }
    }

    # An updated runner file is not active while the old Scheduled Task
    # process keeps running. Reconcile the description revision to activate
    # the installed recovery fix without a second scheduler or relay.
    if ($task -and -not ([string]$task.Description).Contains($RemoteRelayTaskSpecVersion)) {
      $drift.Add('runner_version_mismatch') | Out-Null
    }

    if ($drift.Count -gt 0) {
      if ($task -and $task.State -eq 'Running') {
        Stop-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue | Out-Null
        Start-Sleep -Seconds 1
      }

      $desiredAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $relayArgs -WorkingDirectory $PSScriptRoot
      $desiredTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
      $desiredSettings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -RestartCount 999 `
        -StartWhenAvailable `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -Hidden
      $desiredPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
      $description = "J Fortitude Remote Desktop Commander relay spec $RemoteRelayTaskSpecVersion"
      Register-ScheduledTask -TaskName $RemoteRelayTaskName -Action $desiredAction -Trigger $desiredTrigger `
        -Settings $desiredSettings -Principal $desiredPrincipal -Description $description -Force | Out-Null
      Log "Reconciled dedicated Remote Desktop Commander relay task. drift=$($drift -join ',') spec=$RemoteRelayTaskSpecVersion"
      $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue
    }

    if (-not $task) { return $false }

    $ownedRelay = Find-TaskOwnedRemoteDesktopCommanderProcess
    if ($task.State -eq 'Running' -and -not $ownedRelay) {
      Log "Remote Desktop Commander task is Running without a task-owned relay child; restarting task ownership."
      Stop-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue | Out-Null
      Start-Sleep -Seconds 1
      $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue
    }

    if ($task.State -ne "Running") {
      $relayProcesses = @(Get-RemoteDesktopCommanderProcesses)
      # Jwoffice can also have a previously installed primary Remote Desktop
      # Commander Scheduled Task. Never kill its relay as "unmanaged" just
      # because this secondary Unk task is idle: two restart loops can
      # otherwise terminate each other's working child process.
      $primaryTask = Get-ScheduledTask -TaskName 'JFortitude-RemoteDesktopCommander' -ErrorAction SilentlyContinue
      if ($primaryTask -and $primaryTask.State -eq "Running" -and $relayProcesses.Count -gt 0) {
        Log "Primary Remote Desktop Commander task is running with a relay; preserving existing process. Execution remains unverified."
        Write-RemoteRelayReceipt @{ ok = $false; state = 'primary_relay_owner_execution_unverified'; primary_task_name = 'JFortitude-RemoteDesktopCommander'; primary_task_running = $true; relay_present = $true; dedicated_task = $false; execution_probe_required = $true }
        return $true  # handled by the existing primary task; do not launch fallback
      }
      if ($relayProcesses.Count -gt 0) {
        # Unknown process ownership is not evidence that a relay is disposable.
        # Preserve the already-running transport rather than starting a competing
        # relay. Execution readiness still requires a real remote tool-call probe.
        $relayPids = @($relayProcesses | ForEach-Object { [int]$_.ProcessId })
        Log "Preserving relay with unverified task owner. pids=$($relayPids -join ',')."
        Write-RemoteRelayReceipt @{ ok = $false; state = 'unowned_relay_execution_unverified'; relay_present = $true; dedicated_task = $false; execution_probe_required = $true }
        return $true
      }
      Start-ScheduledTask -TaskName $RemoteRelayTaskName | Out-Null
      Start-Sleep -Seconds 3
      $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue
    }

    $ownedRelay = Find-TaskOwnedRemoteDesktopCommanderProcess
    if ($task -and $task.State -eq "Running" -and $ownedRelay) {
      $runnerReceiptState = 'missing'
      $runnerReceiptAgeSeconds = ReceiptAgeSeconds $RemoteRelayRunnerReceipt
      try {
        if (Test-Path $RemoteRelayRunnerReceipt) {
          $runnerReceipt = Get-Content $RemoteRelayRunnerReceipt -Raw -ErrorAction Stop | ConvertFrom-Json
          $runnerReceiptState = [string]$runnerReceipt.state
        }
      } catch {
        $runnerReceiptState = 'unreadable'
      }

      # Process supervision is proven, but neither Task Scheduler nor a remote
      # presence ping proves that the local MCP execution plane can forward a
      # command. Keep the task alive while reporting readiness fail-closed.
      Write-RemoteRelayReceipt @{
        ok = $false
        state = 'task_owned_relay_execution_unverified'
        process_supervised = $true
        task_owner_pid = [int]$ownedRelay.Runner.ProcessId
        relay_pid = [int]$ownedRelay.Relay.ProcessId
        dedicated_task = $true
        persisted_session = $true
        runner_receipt_state = $runnerReceiptState
        runner_receipt_age_seconds = $runnerReceiptAgeSeconds
        execution_probe_required = $true
        task_reconciled = ($drift.Count -gt 0)
        drift_reasons = @($drift)
        unmanaged_relay_migrated = $unmanagedRelayMigrated
      }
      return $true
    }

    $relayProcess = Find-RemoteDesktopCommanderProcess
    Log "Remote Desktop Commander dedicated task/relay is not task-owned. task_state=$($task.State) relay_present=$([bool]$relayProcess)"
    Write-RemoteRelayReceipt @{ ok = $false; state = 'task_or_relay_not_task_owned'; dedicated_task = $true; task_state = [string]$task.State; relay_present = [bool]$relayProcess; execution_probe_required = $true; task_reconciled = ($drift.Count -gt 0); drift_reasons = @($drift); unmanaged_relay_migrated = $unmanagedRelayMigrated }
    return $false
  } catch {
    Log "Remote Desktop Commander dedicated task repair failed: $($_.Exception.Message)"
    Write-RemoteRelayReceipt @{ ok = $false; state = 'task_registration_or_start_failed'; dedicated_task = $true; reason = $_.Exception.Message }
    return $false
  }
}

function Ensure-RemoteDesktopCommander {
  # Remote Desktop Commander stores the paired-device session under the user
  # profile and its remote agent is intentionally foreground by default. Run
  # this only in the interactive user's context; the boot/SYSTEM keepalive must
  # not create a second device identity or use another user's credential store.
  if ($env:USERNAME -eq "SYSTEM") {
    Write-RemoteRelayReceipt @{ ok = $false; state = 'deferred_to_user_session'; reason = 'system_context_not_allowed' }
    return
  }

  try {
    # The dedicated Scheduled Task is the canonical owner. Reconcile/start it
    # even if a legacy relay process is already present; unmanaged processes are
    # migrated into task ownership so restart policy cannot remain bypassed.
    if (Ensure-RemoteDesktopCommanderTask) { return }

    # Scheduled-task reconciliation can fail while an independently owned
    # relay still exists. Do not spawn a competing device session in the
    # fallback: this recovery owns no such process and cannot safely kill it.
    # A live authenticated tool call is still required to prove delivery.
    $existingRelays = @(Get-RemoteDesktopCommanderProcesses)
    if ($existingRelays.Count -gt 0) {
      Log "Preserving existing relay after scheduled-task repair failure; fallback suppressed. Remote tool execution remains unverified."
      Write-RemoteRelayReceipt @{ ok = $false; state = 'fallback_suppressed_existing_relay_execution_unverified'; relay_present = $true; dedicated_task = $false; execution_probe_required = $true }
      return
    }

    $npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
    if (-not $npx) { $npx = Get-Command npx -ErrorAction SilentlyContinue }
    if (-not $npx) {
      Log "Remote Desktop Commander ensure failed; npx not found."
      Write-RemoteRelayReceipt @{ ok = $false; state = 'not_running'; reason = 'npx_not_found' }
      return
    }

    # Fallback direct launch remains available only if dedicated task ownership
    # cannot be established. The next healthy keepalive will attempt migration
    # back into the task rather than accepting fallback as a permanent state.
    $comspec = if ($env:ComSpec) { $env:ComSpec } else { 'C:\Windows\System32\cmd.exe' }
    if (-not (Test-Path $comspec)) {
      Log "Remote Desktop Commander ensure failed; cmd.exe not found."
      Write-RemoteRelayReceipt @{ ok = $false; state = 'not_running'; reason = 'cmd_not_found' }
      return
    }

    $stdout = Join-Path $StateDir 'remote_desktop_commander.stdout.log'
    $stderr = Join-Path $StateDir 'remote_desktop_commander.stderr.log'
    $command = "npx --yes $RemoteDesktopCommanderPackage remote --persist-session"
    $proc = Start-Process -FilePath $comspec -ArgumentList @('/d','/s','/c',$command) -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    Start-Sleep -Seconds 3

    $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if ($stillRunning) {
      Log "Remote Desktop Commander relay fallback start requested. pid=$($proc.Id) package=$RemoteDesktopCommanderPackage"
      Write-RemoteRelayReceipt @{ ok = $false; state = 'fallback_start_execution_unverified'; pid = [int]$proc.Id; started = $true; persisted_session = $true; windows_cmd_wrapper = $true; dedicated_task = $false; execution_probe_required = $true }
    } else {
      $tail = ''
      try { $tail = ((Get-Content $stderr -Tail 20 -ErrorAction SilentlyContinue) -join "`n") } catch {}
      Log "Remote Desktop Commander relay exited during fallback startup."
      Write-RemoteRelayReceipt @{ ok = $false; state = 'startup_exited'; started = $true; windows_cmd_wrapper = $true; dedicated_task = $false; error_tail = $tail }
    }
  } catch {
    Log "Remote Desktop Commander ensure failed: $($_.Exception.Message)"
    Write-RemoteRelayReceipt @{ ok = $false; state = 'watchdog_error'; reason = $_.Exception.Message }
  }
}

function Assert-PowerPosture {
  if (-not (Test-Path $PersistenceRepair)) {
    Log "Power posture repair skipped; repair_persistence.ps1 missing."
    return
  }
  $age = ReceiptAgeSeconds $PowerReceiptFile
  if ($null -ne $age -and $age -lt $PowerRepairCadenceSeconds) { return }
  try {
    $actionId = if ($env:USERNAME -eq "SYSTEM") { "boot_keepalive" } else { "keepalive_tick" }
    $out = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $PersistenceRepair -Apply -ActionId $actionId 2>&1 | Out-String
    $tail = $out.Substring([Math]::Max(0, $out.Length - 800))
    Log "Power posture assertion completed. action=$actionId receipt_age_secs=$age output_tail=$tail"
  } catch {
    Log "Power posture assertion failed: $($_.Exception.Message)"
  }
}


# The installed companion is a long-lived copy, not a read-through to GitHub.
# A stale installation can keep heartbeating the forbidden legacy source even
# after the canonical package has been corrected. Repair exactly that known
# config drift, then let the existing supervisor restart ONE Unk process.
# Never touch Kim's private planner, queue, or inference workers.
# The installed supervisor may also retain a Lovable-managed reporting origin.
# Use the same canonical target as the companion and never allow an inherited
# UNK_SUPABASE_URL to redirect privileged supervisor reports to legacy.
function Repair-StaleUnkSupervisorRoute {
  $scriptFile = Join-Path $PSScriptRoot "unk_supervisor.py"
  if (-not (Test-Path -LiteralPath $scriptFile)) { return }
  try {
    $installed = [System.IO.File]::ReadAllText($scriptFile)
    $canonicalRef = 'SUPABASE_URL = "https://kwbegsybeyyxfmavjswv.supabase.co"'
    if ($installed.Contains($canonicalRef) -and
        -not $installed.Contains('SUPABASE_URL = os.environ.get("UNK_SUPABASE_URL")')) { return }
    $blockRegex = [regex]::new('(?ms)^SUPABASE_URL = [^\r\n]+.{0,1400}?(?=\r?\nSTART_REQUEST_FILE = )')
    $matches = $blockRegex.Matches($installed)
    if ($matches.Count -ne 1 -or
        -not $matches[0].Value.Contains('SUPABASE_ANON_KEY =') -or
        -not $matches[0].Value.Contains('REPORT_URL =') -or
        -not ($matches[0].Value.Contains('https://pefatniumnrxwbgnwvvh.supabase.co') -or
              $matches[0].Value.Contains('os.environ.get("UNK_SUPABASE_URL")'))) {
      Log "Unk supervisor K-route recovery deferred: unexpected installed config."
      return
    }
    $canonicalBlock = @'
SUPABASE_URL = "https://kwbegsybeyyxfmavjswv.supabase.co"
SUPABASE_ANON_KEY = os.environ.get("UNK_SUPABASE_ANON_KEY") or "sb_publishable_71YhGNn088MamieIZXBAaw_kv3w4wc9"
REPORT_URL = f"{SUPABASE_URL}/functions/v1/desktop-supervisor-report"
'@
    $patched = $blockRegex.Replace($installed, $canonicalBlock, 1)
    if (-not $patched.Contains($canonicalRef) -or
        $patched.Contains('https://pefatniumnrxwbgnwvvh.supabase.co')) {
      Log "Unk supervisor K-route recovery refused: post-write target invalid."
      return
    }
    $temporary = "$scriptFile.project-k.tmp.py"
    $backup = "$scriptFile.before-project-k-$(Get-Date -Format 'yyyyMMddHHmmss').bak"
    [System.IO.File]::WriteAllText($temporary, $patched, (New-Object System.Text.UTF8Encoding($false)))
    python -m py_compile $temporary 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
      Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
      Log "Unk supervisor K-route recovery deferred: Python syntax failed."
      return
    }
    [System.IO.File]::Replace($temporary, $scriptFile, $backup)
    Log "Unk supervisor reporting route repaired atomically to owner Project K."
    # Only the existing supervisor process may be stopped; its registered
    # UnkSupervisor task and keepalive retain independent restart ownership.
    $live = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
      $_.Name -match '^python' -and $_.CommandLine -match 'unk_supervisor[.]py'
    })
    if ($live.Count -eq 1) {
      Stop-Process -Id $live[0].ProcessId -ErrorAction Stop
      Log "Unk supervisor stale process stopped for existing scheduled-task restart."
    } elseif ($live.Count -gt 1) {
      Log "Unk supervisor K-route installed; duplicate processes require existing-task reconciliation."
    }
  } catch {
    Log "Unk supervisor K-route recovery failed; error_class=$($_.Exception.GetType().Name)"
  }
}

function Repair-StaleUnkCompanionRoute {
  $scriptFile = Join-Path $PSScriptRoot "unk_companion.py"
  if (-not (Test-Path -LiteralPath $scriptFile)) {
    Log "Unk K-route recovery deferred: installed companion missing."
    return
  }
  try {
    $installed = [System.IO.File]::ReadAllText($scriptFile)
    $newRef = 'SUPABASE_PROJECT_REF = "kwbegsybeyyxfmavjswv"'
    $oldRef = 'SUPABASE_PROJECT_REF = "pefatniumnrxwbgnwvvh"'
    if ($installed.Contains($newRef) -and -not $installed.Contains($oldRef)) { return }
    if (-not $installed.Contains($oldRef)) {
      Log "Unk K-route recovery deferred: unrecognized installed target."
      return
    }
    # This bounded match covers only the original public routing block; do not
    # replace unrelated credentials, runtime capabilities, or user-owned state.
    $blockRegex = [regex]::new('(?ms)^SUPABASE_PROJECT_REF = "pefatniumnrxwbgnwvvh".{0,1200}?(?=\r?\nPOLL_SECONDS = )')
    $found = $blockRegex.Matches($installed)
    if ($found.Count -ne 1 -or
        -not $found[0].Value.Contains('FUNCTIONS_BASE =') -or
        -not $found[0].Value.Contains('COMPANION_URL =')) {
      Log "Unk K-route recovery deferred: ambiguous legacy routing block."
      return
    }
    $canonicalBlock = @'
SUPABASE_PROJECT_REF = "kwbegsybeyyxfmavjswv"
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip() or "sb_publishable_71YhGNn088MamieIZXBAaw_kv3w4wc9"
FUNCTIONS_BASE = f"https://{SUPABASE_PROJECT_REF}.functions.supabase.co"
COMPANION_URL = f"{FUNCTIONS_BASE}/desktop-companion"
'@
    $patched = $blockRegex.Replace($installed, $canonicalBlock, 1)
    if ($patched.Contains($oldRef) -or -not $patched.Contains($newRef)) {
      Log "Unk K-route recovery refused: target verification failed."
      return
    }
    $temporary = "$scriptFile.project-k.tmp.py"
    $backup = "$scriptFile.before-project-k-$(Get-Date -Format 'yyyyMMddHHmmss').bak"
    [System.IO.File]::WriteAllText($temporary, $patched, (New-Object System.Text.UTF8Encoding($false)))
    python -m py_compile $temporary 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
      Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
      Log "Unk K-route recovery deferred: candidate Python syntax check failed."
      return
    }
    [System.IO.File]::Replace($temporary, $scriptFile, $backup)
    Log "Unk companion installed routing repaired atomically to owner Project K."
    # A running Python interpreter retains its OLD loaded routing constants.
    # Stop precisely one old Unk child; existing supervisor owns restart and
    # heartbeat verification. No second scheduler or companion is created.
    $live = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
      $_.Name -match '^python' -and $_.CommandLine -match 'unk_companion[.]py'
    })
    if ($live.Count -eq 1) {
      Stop-Process -Id $live[0].ProcessId -ErrorAction Stop
      Log "Unk companion legacy process stopped for supervised K-route restart."
    } elseif ($live.Count -gt 1) {
      Log "Unk K-route repair installed; multiple child processes require existing supervisor reconciliation."
    }
  } catch {
    Log "Unk K-route recovery failed; error_class=$($_.Exception.GetType().Name)"
  }
}

try {
  Repair-StaleUnkCompanionRoute
  Repair-StaleUnkSupervisorRoute
  Assert-PowerPosture
  Ensure-AIBridge
  Ensure-FixerWorker
  Ensure-MediaMirrorWorker
  Ensure-RemoteDesktopCommander

  $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

  $needsReinstall = $false
  if ($task) {
    try {
      $actionArg = ($task.Actions | Select-Object -First 1).Arguments
      if ($actionArg -match '"?([A-Za-z]:\\[^"]+unk_supervisor\.py)"?') {
        $scriptPath = $Matches[1]
        if (-not (Test-Path $scriptPath)) {
          Log "Registered supervisor script missing: $scriptPath; will reinstall from durable copy."
          $needsReinstall = $true
        }
      }
    } catch {}
  }

  if (-not $task -or $needsReinstall) {
    if ($env:USERNAME -eq "SYSTEM") {
      Log "Supervisor task missing/stale, but running as SYSTEM; waiting for user-session keepalive to repair."
      exit 0
    }
    Log "Supervisor task missing or stale; repairing task registration."
    $durableInstaller = Join-Path (Join-Path $env:LOCALAPPDATA "UnkCompanion") "install_supervisor.ps1"
    $localInstaller = Join-Path $PSScriptRoot "install_supervisor.ps1"
    $installer = if (Test-Path $durableInstaller) { $durableInstaller } elseif (Test-Path $localInstaller) { $localInstaller } else { $null }
    if ($installer) {
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -RepairOnly -SkipVerify | Out-Null
    }
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  }

  if (-not $task) {
    Log "Supervisor task still missing after repair attempt."
    exit 1
  }

  $age = MarkerAgeSeconds
  $stale = ($null -eq $age) -or ($age -gt 240)
  if ($task.State -ne "Running" -or $stale) {
    Log "Starting supervisor task. state=$($task.State) marker_age_secs=$age"
    if ($task.State -eq "Running") {
      Stop-ScheduledTask -TaskName $TaskName | Out-Null
      Start-Sleep -Seconds 2
    }
    try {
      Start-ScheduledTask -TaskName $TaskName | Out-Null
      Log "Supervisor start requested by keepalive."
    } catch {
      Log "Supervisor start failed from keepalive: $($_.Exception.Message)"
    }
  } else {
    Log "Supervisor healthy. state=$($task.State) marker_age_secs=$age"
  }
} catch {
  Log "Keepalive failure: $($_.Exception.Message)"
  exit 1
}
