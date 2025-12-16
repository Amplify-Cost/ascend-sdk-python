"""
ASCEND Lambda Authorizer - Handler Tests
========================================

Tests for the main Lambda handler including:
- Happy path authorization
- FAIL SECURE behavior
- Cache behavior
- Error handling

Author: ASCEND Platform Engineering
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Set test environment variables before imports
os.environ["ASCEND_API_URL"] = "https://test.ascend.owkai.app"
os.environ["ASCEND_API_KEY"] = "test_api_key_12345"
os.environ["ASCEND_ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset module state before each test."""
        # Import after env vars are set
        from src import handler
        handler.reset_state()
        yield
        handler.reset_state()

    @pytest.fixture
    def mock_ascend_response(self):
        """Mock ASCEND API response."""
        return {
            "id": 12345,
            "status": "approved",
            "risk_score": 25.0,
            "risk_level": "low",
            "requires_approval": False,
            "alert_triggered": False,
            "correlation_id": "test-correlation-123"
        }

    @pytest.fixture
    def sample_request_event(self):
        """Sample API Gateway REQUEST authorizer event."""
        return {
            "type": "REQUEST",
            "methodArn": "arn:aws:execute-api:us-east-1:123456789012:abc123/prod/GET/users",
            "resource": "/users",
            "path": "/users",
            "httpMethod": "GET",
            "headers": {
                "X-Ascend-Agent-Id": "test-agent-001",
                "X-Ascend-Environment": "test",
                "Content-Type": "application/json"
            },
            "queryStringParameters": {},
            "pathParameters": {},
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "abc123",
                "stage": "prod",
                "requestId": "test-request-id",
                "identity": {
                    "sourceIp": "192.168.1.1"
                }
            }
        }

    @pytest.fixture
    def sample_http_api_event(self):
        """Sample API Gateway HTTP API v2 event."""
        return {
            "version": "2.0",
            "routeArn": "arn:aws:execute-api:us-east-1:123456789012:abc123/prod/GET/users",
            "headers": {
                "x-ascend-agent-id": "test-agent-001",
                "x-ascend-environment": "production"
            },
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "abc123",
                "stage": "prod",
                "requestId": "http-api-request-id",
                "http": {
                    "method": "GET",
                    "path": "/users",
                    "sourceIp": "192.168.1.1"
                }
            }
        }

    @pytest.fixture
    def mock_context(self):
        """Mock Lambda context."""
        context = Mock()
        context.aws_request_id = "lambda-request-id-12345"
        context.function_name = "ascend-authorizer"
        context.memory_limit_in_mb = 128
        context.get_remaining_time_in_millis = Mock(return_value=5000)
        return context

    def test_approved_action_returns_allow_policy(
        self,
        sample_request_event,
        mock_context,
        mock_ascend_response
    ):
        """Test that approved actions return Allow policy."""
        from src.handler import lambda_handler

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            # Configure mock response
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_ascend_response).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = lambda_handler(sample_request_event, mock_context)

            # Verify Allow policy
            assert result["principalId"] == "test-agent-001"
            assert result["policyDocument"]["Statement"][0]["Effect"] == "Allow"
            assert "context" in result
            assert result["context"]["ascend_status"] == "approved"

    def test_pending_approval_returns_deny_policy(
        self,
        sample_request_event,
        mock_context
    ):
        """Test that pending_approval actions return Deny policy."""
        from src.handler import lambda_handler

        pending_response = {
            "id": 12345,
            "status": "pending_approval",
            "risk_score": 75.0,
            "risk_level": "high",
            "requires_approval": True,
            "alert_triggered": True,
            "workflow_id": 999,
            "correlation_id": "pending-correlation"
        }

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(pending_response).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = lambda_handler(sample_request_event, mock_context)

            # Verify Deny policy
            assert result["principalId"] == "test-agent-001"
            assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
            assert result["context"]["ascend_status"] == "pending_approval"

    def test_denied_action_returns_deny_policy(
        self,
        sample_request_event,
        mock_context
    ):
        """Test that denied actions return Deny policy."""
        from src.handler import lambda_handler

        denied_response = {
            "id": 12345,
            "status": "denied",
            "risk_score": 95.0,
            "risk_level": "critical",
            "requires_approval": True,
            "alert_triggered": True,
            "correlation_id": "denied-correlation"
        }

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(denied_response).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = lambda_handler(sample_request_event, mock_context)

            # Verify Deny policy
            assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
            assert result["context"]["ascend_status"] == "denied"


