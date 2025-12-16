"""
ASCEND Lambda Authorizer - Performance Tests
=============================================

Performance benchmarks to verify:
- <100ms p99 latency target
- >500 RPS minimum throughput
- Cache effectiveness

Run with: pytest tests/test_performance.py -v --benchmark-enable

Author: ASCEND Platform Engineering
"""

import os
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock

import pytest

# Set test environment
os.environ["ASCEND_API_URL"] = "https://test.ascend.owkai.app"
os.environ["ASCEND_API_KEY"] = "test_api_key_12345"
os.environ["ASCEND_ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise


class TestLatencyBenchmarks:
    """Latency performance tests."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset module state."""
        from src import handler
        handler.reset_state()
        yield
        handler.reset_state()

    @pytest.fixture
    def mock_fast_response(self):
        """Mock fast ASCEND API response."""
        return {
            "id": 12345,
            "status": "approved",
            "risk_score": 25.0,
            "risk_level": "low",
            "requires_approval": False,
            "alert_triggered": False
        }

    @pytest.fixture
    def sample_event(self):
        """Sample request event."""
        return {
            "type": "REQUEST",
            "methodArn": "arn:aws:execute-api:us-east-1:123:api/stage/GET/users",
            "httpMethod": "GET",
            "path": "/users",
            "headers": {"X-Ascend-Agent-Id": "perf-test-agent"},
            "requestContext": {"requestId": "perf-test"}
        }

    @pytest.fixture
    def mock_context(self):
        """Mock Lambda context."""
        ctx = Mock()
        ctx.aws_request_id = "perf-test-id"
        return ctx

    def test_cold_start_latency(self, sample_event, mock_context, mock_fast_response):
        """
        Test cold start latency.

        Target: <500ms for cold start (initialization + first request)
        """
        from src import handler
        handler.reset_state()  # Ensure cold start

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_fast_response).encode()
            mock_resp.__enter__ = Mock(return_value=mock_resp)
            mock_resp.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_resp

            start = time.perf_counter()
            result = handler.lambda_handler(sample_event, mock_context)
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert result["policyDocument"]["Statement"][0]["Effect"] == "Allow"
            print(f"\nCold start latency: {elapsed_ms:.2f}ms")

            # Cold start should be <500ms
            assert elapsed_ms < 500, f"Cold start too slow: {elapsed_ms:.2f}ms"

    def test_warm_start_latency(self, sample_event, mock_context, mock_fast_response):
        """
        Test warm start latency (cached path).

        Target: <10ms for cached decisions
        """
        from src import handler

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_fast_response).encode()
            mock_resp.__enter__ = Mock(return_value=mock_resp)
            mock_resp.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_resp

            # First call (populates cache)
            handler.lambda_handler(sample_event, mock_context)

            # Second call (should hit cache)
            start = time.perf_counter()
            result = handler.lambda_handler(sample_event, mock_context)
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert result["policyDocument"]["Statement"][0]["Effect"] == "Allow"
            print(f"\nWarm start (cached) latency: {elapsed_ms:.2f}ms")

            # Cached response should be <10ms
            assert elapsed_ms < 10, f"Cached response too slow: {elapsed_ms:.2f}ms"

    def test_api_call_latency_simulation(self, sample_event, mock_context, mock_fast_response):
        """
        Test latency with simulated network delay.

        Target: <100ms p99 with 50ms API latency
        """
        from src import handler
        handler.reset_state()

        def delayed_response(*args, **kwargs):
            time.sleep(0.05)  # 50ms simulated network latency
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_fast_response).encode()
            mock_resp.__enter__ = Mock(return_value=mock_resp)
            mock_resp.__exit__ = Mock(return_value=False)
            return mock_resp

        with patch('src.ascend_client.urlopen', side_effect=delayed_response):
            latencies = []

            # Run multiple requests (first populates cache, rest hit cache)
            for i in range(10):
                sample_event["requestContext"]["requestId"] = f"perf-{i}"
                start = time.perf_counter()
                handler.lambda_handler(sample_event, mock_context)
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

            p50 = statistics.median(latencies)
            p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)

            print(f"\nLatency stats (n={len(latencies)}):")
            print(f"  Min: {min(latencies):.2f}ms")
            print(f"  P50: {p50:.2f}ms")
            print(f"  P99: {p99:.2f}ms")
            print(f"  Max: {max(latencies):.2f}ms")

            # P99 should be <100ms (most are cached)
            assert p99 < 100, f"P99 latency too high: {p99:.2f}ms"


