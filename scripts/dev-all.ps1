param(
  [int]$FrontendPort = 3000,
  [int]$BackendPort = 8000,
  [string]$FrontendHost = "127.0.0.1",
  [string]$BackendHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

function Wait-HttpOk {
  param(
    [Parameter(Mandatory=$true)][string]$Url,
    [int]$TimeoutSec = 90
  )
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
    try {
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
        return $true
      }
    } catch {
      Start-Sleep -Seconds 1
    }
  }
  return $false
}

$root = Resolve-Path "$PSScriptRoot/.."
Write-Host "Repo root: $root"

# Start backend (uvicorn) in a new window
$backendCmd = "cd `"$root/backend`"; `"$root/.venv/Scripts/python.exe`" -m uvicorn app.main:app --host $BackendHost --port $BackendPort --reload"
Start-Process -WindowStyle Minimized -FilePath "powershell" -ArgumentList "-NoExit","-Command", $backendCmd | Out-Null
Write-Host "Started backend on http://${BackendHost}:${BackendPort}"

# Start frontend (Next.js) in a new window
$frontendCmd = "cd `"$root/frontend`"; npm run dev"
Start-Process -WindowStyle Minimized -FilePath "powershell" -ArgumentList "-NoExit","-Command", $frontendCmd | Out-Null
Write-Host "Starting frontend dev server..."

# Wait for backend health
$backendHealth = "http://${BackendHost}:${BackendPort}/paper/health"
if (Wait-HttpOk -Url $backendHealth -TimeoutSec 120) {
  Write-Host "Backend healthy: $backendHealth"
} else {
  Write-Warning "Backend did not become healthy within timeout: $backendHealth"
}

# Wait for frontend root
$frontendUrl = "http://${FrontendHost}:${FrontendPort}"
if (Wait-HttpOk -Url $frontendUrl -TimeoutSec 120) {
  Write-Host "Frontend ready: $frontendUrl"
} else {
  Write-Warning "Frontend did not become ready within timeout: $frontendUrl"
}

# Open browser to frontend
Start-Process $frontendUrl
