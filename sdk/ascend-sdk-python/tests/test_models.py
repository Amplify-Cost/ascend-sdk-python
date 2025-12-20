"""
ASCEND SDK Model Tests
OW-KAI Technologies, Inc.

Tests for AgentAction model schema alignment with backend API.
Evidence: actions_v1_routes.py:287 defines required fields.

Compliance: SOC 2, PCI-DSS, HIPAA, FedRAMP
"""
import pytest
from ascend.models import AgentAction, ActionResult, ConnectionStatus


class TestAgentActionModel:
    """Test AgentAction model matches backend requirements."""

    def test_required_fields_present(self):
        """
        Verify all backend-required fields are mandatory in SDK.
        Evidence: actions_v1_routes.py:287
        Required: agent_id, action_type, description (mapped from resource), tool_name
        """
        action = AgentAction(
            agent_id="test-agent-001",
            agent_name="Test Agent",
            action_type="data_access",
            resource="customer_database",
            tool_name="crm_api"
        )
        assert action.agent_id == "test-agent-001"
        assert action.agent_name == "Test Agent"
        assert action.action_type == "data_access"
        assert action.resource == "customer_database"
        assert action.tool_name == "crm_api"

    def test_tool_name_required(self):
        """
        Verify tool_name is required (not optional).
        Backend will return 422 if missing.
        Evidence: actions_v1_routes.py:287-293
        """
        with pytest.raises(TypeError, match="tool_name"):
            AgentAction(
                agent_id="test",
                agent_name="test",
                action_type="test",
                resource="test"
                # Missing tool_name should raise TypeError
            )

    def test_to_dict_includes_all_required_fields(self):
        """
        Verify to_dict() output matches backend expected schema.
        Evidence: actions_v1_routes.py:287-293
        """
        action = AgentAction(
            agent_id="test-agent",
            agent_name="Test",
            action_type="read",
            resource="database",
            tool_name="sql_client"
        )
        data = action.to_dict()

        # Backend required fields (actions_v1_routes.py:287)
        assert "agent_id" in data
        assert "action_type" in data
        assert "description" in data  # mapped from resource
        assert "tool_name" in data

        # Verify values
        assert data["agent_id"] == "test-agent"
        assert data["action_type"] == "read"
        assert data["description"] == "database"  # resource -> description
        assert data["tool_name"] == "sql_client"

    def test_resource_maps_to_description(self):
        """
        Verify resource field maps to description in API payload.
        Backend expects 'description', SDK uses 'resource' for clarity.
        """
        action = AgentAction(
            agent_id="test",
            agent_name="test",
            action_type="test",
            resource="Access customer PII data",
            tool_name="test"
        )
        data = action.to_dict()

        assert "description" in data
        assert data["description"] == "Access customer PII data"
        assert "resource" not in data  # resource is internal, description is API field

    def test_to_dict_excludes_none_optional_fields(self):
        """Verify optional None fields are not sent to backend."""
        action = AgentAction(
            agent_id="test",
            agent_name="test",
            action_type="test",
            resource="test",
            tool_name="test"
            # All optional fields default to None
        )
        data = action.to_dict()

        # None values should not be in output (cleaner payload)
        assert "resource_id" not in data
        assert "action_details" not in data
        assert "context" not in data
        assert "risk_indicators" not in data

    def test_optional_fields_included_when_set(self):
        """Verify optional fields are included when provided."""
        action = AgentAction(
            agent_id="test",
            agent_name="test",
            action_type="test",
            resource="test",
            tool_name="test",
            resource_id="RES-123",
            context={"environment": "production"},
            action_details={"key": "value"},
            risk_indicators={"score": 50}
        )
        data = action.to_dict()

        assert data.get("resource_id") == "RES-123"
        assert data.get("context") == {"environment": "production"}
        assert data.get("action_details") == {"key": "value"}
        assert data.get("risk_indicators") == {"score": 50}

    def test_repr_format(self):
        """Verify __repr__ provides useful debugging output."""
        action = AgentAction(
            agent_id="bot-001",
            agent_name="Test Bot",
            action_type="query",
            resource="database",
            tool_name="sql"
        )
        repr_str = repr(action)

        assert "AgentAction" in repr_str
        assert "bot-001" in repr_str
        assert "query" in repr_str