class TestThroughputBenchmarks:
    """Throughput performance tests."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset module state."""
        from src import handler
        handler.reset_state()
        yield
        handler.reset_state()

    @pytest.fixture
    def mock_fast_response(self):
        """Mock fast ASCEND API response."""
        return {
            "id": 12345,
            "status": "approved",
            "risk_score": 25.0,
            "risk_level": "low",
            "requires_approval": False,
            "alert_triggered": False
        }

    def test_sequential_throughput(self, mock_fast_response):
        """
        Test sequential request throughput.

        Measures RPS for sequential requests (cache hits).
        """
        from src import handler

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_fast_response).encode()
            mock_resp.__enter__ = Mock(return_value=mock_resp)
            mock_resp.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_resp

            event = {
                "type": "REQUEST",
                "methodArn": "arn:aws:execute-api:us-east-1:123:api/stage/GET/users",
                "httpMethod": "GET",
                "path": "/users",
                "headers": {"X-Ascend-Agent-Id": "throughput-agent"},
                "requestContext": {"requestId": "throughput-test"}
            }
            ctx = Mock()
            ctx.aws_request_id = "throughput-test"

            # Warm up (first call populates cache)
            handler.lambda_handler(event, ctx)

            # Benchmark
            iterations = 100
            start = time.perf_counter()

            for i in range(iterations):
                event["requestContext"]["requestId"] = f"seq-{i}"
                handler.lambda_handler(event, ctx)

            elapsed = time.perf_counter() - start
            rps = iterations / elapsed

            print(f"\nSequential throughput: {rps:.0f} RPS ({iterations} requests in {elapsed:.2f}s)")

            # Should achieve >500 RPS for cached requests
            assert rps > 500, f"Throughput too low: {rps:.0f} RPS"


class TestCacheEffectiveness:
    """Cache effectiveness tests."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset module state."""
        from src import handler
        handler.reset_state()
        yield
        handler.reset_state()

    def test_cache_hit_rate(self):
        """
        Test cache hit rate for repeated requests.

        Target: >90% cache hit rate for same agent/action
        """
        from src import handler
        from src.policy_generator import get_policy_cache

        mock_response = {
            "id": 12345,
            "status": "approved",
            "risk_score": 25.0,
            "risk_level": "low",
            "requires_approval": False,
            "alert_triggered": False
        }

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_resp.__enter__ = Mock(return_value=mock_resp)
            mock_resp.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_resp

            event = {
                "type": "REQUEST",
                "methodArn": "arn:aws:execute-api:us-east-1:123:api/stage/GET/users",
                "httpMethod": "GET",
                "path": "/users",
                "headers": {"X-Ascend-Agent-Id": "cache-test-agent"},
                "requestContext": {"requestId": "cache-test"}
            }
            ctx = Mock()
            ctx.aws_request_id = "cache-test"

            # Run 100 requests for same agent/action
            for i in range(100):
                event["requestContext"]["requestId"] = f"cache-{i}"
                handler.lambda_handler(event, ctx)

            # Count API calls (should be 1 - first request only)
            api_calls = mock_urlopen.call_count
            cache_hit_rate = (100 - api_calls) / 100 * 100

            print(f"\nCache statistics:")
            print(f"  Total requests: 100")
            print(f"  API calls: {api_calls}")
            print(f"  Cache hit rate: {cache_hit_rate:.1f}%")

            # Should have >90% cache hit rate
            assert cache_hit_rate >= 90, f"Cache hit rate too low: {cache_hit_rate:.1f}%"

    def test_cache_key_differentiation(self):
        """Test that different agents/actions have separate cache entries."""
        from src import handler

        mock_response = {
            "id": 12345,
            "status": "approved",
            "risk_score": 25.0,
            "risk_level": "low",
            "requires_approval": False,
            "alert_triggered": False
        }

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_resp.__enter__ = Mock(return_value=mock_resp)
            mock_resp.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_resp

            ctx = Mock()
            ctx.aws_request_id = "cache-key-test"

            # Different agents should have different cache entries
            agents = ["agent-1", "agent-2", "agent-3"]

            for agent in agents:
                event = {
                    "type": "REQUEST",
                    "methodArn": "arn:aws:execute-api:us-east-1:123:api/stage/GET/users",
                    "httpMethod": "GET",
                    "path": "/users",
                    "headers": {"X-Ascend-Agent-Id": agent},
                    "requestContext": {"requestId": f"key-test-{agent}"}
                }
                handler.lambda_handler(event, ctx)

            # Should have 3 API calls (one per unique agent)
            assert mock_urlopen.call_count == 3, \
                f"Expected 3 API calls for 3 agents, got {mock_urlopen.call_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
