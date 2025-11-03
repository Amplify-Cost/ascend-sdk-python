"""
Backfill CVSS scores for existing agent_actions
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# Database connection
DATABASE_URL = "postgresql://localhost/owkai_pilot"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Get all actions with NULL cvss_score but have cvss_assessments
    query = text("""
        SELECT 
            aa.id,
            aa.agent_id,
            ca.base_score,
            ca.severity,
            ca.vector_string
        FROM agent_actions aa
        INNER JOIN cvss_assessments ca ON ca.action_id = aa.id
        WHERE aa.cvss_score IS NULL
        ORDER BY aa.id
    """)
    
    results = db.execute(query).fetchall()
    
    if not results:
        print("✅ No actions need backfilling - all have CVSS scores!")
        sys.exit(0)
    
    print(f"Found {len(results)} actions to backfill:\n")
    
    for row in results:
        action_id = row[0]
        agent_id = row[1]
        cvss_score = row[2]
        cvss_severity = row[3]
        cvss_vector = row[4]
        
        print(f"Action {action_id} ({agent_id}):")
        print(f"  CVSS Score: {cvss_score}")
        print(f"  Severity: {cvss_severity}")
        print(f"  Vector: {cvss_vector}")
        
        # Update the action
        update_query = text("""
            UPDATE agent_actions 
            SET 
                cvss_score = :cvss_score,
                cvss_severity = :cvss_severity,
                cvss_vector = :cvss_vector,
                risk_score = :risk_score
            WHERE id = :action_id
        """)
        
        db.execute(update_query, {
            "action_id": action_id,
            "cvss_score": cvss_score,
            "cvss_severity": cvss_severity,
            "cvss_vector": cvss_vector,
            "risk_score": cvss_score * 10  # 0-100 scale
        })
        
        print(f"  ✅ Updated\n")
    
    # Commit all changes
    db.commit()
    print(f"✅ Successfully backfilled {len(results)} actions!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
