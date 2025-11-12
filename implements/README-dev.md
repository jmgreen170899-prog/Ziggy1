# ZiggyAI Development Environment Setup

This document provides essential development commands and setup procedures for the ZiggyAI paper trading system.

## Paper Trading Development Quick Start

### Prerequisites

1. **PostgreSQL Installation**: Install PostgreSQL locally for database connectivity
2. **Python Environment**: Activate ZiggyAI virtual environment
3. **Clean Environment**: Remove any live broker credentials

### Development Commands

#### Environment Cleanup (Strict Isolation)

```powershell
# Clean live broker environment variables
.\scripts\dev_clean_env.ps1
```

#### Database Startup & Health Check

```powershell
# Start PostgreSQL and verify connectivity
.\scripts\dev_db_check.ps1
```

#### Backend Startup (Strict Paper Mode)

```powershell
# Navigate to backend directory
cd c:\ZiggyClean\backend

# Activate virtual environment
& C:/ZiggyClean/.venv/Scripts/Activate.ps1

# Set paper trading environment variables
$env:PAPER_TRADING_ENABLED="true"
$env:PAPER_STRICT_ISOLATION="true"

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Development Server

```powershell
# Navigate to frontend directory
cd c:\ZiggyClean\frontend

# Start development server
npm run dev
```

### Health Monitoring

#### Check Paper Trading Health

```powershell
# Backend health endpoint (comprehensive metrics)
curl http://localhost:8000/paper/health

# Frontend dashboard
# Open browser to: http://localhost:3000/paper/status
```

#### Expected Healthy Response

```json
{
  "paper_enabled": true,
  "strict_isolation": true,
  "db_ok": true,
  "recent_trades_5m": 1,
  "open_trades": 8,
  "status": "healthy"
}
```

#### Troubleshooting Unhealthy States

**Strict Isolation Failed (HTTP 500)**
```json
{
  "strict_isolation": false,
  "detected_live_vars": ["ALPACA_SECRET_KEY", "IB_HOST"],
  "status": "unhealthy",
  "reason": "strict_isolation_failed"
}
```
**Solution**: Run `.\scripts\dev_clean_env.ps1` and restart backend

**No Recent Trades (HTTP 503)**
```json
{
  "recent_trades_5m": 0,
  "status": "unhealthy", 
  "reason": "no_recent_trades"
}
```
**Solution**: Wait for autonomous trading to generate signals, or check theory allocation

**Database Connectivity Issues**
```json
{
  "db_ok": false,
  "last_error": "Database error: connection refused",
  "status": "unhealthy"
}
```
**Solution**: Run `.\scripts\dev_db_check.ps1` to start PostgreSQL

### Paper Trading Architecture

- **Engine**: Autonomous micro-trade execution with rate limiting
- **Theories**: 5 active strategies (mean_revert, breakout, news_shock_guard, vol_regime, intraday_momentum)
- **Brain Integration**: Real-time learning pipeline with queue processing
- **Monitoring**: Live dashboard with 5-second refresh and comprehensive metrics

### Security Notes

- **Strict Isolation**: Paper trading mode prevents live broker API access
- **Environment Scanning**: Automatic detection of live credentials
- **Safe Defaults**: Paper trading runs with simulated execution only
- **Development Only**: Paper trading features restricted to dev environments

### Development Workflow

1. **Clean Environment**: `.\scripts\dev_clean_env.ps1`
2. **Start Database**: `.\scripts\dev_db_check.ps1`
3. **Start Backend**: Set env vars and run uvicorn
4. **Start Frontend**: `npm run dev`
5. **Monitor Health**: Check `/paper/status` dashboard
6. **Verify Trades**: Confirm autonomous trading operation

This setup ensures safe paper trading development with comprehensive monitoring and strict isolation from live trading systems.