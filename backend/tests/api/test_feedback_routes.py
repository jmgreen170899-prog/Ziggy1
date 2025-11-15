"""
Tests for Feedback API Routes in ZiggyAI Memory & Knowledge System

Tests human feedback endpoints, rating validation, bulk submission,
and feedback statistics generation.
"""

import os
import shutil
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient


# Set test environment
os.environ["FEEDBACK_ENABLED"] = "1"
os.environ["MEMORY_MODE"] = "JSONL"
os.environ["MEMORY_PATH"] = "test_feedback_events.jsonl"

from app.api.routes_feedback import router
from app.memory.events import append_event


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestFeedbackRoutes:
    """Test cases for feedback API routes."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_feedback_events.jsonl")
        os.environ["MEMORY_PATH"] = self.test_file

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_submit_feedback_valid(self):
        """Test submitting valid feedback."""
        # First create a target event
        target_event = {"ticker": "AAPL", "p_up": 0.75, "decision": "BUY"}
        event_id = append_event(target_event)

        # Submit feedback
        feedback_data = {
            "event_id": event_id,
            "rating": "GOOD",
            "tags": ["accurate_prediction", "good_timing"],
            "note": "Great call on the earnings reaction",
        }

        response = client.post("/feedback/decision", json=feedback_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "feedback_id" in result
        assert result["message"] == "Feedback submitted successfully"

    def test_submit_feedback_invalid_rating(self):
        """Test submitting feedback with invalid rating."""
        # Create target event
        event_id = append_event({"ticker": "AAPL", "p_up": 0.75})

        feedback_data = {
            "event_id": event_id,
            "rating": "INVALID_RATING",
            "tags": [],
            "note": "",
        }

        response = client.post("/feedback/decision", json=feedback_data)

        assert response.status_code == 400
        assert "Invalid rating" in response.json()["detail"]

    def test_submit_feedback_event_not_found(self):
        """Test submitting feedback for non-existent event."""
        feedback_data = {
            "event_id": "non-existent-event-id",
            "rating": "GOOD",
            "tags": [],
            "note": "",
        }

        response = client.post("/feedback/decision", json=feedback_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_submit_feedback_minimal_data(self):
        """Test submitting feedback with minimal required data."""
        # Create target event
        event_id = append_event({"ticker": "TSLA", "p_up": 0.6})

        feedback_data = {
            "event_id": event_id,
            "rating": "BAD",
            # No tags or note
        }

        response = client.post("/feedback/decision", json=feedback_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    def test_submit_feedback_disabled(self):
        """Test submitting feedback when system is disabled."""
        # Temporarily disable feedback
        original_enabled = os.environ.get("FEEDBACK_ENABLED")
        os.environ["FEEDBACK_ENABLED"] = "0"

        try:
            event_id = append_event({"ticker": "AAPL", "p_up": 0.75})

            feedback_data = {"event_id": event_id, "rating": "GOOD"}

            response = client.post("/feedback/decision", json=feedback_data)

            assert response.status_code == 503
            assert "disabled" in response.json()["detail"]

        finally:
            # Restore original setting
            if original_enabled:
                os.environ["FEEDBACK_ENABLED"] = original_enabled
            else:
                os.environ.pop("FEEDBACK_ENABLED", None)

    def test_get_event_feedback_basic(self):
        """Test getting feedback for an event."""
        # Create target event
        event_id = append_event({"ticker": "AAPL", "p_up": 0.75})

        # Submit some feedback
        feedback_data = {
            "event_id": event_id,
            "rating": "GOOD",
            "tags": ["accurate"],
            "note": "Nice prediction",
        }
        client.post("/feedback/decision", json=feedback_data)

        # Get feedback summary
        response = client.get(f"/feedback/event/{event_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["event_id"] == event_id
        assert result["total_feedback_count"] == 1
        assert "GOOD" in result["rating_counts"]
        assert result["rating_counts"]["GOOD"] == 1
        assert len(result["recent_feedback"]) == 1

    def test_get_event_feedback_multiple_ratings(self):
        """Test getting feedback with multiple ratings."""
        # Create target event
        event_id = append_event({"ticker": "MSFT", "p_up": 0.8})

        # Submit multiple feedback entries
        feedback_entries = [
            {"event_id": event_id, "rating": "GOOD", "note": "Great call"},
            {"event_id": event_id, "rating": "GOOD", "note": "Excellent timing"},
            {"event_id": event_id, "rating": "BAD", "note": "Poor execution"},
        ]

        for feedback in feedback_entries:
            client.post("/feedback/decision", json=feedback)

        # Get feedback summary
        response = client.get(f"/feedback/event/{event_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["total_feedback_count"] == 3
        assert result["rating_counts"]["GOOD"] == 2
        assert result["rating_counts"]["BAD"] == 1

    def test_get_event_feedback_not_found(self):
        """Test getting feedback for non-existent event."""
        response = client.get("/feedback/event/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_feedback_stats_basic(self):
        """Test getting overall feedback statistics."""
        # Create some events and feedback
        events_and_feedback = [
            ({"ticker": "AAPL", "p_up": 0.75, "decision": "BUY"}, "GOOD"),
            ({"ticker": "TSLA", "p_up": 0.6, "decision": "SELL"}, "BAD"),
            ({"ticker": "MSFT", "p_up": 0.8, "decision": "HOLD"}, "GOOD"),
        ]

        for event_data, rating in events_and_feedback:
            event_id = append_event(event_data)
            feedback_data = {"event_id": event_id, "rating": rating}
            client.post("/feedback/decision", json=feedback_data)

        # Get overall stats
        response = client.get("/feedback/stats")

        assert response.status_code == 200
        result = response.json()
        assert result["enabled"] is True
        assert result["total_feedback"] == 3
        assert "rating_distribution" in result
        assert result["rating_distribution"]["GOOD"] == 2
        assert result["rating_distribution"]["BAD"] == 1
        assert "feedback_coverage_pct" in result
        assert result["total_decision_events"] >= 3

    def test_get_feedback_stats_with_tags(self):
        """Test feedback statistics with tag analysis."""
        # Create event and feedback with tags
        event_id = append_event({"ticker": "AAPL", "p_up": 0.75})

        feedback_entries = [
            {
                "event_id": event_id,
                "rating": "GOOD",
                "tags": ["accurate_prediction", "good_timing"],
            },
            {
                "event_id": event_id,
                "rating": "BAD",
                "tags": ["poor_timing", "market_noise"],
            },
        ]

        for feedback in feedback_entries:
            client.post("/feedback/decision", json=feedback)

        # Get stats
        response = client.get("/feedback/stats")

        assert response.status_code == 200
        result = response.json()
        assert "top_tags" in result

        # Should have tag counts
        tag_dict = dict(result["top_tags"])
        assert "accurate_prediction" in tag_dict
        assert "good_timing" in tag_dict
        assert "poor_timing" in tag_dict
        assert "market_noise" in tag_dict

    def test_bulk_feedback_submission(self):
        """Test bulk feedback submission."""
        # Create multiple events
        event_ids = []
        for i in range(3):
            event_id = append_event({"ticker": f"STOCK{i}", "p_up": 0.5 + i * 0.1})
            event_ids.append(event_id)

        # Submit bulk feedback
        bulk_data = {
            "feedback_items": [
                {
                    "event_id": event_ids[0],
                    "rating": "GOOD",
                    "tags": ["accurate"],
                    "note": "Great call",
                },
                {
                    "event_id": event_ids[1],
                    "rating": "BAD",
                    "tags": ["poor_timing"],
                    "note": "Missed the mark",
                },
                {
                    "event_id": event_ids[2],
                    "rating": "NEUTRAL",
                    "note": "Average performance",
                },
            ]
        }

        response = client.post("/feedback/bulk", json=bulk_data)

        assert response.status_code == 200
        result = response.json()
        assert result["total_submitted"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert len(result["feedback_ids"]) == 3
        assert len(result["errors"]) == 0

    def test_bulk_feedback_partial_failure(self):
        """Test bulk feedback with partial failures."""
        # Create one valid event
        valid_event_id = append_event({"ticker": "AAPL", "p_up": 0.75})

        bulk_data = {
            "feedback_items": [
                {
                    "event_id": valid_event_id,
                    "rating": "GOOD",
                    "note": "Valid feedback",
                },
                {
                    "event_id": "non-existent-id",
                    "rating": "BAD",
                    "note": "Invalid event ID",
                },
                {
                    "event_id": valid_event_id,
                    "rating": "INVALID_RATING",  # Invalid rating
                    "note": "Invalid rating",
                },
            ]
        }

        response = client.post("/feedback/bulk", json=bulk_data)

        assert response.status_code == 200
        result = response.json()
        assert result["total_submitted"] == 3
        assert result["successful"] == 1
        assert result["failed"] == 2
        assert len(result["feedback_ids"]) == 1
        assert len(result["errors"]) == 2

    def test_feedback_health_check(self):
        """Test feedback system health check."""
        response = client.get("/feedback/health")

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
        assert result["enabled"] is True
        assert "timestamp" in result

    def test_feedback_health_check_disabled(self):
        """Test health check when feedback is disabled."""
        # Temporarily disable feedback
        original_enabled = os.environ.get("FEEDBACK_ENABLED")
        os.environ["FEEDBACK_ENABLED"] = "0"

        try:
            response = client.get("/feedback/health")

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "disabled"
            assert result["enabled"] is False

        finally:
            # Restore original setting
            if original_enabled:
                os.environ["FEEDBACK_ENABLED"] = original_enabled
            else:
                os.environ.pop("FEEDBACK_ENABLED", None)


class TestFeedbackIntegration:
    """Integration tests for feedback system."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "integration_events.jsonl")
        os.environ["MEMORY_PATH"] = self.test_file

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_feedback_workflow_end_to_end(self):
        """Test complete feedback workflow from event creation to analysis."""
        # 1. Create trading decision event
        decision_event = {
            "ticker": "AAPL",
            "features_v": "1.0.0",
            "regime": "normal",
            "p_up": 0.75,
            "decision": "BUY",
            "size": 0.3,
            "explain": {"shap_top": [["momentum", 0.4], ["sentiment", 0.3]]},
        }

        event_id = append_event(decision_event)

        # 2. Submit human feedback
        feedback_data = {
            "event_id": event_id,
            "rating": "GOOD",
            "tags": ["accurate_prediction", "good_entry"],
            "note": "Model correctly predicted earnings reaction",
        }

        feedback_response = client.post("/feedback/decision", json=feedback_data)
        assert feedback_response.status_code == 200

        # 3. Verify feedback is stored and retrievable
        event_feedback_response = client.get(f"/feedback/event/{event_id}")
        assert event_feedback_response.status_code == 200

        event_feedback = event_feedback_response.json()
        assert event_feedback["total_feedback_count"] == 1
        assert event_feedback["rating_counts"]["GOOD"] == 1

        # 4. Check overall statistics
        stats_response = client.get("/feedback/stats")
        assert stats_response.status_code == 200

        stats = stats_response.json()
        assert stats["total_feedback"] >= 1
        assert "GOOD" in stats["rating_distribution"]

    def test_feedback_impact_on_learning(self):
        """Test how feedback impacts the learning system."""
        # This would test integration with the learning module
        # For now, we'll test the data structures are compatible

        # Create event with outcome
        event_data = {
            "ticker": "TSLA",
            "p_up": 0.6,
            "decision": "SELL",
            "outcome": {"label": 0, "pnl": 0.02},  # Good prediction
        }

        event_id = append_event(event_data)

        # Add positive feedback
        feedback_data = {
            "event_id": event_id,
            "rating": "GOOD",
            "tags": ["correct_direction", "good_timing"],
            "note": "Predicted the drop correctly",
        }

        client.post("/feedback/decision", json=feedback_data)

        # Verify feedback can be retrieved for learning analysis
        from app.memory.events import iter_events

        feedback_events = []
        for event in iter_events(include_updates=True):
            if event.get("_feedback_type") == "decision_rating":
                feedback_events.append(event)

        assert len(feedback_events) >= 1

        # Verify feedback structure is suitable for learning
        feedback_event = feedback_events[0]
        assert feedback_event["_feedback_for"] == event_id
        assert feedback_event["rating"] == "GOOD"
        assert "correct_direction" in feedback_event["tags"]

    def test_feedback_performance_characteristics(self):
        """Test feedback system performance."""
        import time

        # Create multiple events
        event_ids = []
        for i in range(20):
            event_id = append_event(
                {
                    "ticker": f"STOCK{i}",
                    "p_up": 0.5 + i * 0.02,
                    "decision": "BUY" if i % 2 == 0 else "SELL",
                }
            )
            event_ids.append(event_id)

        # Measure bulk feedback submission time
        feedback_items = []
        for i, event_id in enumerate(event_ids):
            feedback_items.append(
                {
                    "event_id": event_id,
                    "rating": "GOOD" if i % 3 == 0 else "BAD",
                    "tags": [f"tag_{i % 5}"],
                    "note": f"Feedback for event {i}",
                }
            )

        start_time = time.time()

        bulk_response = client.post(
            "/feedback/bulk", json={"feedback_items": feedback_items}
        )

        end_time = time.time()
        submission_time = end_time - start_time

        # Should complete quickly
        assert submission_time < 1.0  # < 1 second for 20 items
        assert bulk_response.status_code == 200

        result = bulk_response.json()
        assert result["successful"] == 20
        assert result["failed"] == 0

    def test_feedback_data_consistency(self):
        """Test feedback data consistency across multiple operations."""
        # Create event
        event_id = append_event({"ticker": "AAPL", "p_up": 0.8})

        # Submit multiple feedback entries over time
        feedback_sequence = [
            {"rating": "GOOD", "note": "Initial positive feedback"},
            {"rating": "NEUTRAL", "note": "Revised assessment"},
            {"rating": "GOOD", "note": "Final confirmation"},
        ]

        submitted_ids = []
        for feedback in feedback_sequence:
            feedback["event_id"] = event_id
            response = client.post("/feedback/decision", json=feedback)
            result = response.json()
            submitted_ids.append(result["feedback_id"])

        # Verify all feedback is tracked
        event_response = client.get(f"/feedback/event/{event_id}")
        event_data = event_response.json()

        assert event_data["total_feedback_count"] == 3
        assert event_data["rating_counts"]["GOOD"] == 2
        assert event_data["rating_counts"]["NEUTRAL"] == 1

        # Verify recent feedback ordering (newest first)
        recent_feedback = event_data["recent_feedback"]
        assert len(recent_feedback) == 3

        # Should be ordered by submission time (newest first)
        timestamps = [fb["submitted_at"] for fb in recent_feedback]
        assert timestamps == sorted(timestamps, reverse=True)
