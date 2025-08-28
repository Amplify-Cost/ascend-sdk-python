from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check current schema
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name LIKE '%password%';"))
    current_columns = [row[0] for row in result]
    print(f"Current password columns: {current_columns}")
    
    # Rename column if needed
    if 'password' in current_columns and 'hashed_password' not in current_columns:
        conn.execute(text("ALTER TABLE users RENAME COLUMN password TO hashed_password;"))
        conn.commit()
        print("✅ Renamed password column to hashed_password")
    else:
        print("✅ Schema already correct")
