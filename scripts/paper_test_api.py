"""
Minimal Paper Trading API for Frontend Testing
"""

from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Paper Trading Test API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/paper/health")
async def paper_health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "environment": "development",
        "debug_mode": True,
        "components": {
            "paper_engine": "available",
            "bandit_allocator": "available",
            "online_learner": "available",
            "database": "connected",
        },
    }


@app.get("/paper/runs")
async def list_paper_runs():
    return [
        {
            "id": 1,
            "name": "Demo Paper Run",
            "status": "ACTIVE",
            "started_at": datetime.utcnow(),
            "total_trades": 15,
            "total_pnl": 127.50,
            "current_balance": 100127.50,
            "win_rate": 0.67,
            "avg_fill_latency_ms": 45.2,
        }
    ]


@app.get("/paper/runs/1/trades")
async def get_trades():
    return [
        {
            "id": 1,
            "trade_id": "trade_001",
            "ticker": "SPY",
            "direction": "BUY",
            "quantity": 1.0,
            "theory_name": "mean_revert",
            "status": "FILLED",
            "signal_time": datetime.utcnow(),
            "fill_price": 582.45,
            "realized_pnl": 12.50,
        },
        {
            "id": 2,
            "trade_id": "trade_002",
            "ticker": "QQQ",
            "direction": "SELL",
            "quantity": 2.0,
            "theory_name": "breakout",
            "status": "FILLED",
            "signal_time": datetime.utcnow(),
            "fill_price": 487.23,
            "realized_pnl": -5.20,
        },
    ]


@app.get("/paper/runs/1/theories")
async def get_theory_performance():
    return [
        {
            "theory_name": "mean_revert",
            "status": "ACTIVE",
            "current_allocation": 0.25,
            "total_trades_executed": 5,
            "total_pnl": 45.30,
            "win_rate": 0.80,
            "sharpe_ratio": 1.25,
            "avg_fill_latency_ms": 42.1,
        },
        {
            "theory_name": "breakout",
            "status": "ACTIVE",
            "current_allocation": 0.20,
            "total_trades_executed": 3,
            "total_pnl": -15.20,
            "win_rate": 0.33,
            "sharpe_ratio": -0.45,
            "avg_fill_latency_ms": 38.5,
        },
        {
            "theory_name": "news_shock_guard",
            "status": "ACTIVE",
            "current_allocation": 0.15,
            "total_trades_executed": 2,
            "total_pnl": 67.40,
            "win_rate": 1.0,
            "sharpe_ratio": 2.15,
            "avg_fill_latency_ms": 51.2,
        },
        {
            "theory_name": "vol_regime",
            "status": "ACTIVE",
            "current_allocation": 0.25,
            "total_trades_executed": 4,
            "total_pnl": 22.10,
            "win_rate": 0.75,
            "sharpe_ratio": 0.85,
            "avg_fill_latency_ms": 47.8,
        },
        {
            "theory_name": "intraday_momentum",
            "status": "ACTIVE",
            "current_allocation": 0.15,
            "total_trades_executed": 1,
            "total_pnl": 7.90,
            "win_rate": 1.0,
            "sharpe_ratio": 1.65,
            "avg_fill_latency_ms": 35.4,
        },
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
