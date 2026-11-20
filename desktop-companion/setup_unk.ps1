# setup_unk.ps1 — one-shot installer + launcher for the UNK desktop companion.
# Run from inside the extracted desktop-companion folder:
#   powershell -ExecutionPolicy Bypass -File .\setup_unk.ps1
# Optional: pass the 8-char enrollment code as an argument to skip the prompt.
param(
  [string]$EnrollCode = ""
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "==> UNK desktop companion setup" -ForegroundColor Cyan
Write-Host "Working folder: $PSScriptRoot"

$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue) }
if (-not $python) {
  Write-Host "Python not found. Install Python 3 from https://python.org and re-run." -ForegroundColor Red
  exit 1
}
$pyExe = $python.Source
Write-Host "Using Python: $pyExe"

Write-Host "==> Installing Python dependencies..." -ForegroundColor Cyan
& $pyExe -m pip install --quiet --disable-pip-version-check requests pillow keyring playwright cryptography

Write-Host "==> Ensuring Playwright browser is installed..." -ForegroundColor Cyan
& $pyExe -m playwright install chromium

if (-not $EnrollCode) {
  $EnrollCode = Read-Host "Paste the 8-character enrollment code from /grant-engine/desktop-command, or press Enter if already enrolled"
}
$EnrollCode = $EnrollCode.Trim()

if ($EnrollCode) { $env:UNK_ENROLL_CODE = $EnrollCode }

Write-Host "==> Verifying enrollment / credentials..." -ForegroundColor Cyan
& $pyExe .\unk_companion.py --status | Out-Host

$supervisor = Join-Path $PSScriptRoot "install_supervisor.ps1"
if (Test-Path $supervisor) {
  Write-Host "==> Installing always-on supervisor..." -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $supervisor
} else {
  Write-Host "install_supervisor.ps1 not found; launching companion directly." -ForegroundColor Yellow
  & $pyExe .\unk_companion.py
}