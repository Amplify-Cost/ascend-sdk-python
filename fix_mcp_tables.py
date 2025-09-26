from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://owkai_user:owkai_password@owkai-db.c9oan3mxhqvc.us-east-2.rds.amazonaws.com:5432/owkai_db")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS mcp_actions (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(255) NOT NULL,
            action_type VARCHAR(255) NOT NULL,
            resource TEXT,
            context JSONB,
            risk_level VARCHAR(50),
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    conn.commit()
    print("✅ MCP tables verified")
