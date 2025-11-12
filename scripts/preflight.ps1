# Preflight checks for Ziggy dev environment (Windows PowerShell)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section($title) {
  Write-Host "`n=== $title ===" -ForegroundColor Cyan
}

function Test-Cmd($name, $args="--version") {
  try {
    $p = Start-Process -FilePath $name -ArgumentList $args -NoNewWindow -PassThru -Wait -ErrorAction Stop
    return @{ ok = $true; code = $p.ExitCode }
  } catch {
    return @{ ok = $false; error = $_.Exception.Message }
  }
}

function Test-Port($host, $port) {
  try {
    $res = Test-NetConnection -ComputerName $host -Port $port -WarningAction SilentlyContinue
    return @{ ok = [bool]$res.TcpTestSucceeded; detail = $res }
  } catch {
    return @{ ok = $false; error = $_.Exception.Message }
  }
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$fixtures = Join-Path $backend "app\data\fixtures"
$backendBase = $env:ZIGGY_BACKEND_BASE
if (-not $backendBase) { $backendBase = "http://127.0.0.1:8000" }

Write-Section "Tools"
$node = Test-Cmd "node.exe" "--version"
$npm  = Test-Cmd "npm.cmd" "--version"
$py   = Test-Cmd (Join-Path $root ".venv\Scripts\python.exe") "--version"
if (-not $py.ok) { $py = Test-Cmd "python.exe" "--version" }
Write-Host ("node:    {0}" -f ($(if ($node.ok) { (node --version) } else { 'missing' })))
Write-Host ("npm:     {0}" -f ($(if ($npm.ok) { (npm --version) } else { 'missing' })))
Write-Host ("python:  {0}" -f ($(if ($py.ok) { (& python --version) } else { 'missing' })))

Write-Section "Environment"
$envVars = @{
  ENV = $env:ENV
  PROVIDER_MODE = $env:PROVIDER_MODE
  DATABASE_URL = $env:DATABASE_URL
  DEV_DB = $env:DEV_DB
}
$envVars.GetEnumerator() | ForEach-Object { Write-Host ("{0}={1}" -f $_.Key, ($_.Value -as [string])) }

Write-Section "Folders"
Write-Host ("backend:  {0}" -f $backend)
Write-Host ("frontend: {0}" -f $frontend)
Write-Host ("fixtures: {0}" -f $fixtures)
if (-not (Test-Path $fixtures)) { Write-Warning "Fixtures folder missing: $fixtures" } else { Write-Host "Fixtures present" -ForegroundColor Green }

Write-Section "Ports"
$apiPort = 8000
$webPort = 3000
$api = Test-Port "127.0.0.1" $apiPort
$web = Test-Port "127.0.0.1" $webPort
Write-Host ("API : {0}" -f ($(if ($api.ok) { 'LISTENING' } else { 'down' })))
Write-Host ("Web : {0}" -f ($(if ($web.ok) { 'LISTENING' } else { 'down' })))

Write-Section "HTTP health"
try {
  $health = Invoke-RestMethod -Uri ("{0}/health" -f $backendBase) -Method GET -TimeoutSec 5
  Write-Host ("/health: {0}" -f $health) -ForegroundColor Green
} catch { Write-Warning "/health failed: $($_.Exception.Message)" }
try {
  $phealth = Invoke-RestMethod -Uri ("{0}/paper/health" -f $backendBase) -Method GET -TimeoutSec 5
  $pmode = $phealth.provider_mode
  $db = $phealth.db
  Write-Host ("/paper/health: mode={0} db={1} status={2}" -f $pmode, $db, $phealth.status) -ForegroundColor Green
} catch { Write-Warning "/paper/health failed: $($_.Exception.Message)" }

Write-Section "Summary"
if (-not $node.ok -or -not $npm.ok) { Write-Warning "Node/NPM not found. Frontend may not run." }
if (-not $py.ok) { Write-Warning "Python not found. Backend may not run." }
if (-not $api.ok) { Write-Host "Tip: Start backend via VS Code task 'Backend: Dev'" -ForegroundColor Yellow }
if (-not $web.ok) { Write-Host "Tip: Start frontend via VS Code task 'Frontend: Dev'" -ForegroundColor Yellow }

Write-Host "Preflight complete." -ForegroundColor Cyan
