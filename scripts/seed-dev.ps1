# Seed dev environment: ensure DB init, set up dev portfolio, and warm caches
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section($title) {
  Write-Host "`n=== $title ===" -ForegroundColor Cyan
}

$backendBase = $env:ZIGGY_BACKEND_BASE
if (-not $backendBase) { $backendBase = "http://127.0.0.1:8000" }

Write-Section "Ping backend"
try {
  $pong = Invoke-RestMethod -Uri ("{0}/health" -f $backendBase) -Method GET -TimeoutSec 5
  Write-Host "Backend reachable." -ForegroundColor Green
} catch {
  Write-Error "Backend not reachable at $backendBase. Start 'Backend: Dev' task first."; exit 1
}

Write-Section "DB init"
try {
  $init = Invoke-RestMethod -Uri ("{0}/dev/db/init" -f $backendBase) -Method POST -TimeoutSec 5
  Write-Host ("DB init scheduled: {0}" -f ($init.scheduled))
} catch { Write-Warning "DB init call failed: $($_.Exception.Message)" }

Start-Sleep -Seconds 1
try {
  $dbs = Invoke-RestMethod -Uri ("{0}/dev/db/status" -f $backendBase) -Method GET -TimeoutSec 5
  Write-Host ("DB connected={0}, dialect={1}" -f $dbs.db.connected, $dbs.db.dialect)
} catch { Write-Warning "DB status failed: $($_.Exception.Message)" }

Write-Section "Dev portfolio setup"
try {
  $setup = Invoke-RestMethod -Uri ("{0}/dev/portfolio/setup" -f $backendBase) -Method POST -TimeoutSec 10
  Write-Host ("Portfolio setup: {0}" -f ($setup.status)) -ForegroundColor Green
  if ($setup.portfolio_id) { Write-Host ("PortfolioId: {0}" -f $setup.portfolio_id) }
} catch {
  Write-Warning "Portfolio setup failed: $($_.Exception.Message)"
}

try {
  $fund = @{ additional_capital = 50000 }
  $funded = Invoke-RestMethod -Uri ("{0}/dev/portfolio/fund" -f $backendBase) -Method POST -ContentType 'application/json' -Body ($fund | ConvertTo-Json) -TimeoutSec 10
  Write-Host ("Funding status: {0}" -f ($funded.status))
} catch {
  Write-Warning "Funding skipped/failed: $($_.Exception.Message)"
}

try {
  $status = Invoke-RestMethod -Uri ("{0}/dev/portfolio/status" -f $backendBase) -Method GET -TimeoutSec 10
  Write-Host ("Portfolio: balance=${0} trading={1}" -f $status.current_balance, $status.autonomous_trading.enabled)
} catch { Write-Warning "Portfolio status failed: $($_.Exception.Message)" }

Write-Section "Warm signals cache"
try {
  $tickers = @("AAPL","MSFT","NVDA","SPY","QQQ")
  $payload = @{ tickers = $tickers; include_regime = $true } | ConvertTo-Json
  $resp = Invoke-RestMethod -Uri ("{0}/signals/watchlist" -f $backendBase) -Method POST -ContentType 'application/json' -Body $payload -TimeoutSec 15
  Write-Host ("Signals generated: {0} / {1}" -f $resp.signal_count, $resp.total_tickers)
} catch {
  Write-Warning "Signal warm-up failed: $($_.Exception.Message)"
}

Write-Host "Seed complete." -ForegroundColor Cyan
