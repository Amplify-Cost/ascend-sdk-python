"""
OW-kai Enterprise Enrichment System - SEC-059 Unit Tests

Testing: SEC-059 Enrichment Action Type Expansion
Coverage: Action type classification, NIST/MITRE mappings, risk level assignment

Security Tests:
- High-risk action type detection
- Medium-risk action type detection
- Low-risk action type detection (NEW)
- NIST SP 800-53 control mapping accuracy
- MITRE ATT&CK technique mapping accuracy
- Context-aware risk elevation

Compliance: SOC 2 CC6.1, NIST 800-53, MITRE ATT&CK Framework
Document ID: SEC-059-TESTS
Version: 1.0.0
Date: December 3, 2025
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enrichment import (
    evaluate_action_enrichment,
    get_enterprise_compliance_mapping,
    HIGH_RISK_ACTION_TYPES,
    MEDIUM_RISK_ACTION_TYPES,
    LOW_RISK_ACTION_TYPES,
    ENTERPRISE_COMPLIANCE_MAPPINGS
)


class TestActionTypeClassification:
    """Test suite for action type risk classification"""

    # =========================================================================
    # HIGH-RISK ACTION TYPE TESTS
    # =========================================================================

    def test_high_risk_action_types_count(self):
        """SEC-059: Verify HIGH_RISK_ACTION_TYPES has expected count"""
        assert len(HIGH_RISK_ACTION_TYPES) == 24

    @pytest.mark.parametrize("action_type", [
        "database_write",
        "database_delete",
        "data_export",
        "data_exfiltration",
        "bulk_delete",
        "bulk_write",
        "shell_command",
        "process_execute",
        "script_run",
        "encryption_key_access",
        "audit_log_modify",
        "privilege_escalation",
        "system_shutdown",
        "firewall_modify",
    ])
    def test_high_risk_action_returns_high_level(self, action_type):
        """SEC-059: High-risk action types should return risk_level='high'"""
        result = evaluate_action_enrichment(action_type, "Test action", db=None)
        assert result["risk_level"] == "high", f"{action_type} should be high risk"

    def test_database_write_nist_control(self):
        """SEC-059: database_write should map to AC-3 (Access Enforcement)"""
        result = evaluate_action_enrichment("database_write", "Write to database", db=None)
        assert result["nist_control"] == "AC-3"

    def test_bulk_delete_mitre_technique(self):
        """SEC-059: bulk_delete should map to T1485 (Data Destruction)"""
        result = evaluate_action_enrichment("bulk_delete", "Delete all records", db=None)
        assert result["mitre_technique"] == "T1485"
        assert result["mitre_tactic"] == "TA0040"  # Impact

    def test_shell_command_mitre_technique(self):
        """SEC-059: shell_command should map to T1059 (Command Interpreter)"""
        result = evaluate_action_enrichment("shell_command", "Execute shell command", db=None)
        assert result["mitre_technique"] == "T1059"
        assert result["mitre_tactic"] == "TA0002"  # Execution

    def test_encryption_key_access_nist_control(self):
        """SEC-059: encryption_key_access should map to SC-12 (Cryptographic Key Management)"""
        result = evaluate_action_enrichment("encryption_key_access", "Access encryption keys", db=None)
        assert result["nist_control"] == "SC-12"
        assert result["mitre_technique"] == "T1552.004"  # Private Keys

    def test_audit_log_modify_nist_control(self):
        """SEC-059: audit_log_modify should map to AU-9 (Protection of Audit Information)"""
        result = evaluate_action_enrichment("audit_log_modify", "Modify audit logs", db=None)
        assert result["nist_control"] == "AU-9"
        assert result["mitre_technique"] == "T1070"  # Indicator Removal

    # =========================================================================
    # MEDIUM-RISK ACTION TYPE TESTS
    # =========================================================================

    def test_medium_risk_action_types_count(self):
        """SEC-059: Verify MEDIUM_RISK_ACTION_TYPES has expected count"""
        assert len(MEDIUM_RISK_ACTION_TYPES) == 23

    @pytest.mark.parametrize("action_type", [
        "data_access",
        "data_read",
        "database_read",
        "database_query",
        "file_read",
        "file_delete",
        "file_upload",
        "file_download",
        "email_send",
        "webhook_trigger",
        "external_api_call",
    ])
    def test_medium_risk_action_returns_medium_level(self, action_type):
        """SEC-059: Medium-risk action types should return risk_level='medium'"""
        result = evaluate_action_enrichment(action_type, "Test action", db=None)
        assert result["risk_level"] == "medium", f"{action_type} should be medium risk"

    def test_data_access_nist_control(self):
        """SEC-059: data_access should map to AU-2 (Audit Events)"""
        result = evaluate_action_enrichment("data_access", "Access customer data", db=None)
        assert result["nist_control"] == "AU-2"
        assert result["mitre_tactic"] == "TA0009"  # Collection

    def test_file_delete_mitre_technique(self):
        """SEC-059: file_delete should map to T1485 (Data Destruction)"""
        result = evaluate_action_enrichment("file_delete", "Delete file", db=None)
        assert result["mitre_technique"] == "T1485"

    def test_email_send_mitre_technique(self):
        """SEC-059: email_send should map to T1048.003 (Exfiltration Over Non-C2)"""
        result = evaluate_action_enrichment("email_send", "Send email", db=None)
        assert result["mitre_technique"] == "T1048.003"
        assert result["mitre_tactic"] == "TA0010"  # Exfiltration

    def test_webhook_trigger_mitre_technique(self):
        """SEC-059: webhook_trigger should map to T1071.001 (Web Protocols)"""
        result = evaluate_action_enrichment("webhook_trigger", "Trigger webhook", db=None)
        assert result["mitre_technique"] == "T1071.001"

    # =========================================================================
    # LOW-RISK ACTION TYPE TESTS (NEW in SEC-059)
    # =========================================================================

    def test_low_risk_action_types_count(self):
        """SEC-059: Verify LOW_RISK_ACTION_TYPES has expected count"""
        assert len(LOW_RISK_ACTION_TYPES) == 15

    @pytest.mark.parametrize("action_type", [
        "llm_call",
        "model_inference",
        "embedding_generate",
        "vector_search",
        "http_request",
        "dns_lookup",
        "log_read",
        "metrics_read",
        "cache_read",
        "cache_write",
        "status_check",
        "ping",
        "version_check",
        "discovery",
    ])
    def test_low_risk_action_returns_low_level(self, action_type):
        """SEC-059: Low-risk action types should return risk_level='low'"""
        result = evaluate_action_enrichment(action_type, "Test action", db=None)
        assert result["risk_level"] == "low", f"{action_type} should be low risk"

    def test_llm_call_mitre_technique(self):
        """SEC-059: llm_call should map to T1059.006 (Python execution)

        Rationale: Most LLM API calls are made via Python SDKs (OpenAI, Anthropic, etc.)
        The T1059.006 technique represents programmatic execution which aligns with
        how LLM calls are typically invoked in agent workflows.
        """
        result = evaluate_action_enrichment("llm_call", "Call LLM API", db=None)
        assert result["mitre_technique"] == "T1059.006"
        assert result["mitre_tactic"] == "TA0002"  # Execution

    def test_vector_search_nist_control(self):
        """SEC-059: vector_search should map to AU-2 (Audit Events)"""
        result = evaluate_action_enrichment("vector_search", "Search vector database", db=None)
        assert result["nist_control"] == "AU-2"

    def test_dns_lookup_mitre_technique(self):
        """SEC-059: dns_lookup should map to T1071.004 (DNS protocol)"""
        result = evaluate_action_enrichment("dns_lookup", "DNS lookup", db=None)
        assert result["mitre_technique"] == "T1071.004"

    def test_status_check_nist_control(self):
        """SEC-059: status_check should map to SI-4 (System Monitoring)"""
        result = evaluate_action_enrichment("status_check", "Health check", db=None)
        assert result["nist_control"] == "SI-4"

    def test_low_risk_recommendation(self):
        """SEC-059: Low-risk actions should have appropriate recommendation"""
        result = evaluate_action_enrichment("llm_call", "Call API", db=None)
        # Recommendation may be AI-generated or fallback - just ensure it exists
        assert result["recommendation"] is not None
        assert len(result["recommendation"]) > 10  # Non-empty recommendation


class TestEnterpriseComplianceMappings:
    """Test suite for ENTERPRISE_COMPLIANCE_MAPPINGS dictionary"""

    def test_all_high_risk_types_have_mappings(self):
        """SEC-059: All HIGH_RISK_ACTION_TYPES should have compliance mappings"""
        for action_type in HIGH_RISK_ACTION_TYPES:
            assert action_type in ENTERPRISE_COMPLIANCE_MAPPINGS, \
                f"Missing mapping for high-risk type: {action_type}"

    def test_all_medium_risk_types_have_mappings(self):
        """SEC-059: All MEDIUM_RISK_ACTION_TYPES should have compliance mappings"""
        for action_type in MEDIUM_RISK_ACTION_TYPES:
            assert action_type in ENTERPRISE_COMPLIANCE_MAPPINGS, \
                f"Missing mapping for medium-risk type: {action_type}"

    def test_all_low_risk_types_have_mappings(self):
        """SEC-059: All LOW_RISK_ACTION_TYPES should have compliance mappings"""
        for action_type in LOW_RISK_ACTION_TYPES:
            assert action_type in ENTERPRISE_COMPLIANCE_MAPPINGS, \
                f"Missing mapping for low-risk type: {action_type}"

    def test_mapping_has_required_fields(self):
        """SEC-059: Each mapping should have all required fields"""
        required_fields = [
            "nist_control",
            "nist_family",
            "nist_description",
            "mitre_tactic",
            "mitre_tactic_name",
            "mitre_technique",
            "mitre_technique_name"
        ]
        for action_type, mapping in ENTERPRISE_COMPLIANCE_MAPPINGS.items():
            for field in required_fields:
                assert field in mapping, \
                    f"Missing field '{field}' in mapping for: {action_type}"

    def test_nist_control_format(self):
        """SEC-059: NIST controls should follow XX-N format"""
        import re
        pattern = r'^[A-Z]{2}-\d+(\.\d+)?$'
        for action_type, mapping in ENTERPRISE_COMPLIANCE_MAPPINGS.items():
            assert re.match(pattern, mapping["nist_control"]), \
                f"Invalid NIST control format for {action_type}: {mapping['nist_control']}"

    def test_mitre_tactic_format(self):
        """SEC-059: MITRE tactics should follow TA00XX format"""
        import re
        pattern = r'^TA00\d{2}$'
        for action_type, mapping in ENTERPRISE_COMPLIANCE_MAPPINGS.items():
            assert re.match(pattern, mapping["mitre_tactic"]), \
                f"Invalid MITRE tactic format for {action_type}: {mapping['mitre_tactic']}"

    def test_mitre_technique_format(self):
        """SEC-059: MITRE techniques should follow T1XXX or T1XXX.XXX format"""
        import re
        pattern = r'^T\d{4}(\.\d{3})?$'
        for action_type, mapping in ENTERPRISE_COMPLIANCE_MAPPINGS.items():
            assert re.match(pattern, mapping["mitre_technique"]), \
                f"Invalid MITRE technique format for {action_type}: {mapping['mitre_technique']}"


class TestGetEnterpriseComplianceMapping:
    """Test suite for get_enterprise_compliance_mapping function"""

    def test_known_action_type_returns_mapping(self):
        """SEC-059: Known action types should return their specific mapping"""
        mapping = get_enterprise_compliance_mapping("database_write", "")
        assert mapping["nist_control"] == "AC-3"

    def test_unknown_action_type_returns_default(self):
        """SEC-059: Unknown action types should return default mapping"""
        mapping = get_enterprise_compliance_mapping("unknown_action_xyz", "")
        assert mapping["nist_control"] == "SI-3"  # Default from api_call

    def test_financial_context_override(self):
        """SEC-059: Financial context should override to AU-9"""
        mapping = get_enterprise_compliance_mapping("data_access", "Process payment transaction")
        assert mapping["nist_control"] == "AU-9"
        assert mapping["mitre_tactic"] == "TA0040"

    def test_credential_context_override(self):
        """SEC-059: Credential context should override to IA-5"""
        mapping = get_enterprise_compliance_mapping("data_access", "Access user passwords")
        assert mapping["nist_control"] == "IA-5"
        assert mapping["mitre_tactic"] == "TA0006"


class TestContextAwareRiskElevation:
    """Test suite for context-aware risk elevation"""

    def test_production_context_elevates_risk(self):
        """SEC-059: Production system mentions should elevate risk"""
        # Low-risk action with production context
        result = evaluate_action_enrichment(
            "cache_read",
            "Read from production cache server",
            db=None
        )
        # Should be elevated from low to medium
        assert result["risk_level"] in ["medium", "high"]

    def test_pii_context_elevates_risk(self):
        """SEC-059: PII mentions should elevate risk"""
        result = evaluate_action_enrichment(
            "data_access",
            "Access customer PII data including SSN",
            db=None
        )
        # Should be elevated due to PII context
        assert result["risk_level"] == "high"

    def test_sensitive_data_context(self):
        """SEC-059: Sensitive data mentions should affect risk"""
        result = evaluate_action_enrichment(
            "file_read",
            "Read confidential financial records",
            db=None
        )
        # Should be elevated due to sensitive context
        assert result["risk_level"] in ["medium", "high"]


class TestResultStructure:
    """Test suite for result structure consistency"""

    def test_result_has_required_keys(self):
        """SEC-059: Result should contain all required keys"""
        required_keys = [
            "risk_level",
            "mitre_tactic",
            "mitre_technique",
            "nist_control",
            "nist_description",
            "recommendation"
        ]
        result = evaluate_action_enrichment("data_access", "Test", db=None)
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_risk_level_valid_values(self):
        """SEC-059: risk_level should be low, medium, or high"""
        valid_levels = ["low", "medium", "high"]

        for action_type in list(HIGH_RISK_ACTION_TYPES)[:3]:
            result = evaluate_action_enrichment(action_type, "Test", db=None)
            assert result["risk_level"] in valid_levels

        for action_type in list(MEDIUM_RISK_ACTION_TYPES)[:3]:
            result = evaluate_action_enrichment(action_type, "Test", db=None)
            assert result["risk_level"] in valid_levels

        for action_type in list(LOW_RISK_ACTION_TYPES)[:3]:
            result = evaluate_action_enrichment(action_type, "Test", db=None)
            assert result["risk_level"] in valid_levels


class TestMITRETechniqueRationale:
    """
    Test suite documenting MITRE technique selection rationale

    SEC-059: Each test documents WHY a specific MITRE technique was chosen
    for the action type. This serves as living documentation for security
    analysts and auditors.
    """

    def test_llm_call_uses_python_execution(self):
        """
        T1059.006 (Python) rationale for llm_call:

        Most LLM interactions occur via Python SDKs:
        - OpenAI Python SDK (openai.ChatCompletion.create)
        - Anthropic Python SDK (anthropic.messages.create)
        - LangChain (Python-first framework)
        - Hugging Face Transformers (Python library)

        The execution context is programmatic, making T1059.006 the
        most accurate technique for tracking LLM-based agent actions.
        """
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS["llm_call"]
        assert mapping["mitre_technique"] == "T1059.006"
        assert mapping["mitre_technique_name"] == "Python"

    def test_time_sync_uses_timestomp(self):
        """
        T1070.006 (Timestomp) rationale for time_sync:

        Time synchronization operations can be used maliciously to:
        - Alter file timestamps to hide activity
        - Defeat time-based access controls
        - Evade time-window-based security monitoring

        While legitimate time sync is common, the potential for
        abuse aligns with T1070.006 (Defense Evasion via Timestomp).
        """
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS["time_sync"]
        assert mapping["mitre_technique"] == "T1070.006"
        assert mapping["mitre_tactic"] == "TA0005"  # Defense Evasion

    def test_firewall_modify_uses_disable_firewall(self):
        """
        T1562.004 (Disable/Modify System Firewall) rationale:

        Firewall modification is a classic defense evasion technique:
        - Opening ports for C2 communication
        - Disabling rules that block malicious traffic
        - Creating exceptions for malware persistence

        T1562.004 specifically addresses firewall manipulation.
        """
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS["firewall_modify"]
        assert mapping["mitre_technique"] == "T1562.004"
        assert mapping["mitre_technique_name"] == "Disable or Modify System Firewall"

    def test_encryption_key_access_uses_private_keys(self):
        """
        T1552.004 (Private Keys) rationale:

        Encryption key access typically targets:
        - SSH private keys for lateral movement
        - API keys for service impersonation
        - TLS/SSL certificates for MITM attacks
        - Encryption keys for data decryption

        T1552.004 is the sub-technique specifically for private key theft.
        """
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS["encryption_key_access"]
        assert mapping["mitre_technique"] == "T1552.004"
        assert mapping["mitre_technique_name"] == "Private Keys"

    def test_discovery_uses_network_service_discovery(self):
        """
        T1046 (Network Service Discovery) rationale:

        Service discovery operations are reconnaissance activities:
        - Port scanning to find open services
        - Service enumeration for vulnerability assessment
        - Network mapping for lateral movement planning

        T1046 covers network service discovery techniques.
        """
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS["discovery"]
        assert mapping["mitre_technique"] == "T1046"
        assert mapping["mitre_tactic"] == "TA0007"  # Discovery


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
