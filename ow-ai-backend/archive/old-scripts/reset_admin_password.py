from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash the password correctly (will be <72 bytes)
hashed = pwd_context.hash("admin123")
print(f"New hash: {hashed}")

# Get DB URL from env
db_url = os.getenv("DATABASE_URL") or "postgresql://owkai_admin:REDACTED-CREDENTIAL@owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com:5432/owkai_pilot"

engine = create_engine(db_url)
with engine.connect() as conn:
    conn.execute(text("""
        UPDATE users 
        SET password = :pwd 
        WHERE email = 'admin@owkai.com'
    """), {"pwd": hashed})
    conn.commit()
    print("✅ Admin password reset successfully")
