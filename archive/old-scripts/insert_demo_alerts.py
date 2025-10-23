from database import SQLALCHEMY_DATABASE_URL
from sqlalchemy import create_engine, text
from datetime import datetime, UTC

engine = create_engine(SQLALCHEMY_DATABASE_URL)

print("🔧 Inserting demo alerts into database...")

demo_alerts = [
    (3001, "High Risk Agent Action", "high", "Multiple failed login attempts detected", "agent-001"),
    (3002, "Compliance Violation", "medium", "Data access outside approved hours", "agent-002"),
    (3003, "Threat Detection", "high", "Suspicious API calls detected", "agent-003"),
    (3004, "Data Loss Prevention", "medium", "Attempted file transfer to unauthorized location", "agent-004"),
    (3005, "Privilege Escalation", "high", "Unauthorized permission change attempt", "agent-005"),
]

with engine.connect() as conn:
    # Clear existing demo alerts
    conn.execute(text("DELETE FROM alerts WHERE id >= 3001 AND id <= 3005"))
    
    # Insert demo alerts
    for alert_id, alert_type, severity, message, agent_id in demo_alerts:
        conn.execute(text("""
            INSERT INTO alerts (id, alert_type, severity, message, agent_id, status, timestamp)
            VALUES (:id, :alert_type, :severity, :message, :agent_id, 'new', NOW())
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": alert_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "agent_id": agent_id
        })
    
    conn.commit()
    print("✅ Demo alerts inserted successfully")
    
    # Verify
    result = conn.execute(text("SELECT id, alert_type, severity, status FROM alerts WHERE id >= 3001 ORDER BY id"))
    print("\n📊 Demo alerts in database:")
    for row in result:
        print(f"  Alert {row[0]}: {row[1]} ({row[2]}) - Status: {row[3]}")

