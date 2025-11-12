"""
ZiggyAI Explain Signal Routes - Emotive Interface

Brain-first data flow: Every explain request must read/write through memory layer.
Mission: Trust ↑, clarity ↑ - Make decisions transparent and teach the user what mattered.

Routes:
- GET /signal/explain - Detailed signal explanation with SHAP, calibration, neighbors
- POST /signal/explain/feedback - Thumbs up/down feedback on explanations
"""

import logging
import os
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


# Environment configuration
EXPLAIN_TOPK = int(os.getenv("EXPLAIN_TOPK", "5"))
EXPLAIN_ENABLE_TRACE = os.getenv("EXPLAIN_ENABLE_TRACE", "1") == "1"
EXPLAIN_CALIB_POINTS = int(os.getenv("EXPLAIN_CALIB_POINTS", "12"))
STALE_TTL_SECONDS = int(os.getenv("STALE_TTL_SECONDS", "60"))
BRAIN_STRICT = os.getenv("BRAIN_STRICT", "1") == "1"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/signal", tags=["explain"])

# Import core functions
from app.memory.events import append_event, iter_events


# Check if optional services are available
try:
    from app.memory.vecdb import build_embedding, search_similar, upsert_event
    from app.services.explain import (
        build_waterfall,
        compute_mind_flip,
        compute_staleness,
        get_top_features,
        sample_calibration,
    )

    EXPLAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Explain services not fully available: {e}")
    EXPLAIN_AVAILABLE = False

    # Minimal fallbacks for vector functions
    def search_similar(vec, k=10, filter_metadata=None):
        return []

    def upsert_event(event_id, vec, metadata):
        pass

    def build_embedding(event):
        return [0.0] * 384


class ExplainRequest(BaseModel):
    """Request model for signal explanation."""

    ticker: str = Field(..., description="Stock symbol")
    dt: str | None = Field(None, description="ISO timestamp for historical explanation")
    interval: str = Field("1D", description="Time interval")
    include_trace: bool = Field(False, description="Include trace data")


class StalenessInfo(BaseModel):
    """Staleness information for data freshness."""

    age_ms: int = Field(..., description="Age in milliseconds")
    ttl_s: int = Field(..., description="TTL in seconds")
    is_stale: bool = Field(..., description="Whether data is stale")


class MindFlipInfo(BaseModel):
    """Information about feature changes since last signal."""

    since_event: str | None = Field(None, description="Previous event ID")
    flipped: bool = Field(..., description="Whether mind flipped")
    diff: list[list[Any]] = Field(default_factory=list, description="Feature differences")


class CalibrationInfo(BaseModel):
    """Calibration curve information."""

    bins: list[list[float]] = Field(..., description="Calibration bins")
    ece: float = Field(..., description="Expected Calibration Error")


class NeighborInfo(BaseModel):
    """Neighbor case information."""

    id: str = Field(..., description="Event ID")
    p_outcome: float | None = Field(None, description="Historical outcome probability")
    similarity: float = Field(..., description="Similarity score")
    context: dict[str, Any] | None = Field(None, description="Neighbor context")


class ExplainResponse(BaseModel):
    """Response model for signal explanation."""

    event_id: str = Field(..., description="Memory event ID")
    ticker: str = Field(..., description="Stock symbol")
    regime: str = Field(..., description="Market regime")
    p_up_model: float = Field(..., description="Model prediction")
    p_up_prior: float | None = Field(None, description="RAG prior")
    p_up_blend: float = Field(..., description="Blended prediction")

    # Explainability features
    calibration: CalibrationInfo = Field(..., description="Calibration information")
    top_features: list[list[Any]] = Field(..., description="Top contributing features")
    waterfall: list[dict[str, Any]] = Field(..., description="Waterfall breakdown")
    neighbors: list[NeighborInfo] = Field(..., description="Similar historical cases")

    # Freshness and comparison
    staleness: StalenessInfo = Field(..., description="Data freshness")
    mind_flip: MindFlipInfo = Field(..., description="Changes since last signal")

    # Metadata
    latency_ms: float = Field(..., description="Request latency")
    trace_available: bool = Field(..., description="Whether trace data is available")


class ExplainFeedbackRequest(BaseModel):
    """Feedback request for explanations."""

    event_id: str = Field(..., description="Explanation event ID")
    rating: str = Field(..., description="thumbs_up or thumbs_down")
    notes: str | None = Field(None, description="Optional feedback notes")


