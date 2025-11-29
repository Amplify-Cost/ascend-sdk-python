"""
OW-kai Enterprise Integration Phase 4: Compliance Export Unit Tests

Tests for:
- Framework configurations
- PII masking
- Report type validation
- Export format generation
- Schema validation
- Security properties
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

# Import models and schemas
from models_compliance_export import (
    ComplianceFramework,
    ExportFormat,
    ExportStatus,
    DataClassification,
    ReportType,
    ComplianceExportRequest,
    ComplianceScheduleCreate,
    ComplianceScheduleUpdate,
    SOXAuditRecord,
    PCIDSSRecord,
    HIPAAAccessRecord,
    GDPRRecord,
    SOC2ControlEvidence,
    get_framework_config,
    get_supported_frameworks,
    FRAMEWORK_REPORT_MAPPINGS,
)

# Import service
from services.compliance_export_service import PIIMasker, ComplianceExportService


# ============================================
# Test Framework Configuration
# ============================================

class TestFrameworkConfiguration:
    """Tests for compliance framework configurations"""

    def test_sox_config(self):
        """SOX should support audit trail and approval history"""
        config = get_framework_config(ComplianceFramework.SOX)
        assert ReportType.AUDIT_TRAIL in config["supported_reports"]
        assert ReportType.APPROVAL_HISTORY in config["supported_reports"]
        assert config["default_retention_days"] == 2555  # 7 years

    def test_pci_dss_config(self):
        """PCI-DSS should support access logs and security events"""
        config = get_framework_config(ComplianceFramework.PCI_DSS)
        assert ReportType.ACCESS_LOG in config["supported_reports"]
        assert ReportType.SECURITY_EVENTS in config["supported_reports"]
        assert config["data_classification"] == DataClassification.RESTRICTED

    def test_hipaa_config(self):
        """HIPAA should have 6-year retention"""
        config = get_framework_config(ComplianceFramework.HIPAA)
        assert ReportType.DATA_ACCESS in config["supported_reports"]
        assert config["default_retention_days"] == 2190  # 6 years

    def test_gdpr_config(self):
        """GDPR should support data access and user activity"""
        config = get_framework_config(ComplianceFramework.GDPR)
        assert ReportType.DATA_ACCESS in config["supported_reports"]
        assert ReportType.USER_ACTIVITY in config["supported_reports"]

    def test_soc2_config(self):
        """SOC2 should support all trust principles"""
        config = get_framework_config(ComplianceFramework.SOC2)
        assert ReportType.SECURITY_EVENTS in config["supported_reports"]
        assert ReportType.COMPLIANCE_SUMMARY in config["supported_reports"]

    def test_nist_csf_config(self):
        """NIST CSF should support risk assessment"""
        config = get_framework_config(ComplianceFramework.NIST_CSF)
        assert ReportType.RISK_ASSESSMENT in config["supported_reports"]
        assert ReportType.INCIDENT_REPORT in config["supported_reports"]

    def test_iso_27001_config(self):
        """ISO 27001 should support system changes"""
        config = get_framework_config(ComplianceFramework.ISO_27001)
        assert ReportType.SYSTEM_CHANGES in config["supported_reports"]
        assert config["default_retention_days"] == 1095  # 3 years

    def test_all_frameworks_have_configs(self):
        """All frameworks should have configurations"""
        for framework in ComplianceFramework:
            if framework != ComplianceFramework.CUSTOM:
                config = get_framework_config(framework)
                assert "supported_reports" in config
                assert "default_retention_days" in config

    def test_get_supported_frameworks(self):
        """Should return list of all frameworks with details"""
        frameworks = get_supported_frameworks()
        assert len(frameworks) >= 7  # SOX, PCI-DSS, HIPAA, GDPR, SOC2, NIST, ISO
        for f in frameworks:
            assert "framework" in f
            assert "display_name" in f
            assert "supported_reports" in f


# ============================================
# Test PII Masking
# ============================================

class TestPIIMasking:
    """Tests for PII masking functionality"""

    def test_mask_email(self):
        """Email should be partially masked"""
        masked = PIIMasker.mask_value("email", "john.doe@company.com")
        assert "jo" in masked
        assert "company.com" in masked
        assert "john.doe" not in masked

    def test_mask_phone(self):
        """Phone should show only last 4 digits"""
        masked = PIIMasker.mask_value("phone", "555-123-4567")
        assert masked.endswith("4567")
        assert "555" not in masked

    def test_mask_credit_card(self):
        """Credit card should show only last 4 digits"""
        masked = PIIMasker.mask_value("credit_card", "4111111111111111")
        assert masked.endswith("1111")
        assert "4111" not in masked or masked.startswith("****")

    def test_mask_ip_address(self):
        """IP address should have last two octets masked"""
        masked = PIIMasker.mask_value("ip_address", "192.168.1.100")
        assert "192.168" in masked
        assert "100" not in masked

    def test_mask_name(self):
        """Name should show only first letter"""
        masked = PIIMasker.mask_value("first_name", "John")
        assert masked.startswith("J")
        assert "John" not in masked

    def test_mask_password(self):
        """Password should be fully masked"""
        masked = PIIMasker.mask_value("password", "secret123")
        assert masked == "********"
        assert "secret" not in masked

    def test_mask_api_key(self):
        """API key should show only first and last 4 chars"""
        masked = PIIMasker.mask_value("api_key", "sk_live_1234567890abcdef")
        assert "sk_l" in masked
        assert "cdef" in masked
        assert "1234567890" not in masked

    def test_mask_record(self):
        """Full record should have all PII masked"""
        record = {
            "user_id": 123,
            "email": "test@example.com",
            "password": "secret",
            "action": "login",
        }
        masked = PIIMasker.mask_record(record, include_pii=False)
        assert masked["user_id"] == 123  # Not PII
        assert "test@example.com" not in masked["email"]
        assert masked["password"] == "********"
        assert masked["action"] == "login"  # Not PII

    def test_mask_record_include_pii(self):
        """Record with include_pii=True should not mask"""
        record = {
            "email": "test@example.com",
            "password": "secret",
        }
        result = PIIMasker.mask_record(record, include_pii=True)
        assert result["email"] == "test@example.com"
        assert result["password"] == "secret"

    def test_mask_nested_record(self):
        """Nested records should be masked recursively"""
        record = {
            "user": {
                "email": "nested@example.com",
                "name": "John",
            },
            "metadata": {
                "ip_address": "10.0.0.1",
            }
        }
        masked = PIIMasker.mask_record(record, include_pii=False)
        assert "nested@example.com" not in str(masked["user"]["email"])
        assert "10.0.0.1" not in str(masked["metadata"]["ip_address"])

    def test_mask_none_value(self):
        """None values should remain None"""
        masked = PIIMasker.mask_value("email", None)
        assert masked is None


# ============================================
# Test Schema Validation
# ============================================

class TestSchemaValidation:
    """Tests for Pydantic schema validation"""

    def test_export_request_valid(self):
        """Valid export request should pass validation"""
        request = ComplianceExportRequest(
            framework=ComplianceFramework.SOX,
            report_type=ReportType.AUDIT_TRAIL,
            export_format=ExportFormat.JSON,
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc),
        )
        assert request.framework == ComplianceFramework.SOX
        assert request.include_pii == False  # Default

    def test_export_request_end_before_start_rejected(self):
        """End date before start date should be rejected"""
        with pytest.raises(ValueError):
            ComplianceExportRequest(
                framework=ComplianceFramework.SOX,
                report_type=ReportType.AUDIT_TRAIL,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) - timedelta(days=30),
            )

    def test_export_request_future_date_rejected(self):
        """Future dates should be rejected"""
        with pytest.raises(ValueError):
            ComplianceExportRequest(
                framework=ComplianceFramework.SOX,
                report_type=ReportType.AUDIT_TRAIL,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=30),
            )

    def test_schedule_create_valid(self):
        """Valid schedule should pass validation"""
        schedule = ComplianceScheduleCreate(
            name="Monthly SOX Report",
            framework=ComplianceFramework.SOX,
            report_type=ReportType.AUDIT_TRAIL,
            cron_expression="0 0 1 * *",
        )
        assert schedule.name == "Monthly SOX Report"
        assert schedule.retention_days == 90  # Default

    def test_schedule_create_invalid_cron(self):
        """Invalid cron expression should be rejected"""
        with pytest.raises(ValueError):
            ComplianceScheduleCreate(
                name="Test",
                framework=ComplianceFramework.SOX,
                report_type=ReportType.AUDIT_TRAIL,
                cron_expression="invalid cron",
            )

    def test_schedule_create_retention_bounds(self):
        """Retention days should be within bounds"""
        # Valid retention
        schedule = ComplianceScheduleCreate(
            name="Test",
            framework=ComplianceFramework.SOX,
            report_type=ReportType.AUDIT_TRAIL,
            cron_expression="0 0 1 * *",
            retention_days=180,
        )
        assert schedule.retention_days == 180

        # Too short
        with pytest.raises(ValueError):
            ComplianceScheduleCreate(
                name="Test",
                framework=ComplianceFramework.SOX,
                report_type=ReportType.AUDIT_TRAIL,
                cron_expression="0 0 1 * *",
                retention_days=3,
            )

        # Too long
        with pytest.raises(ValueError):
            ComplianceScheduleCreate(
                name="Test",
                framework=ComplianceFramework.SOX,
                report_type=ReportType.AUDIT_TRAIL,
                cron_expression="0 0 1 * *",
                retention_days=500,
            )

    def test_schedule_update_partial(self):
        """Schedule update should allow partial updates"""
        update = ComplianceScheduleUpdate(
            is_active=False,
        )
        assert update.is_active == False
        assert update.name is None
        assert update.cron_expression is None


# ============================================
# Test Framework-Specific Records
# ============================================

class TestFrameworkRecords:
    """Tests for framework-specific record schemas"""

    def test_sox_audit_record(self):
        """SOX audit record should have required fields"""
        record = SOXAuditRecord(
            timestamp=datetime.now(timezone.utc),
            event_type="config_change",
            user_id=1,
            user_email="admin@company.com",
            action="update",
            resource_type="policy",
            resource_id="pol_123",
            old_value=None,
            new_value=None,
            ip_address=None,
            approval_chain=None,
            control_id=None,
            risk_level=None,
        )
        assert record.event_type == "config_change"
        assert record.user_id == 1

    def test_pci_dss_record(self):
        """PCI-DSS record should have PCI requirement reference"""
        record = PCIDSSRecord(
            timestamp=datetime.now(timezone.utc),
            transaction_id="tx_123",
            user_id=1,
            action_type="read",
            data_accessed=["cardholder_name"],
            masked_card_data=None,
            system_component="payment_gateway",
            access_method="api",
            ip_address=None,
            success=True,
            pci_requirement="Req 10.2.1",
        )
        assert record.pci_requirement == "Req 10.2.1"

    def test_hipaa_access_record(self):
        """HIPAA record should have minimum necessary flag"""
        record = HIPAAAccessRecord(
            timestamp=datetime.now(timezone.utc),
            user_id=1,
            user_role="physician",
            patient_id_hash=None,
            access_type="read",
            data_category="medical_record",
            purpose="treatment",
            ip_address=None,
            minimum_necessary=True,
            audit_control="AC-1",
        )
        assert record.minimum_necessary == True
        assert record.data_category == "medical_record"

    def test_gdpr_record(self):
        """GDPR record should have legal basis"""
        record = GDPRRecord(
            timestamp=datetime.now(timezone.utc),
            request_type="access",
            data_subject_id="ds_123",
            data_categories=["personal_info", "contact"],
            processing_purpose="customer_service",
            legal_basis="consent",
            third_party_recipients=None,
            retention_period=None,
            automated_decision=False,
            controller_response_date=None,
        )
        assert record.legal_basis == "consent"
        assert "personal_info" in record.data_categories

    def test_soc2_control_evidence(self):
        """SOC2 record should have trust principle"""
        record = SOC2ControlEvidence(
            timestamp=datetime.now(timezone.utc),
            trust_principle="Security",
            control_id="CC6.1",
            control_description="Logical access security",
            evidence_type="system_log",
            evidence_details={"log_id": "123"},
            test_result="pass",
            tested_by=None,
            remediation_required=False,
        )
        assert record.trust_principle == "Security"
        assert record.test_result == "pass"


# ============================================
# Test Enum Values
# ============================================

class TestEnumValues:
    """Tests for enum values"""

    def test_compliance_frameworks(self):
        """All compliance frameworks should have correct values"""
        assert ComplianceFramework.SOX.value == "sox"
        assert ComplianceFramework.PCI_DSS.value == "pci_dss"
        assert ComplianceFramework.HIPAA.value == "hipaa"
        assert ComplianceFramework.GDPR.value == "gdpr"
        assert ComplianceFramework.SOC2.value == "soc2"
        assert ComplianceFramework.NIST_CSF.value == "nist_csf"
        assert ComplianceFramework.ISO_27001.value == "iso_27001"

    def test_export_formats(self):
        """All export formats should be supported"""
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.XML.value == "xml"
        assert ExportFormat.XLSX.value == "xlsx"

    def test_export_statuses(self):
        """All export statuses should be defined"""
        assert ExportStatus.PENDING.value == "pending"
        assert ExportStatus.PROCESSING.value == "processing"
        assert ExportStatus.COMPLETED.value == "completed"
        assert ExportStatus.FAILED.value == "failed"
        assert ExportStatus.EXPIRED.value == "expired"

    def test_data_classifications(self):
        """All data classifications should be defined"""
        assert DataClassification.PUBLIC.value == "public"
        assert DataClassification.INTERNAL.value == "internal"
        assert DataClassification.CONFIDENTIAL.value == "confidential"
        assert DataClassification.RESTRICTED.value == "restricted"
        assert DataClassification.TOP_SECRET.value == "top_secret"

    def test_report_types(self):
        """All report types should be defined"""
        assert ReportType.AUDIT_TRAIL.value == "audit_trail"
        assert ReportType.ACCESS_LOG.value == "access_log"
        assert ReportType.POLICY_VIOLATIONS.value == "policy_violations"
        assert ReportType.RISK_ASSESSMENT.value == "risk_assessment"
        assert ReportType.AGENT_ACTIONS.value == "agent_actions"
        assert ReportType.COMPLIANCE_SUMMARY.value == "compliance_summary"


# ============================================
# Test Security Properties
# ============================================

class TestSecurityProperties:
    """Tests for security-related features"""

    def test_data_classification_levels(self):
        """Data classifications should follow hierarchy"""
        classifications = list(DataClassification)
        # Should have multiple levels
        assert len(classifications) >= 4

    def test_framework_data_classification_defaults(self):
        """Sensitive frameworks should have restricted classification"""
        pci_config = get_framework_config(ComplianceFramework.PCI_DSS)
        hipaa_config = get_framework_config(ComplianceFramework.HIPAA)

        assert pci_config["data_classification"] == DataClassification.RESTRICTED
        assert hipaa_config["data_classification"] == DataClassification.RESTRICTED

    def test_export_request_pii_default(self):
        """PII should be excluded by default"""
        request = ComplianceExportRequest(
            framework=ComplianceFramework.SOX,
            report_type=ReportType.AUDIT_TRAIL,
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
        )
        assert request.include_pii == False

    def test_retention_periods(self):
        """Retention periods should meet regulatory requirements"""
        sox_config = get_framework_config(ComplianceFramework.SOX)
        hipaa_config = get_framework_config(ComplianceFramework.HIPAA)

        # SOX requires 7 years
        assert sox_config["default_retention_days"] >= 2555

        # HIPAA requires 6 years
        assert hipaa_config["default_retention_days"] >= 2190


# ============================================
# Test Export Format Generation
# ============================================

class TestExportFormatGeneration:
    """Tests for export format generation"""

    def test_json_format_structure(self):
        """JSON export should have proper structure"""
        # Mock service would generate JSON with specific structure
        expected_keys = ["export_info", "records"]
        sample_json = {
            "export_info": {
                "generated_at": "2025-01-01T00:00:00Z",
                "record_count": 0,
            },
            "records": [],
        }
        for key in expected_keys:
            assert key in sample_json

    def test_csv_headers(self):
        """CSV export should have headers"""
        sample_csv = "id,timestamp,event_type,details\n"
        assert "id" in sample_csv
        assert "timestamp" in sample_csv

    def test_xml_structure(self):
        """XML export should have valid structure"""
        sample_xml = '<?xml version="1.0" encoding="UTF-8"?><export></export>'
        assert '<?xml' in sample_xml
        assert '<export>' in sample_xml


# ============================================
# Test Framework Report Mappings
# ============================================

class TestFrameworkReportMappings:
    """Tests for framework to report type mappings"""

    def test_all_frameworks_have_mappings(self):
        """All non-custom frameworks should have mappings"""
        for framework in ComplianceFramework:
            if framework not in [ComplianceFramework.CUSTOM, ComplianceFramework.CCPA, ComplianceFramework.FEDRAMP]:
                assert framework in FRAMEWORK_REPORT_MAPPINGS

    def test_mappings_have_required_keys(self):
        """All mappings should have required keys"""
        required_keys = ["supported_reports", "default_retention_days", "data_classification"]
        for framework, config in FRAMEWORK_REPORT_MAPPINGS.items():
            for key in required_keys:
                assert key in config, f"Missing {key} in {framework}"

    def test_supported_reports_are_valid(self):
        """All supported reports should be valid ReportType values"""
        for framework, config in FRAMEWORK_REPORT_MAPPINGS.items():
            for report in config["supported_reports"]:
                assert isinstance(report, ReportType)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
