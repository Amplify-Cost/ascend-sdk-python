from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=== WORKFLOW TABLE SCHEMA ===")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'workflows'
        ORDER BY ordinal_position
    """))
    
    print("Actual columns in workflows table:")
    for col in result.fetchall():
        print(f"  • {col[0]}: {col[1]}")
    
    print()
    print("Existing workflows:")
    result = conn.execute(text("SELECT * FROM workflows LIMIT 3"))
    rows = result.fetchall()
    print(f"  Total: {len(rows)}")
    for row in rows:
        print(f"  • ID: {row[0]}, Data: {row[:5]}...")
