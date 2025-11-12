# ZiggyAI One-Command Startup Script
# This script starts both frontend and backend services

param(
    [switch]$Frontend,
    [switch]$Backend,
    [switch]$All = $true
)

$ErrorActionPreference = "Stop"

# Colors for output
$Green = @{ForegroundColor = "Green"}
$Blue = @{ForegroundColor = "Blue"}
$Yellow = @{ForegroundColor = "Yellow"}
$Red = @{ForegroundColor = "Red"}

Write-Host "🚀 ZiggyAI Application Launcher" @Green
Write-Host "================================" @Green

# Check if we're in the right directory
$currentPath = Get-Location
if (-not (Test-Path "frontend\package.json") -and -not (Test-Path "backend\pyproject.toml")) {
    Write-Host "❌ Please run this script from the ZiggyClean root directory" @Red
    exit 1
}

# Function to start frontend
function Start-Frontend {
    Write-Host "📱 Starting Frontend (Next.js)..." @Blue
    
    if (-not (Test-Path "frontend\node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." @Yellow
        Set-Location frontend
        npm install
        Set-Location ..
    }
    
    Set-Location frontend
    Write-Host "✅ Frontend starting on http://localhost:3000" @Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
    Set-Location ..
}

# Function to start backend
function Start-Backend {
    Write-Host "⚙️ Starting Backend (FastAPI)..." @Blue
    
    if (-not (Test-Path "backend\.venv")) {
        Write-Host "🐍 Setting up Python virtual environment..." @Yellow
        Set-Location backend
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        pip install poetry
        poetry install
        Set-Location ..
    }
    
    Set-Location backend
    Write-Host "✅ Backend starting on http://localhost:8000" @Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\Activate.ps1; poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Set-Location ..
}

# Function to check prerequisites
function Check-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." @Blue
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        Write-Host "✅ Node.js: $nodeVersion" @Green
    } catch {
        Write-Host "❌ Node.js not found. Please install Node.js 18+" @Red
        exit 1
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-Host "✅ Python: $pythonVersion" @Green
    } catch {
        Write-Host "❌ Python not found. Please install Python 3.11+" @Red
        exit 1
    }
    
    # Check Poetry
    try {
        $poetryVersion = poetry --version
        Write-Host "✅ Poetry: $poetryVersion" @Green
    } catch {
        Write-Host "⚠️ Poetry not found. Will install during backend setup..." @Yellow
    }
}

# Main execution
try {
    Check-Prerequisites
    
    if ($All -or (-not $Frontend -and -not $Backend)) {
        Write-Host "🌟 Starting full ZiggyAI stack..." @Blue
        Start-Backend
        Start-Sleep -Seconds 3  # Give backend time to start
        Start-Frontend
        
        Write-Host ""
        Write-Host "🎉 ZiggyAI is starting up!" @Green
        Write-Host "Frontend: http://localhost:3000" @Green
        Write-Host "Backend:  http://localhost:8000" @Green
        Write-Host "API Docs: http://localhost:8000/docs" @Green
        Write-Host ""
        Write-Host "Press Ctrl+C in each terminal to stop services" @Yellow
        
    } elseif ($Frontend) {
        Start-Frontend
    } elseif ($Backend) {
        Start-Backend
    }
    
} catch {
    Write-Host "❌ Error starting ZiggyAI: $($_.Exception.Message)" @Red
    exit 1
}

Write-Host "✨ Startup complete! Check the new terminal windows." @Green