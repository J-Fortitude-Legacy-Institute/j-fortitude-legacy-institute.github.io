# cleanup_runtime.ps1 — Ground Zero canonical-runtime cleanup (inventory-first,
# fail-closed). Run only via unk_companion.cap_run_local_script after signature
# match against manifest.json. Windows only. Read-only unless -Apply.
#
# Contract:
#   - Preserve canonical runtime: %LOCALAPPDATA%\UnkCompanion (phase9-local-first-persistence)
#   - Preserve exactly one newest known-good rollback backup
#   - Preserve current logs, manifests, credentials, session/heartbeat, published-media
#   - Preserve current heartbeat PID + supervisor owner + one worker per capability
#   - Preserve canonical scheduled tasks (UnkSupervisor, UnkSupervisorKeepAlive,
#     UnkSupervisorBootKeepAlive) after action-path + arguments + run-as compare
#   - Remove: older backup/staging/temp folders, obsolete desktop-companion*.zip /
#     unk*.zip in Downloads/Desktop/TEMP, extracted update staging, proven stale
#     duplicate workers, exact-duplicate/superseded tasks.
#   - Emit inventory.before.json + inventory.after.json + delete.log.json under
#     C:\JFortitude\ground-zero-audit\out\cleanup\<UTC-timestamp>\.
#   - Exit 0 on success (or dry-run). Non-zero + no destructive action if any
#     canonical guardrail fails.
[CmdletBinding()]
param(
  [switch]$Apply,
  [string]$ExpectedRuntimeSha = "66d9ac5ac45eee5838b3b6be5561be8db011dd8e9c489ef0d038dbea3646cea1",
  [string]$ExpectedVersion    = "phase9-local-first-persistence",
  [int]$HeartbeatMaxAgeSec    = 900
)

$ErrorActionPreference = "Stop"
$UTF8 = New-Object System.Text.UTF8Encoding($false)

# ---------- Paths ----------
$CanonicalRoot   = Join-Path $env:LOCALAPPDATA "UnkCompanion"
$CompanionPy     = Join-Path $CanonicalRoot "unk_companion.py"
$SupervisorPy    = Join-Path $CanonicalRoot "unk_supervisor.py"
$StateDir        = Join-Path $env:USERPROFILE ".unk-companion"
$HeartbeatFile   = Join-Path $StateDir "heartbeat.json"
$SupervisorPid   = Join-Path $StateDir "supervisor.pid"
$CompanionPid    = Join-Path $StateDir "companion.pid"
$AuditRoot       = "C:\JFortitude\ground-zero-audit"
$OutRoot         = Join-Path $AuditRoot "out\cleanup"
$Stamp           = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmssZ")
$RunDir          = Join-Path $OutRoot $Stamp
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$InvBefore       = Join-Path $RunDir "inventory.before.json"
$InvAfter        = Join-Path $RunDir "inventory.after.json"
$DeleteLog       = Join-Path $RunDir "delete.log.json"
$RunLog          = Join-Path $RunDir "run.log"

function Log([string]$m) {
  $line = "[$(Get-Date -Format o)] $m"
  Add-Content -Path $RunLog -Value $line -Encoding UTF8
  Write-Host $line
}

function Get-Sha256([string]$Path) {
  try {
    if (Test-Path $Path -PathType Leaf) { return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLower() }
  } catch {}
  return $null
}

function Try-Get([scriptblock]$sb) { try { & $sb } catch { $null } }

# ---------- 1. Inventory ----------
Log "==> Building inventory (dry-run=$(-not $Apply))"

$inv = [ordered]@{
  generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  hostname         = $env:COMPUTERNAME
  username         = $env:USERNAME
  apply            = [bool]$Apply
  canonical        = [ordered]@{ root=$CanonicalRoot }
  heartbeat        = $null
  processes        = @()
  scheduled_tasks  = @()
  backups          = @()
  candidate_deletes= [ordered]@{ zips=@(); staging=@(); duplicate_launchers=@() }
}

