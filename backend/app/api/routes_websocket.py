# app/api/routes_websocket.py
"""
WebSocket endpoints for real-time data streaming
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.websocket import connection_manager, market_streamer


logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/market")
async def websocket_market_data(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data streaming
    
    Clients can subscribe to symbols and receive live price updates
    """
    await connection_manager.connect(websocket, "market_data")
    
    try:
        while True:
            # Receive messages from client (subscriptions, commands, etc.)
            data = await websocket.receive_json()
            
            message_type = data.get("type", "")
            
            if message_type == "subscribe":
                # Subscribe to symbols
                symbols = data.get("symbols", [])
                if symbols:
                    logger.info(f"WebSocket subscribing to symbols: {symbols}")
                    await market_streamer.start_streaming(symbols)
                    
                    # Send acknowledgment
                    await connection_manager.send_json_personal(
                        {
                            "type": "subscription_ack",
                            "symbols": symbols,
                            "status": "subscribed"
                        },
                        websocket
                    )
            
            elif message_type == "unsubscribe":
                # Unsubscribe from symbols
                symbols = data.get("symbols", [])
                if symbols:
                    logger.info(f"WebSocket unsubscribing from symbols: {symbols}")
                    await market_streamer.stop_streaming(symbols)
                    
                    # Send acknowledgment
                    await connection_manager.send_json_personal(
                        {
                            "type": "subscription_ack",
                            "symbols": symbols,
                            "status": "unsubscribed"
                        },
                        websocket
                    )
            
            elif message_type == "ping":
                # Respond to ping with pong
                await connection_manager.send_json_personal(
                    {"type": "pong", "ts": data.get("ts")},
                    websocket
                )
                
    except WebSocketDisconnect:
        logger.info("WebSocket market data client disconnected")
    except Exception as e:
        logger.error(f"WebSocket market data error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/news")
async def websocket_news_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time news streaming
    
    Receives live news updates as they become available
    """
    await connection_manager.connect(websocket, "news_feed")
    
    # Start news streaming service if not already running
    try:
        from app.services.news_streaming import news_streamer
        await news_streamer.start_streaming()
    except Exception as e:
        logger.warning(f"Could not start news streaming: {e}")
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()
            
            message_type = data.get("type", "")
            
            if message_type == "ping":
                # Respond to ping with pong
                await connection_manager.send_json_personal(
                    {"type": "pong", "ts": data.get("ts")},
                    websocket
                )
                
    except WebSocketDisconnect:
        logger.info("WebSocket news client disconnected")
    except Exception as e:
        logger.error(f"WebSocket news error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert notifications
    
    Receives alerts as they are triggered
    """
    await connection_manager.connect(websocket, "alerts")
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()
            
            message_type = data.get("type", "")
            
            if message_type == "ping":
                # Respond to ping with pong
                await connection_manager.send_json_personal(
                    {"type": "pong", "ts": data.get("ts")},
                    websocket
                )
                
    except WebSocketDisconnect:
        logger.info("WebSocket alerts client disconnected")
    except Exception as e:
        logger.error(f"WebSocket alerts error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/signals")
async def websocket_trading_signals(websocket: WebSocket):
    """
    WebSocket endpoint for real-time trading signals
    
    Receives trading signals as they are generated
    """
    await connection_manager.connect(websocket, "trading_signals")
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()
            
            message_type = data.get("type", "")
            
            if message_type == "ping":
                # Respond to ping with pong
                await connection_manager.send_json_personal(
                    {"type": "pong", "ts": data.get("ts")},
                    websocket
                )
                
    except WebSocketDisconnect:
        logger.info("WebSocket signals client disconnected")
    except Exception as e:
        logger.error(f"WebSocket signals error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/portfolio")
async def websocket_portfolio(websocket: WebSocket):
    """
    WebSocket endpoint for real-time portfolio updates
    
    Receives portfolio updates as positions change
    """
    await connection_manager.connect(websocket, "portfolio")
    
    # Start portfolio streaming if available
    try:
        from app.services.portfolio_streaming import portfolio_streamer
        await portfolio_streamer.start_streaming()
    except Exception as e:
        logger.debug(f"Could not start portfolio streaming: {e}")
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()
            
            message_type = data.get("type", "")
            
            if message_type == "ping":
                # Respond to ping with pong
                await connection_manager.send_json_personal(
                    {"type": "pong", "ts": data.get("ts")},
                    websocket
                )
                
    except WebSocketDisconnect:
        logger.info("WebSocket portfolio client disconnected")
    except Exception as e:
        logger.error(f"WebSocket portfolio error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/charts")
async def websocket_charts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chart data streaming
    
    Receives candlestick/OHLC updates for charting
    """
    await connection_manager.connect(websocket, "charts")
    
    try:
        while True:
            # Receive messages from client (symbol subscriptions, timeframe changes, etc.)
            data = await websocket.receive_json()
            
            message_type = data.get("type", "")
            
            if message_type == "subscribe":
                # Subscribe to chart data for symbols
                symbols = data.get("symbols", [])
                timeframe = data.get("timeframe", "1m")
                
                if symbols:
                    logger.info(f"WebSocket subscribing to chart data: {symbols} ({timeframe})")
                    
                    # Send acknowledgment
                    await connection_manager.send_json_personal(
                        {
                            "type": "subscription_ack",
                            "symbols": symbols,
                            "timeframe": timeframe,
                            "status": "subscribed"
                        },
                        websocket
                    )
            
            elif message_type == "ping":
                # Respond to ping with pong
                await connection_manager.send_json_personal(
                    {"type": "pong", "ts": data.get("ts")},
                    websocket
                )
                
    except WebSocketDisconnect:
        logger.info("WebSocket charts client disconnected")
    except Exception as e:
        logger.error(f"WebSocket charts error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.get("/ws/status", response_model=None)
async def websocket_status():
    """
    Get WebSocket connection statistics
    
    Returns connection counts and metrics for all WebSocket channels
    """
    return connection_manager.get_connection_stats()
