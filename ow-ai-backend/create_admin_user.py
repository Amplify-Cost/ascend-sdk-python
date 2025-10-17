from sqlalchemy import create_engine, text
from passlib.context import CryptContext
import os

print("Creating enterprise admin user...")

# Get database connection
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("admin123")

# Create admin user
with engine.connect() as conn:
    # Create users table if it doesn't exist
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approval_level INTEGER DEFAULT 1,
            is_emergency_approver BOOLEAN DEFAULT FALSE,
            max_risk_approval INTEGER DEFAULT 50
        )
    """))
    
    # Insert or update admin user
    conn.execute(text("""
        INSERT INTO users (email, password_hash, password, role, approval_level, is_emergency_approver, max_risk_approval)
        VALUES (:email, :password_hash, :password, 'admin', 5, TRUE, 100)
        ON CONFLICT (email) DO UPDATE SET
        password_hash = :password_hash,
        password = :password,
        role = 'admin',
        approval_level = 5,
        is_emergency_approver = TRUE,
        max_risk_approval = 100
    """), {
        'email': 'admin@owkai.com',
        'password_hash': hashed_password,
        'password': hashed_password
    })
    
    conn.commit()

print("Enterprise admin user created successfully!")
print("Email: admin@owkai.com")
print("Password: admin123")
