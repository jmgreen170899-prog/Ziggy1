"""
Feedback Routes for ZiggyAI Memory & Knowledge System

Handles human feedback on trading decisions (Good/Bad Call logging).
Supports rating, tagging, and note capture for continuous learning.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from ..memory.events import append_event, get_event_by_id


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])


# Configuration
FEEDBACK_ENABLED = os.getenv("FEEDBACK_ENABLED", "1") == "1"


class FeedbackRequest(BaseModel):
    """Request model for decision feedback."""

    event_id: str = Field(..., description="ID of the event to provide feedback on")
    rating: str = Field(..., description="Feedback rating: GOOD or BAD")
    tags: list[str] | None = Field(None, description="Optional feedback tags")
    note: str | None = Field(None, description="Optional feedback note")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "12345678-1234-1234-1234-123456789012",
                "rating": "GOOD",
                "tags": ["accurate_prediction", "good_timing"],
                "note": "Model correctly predicted the earnings reaction",
            }
        }
    )


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""

    success: bool
    feedback_id: str
    message: str


class FeedbackSummary(BaseModel):
    """Summary of feedback for an event."""

    event_id: str
    total_feedback_count: int
    rating_counts: dict[str, int]
    recent_feedback: list[dict[str, Any]]


@router.post("/decision", response_model=FeedbackResponse)
async def submit_decision_feedback(feedback: FeedbackRequest) -> FeedbackResponse:
    """
    Submit feedback on a trading decision.

    Args:
        feedback: Feedback data including event_id, rating, tags, and note

    Returns:
        Feedback submission response
    """
    if not FEEDBACK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback system is currently disabled",
        )

    # Validate rating
    valid_ratings = {"GOOD", "BAD", "NEUTRAL"}
    if feedback.rating not in valid_ratings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rating. Must be one of: {', '.join(valid_ratings)}",
        )

    # Check if the target event exists
    target_event = get_event_by_id(feedback.event_id)
    if target_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {feedback.event_id} not found",
        )

    try:
        # Create feedback event
        feedback_payload = {
            "_feedback_for": feedback.event_id,
            "_feedback_type": "decision_rating",
            "rating": feedback.rating,
            "tags": feedback.tags or [],
            "note": feedback.note,
            "submitted_at": datetime.utcnow().isoformat() + "Z",
        }

        # Append feedback to event store
        feedback_id = append_event(feedback_payload)

        logger.info(
            f"Feedback submitted for event {feedback.event_id}: {feedback.rating}"
        )

        return FeedbackResponse(
            success=True,
            feedback_id=feedback_id,
            message="Feedback submitted successfully",
        )

    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback",
        )


@router.get("/event/{event_id}", response_model=FeedbackSummary)
async def get_event_feedback(event_id: str) -> FeedbackSummary:
    """
    Get feedback summary for a specific event.

    Args:
        event_id: Event ID to get feedback for

    Returns:
        Feedback summary including counts and recent feedback
    """
    if not FEEDBACK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback system is currently disabled",
        )

    # Check if the target event exists
    target_event = get_event_by_id(event_id)
    if target_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found"
        )

    try:
        # Collect all feedback for this event
        from ..memory.events import iter_events

        feedback_list = []
        for event in iter_events(include_updates=True):
            if event.get("_feedback_for") == event_id:
                feedback_list.append(event)

        # Sort by submission time
        feedback_list.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)

        # Count ratings
        rating_counts = {}
        for feedback in feedback_list:
            rating = feedback.get("rating", "UNKNOWN")
            rating_counts[rating] = rating_counts.get(rating, 0) + 1

        # Prepare recent feedback (last 10)
        recent_feedback = []
        for feedback in feedback_list[:10]:
            recent_feedback.append(
                {
                    "id": feedback.get("id"),
                    "rating": feedback.get("rating"),
                    "tags": feedback.get("tags", []),
                    "note": feedback.get("note"),
                    "submitted_at": feedback.get("submitted_at"),
                }
            )

        return FeedbackSummary(
            event_id=event_id,
            total_feedback_count=len(feedback_list),
            rating_counts=rating_counts,
            recent_feedback=recent_feedback,
        )

    except Exception as e:
        logger.error(f"Failed to get event feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event feedback",
        )


@router.get("/stats", response_model=None)
async def get_feedback_stats() -> dict[str, Any]:
    """
    Get overall feedback statistics.

    Returns:
        Dictionary with feedback statistics
    """
    if not FEEDBACK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback system is currently disabled",
        )

    try:
        from ..memory.events import iter_events

        # Collect all feedback events
        feedback_events = []
        for event in iter_events(include_updates=True):
            if event.get("_feedback_type") == "decision_rating":
                feedback_events.append(event)

        # Calculate statistics
        total_feedback = len(feedback_events)

        # Rating distribution
        rating_counts = {}
        for feedback in feedback_events:
            rating = feedback.get("rating", "UNKNOWN")
            rating_counts[rating] = rating_counts.get(rating, 0) + 1

        # Tag analysis
        tag_counts = {}
        for feedback in feedback_events:
            tags = feedback.get("tags", [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Recent activity (last 7 days)
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=7)
        cutoff_str = cutoff_date.isoformat()

        recent_feedback = [
            f for f in feedback_events if f.get("submitted_at", "") >= cutoff_str
        ]

        # Events with feedback vs total events
        events_with_feedback = set()
        for feedback in feedback_events:
            target_id = feedback.get("_feedback_for")
            if target_id:
                events_with_feedback.add(target_id)

        # Count total decision events
        total_decision_events = 0
        for event in iter_events():
            if event.get("decision") and not event.get("_feedback_for"):
                total_decision_events += 1

        feedback_coverage = (
            len(events_with_feedback) / max(total_decision_events, 1)
        ) * 100

        return {
            "enabled": FEEDBACK_ENABLED,
            "total_feedback": total_feedback,
            "rating_distribution": rating_counts,
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ],
            "recent_activity_7d": len(recent_feedback),
            "feedback_coverage_pct": round(feedback_coverage, 2),
            "events_with_feedback": len(events_with_feedback),
            "total_decision_events": total_decision_events,
        }

    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback statistics",
        )


class BulkFeedbackRequest(BaseModel):
    """Request model for bulk feedback submission."""

    feedback_items: list[FeedbackRequest] = Field(
        ..., description="List of feedback items"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feedback_items": [
                    {
                        "event_id": "event1",
                        "rating": "GOOD",
                        "tags": ["accurate"],
                        "note": "Great call",
                    },
                    {
                        "event_id": "event2",
                        "rating": "BAD",
                        "tags": ["poor_timing"],
                        "note": "Missed the mark",
                    },
                ]
            }
        }
    )


class BulkFeedbackResponse(BaseModel):
    """Response model for bulk feedback submission."""

    total_submitted: int
    successful: int
    failed: int
    feedback_ids: list[str]
    errors: list[str]


@router.post("/bulk", response_model=BulkFeedbackResponse)
async def submit_bulk_feedback(request: BulkFeedbackRequest) -> BulkFeedbackResponse:
    """
    Submit feedback for multiple decisions at once.

    Args:
        request: Bulk feedback request with multiple feedback items

    Returns:
        Bulk submission results
    """
    if not FEEDBACK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback system is currently disabled",
        )

    feedback_ids = []
    errors = []
    successful = 0

    for i, feedback in enumerate(request.feedback_items):
        try:
            # Validate rating
            valid_ratings = {"GOOD", "BAD", "NEUTRAL"}
            if feedback.rating not in valid_ratings:
                errors.append(f"Item {i}: Invalid rating '{feedback.rating}'")
                continue

            # Check if event exists
            target_event = get_event_by_id(feedback.event_id)
            if target_event is None:
                errors.append(f"Item {i}: Event {feedback.event_id} not found")
                continue

            # Submit feedback
            feedback_payload = {
                "_feedback_for": feedback.event_id,
                "_feedback_type": "decision_rating",
                "rating": feedback.rating,
                "tags": feedback.tags or [],
                "note": feedback.note,
                "submitted_at": datetime.utcnow().isoformat() + "Z",
            }

            feedback_id = append_event(feedback_payload)
            feedback_ids.append(feedback_id)
            successful += 1

        except Exception as e:
            errors.append(f"Item {i}: {e!s}")

    return BulkFeedbackResponse(
        total_submitted=len(request.feedback_items),
        successful=successful,
        failed=len(errors),
        feedback_ids=feedback_ids,
        errors=errors,
    )


# Health check endpoint
@router.get("/health", response_model=None)
async def feedback_health_check() -> dict[str, Any]:
    """
    Check feedback system health.

    Returns:
        Health status information
    """
    return {
        "status": "healthy" if FEEDBACK_ENABLED else "disabled",
        "enabled": FEEDBACK_ENABLED,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
