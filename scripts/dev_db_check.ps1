# ZiggyAI Development Database Startup & Health Check
# Starts PostgreSQL locally and waits until connectable

param(
    [int]$Port = 5432,
    [string]$DatabaseHost = "localhost",
    [int]$TimeoutSeconds = 30
)

Write-Host "Checking PostgreSQL status..." -ForegroundColor Cyan

# Check if PostgreSQL service is running
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($pgService) {
    if ($pgService.Status -ne "Running") {
        Write-Host "Starting PostgreSQL service..." -ForegroundColor Yellow
        try {
            Start-Service $pgService.Name
            Write-Host "PostgreSQL service started" -ForegroundColor Green
        } catch {
            Write-Host "Failed to start PostgreSQL service: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "PostgreSQL service already running" -ForegroundColor Green
    }
} else {
    Write-Host "PostgreSQL service not found - trying direct connection..." -ForegroundColor Yellow
}

# Test database connectivity
Write-Host "Testing database connection..." -ForegroundColor Cyan
$startTime = Get-Date
$connected = $false

while ((Get-Date) -lt $startTime.AddSeconds($TimeoutSeconds)) {
    try {
        # Test connection using Python (since we're in a Python project)
        python -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect(host='$DatabaseHost', port='$Port', dbname='postgres', user='postgres', password='password', connect_timeout=2)
    conn.close()
    print('SUCCESS')
    sys.exit(0)
except Exception as e:
    print(f'FAILED: {e}')
    sys.exit(1)
"
        
        if ($LASTEXITCODE -eq 0) {
            $connected = $true
            break
        }
    } catch {
        # Continue trying
    }
    
    Write-Host "Waiting for database..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

if ($connected) {
    Write-Host "PostgreSQL is ready and accepting connections!" -ForegroundColor Green
    Write-Host "Connection: ${DatabaseHost}:${Port}" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "Failed to connect to PostgreSQL within $TimeoutSeconds seconds" -ForegroundColor Red
    Write-Host "Try:" -ForegroundColor Yellow
    Write-Host "   - Install PostgreSQL if not installed" -ForegroundColor Gray
    Write-Host "   - Check if postgres user/password is configured" -ForegroundColor Gray
    Write-Host "   - Verify PostgreSQL is listening on ${DatabaseHost}:${Port}" -ForegroundColor Gray
    exit 1
}