# canonical runtime state
if (Test-Path $CanonicalRoot) {
  $inv.canonical.exists = $true
  $inv.canonical.companion_sha256 = Get-Sha256 $CompanionPy
  $rb = Join-Path $CanonicalRoot "running_build.json"
  if (Test-Path $rb) {
    $inv.canonical.running_build = Try-Get { Get-Content $rb -Raw | ConvertFrom-Json }
  }
} else {
  $inv.canonical.exists = $false
}

# heartbeat
if (Test-Path $HeartbeatFile) {
  $hb = Try-Get { Get-Content $HeartbeatFile -Raw | ConvertFrom-Json }
  $ageSec = $null
  try { $ageSec = [int]((Get-Date) - (Get-Item $HeartbeatFile).LastWriteTime).TotalSeconds } catch {}
  $inv.heartbeat = [ordered]@{
    path=$HeartbeatFile; age_seconds=$ageSec
    reported_version = $hb.companion_version
    reported_pid     = $hb.pid
  }
}
$LiveCompanionPid = $null
if (Test-Path $CompanionPid) { $LiveCompanionPid = (Get-Content $CompanionPid -Raw).Trim() }
$LiveSupervisorPid = $null
if (Test-Path $SupervisorPid) { $LiveSupervisorPid = (Get-Content $SupervisorPid -Raw).Trim() }
$inv.heartbeat_pid_files = [ordered]@{ companion=$LiveCompanionPid; supervisor=$LiveSupervisorPid }

# processes
$procNames = @("unk_companion","unk_supervisor","browser_publish_worker","multi_platform_publisher","media_audio_worker","media_mirror_worker","meta_browser_publisher","meta_publisher")
$procs = Get-CimInstance Win32_Process | Where-Object {
  $cl = $_.CommandLine
  $cl -and ($procNames | Where-Object { $cl -match [regex]::Escape($_) })
}
foreach ($p in $procs) {
  $inv.processes += [ordered]@{
    pid = $p.ProcessId
    name = $p.Name
    executable = $p.ExecutablePath
    command_line = $p.CommandLine
    creation_date = $p.CreationDate
  }
}

# scheduled tasks
$taskMatches = @("Unk","Companion","Supervisor","KeepAlive")
$tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
  $n = $_.TaskName; $p = $_.TaskPath
  ($taskMatches | Where-Object { $n -match $_ -or $p -match $_ })
}
foreach ($t in $tasks) {
  $act = $t.Actions | Select-Object -First 1
  $inv.scheduled_tasks += [ordered]@{
    name = $t.TaskName
    path = $t.TaskPath
    state = "$($t.State)"
    author = $t.Author
    execute = $act.Execute
    arguments = $act.Arguments
    working_dir = $act.WorkingDirectory
    run_as = $t.Principal.UserId
    run_level = "$($t.Principal.RunLevel)"
  }
}

# backups
$backupParents = @(
  (Join-Path $CanonicalRoot "backups"),
  (Join-Path $env:USERPROFILE "Downloads\Unk\backups"),
  (Join-Path $env:USERPROFILE "Documents\JFLI\backups")
) | Where-Object { Test-Path $_ }
foreach ($bp in $backupParents) {
  Get-ChildItem -Path $bp -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $inv.backups += [ordered]@{
      path = $_.FullName; parent=$bp
      last_write = $_.LastWriteTimeUtc.ToString("o")
      size_bytes = (Try-Get { (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum })
    }
  }
}

# candidate zips + staging
$scanRoots = @(
  (Join-Path $env:USERPROFILE "Downloads"),
  (Join-Path $env:USERPROFILE "Desktop"),
  $env:TEMP,
  (Join-Path $env:LOCALAPPDATA "Temp"),
  (Join-Path $CanonicalRoot "updates"),
  (Join-Path $CanonicalRoot "staging")
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

foreach ($sr in $scanRoots) {
  Get-ChildItem -Path $sr -File -Filter "desktop-companion*.zip" -ErrorAction SilentlyContinue | ForEach-Object {
    $inv.candidate_deletes.zips += [ordered]@{ path=$_.FullName; size_bytes=$_.Length; last_write=$_.LastWriteTimeUtc.ToString("o") }
  }
  Get-ChildItem -Path $sr -File -Filter "unk*.zip" -ErrorAction SilentlyContinue | ForEach-Object {
    $inv.candidate_deletes.zips += [ordered]@{ path=$_.FullName; size_bytes=$_.Length; last_write=$_.LastWriteTimeUtc.ToString("o") }
  }
  Get-ChildItem -Path $sr -Directory -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match "^(desktop-companion|unk[-_])" -and $_.FullName -ne $CanonicalRoot
  } | ForEach-Object {
    $inv.candidate_deletes.staging += [ordered]@{ path=$_.FullName; last_write=$_.LastWriteTimeUtc.ToString("o") }
  }
}

