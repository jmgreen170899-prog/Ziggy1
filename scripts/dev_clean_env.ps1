# ZiggyAI Development Environment Cleanup
# Unsets known live broker environment variables for strict paper trading isolation

Write-Host "Cleaning live broker environment variables..." -ForegroundColor Cyan

# Define known live broker environment variables
$LiveBrokerVars = @(
    # Alpaca
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY", 
    "ALPACA_BASE_URL",
    "ALPACA_PAPER_BASE_URL",
    
    # Interactive Brokers
    "IB_HOST",
    "IB_PORT", 
    "IB_CLIENT_ID",
    "IB_ACCOUNT",
    "IB_GATEWAY_PORT",
    
    # TD Ameritrade
    "TDA_API_KEY",
    "TDA_CLIENT_ID",
    "TDA_REDIRECT_URI",
    "TDA_ACCOUNT",
    
    # E*TRADE
    "ETRADE_API_KEY",
    "ETRADE_SECRET_KEY",
    "ETRADE_SANDBOX",
    
    # Robinhood
    "ROBINHOOD_USERNAME",
    "ROBINHOOD_PASSWORD",
    "ROBINHOOD_MFA_CODE",
    
    # Other common broker vars
    "BROKER_API_KEY",
    "BROKER_SECRET",
    "TRADING_API_KEY",
    "LIVE_TRADING_ENABLED"
)

$clearedVars = @()
$foundVars = @()

foreach ($var in $LiveBrokerVars) {
    $value = [Environment]::GetEnvironmentVariable($var, "Process")
    if ($value) {
        $foundVars += $var
        try {
            Remove-Item "env:$var" -ErrorAction SilentlyContinue
            $clearedVars += $var
            Write-Host "Cleared: $var" -ForegroundColor Green
        } catch {
            Write-Host "Failed to clear: $var" -ForegroundColor Yellow
        }
    }
}

# Summary
Write-Host ""
Write-Host "Environment Cleanup Summary:" -ForegroundColor Cyan
if ($foundVars.Count -eq 0) {
    Write-Host "No live broker variables found - environment already clean!" -ForegroundColor Green
} else {
    Write-Host "Found $($foundVars.Count) live broker variables:" -ForegroundColor Yellow
    foreach ($var in $foundVars) {
        Write-Host "   - $var" -ForegroundColor Gray
    }
    
    if ($clearedVars.Count -gt 0) {
        Write-Host "Successfully cleared $($clearedVars.Count) variables" -ForegroundColor Green
    }
}

# Verification
Write-Host ""
Write-Host "Verifying strict isolation..." -ForegroundColor Cyan
$remainingVars = @()
foreach ($var in $LiveBrokerVars) {
    $value = [Environment]::GetEnvironmentVariable($var, "Process")
    if ($value) {
        $remainingVars += $var
    }
}

if ($remainingVars.Count -eq 0) {
    Write-Host "Strict paper trading isolation achieved!" -ForegroundColor Green
    Write-Host "Now set: `$env:PAPER_TRADING_ENABLED=`"true`"; `$env:PAPER_STRICT_ISOLATION=`"true`"" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "$($remainingVars.Count) variables still present:" -ForegroundColor Yellow
    foreach ($var in $remainingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host "These may be system-level environment variables that require manual removal" -ForegroundColor Gray
    exit 1
}