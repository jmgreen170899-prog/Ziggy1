"""
ZiggyAI Trace Routes - Decision DAG Visualization

Brain-first data flow: Every trace request must read/write through memory layer.
Mission: Show actual decision graph (inputs → transforms → fusion → risk → sizing).

Routes:
- GET /signal/trace - Get decision trace DAG and raw JSON for power users
"""

import logging
import os
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


# Environment configuration
TRACE_ENABLED = os.getenv("EXPLAIN_ENABLE_TRACE", "1") == "1"
BRAIN_STRICT = os.getenv("BRAIN_STRICT", "1") == "1"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/signal", tags=["trace"])

# Check if services are available
try:
    from app.memory.events import append_event, get_event_by_id, iter_events
    from app.services.trace import build_trace

    TRACE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Trace services not available: {e}")
    TRACE_AVAILABLE = False


class TraceNode(BaseModel):
    """Node in the decision DAG."""

    id: str = Field(..., description="Node ID")
    type: str = Field(..., description="Node type")
    name: str = Field(..., description="Display name")
    latency_ms: float | None = Field(None, description="Processing latency")


class TraceEdge(BaseModel):
    """Edge in the decision DAG."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str | None = Field(None, description="Edge label")


class TraceGraph(BaseModel):
    """Decision DAG structure."""

    nodes: list[TraceNode] = Field(..., description="Graph nodes")
    edges: list[TraceEdge] = Field(..., description="Graph edges")


class TraceResponse(BaseModel):
    """Response model for trace data."""

    event_id: str = Field(..., description="Memory event ID")
    trace_id: str = Field(..., description="Unique trace ID")
    ticker: str = Field(..., description="Stock symbol")

    # Graph structure
    graph: TraceGraph = Field(..., description="Decision DAG")

    # Raw data for power users
    raw: dict[str, Any] = Field(..., description="Raw trace data")

    # Metadata
    total_latency_ms: float = Field(..., description="Total processing time")
    timestamp: str = Field(..., description="Trace timestamp")
    cached: bool = Field(..., description="Whether trace was cached")


def _build_trace_data(event_id: str) -> dict[str, Any]:
    """Build trace data for an event."""
    start_time = time.time()

    # Try to get existing event from memory
    try:
        existing_event = get_event_by_id(event_id)
        if existing_event and existing_event.get("trace_data"):
            # Return cached trace
            trace_data = existing_event["trace_data"]
            trace_data["cached"] = True
            return trace_data
    except Exception as e:
        logger.warning(f"Could not retrieve event {event_id}: {e}")
        existing_event = None

    if not existing_event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    # Build trace from event data
    try:
        # Extract data for trace construction
        ticker = existing_event.get("ticker", "UNKNOWN")

        # Mock input data (replace with real data extraction)
        inputs = {
            "ticker": ticker,
            "market_data": {"price": 150.0, "volume": 1000000},
            "timestamp": existing_event.get("ts"),
        }

        # Mock feature extraction results
        features = existing_event.get("explain", {}).get(
            "features", {"momentum": 0.3, "sentiment": 0.2, "volatility": 0.15, "volume": 0.1}
        )

        # Mock fusion results
        fusion = {
            "p_up_raw": existing_event.get("p_up_model", 0.5),
            "confidence": 0.75,
            "regime": existing_event.get("regime", "normal"),
        }

        # Mock calibration step
        calibration = {"p_up_calibrated": existing_event.get("p_up", 0.5), "ece": 0.05}

        # Mock risk management
        risk = {"max_position_size": 0.05, "stop_loss": 0.02, "risk_score": 0.3}

        # Mock position sizing
        sizing = {"position_size": 0.025, "shares": 100, "dollar_amount": 15000}

        # Build trace using service
        if TRACE_AVAILABLE:
            trace_data = build_trace(inputs, features, fusion, calibration, risk, sizing)
        else:
            # Fallback trace structure
            trace_data = {
                "graph": {
                    "nodes": [
                        {"id": "inputs", "type": "source", "name": "Market Inputs"},
                        {"id": "features", "type": "transform", "name": "Feature Extraction"},
                        {"id": "fusion", "type": "model", "name": "Signal Fusion"},
                        {"id": "calibration", "type": "transform", "name": "Calibration"},
                        {"id": "risk", "type": "filter", "name": "Risk Management"},
                        {"id": "sizing", "type": "output", "name": "Position Sizing"},
                    ],
                    "edges": [
                        {"source": "inputs", "target": "features"},
                        {"source": "features", "target": "fusion"},
                        {"source": "fusion", "target": "calibration"},
                        {"source": "calibration", "target": "risk"},
                        {"source": "risk", "target": "sizing"},
                    ],
                },
                "raw": {
                    "inputs": inputs,
                    "features": features,
                    "fusion": fusion,
                    "calibration": calibration,
                    "risk": risk,
                    "sizing": sizing,
                },
            }

        # Generate trace ID
        import uuid

        trace_id = str(uuid.uuid4())

        # Complete trace data
        complete_trace = {
            "event_id": event_id,
            "trace_id": trace_id,
            "ticker": ticker,
            "graph": trace_data["graph"],
            "raw": trace_data["raw"],
            "total_latency_ms": (time.time() - start_time) * 1000,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "cached": False,
        }

        # Store trace in memory (brain-first)
        try:
            trace_event = {
                "event_type": "trace_request",
                "original_event_id": event_id,
                "trace_id": trace_id,
                "trace_data": complete_trace,
                "ticker": ticker,
            }

            trace_event_id = append_event(trace_event)
            logger.info(f"Stored trace {trace_id} as event {trace_event_id}")

            # Also update original event with trace reference
            if existing_event:
                existing_event["trace_id"] = trace_id
                existing_event["trace_data"] = complete_trace

        except Exception as e:
            if BRAIN_STRICT:
                raise HTTPException(status_code=500, detail=f"Brain storage failed: {e}")
            else:
                logger.warning(f"Brain storage failed: {e}")

        return complete_trace

    except Exception as e:
        if BRAIN_STRICT:
            raise HTTPException(status_code=500, detail=f"Trace construction failed: {e}")
        else:
            # Fallback minimal trace
            return {
                "event_id": event_id,
                "trace_id": "error_" + str(int(time.time())),
                "ticker": existing_event.get("ticker", "UNKNOWN"),
                "graph": {
                    "nodes": [{"id": "error", "type": "error", "name": "Trace Error"}],
                    "edges": [],
                },
                "raw": {"error": str(e)},
                "total_latency_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "cached": False,
            }


@router.get("/trace", response_model=TraceResponse)
async def get_signal_trace(event_id: str = Query(..., description="Event ID to trace")):
    """
    Get decision trace DAG and raw JSON for an event.

    Brain-first: Always reads from or writes to memory layer.
    Returns decision graph visualization and raw data for power users.
    """
    if not TRACE_ENABLED:
        raise HTTPException(
            status_code=403, detail="Trace feature not enabled. Set EXPLAIN_ENABLE_TRACE=1"
        )

    try:
        trace_data = _build_trace_data(event_id)
        return TraceResponse(**trace_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trace failed: {e!s}")


@router.get("/trace/list")
async def list_traces(
    ticker: str | None = Query(None, description="Filter by ticker"),
    limit: int = Query(20, ge=1, le=100, description="Maximum traces to return"),
):
    """
    List available traces with basic metadata.
    """
    try:
        traces = []
        count = 0

        # Search through events for traces
        for event in iter_events():
            if count >= limit:
                break

            if event.get("event_type") == "trace_request":
                if ticker and event.get("ticker", "").upper() != ticker.upper():
                    continue

                traces.append(
                    {
                        "trace_id": event.get("trace_id"),
                        "event_id": event.get("original_event_id"),
                        "ticker": event.get("ticker"),
                        "timestamp": event.get("ts"),
                        "latency_ms": event.get("trace_data", {}).get("total_latency_ms"),
                    }
                )
                count += 1

        return {
            "status": "success",
            "traces": traces,
            "total_returned": len(traces),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list traces: {e!s}")


@router.get("/trace/health")
async def trace_health_check():
    """Health check for trace service."""
    return {
        "status": "healthy" if TRACE_AVAILABLE else "partial",
        "trace_enabled": TRACE_ENABLED,
        "trace_available": TRACE_AVAILABLE,
        "brain_strict": BRAIN_STRICT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
