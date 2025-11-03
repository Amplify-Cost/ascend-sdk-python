#!/bin/bash
set -e

echo "🏢 ENTERPRISE: Starting OW-AI Backend..."

# Wait for database
echo "⏳ Waiting for database..."
sleep 5

echo "📊 Creating database tables..."

# Run Python inline to create admin user
python3 << 'PYTHON'
from sqlalchemy import create_engine, text
from auth_utils import hash_password
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./owai.db")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check if admin exists
    result = conn.execute(text("SELECT id FROM users WHERE email = 'admin@owkai.com'"))
    admin = result.fetchone()
    
    if admin:
        print(f"📋 Admin user exists: admin@owkai.com (ID: {admin[0]})")
        # Update password with new hash
        new_password = hash_password("Admin123!")
        conn.execute(
            text("UPDATE users SET password = :pwd WHERE email = 'admin@owkai.com'"),
            {"pwd": new_password}
        )
        conn.commit()
        print("✅ Admin password updated with SHA-256+bcrypt")
    else:
        hashed_pwd = hash_password("Admin123!")
        conn.execute(
            text("INSERT INTO users (email, password, role) VALUES (:email, :pwd, :role)"),
            {"email": "admin@owkai.com", "pwd": hashed_pwd, "role": "admin"}
        )
        conn.commit()
        print("✅ Admin user created: admin@owkai.com with SHA-256+bcrypt")

print("✅ Startup complete - Database ready")
PYTHON

echo "🔧 Running Alembic migrations..."
alembic upgrade head || echo "⚠️ Migration failed or already applied"

echo "🚀 Starting application server..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
