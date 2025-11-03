from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import AgentAction
from services.cvss_auto_mapper import cvss_auto_mapper
from datetime import datetime, UTC

# Connect
engine = create_engine("postgresql://localhost/owkai_pilot")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Create a test action (simulating what the endpoint does)
    action = AgentAction(
        agent_id="direct-db-test",
        action_type="privilege_escalation",
        description="Direct DB test of CVSS fix",
        tool_name="test",
        risk_level="high",
        status="pending",
        timestamp=datetime.now(UTC)
    )
    
    db.add(action)
    db.commit()
    db.refresh(action)
    print(f"✅ Created action {action.id}")
    
    # Now apply CVSS (this is what the fix does)
    cvss_result = cvss_auto_mapper.auto_assess_action(
        db=db,
        action_id=action.id,
        action_type="privilege_escalation",
        context={"risk_level": "high"}
    )
    
    print(f"CVSS calculated: {cvss_result}")
    
    # Update with CVSS (using the fix)
    action.cvss_score = cvss_result["base_score"]
    action.cvss_severity = cvss_result["severity"]
    action.cvss_vector = cvss_result["vector_string"]
    
    db.add(action)  # Re-add (the fix!)
    db.flush()      # Flush (the fix!)
    db.commit()     # Commit
    db.refresh(action)  # Reload
    
    print(f"\n✅ SUCCESS! Action {action.id} updated:")
    print(f"   CVSS Score: {action.cvss_score}")
    print(f"   Severity: {action.cvss_severity}")
    print(f"   Vector: {action.cvss_vector}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
