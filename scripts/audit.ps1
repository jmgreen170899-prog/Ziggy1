# ZiggyAI Code Health Audit - PowerShell Script
# UI-First, then API approach
# Usage: .\audit.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColoredOutput {
    param($Color, $Message)
    Write-Host "$Color$Message$Reset"
}

function Show-Help {
    Write-ColoredOutput $Blue "🏥 ZiggyAI Code Health Audit System"
    Write-ColoredOutput $Yellow "Strategy: UI-First → API-Second"
    Write-Host ""
    Write-ColoredOutput $Green "📱 Frontend Audit Commands:"
    Write-Host "  .\audit.ps1 install-frontend-deps    Install frontend audit dependencies"
    Write-Host "  .\audit.ps1 audit-frontend-quick     Type check + lint only"
    Write-Host "  .\audit.ps1 audit-frontend-full      Complete frontend audit with UI tests"
    Write-Host "  .\audit.ps1 audit-frontend-ui        Playwright visual audit + screenshots"
    Write-Host "  .\audit.ps1 audit-frontend-perf      Lighthouse performance audit"
    Write-Host ""
    Write-ColoredOutput $Green "🔧 Backend Audit Commands:"
    Write-Host "  .\audit.ps1 install-backend-deps     Install backend audit dependencies"
    Write-Host "  .\audit.ps1 audit-backend-quick      Syntax + type + security only"
    Write-Host "  .\audit.ps1 audit-backend-full       Complete backend audit with API tests"
    Write-Host "  .\audit.ps1 audit-backend-endpoints  API endpoint smoke tests"
    Write-Host "  .\audit.ps1 audit-backend-fuzz       Schemathesis API fuzzing"
    Write-Host ""
    Write-ColoredOutput $Green "🎯 Complete Audit Commands:"
    Write-Host "  .\audit.ps1 install-deps             Install all dependencies"
    Write-Host "  .\audit.ps1 audit-all                Run complete audit (frontend + backend)"
    Write-Host "  .\audit.ps1 audit-quick              Quick syntax/type checks only"
    Write-Host "  .\audit.ps1 report                   Generate consolidated health report"
    Write-Host ""
    Write-ColoredOutput $Green "🧹 Utility Commands:"
    Write-Host "  .\audit.ps1 clean                    Clean artifacts and reports"
    Write-Host "  .\audit.ps1 dev-setup                Setup development environment"
}

function Install-FrontendDeps {
    Write-ColoredOutput $Blue "📦 Installing frontend audit dependencies..."
    Set-Location frontend
    npm install
    Set-Location ..
    Write-ColoredOutput $Green "✅ Frontend dependencies installed"
}

function Install-BackendDeps {
    Write-ColoredOutput $Blue "📦 Installing backend audit dependencies..."
    python -m pip install ruff mypy bandit vulture jscpd click schemathesis httpx
    Write-ColoredOutput $Green "✅ Backend dependencies installed"
}

function Install-AllDeps {
    Install-FrontendDeps
    Install-BackendDeps
    Write-ColoredOutput $Green "✅ All audit dependencies installed"
}

function Audit-FrontendQuick {
    Write-ColoredOutput $Blue "🔍 Quick Frontend Audit (Types + Lint)..."
    Set-Location frontend
    
    Write-Host "Running TypeScript type check..."
    npm run audit:fe:types
    
    Write-Host "Running ESLint..."
    npm run audit:fe:lint
    
    Set-Location ..
    Write-ColoredOutput $Green "✅ Quick frontend audit complete"
}

function Audit-FrontendUI {
    Write-ColoredOutput $Blue "🔍 Frontend UI Audit (Playwright)..."
    Set-Location frontend
    
    try {
        npm run audit:fe:ui
        Write-ColoredOutput $Green "✅ UI audit complete - check artifacts/ui/ for screenshots"
    }
    catch {
        Write-ColoredOutput $Yellow "⚠️ UI audit failed - check if dev server is running"
    }
    
    Set-Location ..
}

