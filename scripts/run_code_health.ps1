# ZiggyAI Code Health Deep Dive - PowerShell Runner
# Comprehensive automated quality assurance execution script

Write-Host "🏥 ZiggyAI Code Health Deep Dive System" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Gray

# Check if we're in the right directory
if (-not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "❌ Error: Run this script from the ZiggyAI root directory" -ForegroundColor Red
    exit 1
}

# Create reports directory
New-Item -ItemType Directory -Force -Path "reports" | Out-Null

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Host "`n🔧 Checking dependencies..." -ForegroundColor Yellow

# Check Python dependencies
$pythonChecks = @(
    @{Tool="ruff"; Command="python -m ruff --version"},
    @{Tool="mypy"; Command="python -m mypy --version"},
    @{Tool="bandit"; Command="python -m bandit --version"},
    @{Tool="vulture"; Command="python -m vulture --version"},
    @{Tool="black"; Command="python -m black --version"}
)

foreach ($check in $pythonChecks) {
    try {
        $result = Invoke-Expression $check.Command 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $($check.Tool) available" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  $($check.Tool) not available" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠️  $($check.Tool) not available" -ForegroundColor Yellow
    }
}

# Check Node.js dependencies
Write-Host "`n📦 Checking frontend dependencies..." -ForegroundColor Yellow
Push-Location "frontend"

if (Test-Path "node_modules") {
    Write-Host "  ✅ Node modules installed" -ForegroundColor Green
} else {
    Write-Host "  📦 Installing Node dependencies..." -ForegroundColor Yellow
    npm install
}

# Check TypeScript
try {
    $tscVersion = npx tsc --version
    Write-Host "  ✅ TypeScript: $tscVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  TypeScript not available" -ForegroundColor Yellow
}

# Check ESLint
try {
    $eslintVersion = npx eslint --version
    Write-Host "  ✅ ESLint: $eslintVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  ESLint not available" -ForegroundColor Yellow
}

Pop-Location

# Run the master code health script
Write-Host "`n🏥 Starting comprehensive code health analysis..." -ForegroundColor Cyan
Write-Host "This may take a few minutes..." -ForegroundColor Gray

$startTime = Get-Date

try {
    # Execute the Python health checker
    python scripts/code_health_deep_dive.py
    $exitCode = $LASTEXITCODE
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "`n⏱️  Total execution time: $($duration.TotalSeconds.ToString('F1')) seconds" -ForegroundColor Gray
    
    # Check for generated reports
    $reportFiles = Get-ChildItem "reports" -Filter "*code_health_report_*.json" | Sort-Object LastWriteTime -Descending
    
    if ($reportFiles.Count -gt 0) {
        $latestReport = $reportFiles[0]
        Write-Host "📄 Latest report: $($latestReport.Name)" -ForegroundColor Green
        
        # Try to parse the report for quick summary
        try {
            $reportData = Get-Content $latestReport.FullName | ConvertFrom-Json
            $summary = $reportData.summary
            
            Write-Host "`n📊 QUICK SUMMARY:" -ForegroundColor Cyan
            Write-Host "  Total Checks: $($summary.total_checks)" -ForegroundColor Gray
            Write-Host "  Passed: $($summary.passed_checks)" -ForegroundColor Green
            Write-Host "  Failed: $($summary.failed_checks)" -ForegroundColor Red
            Write-Host "  Success Rate: $($summary.success_rate.ToString('F1'))%" -ForegroundColor $(if ($summary.success_rate -ge 80) { "Green" } elseif ($summary.success_rate -ge 60) { "Yellow" } else { "Red" })
        } catch {
            Write-Host "  📄 Report generated but summary parsing failed" -ForegroundColor Yellow
        }
    }
    
    # Provide next steps based on results
    Write-Host "`n🎯 NEXT STEPS:" -ForegroundColor Cyan
    
    if ($exitCode -eq 0) {
        Write-Host "  🎉 Code health is excellent!" -ForegroundColor Green
        Write-Host "  ✅ All systems operational" -ForegroundColor Green
        Write-Host "  🚀 Ready for production deployment" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Issues detected - review the detailed report" -ForegroundColor Yellow
        Write-Host "  🔧 Fix critical issues before deployment" -ForegroundColor Red
        Write-Host "  📋 Check individual tool outputs for specific fixes" -ForegroundColor Gray
    }
    
    # Offer to open reports directory
    Write-Host "`n📂 Open reports directory? (y/n): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'y' -or $response -eq 'Y') {
        Invoke-Item "reports"
    }
    
    exit $exitCode
    
} catch {
    Write-Host "`n❌ Code health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check the error details above and ensure all dependencies are installed." -ForegroundColor Gray
    exit 1
}