# backend/app/api/routes_market_calendar.py
"""
Market calendar and economic events API routes.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from ..services.macro import fred_data, get_market_calendar_data, market_calendar


# Market Brain Integration
try:
    from app.services.market_brain.simple_data_hub import DataSource, enhance_market_data

    BRAIN_AVAILABLE = True
    _enhance_market_data = enhance_market_data
    _DataSource = DataSource
except ImportError:
    BRAIN_AVAILABLE = False
    _enhance_market_data = None
    _DataSource = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market_calendar"])


@router.get("/calendar", response_model=None)
async def get_full_calendar():
    """Get comprehensive market calendar data including holidays, earnings, and economic events."""
    try:
        data = await get_market_calendar_data()

        # Enhance with Market Brain Intelligence
        if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
            try:
                data = _enhance_market_data(data, _DataSource.CALENDAR)
            except Exception as e:
                # Log error but don't break the response
                print(f"Market brain calendar enhancement failed: {e}")

        return data
    except Exception as e:
        logger.error(f"Error in calendar endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holidays", response_model=None)
async def get_holidays(year: int | None = Query(None)):
    """Get market holidays for specified year."""
    try:
        if year is None:
            year = datetime.now().year
        holidays = await market_calendar.get_market_holidays(year)
        return {"holidays": holidays, "year": year}
    except Exception as e:
        logger.error(f"Error fetching holidays: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings", response_model=None)
async def get_earnings_calendar(
    start_date: str | None = Query(None), end_date: str | None = Query(None)
):
    """Get earnings calendar for date range."""
    try:
        earnings = await market_calendar.get_earnings_calendar(start_date, end_date)
        return {
            "earnings": earnings,
            "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
            "end_date": end_date or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        }
    except Exception as e:
        logger.error(f"Error fetching earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economic", response_model=None)
async def get_economic_events(
    start_date: str | None = Query(None), end_date: str | None = Query(None)
):
    """Get economic events calendar."""
    try:
        events = await market_calendar.get_economic_calendar(start_date, end_date)
        result = {
            "events": events,
            "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
            "end_date": end_date or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        }

        # Enhance with Market Brain Intelligence
        if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
            try:
                result = _enhance_market_data(result, _DataSource.CALENDAR)
            except Exception as e:
                # Log error but don't break the response
                print(f"Market brain economic events enhancement failed: {e}")

        return result
    except Exception as e:
        logger.error(f"Error fetching economic events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule", response_model=None)
async def get_market_schedule(date: str | None = Query(None)):
    """Get market schedule for specific date."""
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        schedule = await market_calendar.get_market_schedule(date)
        return schedule
    except Exception as e:
        logger.error(f"Error fetching market schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators", response_model=None)
async def get_economic_indicators():
    """Get key economic indicators from FRED."""
    try:
        indicators = await fred_data.get_key_indicators()
        return {"indicators": indicators, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error fetching economic indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fred/{series_id}", response_model=None)
async def get_fred_series(series_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get specific FRED economic data series."""
    try:
        data = await fred_data.get_series_data(series_id, limit)
        return {"series_id": series_id, "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching FRED series {series_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
