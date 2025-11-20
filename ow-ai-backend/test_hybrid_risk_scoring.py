"""
Enterprise Hybrid Risk Scoring Validation Test Suite
Engineer: Donald King (OW-kai Enterprise)
Date: 2025-11-14

Purpose:
Validate that the hybrid risk scoring system produces correct scores
based on the 8 test scenarios from the OW-AI Testing Report.

Test Scenarios (from report):
1. Dev read, no PII → Expected: 20-30/100 (was 99/100 ❌)
2. Staging write, no PII → Expected: 40-55/100 (was 99/100 ❌)
3. Prod read, no PII → Expected: 45-60/100 (was 59/100 ⚠️)
4. Prod write, no PII → Expected: 70-80/100 (was 99/100 ❌)
5. Prod delete, no PII → Expected: 85-92/100 (was 64/100 ❌)
6. Prod write with PII → Expected: 95-99/100 (was 85/100 ⚠️)
7. Prod read with PII → Expected: 70-85/100
8. Dev write with PII → Expected: 45-60/100
"""
import sys
from services.enterprise_risk_calculator import enterprise_risk_calculator

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def validate_score_range(score: int, expected_min: int, expected_max: int, test_name: str) -> bool:
    """Validate that score falls within expected range"""
    if expected_min <= score <= expected_max:
        print(f"{GREEN}✅ PASS{RESET}: {test_name}")
        print(f"   Score: {score}/100 (expected: {expected_min}-{expected_max}/100)")
        return True
    else:
        print(f"{RED}❌ FAIL{RESET}: {test_name}")
        print(f"   Score: {score}/100 (expected: {expected_min}-{expected_max}/100)")
        delta = score - expected_max if score > expected_max else expected_min - score
        print(f"   Delta: {abs(delta)} points {'too high' if score > expected_max else 'too low'}")
        return False


def print_section_header(title: str):
    """Print formatted section header"""
    print(f"\n{BLUE}{BOLD}{'=' * 80}{RESET}")
    print(f"{BLUE}{BOLD}{title}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 80}{RESET}\n")


def print_test_header(test_num: int, description: str):
    """Print formatted test header"""
    print(f"\n{BOLD}Test {test_num}: {description}{RESET}")
    print("-" * 80)