function Audit-FrontendPerf {
    Write-ColoredOutput $Blue "🔍 Frontend Performance Audit (Lighthouse)..."
    Set-Location frontend
    
    try {
        npm run audit:fe:lighthouse
        Write-ColoredOutput $Green "✅ Performance audit complete"
    }
    catch {
        Write-ColoredOutput $Yellow "⚠️ Performance audit failed - check if dev server is running"
    }
    
    Set-Location ..
}

function Audit-FrontendFull {
    Audit-FrontendQuick
    Write-ColoredOutput $Blue "🔍 Full Frontend Audit..."
    
    Audit-FrontendUI
    Audit-FrontendPerf
    
    Set-Location frontend
    
    Write-Host "Running duplication check..."
    try { npm run audit:fe:dup } catch { Write-Host "Duplication check failed" }
    
    Write-Host "Running unused code check..."
    try { npm run audit:fe:unused } catch { Write-Host "Unused code check failed" }
    
    Write-Host "Generating UI health report..."
    try { npm run audit:fe:report } catch { Write-Host "Report generation failed" }
    
    Set-Location ..
    Write-ColoredOutput $Green "✅ Full frontend audit complete"
    Write-ColoredOutput $Yellow "📝 Check UI_HEALTH_REPORT.md for results"
}

function Audit-BackendQuick {
    Write-ColoredOutput $Blue "🔍 Quick Backend Audit (Syntax + Types + Security)..."
    Set-Location backend
    
    Write-Host "Running Ruff syntax check..."
    try { python -m ruff check . } catch { Write-Host "Ruff check failed" }
    
    Write-Host "Running MyPy type check..."
    try { python -m mypy . --ignore-missing-imports } catch { Write-Host "MyPy check failed" }
    
    Write-Host "Running Bandit security check..."
    try { python -m bandit -r . } catch { Write-Host "Bandit check failed" }
    
    Set-Location ..
    Write-ColoredOutput $Green "✅ Quick backend audit complete"
}

function Audit-BackendEndpoints {
    Write-ColoredOutput $Blue "🔍 Backend Endpoint Smoke Tests..."
    Set-Location backend
    
    try {
        python tests/test_endpoints_smoke.py
        Write-ColoredOutput $Green "✅ Endpoint smoke tests complete"
    }
    catch {
        Write-ColoredOutput $Yellow "⚠️ Endpoint tests failed - check if backend is running"
    }
    
    Set-Location ..
}

function Audit-BackendFuzz {
    Write-ColoredOutput $Blue "🔍 Backend API Fuzzing (Schemathesis)..."
    Set-Location backend
    
    try {
        python scripts/run_schemathesis.py
        Write-ColoredOutput $Green "✅ API fuzzing complete"
    }
    catch {
        Write-ColoredOutput $Yellow "⚠️ API fuzzing failed - check if backend is running"
    }
    
    Set-Location ..
}

function Audit-BackendFull {
    Audit-BackendQuick
    Write-ColoredOutput $Blue "🔍 Full Backend Audit..."
    
    Audit-BackendEndpoints
    Audit-BackendFuzz
    
    Set-Location backend
    
    Write-Host "Running comprehensive backend health audit..."
    try {
        python scripts/backend_health_audit.py
        Write-ColoredOutput $Green "✅ Full backend audit complete"
        Write-ColoredOutput $Yellow "📝 Check API_HEALTH_REPORT.md for results"
    }
    catch {
        Write-ColoredOutput $Yellow "⚠️ Backend health audit failed"
    }
    
    Set-Location ..
}

function Audit-Quick {
    Audit-FrontendQuick
    Audit-BackendQuick
    Write-ColoredOutput $Green "✅ Quick audit complete"
    Write-ColoredOutput $Yellow "💡 Run '.\audit.ps1 audit-all' for comprehensive testing"
}

function Audit-All {
    Write-ColoredOutput $Blue "🚀 Starting Complete Code Health Audit..."
    Write-ColoredOutput $Yellow "Phase 1: Frontend UI (Priority)"
    Audit-FrontendFull
    
    Write-Host ""
    Write-ColoredOutput $Yellow "Phase 2: Backend API (Secondary)"
    Audit-BackendFull
    
    Write-Host ""
    Write-ColoredOutput $Yellow "Phase 3: Consolidated Report"
    Generate-Report
    
    Write-ColoredOutput $Green "🎉 Complete audit finished!"
    Write-ColoredOutput $Yellow "📝 Check CODE_HEALTH_REPORT.md for consolidated results"
}

