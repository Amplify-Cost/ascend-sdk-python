"""Test CVSS auto-mapper"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.cvss_auto_mapper import cvss_auto_mapper
from database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== Testing CVSS Auto-Mapper ===\n")

# Test 1: Data exfiltration from production
print("Test 1: Data Exfiltration (Production + PII)")
result1 = cvss_auto_mapper.auto_assess_action(
    db=db,
    action_id=145,
    action_type="data_exfiltration_check",
    context={"environment": "production", "contains_pii": True}
)
print(f"  Score: {result1['base_score']} - {result1['severity']}")
print(f"  Vector: {result1['vector_string']}\n")

# Test 2: Database write
print("Test 2: Database Write Operation")
result2 = cvss_auto_mapper.auto_assess_action(
    db=db,
    action_id=146,
    action_type="database_write",
    context={}
)
print(f"  Score: {result2['base_score']} - {result2['severity']}")
print(f"  Vector: {result2['vector_string']}\n")

# Test 3: File read (low risk)
print("Test 3: File Read Operation")
result3 = cvss_auto_mapper.auto_assess_action(
    db=db,
    action_id=147,
    action_type="file_read",
    context={}
)
print(f"  Score: {result3['base_score']} - {result3['severity']}")
print(f"  Vector: {result3['vector_string']}\n")

print("Verifying database storage...")
result = db.execute(text("SELECT action_id, base_score, severity FROM cvss_assessments WHERE action_id IN (145, 146, 147)"))
for row in result:
    print(f"  Action {row[0]}: {row[1]} ({row[2]})")

db.close()
print("\n✅ All tests passed!")