def run_validation_tests():
    """Run all validation test scenarios"""
    print_section_header("ENTERPRISE HYBRID RISK SCORING - VALIDATION TEST SUITE")
    print(f"Engineer: Donald King (OW-kai Enterprise)")
    print(f"Purpose: Validate correct risk score calibration\n")

    passed = 0
    failed = 0
    total = 8

    # ========================================================================
    # TEST 1: Development Read, No PII (Safest action)
    # ========================================================================
    print_test_header(1, "Development Database Read (No PII)")
    result1 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=3.0,  # Low CVSS for read operation
        environment="development",
        action_type="read",
        contains_pii=False,
        resource_name="test-data-dev",
        description="AI agent reading test data from dev database"
    )
    if validate_score_range(result1['risk_score'], 20, 30, "Dev read, no PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result1['breakdown']}")
    print(f"   Reasoning: {result1['reasoning']}")

    # ========================================================================
    # TEST 2: Staging Write, No PII
    # ========================================================================
    print_test_header(2, "Staging Database Write (No PII)")
    result2 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=7.0,  # Medium-high CVSS for write operation
        environment="staging",
        action_type="write",
        contains_pii=False,
        resource_name="app-data-staging",
        description="AI agent writing application data to staging database"
    )
    if validate_score_range(result2['risk_score'], 40, 55, "Staging write, no PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result2['breakdown']}")
    print(f"   Reasoning: {result2['reasoning']}")

    # ========================================================================
    # TEST 3: Production Read, No PII
    # ========================================================================
    print_test_header(3, "Production Database Read (No PII)")
    result3 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=3.0,  # Low CVSS for read operation
        environment="production",
        action_type="read",
        contains_pii=False,
        resource_name="inventory-prod",
        description="AI agent reading inventory data from production database"
    )
    if validate_score_range(result3['risk_score'], 45, 60, "Prod read, no PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result3['breakdown']}")
    print(f"   Reasoning: {result3['reasoning']}")

    # ========================================================================
    # TEST 4: Production Write, No PII
    # ========================================================================
    print_test_header(4, "Production Database Write (No PII)")
    result4 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=7.0,  # Medium-high CVSS for write operation
        environment="production",
        action_type="write",
        contains_pii=False,
        resource_name="logs-prod",
        description="AI agent writing log data to production database"
    )
    if validate_score_range(result4['risk_score'], 70, 80, "Prod write, no PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result4['breakdown']}")
    print(f"   Reasoning: {result4['reasoning']}")

    # ========================================================================
    # TEST 5: Production Delete, No PII (Dangerous)
    # ========================================================================
    print_test_header(5, "Production Database Delete (No PII)")
    result5 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=9.0,  # High CVSS for delete operation
        environment="production",
        action_type="delete",
        contains_pii=False,
        resource_name="customer-database-prod",
        description="AI agent calling rds.delete_db_instance"
    )
    if validate_score_range(result5['risk_score'], 85, 92, "Prod delete, no PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result5['breakdown']}")
    print(f"   Reasoning: {result5['reasoning']}")

    # ========================================================================
    # TEST 6: Production Write with PII (Most Dangerous)
    # ========================================================================
    print_test_header(6, "Production S3 Upload with PII (Most Dangerous)")
    result6 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=8.0,  # High CVSS for write with PII
        environment="production",
        action_type="write",
        contains_pii=True,
        resource_name="customer-data-prod",
        description="AI agent calling s3.put_object with credit-card-numbers.csv"
    )
    if validate_score_range(result6['risk_score'], 95, 99, "Prod write with PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result6['breakdown']}")
    print(f"   Reasoning: {result6['reasoning']}")

    # ========================================================================
    # TEST 7: Production Read with PII
    # ========================================================================
    print_test_header(7, "Production Database Read with PII")
    result7 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=3.0,  # Low CVSS for read (but high data sensitivity)
        environment="production",
        action_type="read",
        contains_pii=True,
        resource_name="customer-financials-prod",
        description="AI agent reading customer credit cards from production database"
    )
    if validate_score_range(result7['risk_score'], 70, 85, "Prod read with PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result7['breakdown']}")
    print(f"   Reasoning: {result7['reasoning']}")

    # ========================================================================
    # TEST 8: Development Write with PII (Test data with PII-like structure)
    # ========================================================================
    print_test_header(8, "Development Database Write with PII")
    result8 = enterprise_risk_calculator.calculate_hybrid_risk_score(
        cvss_score=7.0,  # Medium-high CVSS for write
        environment="development",
        action_type="write",
        contains_pii=True,
        resource_name="test-user-data-dev",
        description="AI agent writing test user data (contains PII structure) to dev database"
    )
    if validate_score_range(result8['risk_score'], 45, 60, "Dev write with PII"):
        passed += 1
    else:
        failed += 1
    print(f"   Breakdown: {result8['breakdown']}")
    print(f"   Reasoning: {result8['reasoning']}")

    # ========================================================================
    # FINAL RESULTS
    # ========================================================================
    print_section_header("TEST SUITE RESULTS")
    print(f"Total Tests: {total}")
    print(f"{GREEN}✅ Passed: {passed}{RESET}")
    print(f"{RED}❌ Failed: {failed}{RESET}")
    print(f"Pass Rate: {(passed/total)*100:.1f}%")

    if failed == 0:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED - HYBRID RISK SCORING CALIBRATED CORRECTLY{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}⚠️  SOME TESTS FAILED - CALIBRATION ADJUSTMENT NEEDED{RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = run_validation_tests()
    sys.exit(exit_code)
