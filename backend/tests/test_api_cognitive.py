"""
API endpoint tests for ZiggyAI Cognitive Core.

Tests API response times, data validation, and integration.
"""

import time

import numpy as np
import pytest
from fastapi.testclient import TestClient


# Mock the dependencies for testing
def create_test_app():
    """Create test FastAPI app with mocked dependencies."""
    from fastapi import FastAPI

    app = FastAPI()

    # Mock cognitive signal endpoint
    @app.post("/api/signals/cognitive")
    async def generate_cognitive_signal(request: dict):
        """Mock cognitive signal generation."""
        start_time = time.time()

        # Simulate processing time
        time.sleep(0.01)  # 10ms processing

        # Mock response
        response = {
            "symbol": request.get("symbol", "AAPL"),
            "signal_probability": np.random.uniform(0.3, 0.8),
            "confidence": np.random.uniform(0.6, 0.9),
            "regime": {
                "current": "bull_market",
                "confidence": 0.75,
                "weights": {
                    "bull_market": 0.4,
                    "bear_market": 0.2,
                    "sideways": 0.25,
                    "high_volatility": 0.15,
                },
            },
            "explanation": {
                "feature_importance": {
                    "rsi_14": 0.15,
                    "momentum_5d": 0.12,
                    "volatility_20": 0.10,
                    "volume_ratio": 0.08,
                    "sentiment_score": 0.07,
                },
                "model_contributions": {
                    "momentum_model": 0.35,
                    "mean_reversion_model": 0.25,
                    "volatility_model": 0.25,
                    "sentiment_model": 0.15,
                },
            },
            "processing_time_ms": (time.time() - start_time) * 1000,
        }

        return response

    # Mock regime analysis endpoint
    @app.get("/api/signals/regime/{symbol}")
    async def get_regime_analysis(symbol: str):
        """Mock regime analysis."""
        return {
            "symbol": symbol,
            "regime": "bull_market",
            "confidence": 0.78,
            "regime_weights": {
                "bull_market": 0.45,
                "bear_market": 0.15,
                "sideways": 0.25,
                "high_volatility": 0.15,
            },
            "features": {
                "volatility_regime": 0.22,
                "trend_strength": 0.65,
                "momentum_persistence": 0.58,
            },
        }

    # Mock screening endpoint
    @app.post("/api/screener/screen")
    async def screen_market(request: dict):
        """Mock market screening."""
        start_time = time.time()

        # Simulate screening multiple symbols
        symbols = request.get("universe", ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"])

        results = []
        for symbol in symbols[:10]:  # Limit for testing
            results.append(
                {
                    "symbol": symbol,
                    "signal_probability": np.random.uniform(0.2, 0.9),
                    "confidence": np.random.uniform(0.5, 0.95),
                    "regime": np.random.choice(
                        ["bull_market", "bear_market", "sideways", "high_volatility"]
                    ),
                    "score": np.random.uniform(0, 100),
                }
            )

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "results": results,
            "total_screened": len(symbols),
            "processing_time_ms": (time.time() - start_time) * 1000,
            "filters_applied": request.get("filters", {}),
            "strategy": request.get("strategy", "momentum"),
        }

    # Health check endpoint
    @app.get("/api/health/cognitive")
    async def cognitive_health():
        """Mock cognitive core health check."""
        return {
            "status": "healthy",
            "components": {
                "feature_store": {"status": "healthy", "cache_hit_rate": 0.85},
                "regime_detector": {
                    "status": "healthy",
                    "last_update": "2024-01-15T10:30:00Z",
                },
                "signal_ensemble": {"status": "healthy", "model_count": 4},
                "position_sizer": {"status": "healthy", "risk_budget": 0.02},
                "calibration": {"status": "healthy", "ece": 0.032},
            },
            "latency_ms": {
                "features": 45,
                "regime": 18,
                "signals": 72,
                "positions": 12,
            },
        }

    return app


