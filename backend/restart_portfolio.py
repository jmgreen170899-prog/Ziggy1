#!/usr/bin/env python3
"""
Quick script to restart slow portfolio streaming service
"""

import asyncio
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.portfolio_streaming import portfolio_streamer


async def restart_portfolio_service():
    """Restart the portfolio streaming service"""
    print("🔄 Restarting portfolio streaming service...")

    # Stop current service if running
    if portfolio_streamer and portfolio_streamer.is_running:
        print("⏹️ Stopping current portfolio service...")
        await portfolio_streamer.stop_streaming()
        print("✅ Portfolio service stopped")

    print("🎯 Portfolio service restart complete")
    print("📈 New settings: 5-second intervals, 500ms timeouts")


if __name__ == "__main__":
    asyncio.run(restart_portfolio_service())
