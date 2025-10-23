from database import SQLALCHEMY_DATABASE_URL
from sqlalchemy import create_engine, text

engine = create_engine(SQLALCHEMY_DATABASE_URL)

print("🔧 Creating alerts table...")

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            alert_type VARCHAR(255),
            severity VARCHAR(50),
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_id VARCHAR(255),
            agent_action_id INTEGER,
            status VARCHAR(50) DEFAULT 'new',
            acknowledged_by VARCHAR(255),
            acknowledged_at TIMESTAMP,
            escalated_by VARCHAR(255),
            escalated_at TIMESTAMP,
            CONSTRAINT fk_agent_action FOREIGN KEY (agent_action_id) 
                REFERENCES agent_actions(id) ON DELETE SET NULL
        )
    """))
    
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)"))
    
    conn.commit()
    print("✅ alerts table created successfully")
    
    # Verify
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'alerts'
        ORDER BY ordinal_position
    """))
    
    print("\n📊 Table structure:")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")

