"""Test CVSS v3.1 calculator"""
from services.cvss_calculator import cvss_calculator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import SQLALCHEMY_DATABASE_URL

print("=== Testing CVSS v3.1 Calculator ===\n")

# Test 1: Critical vulnerability (network-accessible, no privileges, high impact)
print("Test 1: Critical Network Vulnerability")
metrics1 = {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "NONE",
    "user_interaction": "NONE",
    "scope": "CHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "HIGH",
    "availability_impact": "HIGH"
}
result1 = cvss_calculator.calculate_base_score(metrics1)
print(f"  Score: {result1['base_score']} - {result1['severity']}")
print(f"  Vector: {result1['vector_string']}\n")

# Test 2: Medium vulnerability (local access required)
print("Test 2: Medium Local Vulnerability")
metrics2 = {
    "attack_vector": "LOCAL",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "UNCHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "NONE",
    "availability_impact": "NONE"
}
result2 = cvss_calculator.calculate_base_score(metrics2)
print(f"  Score: {result2['base_score']} - {result2['severity']}")
print(f"  Vector: {result2['vector_string']}\n")

# Test 3: Low vulnerability (requires user interaction)
print("Test 3: Low Risk with User Interaction")
metrics3 = {
    "attack_vector": "NETWORK",
    "attack_complexity": "HIGH",
    "privileges_required": "LOW",
    "user_interaction": "REQUIRED",
    "scope": "UNCHANGED",
    "confidentiality_impact": "LOW",
    "integrity_impact": "NONE",
    "availability_impact": "NONE"
}
result3 = cvss_calculator.calculate_base_score(metrics3)
print(f"  Score: {result3['base_score']} - {result3['severity']}")
print(f"  Vector: {result3['vector_string']}\n")

# Test 4: Store assessment in database
print("Test 4: Store CVSS Assessment for Action 144")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

result4 = cvss_calculator.assess_agent_action(
    db=db,
    action_id=144,
    metrics=metrics1,
    assessed_by="test_script"
)
print(f"  Assessment ID: {result4['assessment_id']}")
print(f"  Score: {result4['base_score']} - {result4['severity']}")
print(f"  Stored in database successfully!")

db.close()
