from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://owkai_user:owkai_password@owkai-db.c9oan3mxhqvc.us-east-2.rds.amazonaws.com:5432/owkai_db")
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            control_rule_id INTEGER,
            variant_rule_id INTEGER,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    conn.commit()
    print("✅ Smart rules tables verified")
