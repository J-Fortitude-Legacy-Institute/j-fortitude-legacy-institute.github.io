# remote_desktop_commander_relay.ps1 — durable foreground runner for the Remote Desktop Commander relay.
# This script is designed to run as a dedicated Scheduled Task under the signed-in user.
# Task Scheduler owns the long-lived foreground process and can restart it after crashes;
# unk_keepalive.ps1 owns task registration/health and falls back to direct launch only if needed.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$StateDir = Join-Path $env:USERPROFILE ".unk-companion"
$ReceiptFile = Join-Path $StateDir "remote_desktop_commander_relay_latest.json"
$StdoutFile = Join-Path $StateDir "remote_desktop_commander.stdout.log"
$StderrFile = Join-Path $StateDir "remote_desktop_commander.stderr.log"
$Package = '@wonderwhy-er/desktop-commander@latest'

function Write-Receipt([hashtable]$Receipt) {
  try {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    $Receipt['checked_at'] = (Get-Date).ToString('o')
    $Receipt['package'] = $Package
    $Receipt['user'] = $env:USERNAME
    $Receipt | ConvertTo-Json -Depth 6 | Set-Content -Path $ReceiptFile -Encoding UTF8
  } catch {}
}

# Read only new log bytes from the specific child process launched here.
# Parent-process health is not proof of remote tool delivery. These
# signals are recovery hints only, never a successful execution receipt.
function Read-NewRelayLog([string]$Path, [long]$Offset) {
  if (-not (Test-Path -LiteralPath $Path)) {
    return @{ text = ''; offset = $Offset }
  }
  $stream = $null
  $reader = $null
  try {
    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    if ($stream.Length -lt $Offset) { $Offset = 0L }
    [void]$stream.Seek($Offset, [System.IO.SeekOrigin]::Begin)
    $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true, 4096, $true)
    $chunk = $reader.ReadToEnd()
    return @{ text = $chunk; offset = [long]$stream.Position }
  } catch {
    return @{ text = ''; offset = $Offset }
  } finally {
    if ($reader) { $reader.Dispose() }
    if ($stream) { $stream.Dispose() }
  }
}

# Process transport messages in actual log order. A single read can contain
# "Device ready" first and a fatal CHANNEL_ERROR later; the old code reset
# faults whenever ANY ready marker existed in that read and ignored the later
# failure, which made a wedged Online relay appear recovered.
#
# These events are only local recovery hints. "SUBSCRIBED"/"Device ready"
# never certifies remote tool-call delivery or an authenticated user workflow.
function Advance-RelayTransportFaults(
  [string]$Text, [int]$Count, $Since,
  [string]$FaultPattern, [string]$ReadyPattern
) {
  $events = [regex]::Matches($Text, "(?:$ReadyPattern)|(?:$FaultPattern)", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  $currentCount = [int]$Count
  $currentSince = $Since
  foreach ($event in $events) {
    if ($event.Value -match $FaultPattern) {
      if ($null -eq $currentSince) { $currentSince = Get-Date }
      $currentCount += 1
    } elseif ($event.Value -match $ReadyPattern) {
      $currentCount = 0
      $currentSince = $null
    }
  }
  return @{ faults = $currentCount; since = $currentSince; events = $events.Count }
}


# v0.3.1 emits DEBUG-only Realtime subscription state into a separate,
# vendor-redacted device status log even when stdout has no DEBUG output.
# Inspect only status markers since this process launch, never raw data in
# receipts; deduplicate messages moved across the three rotated files.
function Read-VendorTransportSignals([string]$Directory, [datetime]$SinceUtc, [hashtable]$Seen,
  [string]$FaultPattern, [string]$ReadyPattern) {
  $events = New-Object 'System.Collections.Generic.List[object]'
  if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
    return @{ text = ''; events = 0 }
  }
  $now = [datetime]::UtcNow
  $sequence = 0
  foreach ($date in @($now.AddDays(-1),$now)) {
    $day = $date.ToString('ddd',[Globalization.CultureInfo]::InvariantCulture).ToLowerInvariant()
    foreach ($suffix in @('.2','.1','')) {
      $path = Join-Path $Directory ("remote-$day$suffix.log")
      if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
      try {
        foreach ($line in @(Get-Content -LiteralPath $path -Tail 2048 -Encoding UTF8 -ErrorAction Stop)) {
          if ($line -notmatch '^(?<stamp>\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\s{2}(?<message>.*)$') { continue }
          $stampText = [string]$Matches['stamp']
          $message = [string]$Matches['message']
          $stamp = [DateTimeOffset]::MinValue
          if (-not [DateTimeOffset]::TryParse($stampText,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::AssumeUniversal,[ref]$stamp)) { continue }
          $at = $stamp.UtcDateTime
          # Expired entries can leave $Seen after ten minutes; never replay them
          # from still-present rotated logs as fresh transport failures.
          if ($at -lt $SinceUtc.ToUniversalTime() -or $at -lt $now.AddMinutes(-10) -or $at -gt $now.AddMinutes(1)) { continue }
          $hits = [regex]::Matches($message,"(?:$ReadyPattern)|(?:$FaultPattern)",
            [Text.RegularExpressions.RegexOptions]::IgnoreCase)
          if (-not $hits.Count) { continue }
          $identity = "$stampText|$($line.Length)|$($line.GetHashCode())"
          if ($Seen.ContainsKey($identity)) { continue }
          $Seen[$identity] = $at
          foreach ($hit in $hits) {
            $events.Add([pscustomobject]@{ time = $at; sequence = $sequence; signal = [string]$hit.Value })
            $sequence++
          }
        }
      } catch { } # A rotated log can be renamed between listing and read.
    }
  }
  foreach ($key in @($Seen.Keys)) {
    if ($Seen[$key] -lt $now.AddMinutes(-10)) { $Seen.Remove($key) }
  }
  $ordered = @($events | Sort-Object -Property time,sequence)
  $signals = @($ordered | ForEach-Object { $_.signal })
  return @{ text = ($signals -join [Environment]::NewLine); events = $signals.Count }
}