class TestAgentActionEnterpriseCompliance:
    """Tests for enterprise/compliance requirements."""

    def test_no_organization_id_in_payload(self):
        """
        CRITICAL: SDK must NOT send organization_id.
        Multi-tenancy: org_id derived from API key on backend.
        Sending org_id would be a security violation.
        Compliance: SOC 2, PCI-DSS, HIPAA
        """
        action = AgentAction(
            agent_id="test",
            agent_name="test",
            action_type="test",
            resource="test",
            tool_name="test"
        )
        data = action.to_dict()

        # These should NEVER be in the payload
        assert "organization_id" not in data
        assert "org_id" not in data
        assert "tenant_id" not in data

    def test_no_user_id_in_payload(self):
        """
        SDK should not send user_id - derived from auth on backend.
        """
        action = AgentAction(
            agent_id="test",
            agent_name="test",
            action_type="test",
            resource="test",
            tool_name="test"
        )
        data = action.to_dict()

        assert "user_id" not in data

    def test_field_types_are_correct(self):
        """Verify field types match backend expectations."""
        action = AgentAction(
            agent_id="test",
            agent_name="test",
            action_type="test",
            resource="test",
            tool_name="test",
            context={"key": "value"},
            risk_indicators={"score": 50}
        )
        data = action.to_dict()

        assert isinstance(data["agent_id"], str)
        assert isinstance(data["agent_name"], str)
        assert isinstance(data["action_type"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["tool_name"], str)
        assert isinstance(data.get("context", {}), dict)
        assert isinstance(data.get("risk_indicators", {}), dict)

    def test_all_standard_action_types(self):
        """Verify SDK accepts all standard action types."""
        standard_types = [
            "data_access",
            "data_modification",
            "transaction",
            "recommendation",
            "communication",
            "system_operation",
            "query",
            "file_access",
            "api_call",
            "database_operation"
        ]

        for action_type in standard_types:
            action = AgentAction(
                agent_id="test",
                agent_name="test",
                action_type=action_type,
                resource="test",
                tool_name="test"
            )
            assert action.action_type == action_type


class TestActionResult:
    """Tests for ActionResult model."""

    def test_from_dict_complete(self):
        """Test parsing complete API response."""
        data = {
            "id": 123,
            "status": "approved",
            "risk_score": 45.5,
            "risk_level": "medium",
            "reason": "Auto-approved: low risk",
            "policy_matched": "default_policy",
            "timestamp": "2025-12-12T10:00:00Z"
        }
        result = ActionResult.from_dict(data)

        assert result.action_id == "123"
        assert result.status == "approved"
        assert result.risk_score == 45.5
        assert result.risk_level == "medium"
        assert result.reason == "Auto-approved: low risk"

    def test_from_dict_minimal(self):
        """Test parsing minimal API response."""
        data = {"status": "pending"}
        result = ActionResult.from_dict(data)

        assert result.status == "pending"
        assert result.action_id == ""

    def test_is_approved(self):
        """Test approved status helper."""
        result = ActionResult(action_id="1", status="approved")
        assert result.is_approved() is True
        assert result.is_denied() is False
        assert result.is_pending() is False

    def test_is_denied(self):
        """Test denied status helper."""
        result = ActionResult(action_id="1", status="denied")
        assert result.is_approved() is False
        assert result.is_denied() is True
        assert result.is_pending() is False

    def test_is_pending(self):
        """Test pending status helper."""
        result = ActionResult(action_id="1", status="pending")
        assert result.is_approved() is False
        assert result.is_denied() is False
        assert result.is_pending() is True

    def test_action_id_from_id_field(self):
        """Test action_id extraction from 'id' field."""
        data = {"id": 456, "status": "approved"}
        result = ActionResult.from_dict(data)
        assert result.action_id == "456"

    def test_action_id_from_action_id_field(self):
        """Test action_id extraction from 'action_id' field."""
        data = {"action_id": 789, "status": "approved"}
        result = ActionResult.from_dict(data)
        assert result.action_id == "789"


class TestConnectionStatus:
    """Tests for ConnectionStatus model."""

    def test_from_dict(self):
        """Test parsing connection status response."""
        data = {
            "status": "connected",
            "api_version": "1.0.0",
            "server_time": "2025-12-12T10:00:00Z",
            "latency_ms": 45.2
        }
        status = ConnectionStatus.from_dict(data)

        assert status.status == "connected"
        assert status.api_version == "1.0.0"
        assert status.is_connected() is True

    def test_is_connected_false(self):
        """Test connection failure detection."""
        status = ConnectionStatus(status="error", error="Connection refused")
        assert status.is_connected() is False
        assert status.error == "Connection refused"


class TestBackendSchemaAlignment:
    """
    Integration tests verifying SDK matches backend schema.
    Evidence: actions_v1_routes.py:287
    """

    def test_backend_required_fields_match_sdk(self):
        """
        Backend: required = ["agent_id", "action_type", "description", "tool_name"]
        SDK: agent_id, agent_name, action_type, resource (->description), tool_name
        """
        # Create action with all required fields
        action = AgentAction(
            agent_id="backend-test-001",
            agent_name="Backend Test Agent",
            action_type="database_operation",
            resource="SELECT * FROM customers",
            tool_name="postgresql_client"
        )

        data = action.to_dict()

        # Backend required fields (actions_v1_routes.py:287)
        backend_required = ["agent_id", "action_type", "description", "tool_name"]

        for field in backend_required:
            assert field in data, f"Missing backend required field: {field}"
            assert data[field], f"Backend required field is empty: {field}"