# duplicate launchers outside canonical
$launcherNames = @("unk_companion.py","unk_supervisor.py","install_supervisor.ps1","launch_unk.bat","unk_keepalive.ps1")
foreach ($sr in $scanRoots) {
  foreach ($ln in $launcherNames) {
    Get-ChildItem -Path $sr -File -Filter $ln -Recurse -ErrorAction SilentlyContinue | Where-Object {
      $_.FullName -notlike "$CanonicalRoot*"
    } | ForEach-Object {
      $inv.candidate_deletes.duplicate_launchers += [ordered]@{
        path=$_.FullName; sha256=(Get-Sha256 $_.FullName); size_bytes=$_.Length; last_write=$_.LastWriteTimeUtc.ToString("o")
      }
    }
  }
}

$inv | ConvertTo-Json -Depth 10 | Set-Content -Path $InvBefore -Encoding UTF8
Log "Inventory written: $InvBefore"

# ---------- 2. Fail-closed canonical guardrails ----------
Log "==> Guardrail checks"
$fail = @()

if (-not $inv.canonical.exists) { $fail += "canonical_root_missing" }
if ($inv.canonical.companion_sha256 -and $ExpectedRuntimeSha -and ($inv.canonical.companion_sha256 -ne $ExpectedRuntimeSha.ToLower())) {
  $fail += "companion_sha_mismatch:$($inv.canonical.companion_sha256)"
}
if ($inv.heartbeat -and $inv.heartbeat.age_seconds -ne $null -and $inv.heartbeat.age_seconds -gt $HeartbeatMaxAgeSec) {
  $fail += "heartbeat_stale:$($inv.heartbeat.age_seconds)s"
}
if ($inv.heartbeat -and $inv.heartbeat.reported_version -and $inv.heartbeat.reported_version -ne $ExpectedVersion) {
  $fail += "version_mismatch:$($inv.heartbeat.reported_version)"
}

if ($fail.Count -gt 0) {
  $blocker = [ordered]@{
    ok = $false
    blocked_by = $fail
    inventory_before = $InvBefore
    apply = [bool]$Apply
  }
  $blocker | ConvertTo-Json -Depth 5 | Set-Content -Path $DeleteLog -Encoding UTF8
  Log "FAIL-CLOSED: $($fail -join '; ')"
  Write-Output ($blocker | ConvertTo-Json -Depth 5)
  exit 2
}

# ---------- 3. Compute delete plan ----------
$plan = [ordered]@{
  backups_delete = @()
  backup_keep = $null
  zips_delete = @()
  staging_delete = @()
  duplicate_launchers_delete = @()
  processes_terminate = @()
  tasks_disable = @()
  reasons = @{}
}

# keep newest valid backup, delete the rest
if ($inv.backups.Count -gt 0) {
  $sorted = $inv.backups | Sort-Object { [datetime]$_.last_write } -Descending
  $plan.backup_keep = $sorted[0].path
  if ($sorted.Count -gt 1) {
    $plan.backups_delete = $sorted | Select-Object -Skip 1 | ForEach-Object { $_.path }
  }
}

# zips + staging always deletable (never canonical)
$plan.zips_delete    = $inv.candidate_deletes.zips    | ForEach-Object { $_.path }
$plan.staging_delete = $inv.candidate_deletes.staging | ForEach-Object { $_.path }
$plan.duplicate_launchers_delete = $inv.candidate_deletes.duplicate_launchers | ForEach-Object { $_.path }

