"""Test NIST control mapper"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.nist_mapper import nist_mapper
from database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== Testing NIST Control Mapper ===\n")

# Test 1: Map data exfiltration action
print("Test 1: Data Exfiltration Action")
mappings1 = nist_mapper.map_action_to_controls(
    db=db,
    action_id=144,
    action_type="data_exfiltration_check"
)
for m in mappings1:
    print(f"  {m['control_id']} ({m['relevance']}): {m['title']}")

print("\nTest 2: Database Write Action")
mappings2 = nist_mapper.map_action_to_controls(
    db=db,
    action_id=145,
    action_type="database_write"
)
for m in mappings2:
    print(f"  {m['control_id']} ({m['relevance']}): {m['title']}")

print("\nTest 3: Authentication Action")
mappings3 = nist_mapper.map_action_to_controls(
    db=db,
    action_id=146,
    action_type="authentication_check"
)
for m in mappings3:
    print(f"  {m['control_id']} ({m['relevance']}): {m['title']}")

print("\n" + "="*60)
print("Compliance Summary by Control Family:\n")
summary = nist_mapper.get_compliance_summary(db)
for item in summary:
    print(f"{item['family']:40} {item['mapped_controls']}/{item['total_controls']} ({item['coverage_percent']}%)")

db.close()
print("\n✅ NIST mapper tests complete!")
