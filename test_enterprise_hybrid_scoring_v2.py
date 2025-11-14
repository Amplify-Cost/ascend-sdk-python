"""
ENTERPRISE HYBRID RISK SCORING - COMPREHENSIVE TEST SUITE V2.0
Engineer: Donald King (OW-kai Enterprise)
Date: 2025-11-14

Purpose:
Comprehensive test suite validating enterprise_risk_calculator_v2.py with:
- Original 8 validation tests (scoring accuracy)
- 5 error handling tests (invalid inputs)
- 3 fallback scoring tests (graceful degradation)
- 2 audit trail tests (immutable logging - integration readiness)

Total: 18 tests covering all enterprise enhancements
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from services.enterprise_risk_calculator_v2 import enterprise_risk_calculator

# ============================================================================
# TEST UTILITIES
# ============================================================================

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")

def print_test_header(test_num: int, total_tests: int, description: str):
    print(f"\n{Colors.BOLD}Test {test_num}/{total_tests}: {description}{Colors.RESET}")
    print("-" * 80)

def validate_score_range(score: int, min_expected: int, max_expected: int, test_name: str) -> bool:
    """Validate score is within expected range"""
    if min_expected <= score <= max_expected:
        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: {test_name}")
        print(f"   Score: {score}/100 (expected: {min_expected}-{max_expected}/100)")
        return True
    else:
        print(f"{Colors.RED}❌ FAIL{Colors.RESET}: {test_name}")
        print(f"   Score: {score}/100 (expected: {min_expected}-{max_expected}/100)")
        delta = score - max_expected if score > max_expected else min_expected - score
        print(f"   Delta: {delta} points {'too high' if score > max_expected else 'too low'}")
        return False

def validate_field_exists(result: Dict, field_name: str, test_name: str) -> bool:
    """Validate a field exists in result dictionary"""
    if field_name in result:
        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: {test_name} - Field '{field_name}' exists")
        return True
    else:
        print(f"{Colors.RED}❌ FAIL{Colors.RESET}: {test_name} - Field '{field_name}' missing")
        return False

def validate_fallback_mode(result: Dict, expected_fallback: bool, test_name: str) -> bool:
    """Validate fallback mode status"""
    actual = result.get('fallback_mode', False)
    if actual == expected_fallback:
        mode = "Fallback" if expected_fallback else "Normal"
        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: {test_name} - {mode} mode activated correctly")
        return True
    else:
        print(f"{Colors.RED}❌ FAIL{Colors.RESET}: {test_name} - Expected fallback={expected_fallback}, got {actual}")
        return False

# ============================================================================
# CATEGORY 1: ORIGINAL VALIDATION TESTS (8 tests)
# ============================================================================

def run_validation_tests() -> Dict[str, int]:
    """
    Original 8 validation tests from testing report
    These tests verify correct risk score calibration
    """
    print_header("CATEGORY 1: RISK SCORE VALIDATION TESTS (8 tests)")

    results = {"passed": 0, "failed": 0}
    test_num = 1
    total_tests = 18

    # TEST 1: Dev read, no PII → Expected: 20-30
    print_test_header(test_num, total_tests, "Development Database Read (No PII)")
    result1 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=3.0,
        environment="development",
        action_type="read",
        contains_pii=False,
        resource_name="test-data-dev",
        description="AI agent reading test data from dev database"
    )
    if validate_score_range(result1['risk_score'], 20, 30, "Dev read, no PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result1['breakdown']}")
        print(f"   Reasoning: {result1['reasoning']}")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 2: Staging write, no PII → Expected: 40-55
    print_test_header(test_num, total_tests, "Staging Database Write (No PII)")
    result2 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=5.5,
        environment="staging",
        action_type="write",
        contains_pii=False,
        resource_name="staging-database",
        description="AI agent writing configuration to staging database"
    )
    if validate_score_range(result2['risk_score'], 40, 55, "Staging write, no PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result2['breakdown']}")
        print(f"   Reasoning: {result2['reasoning']}")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 3: Prod read, no PII → Expected: 45-60
    print_test_header(test_num, total_tests, "Production Database Read (No PII)")
    result3 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=3.5,
        environment="production",
        action_type="read",
        contains_pii=False,
        resource_name="analytics-data-prod",
        description="AI agent reading analytics from production database"
    )
    if validate_score_range(result3['risk_score'], 45, 60, "Prod read, no PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result3['breakdown']}")
        print(f"   Reasoning: {result3['reasoning']}")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 4: Prod write, no PII → Expected: 70-80
    print_test_header(test_num, total_tests, "Production Database Write (No PII)")
    result4 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=6.8,
        environment="production",
        action_type="write",
        contains_pii=False,
        resource_name="config-database-prod",
        description="AI agent updating configuration in production database"
    )
    if validate_score_range(result4['risk_score'], 70, 80, "Prod write, no PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result4['breakdown']}")
        print(f"   Reasoning: {result4['reasoning']}")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 5: Prod delete, no PII → Expected: 85-92
    print_test_header(test_num, total_tests, "Production Database Delete (No PII)")
    result5 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=8.8,
        environment="production",
        action_type="delete",
        contains_pii=False,
        resource_name="customer-database-prod",
        description="AI agent calling RDS.delete_db_instance to remove old customer database"
    )
    if validate_score_range(result5['risk_score'], 85, 92, "Prod delete, no PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result5['breakdown']}")
        print(f"   Reasoning: {result5['reasoning']}")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 6: Prod write with PII (Most Dangerous) → Expected: 95-99
    print_test_header(test_num, total_tests, "Production S3 Upload with PII (Most Dangerous)")
    result6 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=8.0,
        environment="production",
        action_type="write",
        contains_pii=True,
        resource_name="customer-data-prod",
        description="AI agent calling s3.put_object with credit-card-numbers.csv"
    )
    if validate_score_range(result6['risk_score'], 95, 99, "Prod write with PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result6['breakdown']}")
        print(f"   Reasoning: {result6['reasoning']}")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 7: Prod read with PII → Expected: 70-85
    print_test_header(test_num, total_tests, "Production Database Read with PII")
    result7 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=4.0,
        environment="production",
        action_type="read",
        contains_pii=True,
        resource_name="customer-pii-database-prod",
        description="AI agent reading ssn and credit_card data from production"
    )
    if validate_score_range(result7['risk_score'], 70, 85, "Prod read with PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result7['breakdown']}")
        print(f"   Reasoning: {result7['reasoning']}")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 8: Dev write with PII → Expected: 45-60
    print_test_header(test_num, total_tests, "Development Database Write with PII")
    result8 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=6.8,
        environment="development",
        action_type="write",
        contains_pii=True,
        resource_name="test-customer-data-dev",
        description="AI agent writing password and email test data to development database"
    )
    if validate_score_range(result8['risk_score'], 45, 60, "Dev write with PII"):
        results["passed"] += 1
        print(f"   Breakdown: {result8['breakdown']}")
        print(f"   Reasoning: {result8['reasoning']}")
    else:
        results["failed"] += 1

    return results

# ============================================================================
# CATEGORY 2: ERROR HANDLING TESTS (5 tests)
# ============================================================================

def run_error_handling_tests() -> Dict[str, int]:
    """
    5 new error handling tests
    Validate graceful error handling for invalid inputs
    """
    print_header("CATEGORY 2: ERROR HANDLING TESTS (5 tests)")

    results = {"passed": 0, "failed": 0}
    test_num = 9
    total_tests = 18

    # TEST 9: Invalid CVSS score (negative)
    print_test_header(test_num, total_tests, "Invalid CVSS Score - Negative Value")
    result9 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=-5.0,  # Invalid: negative
        environment="production",
        action_type="write",
        contains_pii=False,
        resource_name="test-resource",
        description="Test with invalid CVSS score"
    )
    if validate_fallback_mode(result9, True, "Negative CVSS handling"):
        results["passed"] += 1
        print(f"   Fallback score: {result9['risk_score']}/100")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 10: Invalid CVSS score (> 10)
    print_test_header(test_num, total_tests, "Invalid CVSS Score - Exceeds Maximum")
    result10 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=15.0,  # Invalid: > 10
        environment="production",
        action_type="delete",
        contains_pii=True,
        resource_name="test-resource",
        description="Test with invalid CVSS score"
    )
    if validate_fallback_mode(result10, True, "Excessive CVSS handling"):
        results["passed"] += 1
        print(f"   Fallback score: {result10['risk_score']}/100")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 11: Empty environment string
    print_test_header(test_num, total_tests, "Invalid Environment - Empty String")
    result11 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=5.0,
        environment="",  # Invalid: empty string
        action_type="write",
        contains_pii=False,
        resource_name="test-resource",
        description="Test with empty environment"
    )
    if validate_fallback_mode(result11, True, "Empty environment handling"):
        results["passed"] += 1
        print(f"   Fallback score: {result11['risk_score']}/100")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 12: None resource name
    print_test_header(test_num, total_tests, "Invalid Resource Name - None Value")
    result12 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=5.0,
        environment="production",
        action_type="write",
        contains_pii=False,
        resource_name=None,  # Invalid: None
        description="Test with None resource name"
    )
    if validate_fallback_mode(result12, True, "None resource name handling"):
        results["passed"] += 1
        print(f"   Fallback score: {result12['risk_score']}/100")
    else:
        results["failed"] += 1
    test_num += 1

    # TEST 13: Invalid action type (wrong data type)
    print_test_header(test_num, total_tests, "Invalid Action Type - Wrong Data Type")
    result13 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=5.0,
        environment="production",
        action_type=12345,  # Invalid: integer instead of string
        contains_pii=False,
        resource_name="test-resource",
        description="Test with invalid action type"
    )
    if validate_fallback_mode(result13, True, "Invalid action type handling"):
        results["passed"] += 1
        print(f"   Fallback score: {result13['risk_score']}/100")
    else:
        results["failed"] += 1

    return results

# ============================================================================
# CATEGORY 3: FALLBACK SCORING TESTS (3 tests)
# ============================================================================

def run_fallback_scoring_tests() -> Dict[str, int]:
    """
    3 new fallback scoring tests
    Validate safe fallback scores for edge cases
    """
    print_header("CATEGORY 3: FALLBACK SCORING TESTS (3 tests)")

    results = {"passed": 0, "failed": 0}
    test_num = 14
    total_tests = 18

    # TEST 14: Safe fallback with environment context
    print_test_header(test_num, total_tests, "Safe Fallback - Production Context")
    result14 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=-1.0,  # Triggers validation error
        environment="production",
        action_type="delete",
        contains_pii=True,
        resource_name="critical-resource",
        description="Test fallback with production context"
    )
    # Fallback should be conservative (high score) for production
    if result14['fallback_mode'] and result14['risk_score'] >= 75:
        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: Production fallback is conservative")
        print(f"   Fallback score: {result14['risk_score']}/100 (conservative)")
        results["passed"] += 1
    else:
        print(f"{Colors.RED}❌ FAIL{Colors.RESET}: Production fallback should be >= 75")
        results["failed"] += 1
    test_num += 1

    # TEST 15: Safe fallback with development context
    print_test_header(test_num, total_tests, "Safe Fallback - Development Context")
    result15 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=None,
        environment="development",
        action_type="read",
        contains_pii=False,
        resource_name="",  # Triggers validation error
        description="Test fallback with development context"
    )
    # Fallback should be more permissive for development
    if result15['fallback_mode'] and 40 <= result15['risk_score'] <= 65:
        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: Development fallback is calibrated")
        print(f"   Fallback score: {result15['risk_score']}/100 (permissive)")
        results["passed"] += 1
    else:
        print(f"{Colors.RED}❌ FAIL{Colors.RESET}: Development fallback should be 40-65")
        results["failed"] += 1
    test_num += 1

    # TEST 16: High-risk fallback for production destructive actions
    print_test_header(test_num, total_tests, "High-Risk Fallback - Production Destructive Action")
    result16 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score="INVALID_TYPE",  # Triggers validation error (not critical exception)
        environment="production",
        action_type="delete",
        contains_pii=True,
        resource_name="database-prod",
        description="Test high-risk fallback for prod delete"
    )
    # Production + delete should get high fallback score (75+10=85)
    if result16['fallback_mode'] and result16['risk_score'] >= 80:
        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: Production destructive fallback is appropriately high")
        print(f"   Fallback score: {result16['risk_score']}/100 (production + delete)")
        results["passed"] += 1
    else:
        print(f"{Colors.RED}❌ FAIL{Colors.RESET}: Production destructive fallback should be >= 80")
        results["failed"] += 1

    return results

# ============================================================================
# CATEGORY 4: ENTERPRISE FEATURES TESTS (2 tests)
# ============================================================================

def run_enterprise_features_tests() -> Dict[str, int]:
    """
    2 new enterprise features tests
    Validate algorithm versioning and metadata
    """
    print_header("CATEGORY 4: ENTERPRISE FEATURES TESTS (2 tests)")

    results = {"passed": 0, "failed": 0}
    test_num = 17
    total_tests = 18

    # TEST 17: Algorithm versioning
    print_test_header(test_num, total_tests, "Algorithm Versioning - Metadata Presence")
    result17 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=5.0,
        environment="production",
        action_type="write",
        contains_pii=False,
        resource_name="test-resource",
        description="Test algorithm versioning"
    )
    passed_all = True
    if validate_field_exists(result17, 'algorithm_version', "Algorithm version"):
        results["passed"] += 0.5
    else:
        passed_all = False

    if validate_field_exists(result17, 'calculation_timestamp', "Calculation timestamp"):
        results["passed"] += 0.5
    else:
        passed_all = False

    if passed_all:
        print(f"   Algorithm version: {result17.get('algorithm_version')}")
        print(f"   Timestamp: {result17.get('calculation_timestamp')}")
    else:
        results["failed"] += 1
        results["passed"] -= 0.5 if not passed_all else 0
    test_num += 1

    # TEST 18: get_algorithm_metadata() method
    print_test_header(test_num, total_tests, "Algorithm Metadata - Version Details")
    metadata = enterprise_risk_calculator.get_algorithm_metadata()
    passed_all = True

    required_fields = ['version', 'name', 'date', 'components']
    for field in required_fields:
        if field not in metadata:
            print(f"{Colors.RED}❌ FAIL{Colors.RESET}: Metadata missing field '{field}'")
            passed_all = False

    if passed_all:
        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: All metadata fields present")
        print(f"   Version: {metadata.get('version')}")
        print(f"   Name: {metadata.get('name')}")
        print(f"   Date: {metadata.get('date')}")
        print(f"   Components: {list(metadata.get('components', {}).keys())}")
        results["passed"] += 1
    else:
        results["failed"] += 1

    return results

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all 18 tests and display summary"""
    print_header("ENTERPRISE HYBRID RISK SCORING - COMPREHENSIVE TEST SUITE V2.0")
    print(f"Engineer: Donald King (OW-kai Enterprise)")
    print(f"Purpose: Validate all enterprise enhancements and risk score calibration\n")

    # Run all test categories
    validation_results = run_validation_tests()
    error_handling_results = run_error_handling_tests()
    fallback_results = run_fallback_scoring_tests()
    enterprise_results = run_enterprise_features_tests()

    # Calculate totals
    total_passed = (
        validation_results["passed"] +
        error_handling_results["passed"] +
        fallback_results["passed"] +
        enterprise_results["passed"]
    )
    total_failed = (
        validation_results["failed"] +
        error_handling_results["failed"] +
        fallback_results["failed"] +
        enterprise_results["failed"]
    )
    total_tests = total_passed + total_failed
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    # Display summary
    print_header("TEST SUITE RESULTS")
    print(f"Total Tests: {int(total_tests)}")
    print(f"{Colors.GREEN}✅ Passed: {int(total_passed)}{Colors.RESET}")
    print(f"{Colors.RED}❌ Failed: {int(total_failed)}{Colors.RESET}")
    print(f"Pass Rate: {pass_rate:.1f}%\n")

    # Category breakdown
    print(f"{Colors.BOLD}Category Breakdown:{Colors.RESET}")
    print(f"  1. Validation Tests (8):        {validation_results['passed']}/8 passed")
    print(f"  2. Error Handling Tests (5):    {error_handling_results['passed']}/5 passed")
    print(f"  3. Fallback Scoring Tests (3):  {fallback_results['passed']}/3 passed")
    print(f"  4. Enterprise Features Tests (2): {int(enterprise_results['passed'])}/2 passed\n")

    if total_failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED - ENTERPRISE SOLUTION READY FOR INTEGRATION{Colors.RESET}\n")
        return True
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  SOME TESTS FAILED - REVIEW RESULTS ABOVE{Colors.RESET}\n")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
