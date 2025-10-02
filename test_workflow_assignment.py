"""Test workflow approver assignment"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.workflow_approver_service import workflow_approver_service
from database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== Testing Workflow Approver Assignment ===\n")

# Test assigning approvers to a workflow
result = workflow_approver_service.assign_approvers_to_workflow(
    db=db,
    workflow_execution_id=999,  # Test ID
    action_id=144,  # One of your existing actions
    risk_score=75,
    required_approval_level=2,
    department="Engineering"
)

print(f"Primary Approver: {result['primary']['email']}")
print(f"  - Level: {result['primary']['approval_level']}")
print(f"  - Max Risk: {result['primary']['max_risk_approval']}")
print(f"  - Pending: {result['primary']['pending_count']}")

print(f"\nBackup Approvers: {len(result['backups'])}")
for i, backup in enumerate(result['backups'], 1):
    print(f"  {i}. {backup['email']} (Level {backup['approval_level']})")

print(f"\nTotal Available Approvers: {result['total_available']}")

db.close()