class TestFailSecure:
    """Tests verifying FAIL SECURE behavior."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset module state before each test."""
        from src import handler
        handler.reset_state()
        yield
        handler.reset_state()

    @pytest.fixture
    def sample_event(self):
        """Minimal sample event."""
        return {
            "type": "REQUEST",
            "methodArn": "arn:aws:execute-api:us-east-1:123:api/stage/GET/resource",
            "headers": {
                "X-Ascend-Agent-Id": "test-agent"
            },
            "httpMethod": "GET",
            "path": "/test",
            "requestContext": {}
        }

    @pytest.fixture
    def mock_context(self):
        """Mock Lambda context."""
        context = Mock()
        context.aws_request_id = "test-request-id"
        return context

    def test_timeout_returns_deny(self, sample_event, mock_context):
        """FAIL SECURE: API timeout must return Deny."""
        from src.handler import lambda_handler
        from urllib.error import URLError
        import socket

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = URLError(socket.timeout("timed out"))

            result = lambda_handler(sample_event, mock_context)

            assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
            assert "timeout" in result["context"]["ascend_error"].lower()

    def test_connection_error_returns_deny(self, sample_event, mock_context):
        """FAIL SECURE: Connection error must return Deny."""
        from src.handler import lambda_handler
        from urllib.error import URLError

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = URLError("Connection refused")

            result = lambda_handler(sample_event, mock_context)

            assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"

    def test_authentication_error_returns_deny(self, sample_event, mock_context):
        """FAIL SECURE: Auth error (401) must return Deny."""
        from src.handler import lambda_handler
        from urllib.error import HTTPError

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            error = HTTPError(
                url="https://test.api",
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=None
            )
            mock_urlopen.side_effect = error

            result = lambda_handler(sample_event, mock_context)

            assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
            assert result["context"]["ascend_error_code"] == "AUTH_ERROR"

    def test_server_error_returns_deny(self, sample_event, mock_context):
        """FAIL SECURE: Server error (500) must return Deny."""
        from src.handler import lambda_handler
        from urllib.error import HTTPError

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            error = HTTPError(
                url="https://test.api",
                code=500,
                msg="Internal Server Error",
                hdrs={},
                fp=None
            )
            mock_urlopen.side_effect = error

            result = lambda_handler(sample_event, mock_context)

            assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"

    def test_unexpected_exception_returns_deny(self, sample_event, mock_context):
        """FAIL SECURE: Unexpected errors must return Deny."""
        from src.handler import lambda_handler

        with patch('src.ascend_client.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = RuntimeError("Unexpected error")

            result = lambda_handler(sample_event, mock_context)

            assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
            # RuntimeError in ascend_client is wrapped as AscendAPIError
            assert result["context"]["ascend_error_code"] == "API_ERROR"

    def test_missing_agent_id_returns_deny(self, mock_context):
        """FAIL SECURE: Missing agent ID must return Deny."""
        from src.handler import lambda_handler

        event_without_agent = {
            "type": "REQUEST",
            "methodArn": "arn:aws:execute-api:us-east-1:123:api/stage/GET/resource",
            "headers": {},  # No X-Ascend-Agent-Id
            "httpMethod": "GET",
            "path": "/test",
            "requestContext": {}
        }

        result = lambda_handler(event_without_agent, mock_context)

        assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
        assert "agent" in result["context"]["ascend_error"].lower()


class TestRequestMapping:
    """Tests for request mapping functionality."""

    def test_request_authorizer_mapping(self):
        """Test REQUEST authorizer event mapping."""
        from src.request_mapper import RequestMapper

        mapper = RequestMapper()
        event = {
            "type": "REQUEST",
            "methodArn": "arn:aws:execute-api:us-east-1:123:api/stage/POST/users",
            "httpMethod": "POST",
            "path": "/users",
            "headers": {
                "X-Ascend-Agent-Id": "user-service-agent",
                "X-Ascend-Environment": "production",
                "X-Ascend-Data-Sensitivity": "pii"
            },
            "requestContext": {
                "identity": {"sourceIp": "10.0.0.1"}
            }
        }

        mapped = mapper.map_event(event)

        assert mapped.agent_id == "user-service-agent"
        assert mapped.action_type == "create_users"
        assert mapped.http_method == "POST"
        assert mapped.environment == "production"
        assert mapped.data_sensitivity == "pii"

    def test_http_api_v2_mapping(self):
        """Test HTTP API v2 event mapping."""
        from src.request_mapper import RequestMapper

        mapper = RequestMapper()
        event = {
            "version": "2.0",
            "routeArn": "arn:aws:execute-api:us-east-1:123:api/stage/DELETE/orders/123",
            "headers": {
                "x-ascend-agent-id": "admin-agent"
            },
            "requestContext": {
                "http": {
                    "method": "DELETE",
                    "path": "/orders/123",
                    "sourceIp": "192.168.1.100"
                }
            }
        }

        mapped = mapper.map_event(event)

        assert mapped.agent_id == "admin-agent"
        assert mapped.http_method == "DELETE"
        # /orders/123 doesn't match special patterns, so it's delete_orders
        assert mapped.action_type == "delete_orders"

    def test_action_type_detection_patterns(self):
        """Test action type detection for special paths."""
        from src.request_mapper import RequestMapper

        mapper = RequestMapper()

        test_cases = [
            ("/admin/users", "GET", "admin_access"),
            ("/api/export", "POST", "data_export"),
            ("/settings", "PUT", "configuration"),
            ("/auth/login", "POST", "authentication"),
        ]

        for path, method, expected_action in test_cases:
            event = {
                "type": "REQUEST",
                "methodArn": f"arn:aws:execute-api:us-east-1:123:api/stage/{method}{path}",
                "httpMethod": method,
                "path": path,
                "headers": {"X-Ascend-Agent-Id": "test-agent"},
                "requestContext": {}
            }

            mapped = mapper.map_event(event)
            assert mapped.action_type == expected_action, f"Path {path} should map to {expected_action}"


class TestPolicyGenerator:
    """Tests for policy generation."""

    def test_allow_policy_structure(self):
        """Test Allow policy document structure."""
        from src.policy_generator import PolicyGenerator
        from src.request_mapper import MappedRequest
        from src.ascend_client import AscendResponse

        generator = PolicyGenerator()

        request = MappedRequest(
            agent_id="test-agent",
            action_type="read_users",
            description="GET /users by test-agent via API Gateway",
            tool_name="api_gateway",
            target_system="/users",
            environment="production",
            data_sensitivity="none",
            source_ip="192.168.1.1",
            user_agent="test-client",
            method_arn="arn:aws:execute-api:us-east-1:123:api/stage/GET/users",
            resource_path="/users",
            http_method="GET",
            context={}
        )

        response = AscendResponse(
            id=12345,
            status="approved",
            risk_score=25.0,
            risk_level="low",
            requires_approval=False,
            alert_triggered=False
        )

        policy = generator.generate_policy(request, response, allow=True)

        assert policy.principal_id == "test-agent"
        assert policy.policy_document["Version"] == "2012-10-17"
        assert policy.policy_document["Statement"][0]["Effect"] == "Allow"
        assert policy.context["ascend_action_id"] == 12345  # Integer, not string

    def test_deny_policy_for_error(self):
        """Test Deny policy generation for errors."""
        from src.policy_generator import PolicyGenerator

        generator = PolicyGenerator()

        policy = generator.generate_deny_policy(
            agent_id="unknown-agent",
            method_arn="arn:aws:execute-api:us-east-1:123:api/stage/*",
            reason="Service unavailable",
            error_code="SERVICE_ERROR"
        )

        assert policy.policy_document["Statement"][0]["Effect"] == "Deny"
        assert policy.context["ascend_error"] == "Service unavailable"
        assert policy.context["ascend_error_code"] == "SERVICE_ERROR"


class TestCaching:
    """Tests for policy caching."""

    def test_cache_stores_approved_decisions(self):
        """Test that cache stores approved decisions."""
        from src.policy_generator import PolicyCache, AuthorizationPolicy
        from src.ascend_client import AscendResponse

        cache = PolicyCache(ttl_seconds=60)

        policy = AuthorizationPolicy(
            principal_id="test-agent",
            policy_document={"Statement": [{"Effect": "Allow"}]},
            context={"ascend_status": "approved"}
        )

        response = AscendResponse(
            id=123,
            status="approved",
            risk_score=20.0,
            risk_level="low",
            requires_approval=False,
            alert_triggered=False
        )

        cache.set("test-key", policy, response)

        cached = cache.get("test-key")
        assert cached is not None
        assert cached.principal_id == "test-agent"

    def test_cache_does_not_store_denied_decisions(self):
        """Test that cache does NOT store denied decisions."""
        from src.policy_generator import PolicyCache, AuthorizationPolicy
        from src.ascend_client import AscendResponse

        cache = PolicyCache(ttl_seconds=60)

        policy = AuthorizationPolicy(
            principal_id="test-agent",
            policy_document={"Statement": [{"Effect": "Deny"}]},
            context={"ascend_status": "denied"}
        )

        response = AscendResponse(
            id=123,
            status="denied",
            risk_score=95.0,
            risk_level="critical",
            requires_approval=True,
            alert_triggered=True
        )

        cache.set("denied-key", policy, response)

        cached = cache.get("denied-key")
        assert cached is None  # Should NOT be cached

    def test_cache_expiration(self):
        """Test that cache entries expire."""
        import time
        from src.policy_generator import PolicyCache, AuthorizationPolicy
        from src.ascend_client import AscendResponse

        cache = PolicyCache(ttl_seconds=1)  # 1 second TTL

        policy = AuthorizationPolicy(
            principal_id="test-agent",
            policy_document={"Statement": [{"Effect": "Allow"}]},
            context={}
        )

        response = AscendResponse(
            id=123, status="approved", risk_score=20.0,
            risk_level="low", requires_approval=False, alert_triggered=False
        )

        cache.set("expiring-key", policy, response)

        # Should exist immediately
        assert cache.get("expiring-key") is not None

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        assert cache.get("expiring-key") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
