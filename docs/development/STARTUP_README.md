# 🚀 ZiggyAI One-Command Startup

## Quick Start

Choose your preferred method to start the entire ZiggyAI application:

### Method 1: PowerShell Script (Recommended)

```powershell
.\start-ziggy.ps1
```

### Method 2: Batch File (Simple)

```cmd
start-ziggy.bat
```

### Method 3: PowerShell with Options

```powershell
# Start everything (default)
.\start-ziggy.ps1

# Start only frontend
.\start-ziggy.ps1 -Frontend

# Start only backend
.\start-ziggy.ps1 -Backend
```

## What These Scripts Do

1. **Check Prerequisites** - Verifies Node.js, Python, and Poetry are installed
2. **Install Dependencies** - Automatically installs npm packages and Python dependencies
3. **Start Backend** - Launches FastAPI server on `http://localhost:8000`
4. **Start Frontend** - Launches Next.js dev server on `http://localhost:3000`
5. **Open New Terminals** - Each service runs in its own terminal window

## Prerequisites

Make sure you have these installed:

- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.11+** - [Download](https://python.org/)
- **Poetry** - [Install Guide](https://python-poetry.org/docs/#installation)

## Access Points

After startup, access ZiggyAI at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

## Manual Startup (Alternative)

If you prefer manual control:

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
poetry install
poetry run uvicorn app.main:app --reload
```

## Stopping Services

- **Frontend**: Press `Ctrl+C` in the frontend terminal
- **Backend**: Press `Ctrl+C` in the backend terminal
- **All**: Close the terminal windows

## Troubleshooting

### Common Issues:

**"Execution policy" error (PowerShell)**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**"Port already in use"**

- Kill processes using ports 3000 or 8000
- Or change ports in the respective config files

**"Python/Node not found"**

- Ensure Python and Node.js are in your PATH
- Restart your terminal after installation

**Dependencies fail to install**

- Clear caches: `npm cache clean --force` and `poetry cache clear --all pypi`
- Delete `node_modules` and `.venv` folders, then retry

## Development Features

The startup scripts automatically enable:

- **Hot Reload** - Frontend and backend auto-restart on file changes
- **Development Mode** - Enhanced logging and debugging
- **Mock Data** - Uses mock data when backend services are unavailable
- **CORS Enabled** - Frontend can communicate with backend locally

## Production Deployment

For production, use:

```bash
# Build frontend
cd frontend && npm run build

# Start production backend
cd backend && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

**Happy Trading with ZiggyAI! 📈🤖**
