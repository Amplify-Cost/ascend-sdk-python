from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

print("=== ACTUAL DATABASE SCHEMA FOR ALERTS TABLE ===\n")

with engine.connect() as conn:
    # Get the actual columns in the alerts table
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'alerts'
        ORDER BY ordinal_position
    """))
    
    columns = result.fetchall()
    
    print("Database columns:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")

print("\n" + "="*50)
