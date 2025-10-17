#!/usr/bin/env python3
"""Create smart_rules table"""
import sys
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def create_smart_rules_table():
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Create table
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
            
            # Insert sample data
            conn.execute(text("""
                INSERT INTO smart_rules (agent_id, action_type, description, condition, action, risk_level, recommendation, justification)
                VALUES 
                    ('security-scanner-01', 'vulnerability_scan', 'High-risk scan approval', 'risk_level == "high"', 'require_approval', 'high', 'Manual approval required', 'Prevent unauthorized testing'),
                    ('compliance-agent', 'compliance_check', 'Auto-approve compliance', 'risk_level == "low"', 'auto_approve', 'low', 'Automated checks', 'Routine audits safe'),
                    ('threat-detector', 'anomaly_detection', 'Alert on anomalies', 'action_type == "anomaly_detection"', 'alert', 'medium', 'Monitor activity', 'Early detection')
                ON CONFLICT DO NOTHING
            """))
            
            conn.commit()
            print("✅ smart_rules table created with sample data")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_smart_rules_table()