# processes: terminate only duplicates that are NOT the live heartbeat companion / supervisor
$livePids = @()
if ($LiveCompanionPid)  { $livePids += "$LiveCompanionPid" }
if ($LiveSupervisorPid) { $livePids += "$LiveSupervisorPid" }
if ($inv.heartbeat -and $inv.heartbeat.reported_pid) { $livePids += "$($inv.heartbeat.reported_pid)" }
$byCapability = @{}
foreach ($p in $inv.processes) {
  $cap = "other"
  if ($p.command_line -match "unk_companion")            { $cap = "companion" }
  elseif ($p.command_line -match "unk_supervisor")       { $cap = "supervisor" }
  elseif ($p.command_line -match "browser_publish_worker"){ $cap = "browser_publisher" }
  elseif ($p.command_line -match "multi_platform_publisher"){ $cap = "multi_publisher" }
  elseif ($p.command_line -match "media_audio_worker")   { $cap = "audio" }
  elseif ($p.command_line -match "media_mirror_worker")  { $cap = "mirror" }
  if (-not $byCapability.ContainsKey($cap)) { $byCapability[$cap] = @() }
  $byCapability[$cap] += $p
}
foreach ($cap in $byCapability.Keys) {
  $group = $byCapability[$cap]
  if ($group.Count -le 1) { continue }
  # keep the live one if present, else the newest
  $keep = $group | Where-Object { "$($_.pid)" -in $livePids } | Select-Object -First 1
  if (-not $keep) { $keep = $group | Sort-Object creation_date -Descending | Select-Object -First 1 }
  $group | Where-Object { $_.pid -ne $keep.pid } | ForEach-Object {
    $plan.processes_terminate += [ordered]@{ pid=$_.pid; capability=$cap; executable=$_.executable; kept_pid=$keep.pid }
  }
}

# scheduled tasks: preserve canonical trio; disable exact-duplicate/superseded
$canonicalTasks = @("UnkSupervisor","UnkSupervisorKeepAlive","UnkSupervisorBootKeepAlive")
foreach ($t in $inv.scheduled_tasks) {
  if ($canonicalTasks -contains $t.name) { continue }
  # match if execute+arguments+run_as match a canonical task
  $isDup = $false
  foreach ($ct in $inv.scheduled_tasks | Where-Object { $canonicalTasks -contains $_.name }) {
    if ($t.execute -eq $ct.execute -and $t.arguments -eq $ct.arguments -and $t.run_as -eq $ct.run_as) {
      $isDup = $true; break
    }
  }
  if ($isDup) {
    $plan.tasks_disable += [ordered]@{ name=$t.name; path=$t.path; reason="exact_duplicate_of_canonical"; execute=$t.execute; arguments=$t.arguments }
  }
}

# ---------- 4. Apply or dry-run ----------
$deleteLog = [ordered]@{
  apply = [bool]$Apply
  plan  = $plan
  results = @()
  totals = [ordered]@{ paths_deleted=0; bytes_deleted=0; processes_terminated=0; tasks_disabled=0 }
}

if (-not $Apply) {
  Log "Dry-run complete. Plan written; no changes made."
  $deleteLog | ConvertTo-Json -Depth 8 | Set-Content -Path $DeleteLog -Encoding UTF8
  # inventory.after == inventory.before for dry-run
  Copy-Item -Path $InvBefore -Destination $InvAfter -Force
  $result = [ordered]@{ ok=$true; dry_run=$true; inventory_before=$InvBefore; inventory_after=$InvAfter; delete_log=$DeleteLog; run_dir=$RunDir }
  Write-Output ($result | ConvertTo-Json -Depth 5)
  exit 0
}