# The vendor-redacted channel log and the process streams are separate
# observers with no trustworthy shared ordering. Never discard a new stream
# fault merely because the vendor log also emitted SUBSCRIBED in this poll.
# Preserve the vendor's own ordered markers, then add independent stream
# faults conservatively. An additional later ready poll can clear the streak.
function Merge-RelayTransportSignals(
  [string]$StreamText, [string]$VendorText, [int]$VendorEvents,
  [string]$FaultPattern
) {
  if ($VendorEvents -le 0) { return $StreamText }
  $streamFaults = @([regex]::Matches($StreamText, $FaultPattern,
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) |
    ForEach-Object { [string]$_.Value })
  if ($streamFaults.Count -eq 0) { return $VendorText }
  return $VendorText + [Environment]::NewLine + ($streamFaults -join [Environment]::NewLine)
}

if ($env:USERNAME -eq 'SYSTEM') {
  Write-Receipt @{ ok = $false; state = 'refused_system_context'; reason = 'paired session belongs to interactive user' }
  exit 20
}

# Jwoffice's damaged npx cache produced ENOENT (exit -4058) despite a
# separate verified 0.3.1 install. Prefer that locally staged immutable CLI
# when present, and retain vendor npx as a fallback for other installations.
# Neither mode is evidence that a remote tool call was delivered.
$PinnedVersion = '0.3.1'
$PinnedCliSha256 = '7e58b9d5d64732ff8cd77cd477de30751feb6b59bc2353dfaa78825f015b2f2b'
$LocalPackage = Join-Path $env:LOCALAPPDATA 'UnkCompanion\remote-agent\node_modules\@wonderwhy-er\desktop-commander'
$LocalManifest = Join-Path $LocalPackage 'package.json'
$LocalCli = Join-Path $LocalPackage 'dist\index.js'
$node = Get-Command node.exe -ErrorAction SilentlyContinue
$trustedLocal = $false
try {
  if ($node -and (Test-Path $LocalManifest) -and (Test-Path $LocalCli)) {
    $metadata = Get-Content $LocalManifest -Raw -ErrorAction Stop | ConvertFrom-Json
    $digest = (Get-FileHash -LiteralPath $LocalCli -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
    $trustedLocal = ([string]$metadata.version -eq $PinnedVersion) -and ($digest -eq $PinnedCliSha256)
  }
} catch { $trustedLocal = $false }

if (-not $trustedLocal) {
  $npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
  if (-not $npx) { $npx = Get-Command npx -ErrorAction SilentlyContinue }
  if (-not $npx) {
    Write-Receipt @{ ok = $false; state = 'dependency_missing'; reason = 'verified_local_cli_and_npx_missing' }
    exit 21
  }
}

$comspec = if ($env:ComSpec) { $env:ComSpec } else { 'C:\Windows\System32\cmd.exe' }
if (-not (Test-Path $comspec)) {
  Write-Receipt @{ ok = $false; state = 'dependency_missing'; reason = 'cmd_not_found' }
  exit 22
}

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$command = if ($trustedLocal) { "node `"$LocalCli`" remote --persist-session" } else { "npx --yes $Package remote --persist-session" }
$commandMode = if ($trustedLocal) { 'verified_local_node' } else { 'npx_vendor_fallback' }
try {
  $proc = Start-Process -FilePath $comspec `
    -ArgumentList @('/d','/s','/c',$command) `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $StdoutFile `
    -RedirectStandardError $StderrFile

  # This is a process launch only; remote tool execution is not proven.
  Write-Receipt @{ ok = $false; state = 'launching'; command_mode = $commandMode; persisted_session = $true; pid = [int]$proc.Id; execution_probe_required = $true; cli_hash_verified = $trustedLocal }
  # Windows can advertise Online even after Realtime stops delivering tools.
  # Observe only this launch's log bytes; reconnect clears the fault cluster.
  # Even a SUBSCRIBED log is never accepted as executed-tool evidence.
  $launchTime = Get-Date
  $vendorLogDir = Join-Path $env:USERPROFILE '.desktop-commander-device'
  $vendorSeen = @{}
  $stdoutOffset = 0L
  $stderrOffset = 0L
  $transportFaults = 0
  $faultSince = $null
  $transportFaultPattern = '(?i)CHANNEL_ERROR|channel subscription timed out|channel subscription status:\s*TIMED_OUT|presence track not acknowledged|presence track remained unavailable|presence ack timed out|transport failure|device registered, but NOT reachable|realtime channel is not open|IncreaseConnectionPool|ClientJoinRateLimitReached'
  $transportReadyPattern = '(?i)Device ready|channel subscription status:\s*SUBSCRIBED'
  while (-not $proc.WaitForExit(30000)) {
    $out = Read-NewRelayLog $StdoutFile $stdoutOffset
    $err = Read-NewRelayLog $StderrFile $stderrOffset
    $stdoutOffset = [long]$out.offset
    $stderrOffset = [long]$err.offset
    $delta = [string]$out.text + [Environment]::NewLine + [string]$err.text
    # Prefer new markers in the DEBUG-inclusive, vendor-redacted device log;
    # streams remain a fallback if that log has no new transport signals.
    $vendor = Read-VendorTransportSignals $vendorLogDir $launchTime.ToUniversalTime() $vendorSeen $transportFaultPattern $transportReadyPattern
    $delta = Merge-RelayTransportSignals $delta ([string]$vendor.text) ([int]$vendor.events) $transportFaultPattern
    # Advance through every event IN ORDER; readiness earlier in this
    # batch must not mask a later transport error. Do not count a plain
    # heartbeat or Online registration as execution-ready.
    $faultState = Advance-RelayTransportFaults $delta $transportFaults $faultSince $transportFaultPattern $transportReadyPattern
    $transportFaults = [int]$faultState.faults
    $faultSince = $faultState.since
    if ($null -ne $faultSince -and $transportFaults -ge 4 -and
        ((Get-Date) - $faultSince).TotalSeconds -ge 120 -and
        ((Get-Date) - $launchTime).TotalSeconds -ge 180) {
      # Killing cmd.exe alone strands its Node child; stop the tree owned
      # by this runner and let the existing Scheduled Task retry normally.
      Write-Receipt @{ ok = $false; state = 'sustained_transport_fault_restart_requested'; pid = [int]$proc.Id; fault_count = $transportFaults; execution_probe_required = $true; credentials_preserved = $true }
      try {
        $treeKill = Start-Process -FilePath 'taskkill.exe' -ArgumentList @('/PID', [string]$proc.Id, '/T', '/F') -WindowStyle Hidden -PassThru -Wait
        if ([int]$treeKill.ExitCode -eq 0) {
          Write-Receipt @{ ok = $false; state = 'transport_recovery_tree_stopped'; execution_probe_required = $true; credentials_preserved = $true }
          exit 24
        }
      } catch {}
      # A failed stop cannot justify launching a competing remote identity.
      Write-Receipt @{ ok = $false; state = 'transport_recovery_tree_stop_failed'; pid = [int]$proc.Id; execution_probe_required = $true }
    }
  }
  $proc.WaitForExit()
  $exitCode = [int]$proc.ExitCode
  $tail = ''
  try { $tail = ((Get-Content $StderrFile -Tail 30 -ErrorAction SilentlyContinue) -join "`n") } catch {}
  Write-Receipt @{ ok = $false; state = 'exited'; exit_code = $exitCode; error_tail = $tail; execution_probe_required = $true; cli_hash_verified = $trustedLocal }
  exit $exitCode
} catch {
  $tail = ''
  try { $tail = ((Get-Content $StderrFile -Tail 30 -ErrorAction SilentlyContinue) -join "`n") } catch {}
  Write-Receipt @{ ok = $false; state = 'runner_exception'; reason = $_.Exception.Message; error_tail = $tail }
  exit 23
}
