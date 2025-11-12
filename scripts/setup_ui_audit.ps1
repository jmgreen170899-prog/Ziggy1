# ZiggyAI UI Audit System Setup
# Installs dependencies and configures the complete UI audit workflow

param(
    [switch]$InstallDeps,
    [switch]$RunAudit,
    [switch]$Help
)

if ($Help) {
    Write-Host "ZiggyAI UI Audit System" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Setup and run comprehensive UI audits with Playwright and Lighthouse"
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup_ui_audit.ps1 -InstallDeps    # Install dependencies"
    Write-Host "  .\scripts\setup_ui_audit.ps1 -RunAudit       # Run full audit"
    Write-Host "  .\scripts\setup_ui_audit.ps1 -Help           # Show this help"
    Write-Host ""
    Write-Host "Manual Steps:" -ForegroundColor Yellow
    Write-Host "  1. Start backend: cd backend; uvicorn app.main:app --reload"
    Write-Host "  2. Start frontend: cd frontend; npm run dev"
    Write-Host "  3. Run audit: .\scripts\setup_ui_audit.ps1 -RunAudit"
    Write-Host ""
    exit 0
}

Write-Host "🎯 ZiggyAI UI Audit System Setup" -ForegroundColor Cyan

# Check prerequisites
function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Node.js not found. Please install Node.js" -ForegroundColor Red
        exit 1
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found. Please install Python" -ForegroundColor Red
        exit 1
    }
    
    # Check if in ZiggyClean directory
    if (!(Test-Path "frontend\package.json")) {
        Write-Host "❌ Must be run from ZiggyClean root directory" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Prerequisites check passed" -ForegroundColor Green
}

# Install dependencies
function Install-Dependencies {
    Write-Host "📦 Installing UI audit dependencies..." -ForegroundColor Yellow
    
    # Install Playwright in frontend
    Write-Host "Installing Playwright..." -ForegroundColor Gray
    Push-Location frontend
    try {
        npm install -D @playwright/test playwright
        npx playwright install
        Write-Host "✅ Playwright installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install Playwright" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    
    # Install Lighthouse globally
    Write-Host "Installing Lighthouse..." -ForegroundColor Gray
    try {
        npm install -g lighthouse
        Write-Host "✅ Lighthouse installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install Lighthouse" -ForegroundColor Red
        exit 1
    }
    
    # Create Playwright config if it doesn't exist
    $playwrightConfig = @"
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '../scripts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
"@
    
    if (!(Test-Path "frontend\playwright.config.ts")) {
        $playwrightConfig | Out-File -FilePath "frontend\playwright.config.ts" -Encoding UTF8
        Write-Host "✅ Playwright config created" -ForegroundColor Green
    }
    
    Write-Host "🎉 Dependencies installed successfully!" -ForegroundColor Green
}

# Check if servers are running
function Test-Servers {
    Write-Host "🔍 Checking if servers are running..." -ForegroundColor Yellow
    
    # Check backend
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method HEAD -TimeoutSec 3
        Write-Host "✅ Backend is running" -ForegroundColor Green
    } catch {
        Write-Host "❌ Backend not running at localhost:8000" -ForegroundColor Red
        Write-Host "💡 Start with: cd backend; uvicorn app.main:app --reload" -ForegroundColor Yellow
        return $false
    }
    
    # Check frontend
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -Method HEAD -TimeoutSec 3
        Write-Host "✅ Frontend is running" -ForegroundColor Green
    } catch {
        Write-Host "❌ Frontend not running at localhost:3000" -ForegroundColor Red
        Write-Host "💡 Start with: cd frontend; npm run dev" -ForegroundColor Yellow
        return $false
    }
    
    return $true
}

# Run complete audit
function Start-UIAudit {
    Write-Host "🎯 Running complete UI audit..." -ForegroundColor Cyan
    
    # Ensure artifacts directory exists
    if (!(Test-Path "artifacts\ui")) {
        New-Item -ItemType Directory -Path "artifacts\ui" -Force | Out-Null
    }
    
    # Check servers
    if (!(Test-Servers)) {
        Write-Host "❌ Please start both backend and frontend servers first" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "📸 Step 1/3: Running Playwright audit..." -ForegroundColor Yellow
    Push-Location frontend
    try {
        npx playwright test ../scripts/ui_audit.spec.ts --reporter=line
        Write-Host "✅ Playwright audit completed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Playwright audit had issues, continuing..." -ForegroundColor Yellow
    }
    Pop-Location
    
    Write-Host "🚀 Step 2/3: Running Lighthouse audit..." -ForegroundColor Yellow
    try {
        PowerShell -ExecutionPolicy Bypass -File "scripts\run_lighthouse.ps1"
        Write-Host "✅ Lighthouse audit completed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Lighthouse audit had issues, continuing..." -ForegroundColor Yellow
    }
    
    Write-Host "📊 Step 3/3: Generating report..." -ForegroundColor Yellow
    try {
        python scripts\generate_ui_report.py
        Write-Host "✅ Report generated: ui_improvements.md" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to generate report" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n🎉 UI Audit Complete!" -ForegroundColor Green
    Write-Host "📋 Report: ui_improvements.md" -ForegroundColor Cyan
    Write-Host "📸 Screenshots: artifacts/ui/*.png" -ForegroundColor Cyan
    Write-Host "📊 Raw data: artifacts/ui/*.json" -ForegroundColor Cyan
    
    # Open report if possible
    if (Get-Command code -ErrorAction SilentlyContinue) {
        Write-Host "`n💡 Opening report in VS Code..." -ForegroundColor Yellow
        code ui_improvements.md
    }
}

# Main execution
Test-Prerequisites

if ($InstallDeps) {
    Install-Dependencies
} elseif ($RunAudit) {
    Start-UIAudit
} else {
    Write-Host "Usage: .\scripts\setup_ui_audit.ps1 -InstallDeps | -RunAudit | -Help" -ForegroundColor Yellow
    Write-Host "Run with -Help for detailed usage information" -ForegroundColor Gray
}