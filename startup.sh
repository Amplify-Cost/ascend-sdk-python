#!/bin/bash
set -e

echo "🏢 ENTERPRISE: Starting OW-AI Backend..."
echo "📊 Creating database tables..."

python << 'PYTHON'
from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS smart_rules (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(255),
            action_type VARCHAR(255),
            description TEXT,
            condition TEXT,
            action VARCHAR(100),
            risk_level VARCHAR(50),
            recommendation TEXT,
            justification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    result = conn.execute(text("SELECT COUNT(*) FROM smart_rules"))
    if result.fetchone()[0] == 0:
        conn.execute(text("""
            INSERT INTO smart_rules (agent_id, action_type, description, condition, action, risk_level, recommendation, justification)
            VALUES 
            ('security-scanner-01', 'vulnerability_scan', 'High-risk scan', 'risk_level = high', 'require_approval', 'high', 'Manual approval', 'Security'),
            ('compliance-agent', 'compliance_check', 'Auto-approve', 'risk_level = low', 'auto_approve', 'low', 'Automated', 'Routine'),
            ('threat-detector', 'anomaly_detection', 'Alert', 'action_type = anomaly', 'alert', 'medium', 'Monitor', 'Detection')
        """))
    
    conn.commit()
    print("✅ Database tables ready")
PYTHON

echo "🚀 Starting application server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
