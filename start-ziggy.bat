@echo off
setlocal enabledelayedexpansion

echo.
echo 🚀 ZiggyAI One-Command Startup
echo ==============================

REM Check if we're in the right directory
if not exist "frontend\package.json" (
    if not exist "backend\pyproject.toml" (
        echo ❌ Please run this script from the ZiggyClean root directory
        pause
        exit /b 1
    )
)

echo 📱 Starting ZiggyAI Frontend and Backend...

REM Start Backend
echo ⚙️ Starting Backend (FastAPI)...
start "ZiggyAI Backend" cmd /k "cd backend && python -m venv .venv 2>nul && .venv\Scripts\activate && pip install poetry 2>nul && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

REM Start Frontend
echo 📱 Starting Frontend (Next.js)...
start "ZiggyAI Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo 🎉 ZiggyAI is starting up!
echo ================================
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo ✨ Check the new terminal windows for status
echo Press any key to exit this launcher...
pause >nul