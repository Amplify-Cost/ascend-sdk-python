"""
Test script to see what cvss_auto_mapper.auto_assess_action returns
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.cvss_auto_mapper import cvss_auto_mapper
import json

# Connect to database
DATABASE_URL = "postgresql://localhost/owkai_pilot"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Test with action_id 7 (the latest one)
try:
    result = cvss_auto_mapper.auto_assess_action(
        db=db,
        action_id=7,
        action_type="data_exfiltration",
        context={
            "risk_level": "medium",
            "contains_pii": False,
            "production_system": False,
            "requires_admin": False
        }
    )
    
    print("✅ CVSS Result:")
    print(json.dumps(result, indent=2))
    print("\nKeys in result:")
    for key in result.keys():
        print(f"  - {key}: {type(result[key]).__name__}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

db.close()
