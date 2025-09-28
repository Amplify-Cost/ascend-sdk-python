import os
from sqlalchemy import create_engine, text

# Connect using your connection string
DATABASE_URL = "postgresql://owkai_admin:OWKAI_secure123@owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com:5432/owkai_pilot"

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check exact table structure
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """))
        
        print("=== USERS TABLE STRUCTURE ===")
        for row in result:
            print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
        
        # Check specific users
        result = conn.execute(text("""
            SELECT id, email, 
                   CASE WHEN password IS NULL THEN 'NULL' 
                        WHEN LENGTH(password) < 10 THEN 'TOO_SHORT' 
                        ELSE 'HAS_PASSWORD' END as password_status,
                   role, created_at::text
            FROM users 
            WHERE email IN ('admin@owkai.com', 'saundra@gmail.com')
            ORDER BY created_at;
        """))
        
        print("\n=== USER COMPARISON ===")
        for row in result:
            print(f"  {row[1]}: {row[2]} | Role: {row[3]} | Created: {row[4]}")
        
        # Check all users
        result = conn.execute(text("""
            SELECT email,
                   CASE WHEN password IS NULL THEN 'NULL' 
                        WHEN LENGTH(password) < 10 THEN 'TOO_SHORT' 
                        ELSE 'HAS_PASSWORD' END as password_status,
                   role, created_at::text
            FROM users 
            ORDER BY created_at DESC
            LIMIT 10;
        """))
        
        print("\n=== ALL RECENT USERS ===")
        for row in result:
            print(f"  {row[0]}: {row[1]} | Role: {row[2]} | Created: {row[3]}")

except Exception as e:
    print(f"Connection failed: {e}")