def _find_last_event_for_ticker(
    ticker: str, interval: str, before_ts: str | None = None
) -> dict[str, Any] | None:
    """Find the most recent event for a ticker/interval combination."""
    if not EXPLAIN_AVAILABLE:
        return None

    try:
        # Convert before_ts to datetime for comparison
        before_dt = None
        if before_ts:
            before_dt = datetime.fromisoformat(before_ts.replace("Z", "+00:00"))

        last_event = None
        for event in iter_events():
            if event.get("ticker") == ticker and event.get("interval", "1D") == interval:
                event_dt = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))

                # Skip events after before_ts
                if before_dt and event_dt >= before_dt:
                    continue

                # Keep the most recent valid event
                if last_event is None:
                    last_event = event
                else:
                    last_dt = datetime.fromisoformat(last_event["ts"].replace("Z", "+00:00"))
                    if event_dt > last_dt:
                        last_event = event

        return last_event
    except Exception as e:
        logger.warning(f"Error finding last event: {e}")
        return None


def _build_explain_data(ticker: str, interval: str, dt: str | None = None) -> dict[str, Any]:
    """Build explanation data by computing or retrieving from memory."""
    start_time = time.time()

    # Check if we already have this explanation in memory
    existing_event = None
    if dt:
        # Look for specific datetime event
        for event in iter_events():
            if (
                event.get("ticker") == ticker
                and event.get("interval", "1D") == interval
                and event.get("ts", "").startswith(dt[:19])
            ):  # Match to second precision
                existing_event = event
                break

    if existing_event and existing_event.get("explain_data"):
        # Return cached explanation
        explain_data = existing_event["explain_data"]
        explain_data["event_id"] = existing_event["id"]
        explain_data["latency_ms"] = (time.time() - start_time) * 1000
        return explain_data

    # Compute new explanation
    try:
        # Mock model prediction (replace with real model call)
        p_up_model = 0.65
        regime = "normal"

        # Get top features (mock data for now)
        if EXPLAIN_AVAILABLE:
            top_features = get_top_features(ticker, limit=EXPLAIN_TOPK)
        else:
            top_features = [
                ["momentum", 0.4],
                ["sentiment", 0.3],
                ["volatility", 0.2],
                ["volume", 0.1],
            ]

        # Build waterfall
        if EXPLAIN_AVAILABLE:
            waterfall = build_waterfall(top_features)
        else:
            waterfall = [{"name": k, "delta": float(v)} for k, v in top_features]

        # Get calibration info
        if EXPLAIN_AVAILABLE:
            calibration = sample_calibration(EXPLAIN_CALIB_POINTS)
        else:
            calibration = {"bins": [[i / 12, i / 12] for i in range(1, 13)], "ece": 0.05}

        # Search for neighbors
        neighbors = []
        try:
            # Create embedding for search
            search_event = {
                "ticker": ticker,
                "regime": regime,
                "explain": {"shap_top": top_features},
            }

            if EXPLAIN_AVAILABLE:
                similar_events = search_similar(search_event, k=5)
                for neighbor in similar_events:
                    neighbors.append(
                        NeighborInfo(
                            id=neighbor["id"],
                            p_outcome=neighbor.get("metadata", {}).get("p_outcome"),
                            similarity=neighbor["score"],
                            context=neighbor.get("metadata", {}),
                        )
                    )
        except Exception as e:
            logger.warning(f"Neighbor search failed: {e}")

        # Compute RAG blend if neighbors available
        p_up_prior = None
        if neighbors:
            valid_outcomes = [n.p_outcome for n in neighbors if n.p_outcome is not None]
            if valid_outcomes:
                p_up_prior = sum(valid_outcomes) / len(valid_outcomes)

        rag_weight = 0.25
        p_up_blend = p_up_model
        if p_up_prior is not None:
            p_up_blend = rag_weight * p_up_prior + (1 - rag_weight) * p_up_model

        # Compute staleness
        if EXPLAIN_AVAILABLE:
            staleness = compute_staleness(STALE_TTL_SECONDS)
        else:
            staleness = {"age_ms": 1000, "ttl_s": STALE_TTL_SECONDS, "is_stale": False}

        # Find mind flip compared to last event
        last_event = _find_last_event_for_ticker(ticker, interval, dt)
        if EXPLAIN_AVAILABLE:
            mind_flip = compute_mind_flip(top_features, last_event)
        else:
            mind_flip = {
                "since_event": last_event["id"] if last_event else None,
                "flipped": False,
                "diff": [],
            }

        # Build explanation data
        explain_data = {
            "ticker": ticker,
            "regime": regime,
            "p_up_model": p_up_model,
            "p_up_prior": p_up_prior,
            "p_up_blend": p_up_blend,
            "calibration": calibration,
            "top_features": top_features,
            "waterfall": waterfall,
            "neighbors": [n.dict() for n in neighbors],
            "staleness": staleness,
            "mind_flip": mind_flip,
            "trace_available": EXPLAIN_ENABLE_TRACE,
            "latency_ms": (time.time() - start_time) * 1000,
        }

        # Store in memory (brain-first requirement)
        from app.memory.events import build_durable_event

        memory_event = build_durable_event(
            ticker=ticker,
            regime=regime,
            p_up=p_up_blend,
            explain={"shap_top": top_features},
            event_type="explain_request",
            explain_data=explain_data,
            interval=interval,
            p_up_model=p_up_model,
            p_up_prior=p_up_prior,
            trace_id=str(int(time.time() * 1000000)),  # Microsecond timestamp
        )

        # Override timestamp if specific dt requested
        if dt:
            memory_event["ts"] = dt

        try:
            event_id = append_event(memory_event)
            explain_data["event_id"] = event_id

            # Also upsert to vector database for future neighbor searches
            if EXPLAIN_AVAILABLE:
                try:
                    # Create vector metadata for storage (must include timestamp)
                    vector_metadata = {
                        "ticker": ticker,
                        "timeframe": interval,
                        "ts": memory_event["ts"],
                        "event_type": "explain_request",
                        "confidence": explain_data.get("confidence", 0.0),
                        "p_up_blend": explain_data.get("p_up_blend", 0.0),
                    }

                    # Build embedding and upsert
                    embedding = build_embedding(memory_event)
                    upsert_event(event_id, embedding, vector_metadata)

                except Exception as vec_e:
                    logger.warning(f"Vector storage failed: {vec_e}")

        except Exception as e:
            if BRAIN_STRICT:
                raise HTTPException(status_code=500, detail=f"Brain storage failed: {e}")
            else:
                logger.warning(f"Brain storage failed: {e}")
                explain_data["event_id"] = "temp_" + str(int(time.time()))

        return explain_data

    except Exception as e:
        if BRAIN_STRICT:
            raise HTTPException(status_code=500, detail=f"Explanation computation failed: {e}")
        else:
            # Fallback minimal response
            return {
                "event_id": "error_" + str(int(time.time())),
                "ticker": ticker,
                "regime": "unknown",
                "p_up_model": 0.5,
                "p_up_prior": None,
                "p_up_blend": 0.5,
                "calibration": {"bins": [], "ece": 0.0},
                "top_features": [],
                "waterfall": [],
                "neighbors": [],
                "staleness": {"age_ms": 0, "ttl_s": STALE_TTL_SECONDS, "is_stale": True},
                "mind_flip": {"since_event": None, "flipped": False, "diff": []},
                "trace_available": False,
                "latency_ms": (time.time() - start_time) * 1000,
            }


