#!/bin/bash
set -e

echo "🏢 ENTERPRISE: Starting OW-AI Backend..."
echo "📊 Creating database tables..."

python << 'PYTHON'
from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL
from auth_utils import hash_password

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    conn.commit()
    print("✅ Database tables created")
    
    # Check and create/update admin user
    result = conn.execute(text("SELECT id, email FROM users WHERE email = 'admin@owkai.com'"))
    admin = result.fetchone()
    
    if admin:
        print(f"📋 Admin user exists: {admin[1]} (ID: {admin[0]})")
        # Update password using hash_password from auth_utils
        new_password = hash_password("Admin123!")
        conn.execute(
            text("UPDATE users SET password = :pwd WHERE email = 'admin@owkai.com'"),
            {"pwd": new_password}
        )
        conn.commit()
        print("✅ Admin password updated with SHA-256+bcrypt")
    else:
        # Create new admin user
        hashed_pwd = hash_password("Admin123!")
        conn.execute(
            text("INSERT INTO users (email, password, role) VALUES (:email, :pwd, :role)"),
            {"email": "admin@owkai.com", "pwd": hashed_pwd, "role": "admin"}
        )
        conn.commit()
        print("✅ Admin user created: admin@owkai.com with SHA-256+bcrypt")

print("✅ Startup complete - Database ready")
PYTHON

echo "🚀 Starting application server..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Fix admin user password
python3 fix_admin.py
