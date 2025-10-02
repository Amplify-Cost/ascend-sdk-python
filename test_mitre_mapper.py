"""Test MITRE ATT&CK mapper"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.mitre_mapper import mitre_mapper
from database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== Testing MITRE ATT&CK Mapper ===\n")

# Test 1: Data exfiltration
print("Test 1: Data Exfiltration")
mappings1 = mitre_mapper.map_action_to_techniques(
    db=db,
    action_id=144,
    action_type="data_exfiltration_check"
)
for m in mappings1:
    print(f"  {m['technique_id']} ({m['confidence']}): {m['name']}")
    print(f"    Tactic: {m['tactic']}")

# Test 2: Credential access
print("\nTest 2: Credential Access")
mappings2 = mitre_mapper.map_action_to_techniques(
    db=db,
    action_id=145,
    action_type="credential_access_attempt"
)
for m in mappings2:
    print(f"  {m['technique_id']} ({m['confidence']}): {m['name']}")

# Test 3: Privilege escalation
print("\nTest 3: Privilege Escalation")
mappings3 = mitre_mapper.map_action_to_techniques(
    db=db,
    action_id=146,
    action_type="privilege_escalation_check"
)
for m in mappings3:
    print(f"  {m['technique_id']} ({m['confidence']}): {m['name']}")

print("\n" + "="*60)
print("Threat Landscape:\n")
landscape = mitre_mapper.get_threat_landscape(db)
for item in landscape:
    print(f"{item['tactic']:25} {item['detected_techniques']} techniques, {item['affected_actions']} actions")

db.close()
print("\n✅ MITRE mapper tests complete!")