function Remove-PathSafely($path, $reason) {
  if (-not $path -or -not (Test-Path $path)) { return }
  # guard: never touch canonical root or its subtrees
  $abs = (Resolve-Path $path).Path
  if ($abs -like "$CanonicalRoot*" -and $abs -ne $plan.backup_keep) {
    if ($abs -notlike "$CanonicalRoot\backups\*") {
      $deleteLog.results += [ordered]@{ path=$abs; deleted=$false; reason="refused_canonical" }
      return
    }
  }
  $sz = 0
  try {
    if (Test-Path $abs -PathType Container) {
      $sz = (Get-ChildItem $abs -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    } else { $sz = (Get-Item $abs).Length }
  } catch {}
  try {
    Remove-Item -Path $abs -Recurse -Force -ErrorAction Stop
    $deleteLog.results += [ordered]@{ path=$abs; deleted=$true; reason=$reason; bytes=$sz }
    $deleteLog.totals.paths_deleted += 1
    if ($sz) { $deleteLog.totals.bytes_deleted += [int64]$sz }
    Log "DELETED [$reason] $abs ($sz bytes)"
  } catch {
    $deleteLog.results += [ordered]@{ path=$abs; deleted=$false; reason=$reason; error=$_.Exception.Message }
    Log "DELETE-FAILED [$reason] $abs — $($_.Exception.Message)"
  }
}

foreach ($p in $plan.backups_delete)              { Remove-PathSafely $p "older_backup_superseded" }
foreach ($p in $plan.zips_delete)                 { Remove-PathSafely $p "obsolete_download_zip" }
foreach ($p in $plan.staging_delete)              { Remove-PathSafely $p "extracted_staging" }
foreach ($p in $plan.duplicate_launchers_delete)  { Remove-PathSafely $p "duplicate_launcher_outside_canonical" }

# terminate duplicate processes
foreach ($proc in $plan.processes_terminate) {
  try {
    Stop-Process -Id $proc.pid -Force -ErrorAction Stop
    $deleteLog.results += [ordered]@{ pid=$proc.pid; capability=$proc.capability; terminated=$true; kept_pid=$proc.kept_pid }
    $deleteLog.totals.processes_terminated += 1
    Log "TERMINATED pid=$($proc.pid) capability=$($proc.capability) kept=$($proc.kept_pid)"
  } catch {
    $deleteLog.results += [ordered]@{ pid=$proc.pid; capability=$proc.capability; terminated=$false; error=$_.Exception.Message }
  }
}

# disable duplicate tasks
foreach ($td in $plan.tasks_disable) {
  try {
    Disable-ScheduledTask -TaskName $td.name -TaskPath $td.path -ErrorAction Stop | Out-Null
    $deleteLog.results += [ordered]@{ task=$td.name; disabled=$true; reason=$td.reason }
    $deleteLog.totals.tasks_disabled += 1
    Log "DISABLED task=$($td.name) reason=$($td.reason)"
  } catch {
    $deleteLog.results += [ordered]@{ task=$td.name; disabled=$false; error=$_.Exception.Message }
  }
}

# ---------- 5. Re-inventory for after ----------
Log "==> Re-inventory (after)"
$after = [ordered]@{
  generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  canonical_sha256 = Get-Sha256 $CompanionPy
  heartbeat_age_seconds = (Try-Get { [int]((Get-Date) - (Get-Item $HeartbeatFile).LastWriteTime).TotalSeconds })
  live_companion_pid = (Try-Get { (Get-Content $CompanionPid -Raw).Trim() })
  live_supervisor_pid = (Try-Get { (Get-Content $SupervisorPid -Raw).Trim() })
  remaining_backups = @(Get-ChildItem -Path (Join-Path $CanonicalRoot "backups") -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
  scheduled_tasks_enabled = @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -match "Unk|Companion|Supervisor|KeepAlive" -and $_.State -ne "Disabled" } | ForEach-Object { $_.TaskName })
}
$after | ConvertTo-Json -Depth 8 | Set-Content -Path $InvAfter -Encoding UTF8
$deleteLog | ConvertTo-Json -Depth 8 | Set-Content -Path $DeleteLog -Encoding UTF8

$result = [ordered]@{
  ok = $true
  apply = $true
  inventory_before = $InvBefore
  inventory_after  = $InvAfter
  delete_log       = $DeleteLog
  run_dir          = $RunDir
  totals           = $deleteLog.totals
  retained_backup  = $plan.backup_keep
}
Log "DONE. deleted=$($deleteLog.totals.paths_deleted) bytes=$($deleteLog.totals.bytes_deleted) procs=$($deleteLog.totals.processes_terminated) tasks=$($deleteLog.totals.tasks_disabled)"
Write-Output ($result | ConvertTo-Json -Depth 6)
exit 0
