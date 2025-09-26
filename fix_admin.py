from sqlalchemy import create_engine, text
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://owkai_user:owkai_password@owkai-db.c9oan3mxhqvc.us-east-2.rds.amazonaws.com:5432/owkai_db")

engine = create_engine(DATABASE_URL)

# Use simple bcrypt (like test@example.com) for compatibility
admin_password = pwd_context.hash("Admin123!")

with engine.connect() as conn:
    # Check if admin exists
    result = conn.execute(text("SELECT id FROM users WHERE email = 'admin@owkai.com'"))
    admin = result.fetchone()
    
    if admin:
        # Update existing admin
        conn.execute(
            text("UPDATE users SET password = :pwd, role = 'admin' WHERE email = 'admin@owkai.com'"),
            {"pwd": admin_password}
        )
        print("✅ Admin password updated to legacy bcrypt")
    else:
        # Create new admin
        conn.execute(
            text("INSERT INTO users (email, password, role) VALUES (:email, :pwd, 'admin')"),
            {"email": "admin@owkai.com", "pwd": admin_password}
        )
        print("✅ Admin user created with legacy bcrypt")
    
    conn.commit()
    print("✅ Login: admin@owkai.com / Admin123!")