@router.get("/explain", response_model=ExplainResponse)
async def get_signal_explanation(
    ticker: str = Query(..., description="Stock symbol"),
    dt: str | None = Query(None, description="ISO timestamp"),
    interval: str = Query("1D", description="Time interval"),
):
    """
    Get detailed signal explanation with SHAP features, calibration, and neighbors.

    Brain-first: Always reads from or writes to memory layer.
    Returns waterfall breakdown, mind-flip analysis, and staleness info.
    """
    try:
        explain_data = _build_explain_data(ticker, interval, dt)
        return ExplainResponse(**explain_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {e!s}")


@router.post("/explain/feedback")
async def submit_explanation_feedback(request: ExplainFeedbackRequest):
    """
    Submit thumbs up/down feedback on explanations.
    Integrates with existing feedback system.
    """
    try:
        # Store feedback event in memory
        feedback_event = {
            "_feedback_type": "explanation_rating",
            "_feedback_for": request.event_id,
            "rating": request.rating,
            "notes": request.notes,
            "event_type": "explanation_feedback",
        }

        feedback_id = append_event(feedback_event)

        return {
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Explanation feedback recorded",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {e!s}")


@router.get("/explain/health")
async def explain_health_check():
    """Health check for explain service."""
    return {
        "status": "healthy" if EXPLAIN_AVAILABLE else "partial",
        "explain_enabled": EXPLAIN_AVAILABLE,
        "trace_enabled": EXPLAIN_ENABLE_TRACE,
        "brain_strict": BRAIN_STRICT,
        "config": {
            "topk": EXPLAIN_TOPK,
            "calib_points": EXPLAIN_CALIB_POINTS,
            "stale_ttl_s": STALE_TTL_SECONDS,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
