"""Test the approver selector with different scenarios"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.approver_selector import approver_selector
from database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== Testing Approver Selector ===\n")

# Test 1: Low risk, level 1 approval needed
print("Test 1: Low risk (30), Level 1, Engineering")
approvers = approver_selector.select_approvers(
    db, risk_score=30, approval_level=1, department="Engineering"
)
for i, a in enumerate(approvers, 1):
    print(f"  {i}. {a['email']} - Level {a['approval_level']}, {a['max_risk_approval']}, Pending: {a['pending_count']}")

print("\n" + "="*50 + "\n")

# Test 2: High risk, level 2 approval needed
print("Test 2: High risk (85), Level 2, Security")
approvers = approver_selector.select_approvers(
    db, risk_score=85, approval_level=2, department="Security"
)
for i, a in enumerate(approvers, 1):
    print(f"  {i}. {a['email']} - Level {a['approval_level']}, {a['max_risk_approval']}, Pending: {a['pending_count']}")

print("\n" + "="*50 + "\n")

# Test 3: Critical risk, level 3 approval needed
print("Test 3: Critical risk (95), Level 3, Finance")
approvers = approver_selector.select_approvers(
    db, risk_score=95, approval_level=3, department="Finance"
)
for i, a in enumerate(approvers, 1):
    print(f"  {i}. {a['email']} - Level {a['approval_level']}, {a['max_risk_approval']}, Pending: {a.get('pending_count', 0)}")

print("\n" + "="*50 + "\n")

# Test 4: Impossible scenario - should use emergency approver
print("Test 4: Ultra-high requirements (no qualified approver)")
approvers = approver_selector.select_approvers(
    db, risk_score=99, approval_level=5, department="NonExistent"
)
if approvers:
    print("  Emergency approvers activated:")
    for i, a in enumerate(approvers, 1):
        print(f"  {i}. {a['email']} - Emergency Approver")
else:
    print("  No approvers found!")

db.close()