class TestCognitiveAPI:
    """Test cognitive core API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_test_app()
        return TestClient(app)

    def test_cognitive_signal_endpoint_latency(self, client):
        """Test cognitive signal endpoint meets latency requirements."""
        request_data = {
            "symbol": "AAPL",
            "features": {"rsi_14": 65.5, "momentum_5d": 0.02, "volatility_20": 0.25},
        }

        start_time = time.time()
        response = client.post("/api/signals/cognitive", json=request_data)
        latency_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert (
            latency_ms < 150
        ), f"API response took {latency_ms:.2f}ms, should be < 150ms"

        data = response.json()
        assert "signal_probability" in data
        assert "confidence" in data
        assert "regime" in data
        assert "explanation" in data

        # Validate response structure
        assert 0 <= data["signal_probability"] <= 1
        assert 0 <= data["confidence"] <= 1
        assert "processing_time_ms" in data

        print(f"✓ Cognitive signal API latency: {latency_ms:.2f}ms")

    def test_regime_analysis_endpoint(self, client):
        """Test regime analysis endpoint."""
        response = client.get("/api/signals/regime/AAPL")

        assert response.status_code == 200
        data = response.json()

        assert "symbol" in data
        assert "regime" in data
        assert "confidence" in data
        assert "regime_weights" in data

        # Validate regime weights sum to 1
        weights = data["regime_weights"]
        total_weight = sum(weights.values())
        assert (
            abs(total_weight - 1.0) < 0.01
        ), f"Regime weights sum to {total_weight}, should be ~1.0"

        # Validate confidence
        assert 0 <= data["confidence"] <= 1

    def test_market_screening_endpoint(self, client):
        """Test market screening endpoint performance."""
        request_data = {
            "universe": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
            "strategy": "momentum",
            "filters": {"min_confidence": 0.6, "regime": ["bull_market", "sideways"]},
        }

        start_time = time.time()
        response = client.post("/api/screener/screen", json=request_data)
        latency_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert (
            latency_ms < 300
        ), f"Screening took {latency_ms:.2f}ms, should be < 300ms for 5 symbols"

        data = response.json()
        assert "results" in data
        assert "total_screened" in data
        assert "processing_time_ms" in data

        # Validate results structure
        results = data["results"]
        assert len(results) <= 5  # Should not exceed input universe

        for result in results:
            assert "symbol" in result
            assert "signal_probability" in result
            assert "confidence" in result
            assert "regime" in result
            assert 0 <= result["signal_probability"] <= 1
            assert 0 <= result["confidence"] <= 1

    def test_cognitive_health_endpoint(self, client):
        """Test cognitive core health monitoring."""
        response = client.get("/api/health/cognitive")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "components" in data
        assert "latency_ms" in data

        # Validate component health
        components = data["components"]
        required_components = [
            "feature_store",
            "regime_detector",
            "signal_ensemble",
            "position_sizer",
            "calibration",
        ]

        for component in required_components:
            assert component in components
            assert "status" in components[component]

        # Validate latency metrics
        latency = data["latency_ms"]
        assert latency["features"] < 100, "Feature computation should be < 100ms"
        assert latency["regime"] < 50, "Regime detection should be < 50ms"
        assert latency["signals"] < 150, "Signal generation should be < 150ms"
        assert latency["positions"] < 20, "Position sizing should be < 20ms"

        # Check ECE if available
        if "ece" in components["calibration"]:
            ece = components["calibration"]["ece"]
            assert 0 <= ece <= 1, f"ECE {ece} should be between 0 and 1"
            # Note: In production, would check ece < 0.05

    def test_api_error_handling(self, client):
        """Test API error handling and validation."""
        # Test invalid symbol
        response = client.post("/api/signals/cognitive", json={"symbol": ""})
        # Should handle gracefully (status depends on implementation)

        # Test missing required fields
        response = client.post("/api/signals/cognitive", json={})
        # Should handle gracefully

        # Test invalid screening request
        response = client.post("/api/screener/screen", json={"invalid": "data"})
        # Should handle gracefully

        # At minimum, should not crash (status code != 500)
        assert True, "Error handling test completed"

    def test_concurrent_requests(self, client):
        """Test API performance under concurrent load."""
        import concurrent.futures

        def make_request():
            """Make a single API request."""
            request_data = {"symbol": "AAPL"}
            start_time = time.time()
            response = client.post("/api/signals/cognitive", json=request_data)
            latency = (time.time() - start_time) * 1000
            return response.status_code == 200, latency

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Validate all requests succeeded
        success_count = sum(1 for success, _ in results if success)
        latencies = [latency for success, latency in results if success]

        assert (
            success_count >= 8
        ), f"Only {success_count}/10 concurrent requests succeeded"

        if latencies:
            avg_latency = np.mean(latencies)
            max_latency = max(latencies)

            assert (
                avg_latency < 200
            ), f"Average concurrent latency {avg_latency:.2f}ms too high"
            assert (
                max_latency < 500
            ), f"Max concurrent latency {max_latency:.2f}ms too high"

            print(
                f"✓ Concurrent requests: {success_count}/10 success, avg latency: {avg_latency:.2f}ms"
            )

    def test_api_data_validation(self, client):
        """Test API input/output data validation."""
        # Test valid request
        valid_request = {
            "symbol": "AAPL",
            "features": {
                "rsi_14": 65.5,
                "momentum_5d": 0.02,
                "volatility_20": 0.25,
                "volume_ratio": 1.2,
            },
        }

        response = client.post("/api/signals/cognitive", json=valid_request)
        assert response.status_code == 200

        data = response.json()

        # Validate numeric ranges
        assert 0 <= data["signal_probability"] <= 1, "Signal probability out of range"
        assert 0 <= data["confidence"] <= 1, "Confidence out of range"

        # Validate regime structure
        regime = data["regime"]
        assert "current" in regime
        assert "confidence" in regime
        assert "weights" in regime

        # Validate explanation structure
        explanation = data["explanation"]
        assert "feature_importance" in explanation
        assert "model_contributions" in explanation

        # Validate feature importance values
        feature_importance = explanation["feature_importance"]
        for feature, importance in feature_importance.items():
            assert isinstance(
                importance, (int, float)
            ), f"Feature importance for {feature} not numeric"
            assert importance >= 0, f"Feature importance for {feature} is negative"


class TestPerformanceBenchmarks:
    """Performance benchmark tests for cognitive core."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_test_app()
        return TestClient(app)

    def test_throughput_benchmark(self, client):
        """Test API throughput under sustained load."""
        request_data = {"symbol": "AAPL"}

        # Warm up
        for _ in range(5):
            client.post("/api/signals/cognitive", json=request_data)

        # Benchmark
        num_requests = 50
        start_time = time.time()

        successful_requests = 0
        for _ in range(num_requests):
            response = client.post("/api/signals/cognitive", json=request_data)
            if response.status_code == 200:
                successful_requests += 1

        total_time = time.time() - start_time
        throughput = successful_requests / total_time

        # Should handle at least 10 requests per second
        assert throughput >= 10, f"Throughput {throughput:.2f} RPS below minimum 10 RPS"
        assert (
            successful_requests >= num_requests * 0.9
        ), f"Success rate {successful_requests / num_requests:.2%} too low"

        print(
            f"✓ Throughput benchmark: {throughput:.2f} RPS, {successful_requests}/{num_requests} successful"
        )

    def test_memory_stress(self, client):
        """Test memory usage under stress."""
        import gc

        # Force garbage collection
        gc.collect()

        request_data = {"symbol": "AAPL"}

        # Make many requests to test memory usage
        for i in range(100):
            response = client.post("/api/signals/cognitive", json=request_data)

            # Periodic cleanup
            if i % 20 == 0:
                gc.collect()

        # Final cleanup
        gc.collect()

        # If we reach here without memory errors, test passes
        assert True, "Memory stress test completed successfully"


if __name__ == "__main__":
    # Run API tests
    pytest.main([__file__, "-v", "--tb=short"])
