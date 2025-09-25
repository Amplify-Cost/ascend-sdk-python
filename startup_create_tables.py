from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def create_smart_rules_table_on_startup():
    """Create smart_rules table if it doesn't exist"""
    try:
        engine = create_engine(DATABASE_URL)
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
                    INSERT INTO smart_rules (agent_id, action_type, description, condition, action, risk_level, recommendation, justification) VALUES
                    ('security-scanner-01', 'vulnerability_scan', 'High-risk scan approval', 'risk_level == "high"', 'require_approval', 'high', 'Manual approval required', 'Security'),
                    ('compliance-agent', 'compliance_check', 'Auto-approve compliance', 'risk_level == "low"', 'auto_approve', 'low', 'Automated checks', 'Routine'),
                    ('threat-detector', 'anomaly_detection', 'Alert on anomalies', 'action_type == "anomaly_detection"', 'alert', 'medium', 'Monitor activity', 'Detection')
                """))
            
            conn.commit()
            logger.info("✅ smart_rules table ready")
    except Exception as e:
        logger.error(f"⚠️ Could not create smart_rules table: {e}")
