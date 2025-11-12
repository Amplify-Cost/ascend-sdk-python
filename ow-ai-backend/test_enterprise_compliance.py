#!/usr/bin/env python3
"""
Test script for ARCH-004 enterprise compliance mapping system.

This script tests that different action types and contexts get the correct
NIST SP 800-53 and MITRE ATT&CK mappings.
"""

import logging
from enrichment import evaluate_action_enrichment, get_enterprise_compliance_mapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def test_compliance_mappings():
    """Test the enterprise compliance mapping system."""

    print("=" * 80)
    print("ARCH-004 ENTERPRISE COMPLIANCE MAPPING TEST")
    print("=" * 80)
    print()

    # Test cases with expected results
    test_cases = [
        {
            "name": "Database Write",
            "action_type": "database_write",
            "description": "Write user data to users table",
            "expected_nist": "AC-3",
            "expected_mitre_tactic": "TA0006"
        },
        {
            "name": "API Call (Generic)",
            "action_type": "api_call",
            "description": "Call external weather API",
            "expected_nist": "SI-3",
            "expected_mitre_tactic": "TA0002"
        },
        {
            "name": "API Call (Payment Context Override)",
            "action_type": "api_call",
            "description": "Process payment via Stripe API for invoice #12345",
            "expected_nist": "AU-9",
            "expected_mitre_tactic": "TA0040"
        },
        {
            "name": "System Modification",
            "action_type": "system_modification",
            "description": "Update nginx configuration",
            "expected_nist": "CM-3",
            "expected_mitre_tactic": "TA0005"
        },
        {
            "name": "Credential Access (Context Override)",
            "action_type": "api_call",
            "description": "Retrieve API secret from secrets manager",
            "expected_nist": "IA-5",
            "expected_mitre_tactic": "TA0006"
        },
        {
            "name": "Financial Transaction",
            "action_type": "financial_transaction",
            "description": "Process refund for customer",
            "expected_nist": "AU-9",
            "expected_mitre_tactic": "TA0040"
        },
        {
            "name": "Privilege Escalation (Context Override)",
            "action_type": "user_provision",
            "description": "Grant administrator privileges to user",
            "expected_nist": "AC-6",
            "expected_mitre_tactic": "TA0004"
        },
        {
            "name": "Schema Change",
            "action_type": "database_write",
            "description": "ALTER TABLE users ADD COLUMN phone_number",
            "expected_nist": "CM-3",
            "expected_mitre_tactic": "TA0040"
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"  Action Type: {test_case['action_type']}")
        print(f"  Description: {test_case['description']}")
        print()

        # Get enrichment results (without database session for testing)
        result = evaluate_action_enrichment(
            action_type=test_case['action_type'],
            description=test_case['description'],
            db=None,
            action_id=None
        )

        # Get direct mapping to show what the enterprise mapping function returns
        direct_mapping = get_enterprise_compliance_mapping(
            action_type=test_case['action_type'],
            description=test_case['description']
        )

        print(f"  Results:")
        print(f"    NIST Control: {result['nist_control']} ({result['nist_description']})")
        print(f"    NIST Family: {direct_mapping.get('nist_family', 'N/A')}")
        print(f"    MITRE Tactic: {direct_mapping.get('mitre_tactic', 'N/A')} ({result.get('mitre_tactic', 'N/A')})")
        print(f"    MITRE Technique: {result.get('mitre_technique', 'N/A')}")
        print(f"    Risk Level: {result['risk_level']}")
        print()

        # Verify expected mappings
        nist_match = result['nist_control'] == test_case['expected_nist']
        mitre_match = direct_mapping.get('mitre_tactic') == test_case['expected_mitre_tactic']

        if nist_match and mitre_match:
            print(f"  Status: ✅ PASSED")
            passed += 1
        else:
            print(f"  Status: ❌ FAILED")
            if not nist_match:
                print(f"    Expected NIST: {test_case['expected_nist']}, Got: {result['nist_control']}")
            if not mitre_match:
                print(f"    Expected MITRE: {test_case['expected_mitre_tactic']}, Got: {direct_mapping.get('mitre_tactic')}")
            failed += 1

        print()
        print("-" * 80)
        print()

    # Summary
    print("=" * 80)
    print(f"TEST SUMMARY: {passed}/{len(test_cases)} passed, {failed}/{len(test_cases)} failed")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = test_compliance_mappings()
    exit(0 if success else 1)
