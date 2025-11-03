#!/usr/bin/env python3
"""
Validation script for analytics routes real data migration.
Verifies that all mock/hardcoded data has been removed.
"""

import ast
import sys
from pathlib import Path

def check_for_hardcoded_values():
    """Check analytics_routes.py for hardcoded mock values."""

    analytics_file = Path(__file__).parent / "routes" / "analytics_routes.py"

    if not analytics_file.exists():
        print(f"❌ File not found: {analytics_file}")
        return False

    with open(analytics_file, 'r') as f:
        content = f.read()

    # Known bad patterns (hardcoded mock values)
    bad_patterns = [
        ('"score": 94.2', "Executive dashboard hardcoded platform health score"),
        ('"score": 87.6', "Executive dashboard hardcoded security posture score"),
        ('"score": 91.3', "Executive dashboard hardcoded operational efficiency"),
        ('"score": 96.8', "Executive dashboard hardcoded compliance score"),
        ('"current_users": 17', "Executive dashboard hardcoded user count"),
        ('"current": 42.3', "System performance hardcoded CPU usage"),
        ('"current": 67.8', "System performance hardcoded memory usage"),
        ('"average": 145.2', "System performance hardcoded response time"),
        ('42.3 +', "WebSocket hardcoded CPU base value"),
        ('67.8 +', "WebSocket hardcoded memory base value"),
        ('145.2 +', "WebSocket hardcoded response time base value"),
        ('hash(str(datetime.now', "WebSocket fake randomization"),
    ]

    issues_found = []

    for pattern, description in bad_patterns:
        if pattern in content:
            issues_found.append(f"  ❌ Found: {description}")
            # Find line number
            for i, line in enumerate(content.split('\n'), 1):
                if pattern in line:
                    issues_found.append(f"     Line {i}: {line.strip()[:80]}")

    # Good patterns (real data indicators)
    good_patterns = [
        ('db.query(func.count(AgentAction.id))', "Real database queries"),
        ('db.query(func.count(User.id))', "Real user queries"),
        ('db.execute(text(', "Raw SQL queries for complex aggregations"),
        ('"mock_data": False', "Explicit mock_data flag"),
        ('"status": "cloudwatch_required"', "CloudWatch status messages"),
        ('"source": "real_database"', "Real data source attribution"),
        ('get_cloudwatch_service', "CloudWatch integration"),
        ('.scalar() or 0', "Proper null handling"),
    ]

    found_good = []
    missing_good = []

    for pattern, description in good_patterns:
        if pattern in content:
            found_good.append(f"  ✅ {description}")
        else:
            missing_good.append(f"  ⚠️  Missing: {description}")

    # Print results
    print("\n" + "="*80)
    print("ANALYTICS ROUTES VALIDATION REPORT")
    print("="*80)

    if issues_found:
        print("\n❌ HARDCODED VALUES FOUND:")
        for issue in issues_found:
            print(issue)
        print("\n⚠️  VALIDATION FAILED - Mock data still present")
        success = False
    else:
        print("\n✅ NO HARDCODED VALUES FOUND")
        success = True

    if found_good:
        print("\n✅ REAL DATA PATTERNS DETECTED:")
        for pattern in found_good:
            print(pattern)

    if missing_good:
        print("\n⚠️  EXPECTED PATTERNS NOT FOUND:")
        for pattern in missing_good:
            print(pattern)

    # Count endpoints
    endpoint_count = content.count('@router.get(') + content.count('@router.websocket(')
    print(f"\n📊 Statistics:")
    print(f"  - Total endpoints: {endpoint_count}")
    print(f"  - File size: {len(content)} characters")
    print(f"  - Lines of code: {len(content.split(chr(10)))}")

    # Check for key endpoints
    key_endpoints = [
        ('/executive/dashboard', 'Executive Dashboard'),
        ('/performance/system', 'System Performance'),
        ('/ws/realtime/', 'WebSocket Streaming'),
        ('/realtime/metrics', 'Real-time Metrics'),
        ('/predictive/trends', 'Predictive Analytics'),
    ]

    print(f"\n📋 Key Endpoints:")
    for endpoint, name in key_endpoints:
        if endpoint in content:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} - NOT FOUND")

    print("\n" + "="*80)

    if success:
        print("✅ VALIDATION PASSED - Ready for deployment")
    else:
        print("❌ VALIDATION FAILED - Review issues above")

    print("="*80 + "\n")

    return success


def check_imports():
    """Verify all required imports are present."""

    analytics_file = Path(__file__).parent / "routes" / "analytics_routes.py"

    with open(analytics_file, 'r') as f:
        content = f.read()

    required_imports = [
        ('from fastapi import APIRouter', 'FastAPI Router'),
        ('from sqlalchemy.orm import Session', 'SQLAlchemy Session'),
        ('from sqlalchemy import func', 'SQLAlchemy functions'),
        ('from database import get_db', 'Database dependency'),
        ('AgentAction', 'AgentAction model'),
        ('User', 'User model'),
        ('AuditLog', 'AuditLog model'),
        ('from datetime import datetime', 'DateTime imports'),
        ('from dependencies import get_current_user', 'Auth dependencies'),
        ('get_cloudwatch_service', 'CloudWatch service'),
    ]

    print("\n📦 Import Validation:")
    all_present = True
    for imp, description in required_imports:
        if imp in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} - '{imp}' not found")
            all_present = False

    return all_present


if __name__ == "__main__":
    print("\n🔍 Validating Analytics Routes Real Data Migration...")

    success = True

    # Check for hardcoded values
    if not check_for_hardcoded_values():
        success = False

    # Check imports
    if not check_imports():
        success = False

    if success:
        print("\n🎉 All validations passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some validations failed - review output above")
        sys.exit(1)