function Generate-Report {
    Write-ColoredOutput $Blue "📊 Generating consolidated health report..."
    try {
        python scripts/generate_code_health_report.py
        Write-ColoredOutput $Green "✅ CODE_HEALTH_REPORT.md generated"
        Write-ColoredOutput $Yellow "📖 Open CODE_HEALTH_REPORT.md to see results"
    }
    catch {
        Write-ColoredOutput $Red "❌ Report generation failed"
    }
}

function Setup-DevEnvironment {
    Write-ColoredOutput $Blue "🛠️ Setting up development environment..."
    
    # Create artifacts directories
    if (!(Test-Path "artifacts")) { New-Item -ItemType Directory -Path "artifacts" }
    if (!(Test-Path "artifacts/ui")) { New-Item -ItemType Directory -Path "artifacts/ui" }
    if (!(Test-Path "artifacts/frontend")) { New-Item -ItemType Directory -Path "artifacts/frontend" }
    if (!(Test-Path "artifacts/backend")) { New-Item -ItemType Directory -Path "artifacts/backend" }
    
    Install-AllDeps
    
    Write-ColoredOutput $Green "✅ Development environment ready"
    Write-ColoredOutput $Yellow "💡 Run '.\audit.ps1 audit-all' to start health monitoring"
}

function Clean-Artifacts {
    Write-ColoredOutput $Blue "🧹 Cleaning artifacts and reports..."
    
    if (Test-Path "artifacts") { Remove-Item -Recurse -Force "artifacts" }
    if (Test-Path "UI_HEALTH_REPORT.md") { Remove-Item "UI_HEALTH_REPORT.md" }
    if (Test-Path "API_HEALTH_REPORT.md") { Remove-Item "API_HEALTH_REPORT.md" }
    if (Test-Path "CODE_HEALTH_REPORT.md") { Remove-Item "CODE_HEALTH_REPORT.md" }
    
    Write-ColoredOutput $Green "✅ Cleanup complete"
}

function Show-Status {
    Write-ColoredOutput $Blue "📊 Current Status:"
    
    if (Test-Path "CODE_HEALTH_REPORT.md") {
        Write-ColoredOutput $Green "✅ Health report exists"
        $reportContent = Get-Content "CODE_HEALTH_REPORT.md" -Raw
        if ($reportContent -match "P0.*issues") {
            Write-Host $matches[0]
        }
    } else {
        Write-ColoredOutput $Yellow "⚠️ No health report found - run '.\audit.ps1 audit-all'"
    }
    
    Write-Host ""
    Write-ColoredOutput $Blue "📁 Artifacts:"
    if (Test-Path "artifacts") {
        Get-ChildItem "artifacts" -Recurse | Select-Object Name, Length, LastWriteTime | Format-Table
    } else {
        Write-Host "No artifacts directory"
    }
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install-deps" { Install-AllDeps }
    "install-frontend-deps" { Install-FrontendDeps }
    "install-backend-deps" { Install-BackendDeps }
    "audit-frontend-quick" { Audit-FrontendQuick }
    "audit-frontend-ui" { Audit-FrontendUI }
    "audit-frontend-perf" { Audit-FrontendPerf }
    "audit-frontend-full" { Audit-FrontendFull }
    "audit-backend-quick" { Audit-BackendQuick }
    "audit-backend-endpoints" { Audit-BackendEndpoints }
    "audit-backend-fuzz" { Audit-BackendFuzz }
    "audit-backend-full" { Audit-BackendFull }
    "audit-quick" { Audit-Quick }
    "audit-all" { Audit-All }
    "report" { Generate-Report }
    "dev-setup" { Setup-DevEnvironment }
    "clean" { Clean-Artifacts }
    "status" { Show-Status }
    "fe" { Audit-FrontendFull }
    "be" { Audit-BackendFull }
    "quick" { Audit-Quick }
    "all" { Audit-All }
    default {
        Write-ColoredOutput $Red "❌ Unknown command: $Command"
        Write-Host ""
        Show-Help
    }
}