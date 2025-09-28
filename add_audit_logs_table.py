import sys
from sqlalchemy import text, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def create_audit_logs_table():
    """Create user_audit_logs table for compliance tracking"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(255),
                    action VARCHAR(255),
                    target VARCHAR(255),
                    details TEXT,
                    ip_address VARCHAR(50),
                    risk_level VARCHAR(20),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS enterprise_reports (
                    id VARCHAR(255) PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    type VARCHAR(100),
                    classification VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'completed',
                    format VARCHAR(20) DEFAULT 'PDF',
                    file_size VARCHAR(50),
                    author VARCHAR(255),
                    department VARCHAR(255) DEFAULT 'Information Security',
                    description TEXT,
                    content JSON,
                    download_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()
            print("✅ Audit and reports tables created", flush=True)
    except Exception as e:
        print(f"⚠️ Error creating audit tables: {e}", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    create_audit_logs_table()
