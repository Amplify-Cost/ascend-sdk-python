"""
Fix smart_rules table schema - add missing columns
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

print("🔍 Checking smart_rules table structure...")
print("")

with engine.connect() as conn:
    # Check current columns
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'smart_rules'
        ORDER BY ordinal_position
    """))
    
    columns = {row[0]: row[1] for row in result}
    
    print("Current columns:")
    for col, dtype in columns.items():
        print(f"  • {col}: {dtype}")
    
    print("")
    
    # Check if 'name' column exists
    if 'name' not in columns:
        print("❌ Missing 'name' column")
        print("🔧 Adding 'name' column...")
        
        conn.execute(text("""
            ALTER TABLE smart_rules 
            ADD COLUMN IF NOT EXISTS name VARCHAR(255)
        """))
        conn.commit()
        
        print("✅ Added 'name' column")
    else:
        print("✅ 'name' column exists")
    
    # Check if 'updated_at' column exists
    if 'updated_at' not in columns:
        print("❌ Missing 'updated_at' column")
        print("🔧 Adding 'updated_at' column...")
        
        conn.execute(text("""
            ALTER TABLE smart_rules 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
        """))
        conn.commit()
        
        print("✅ Added 'updated_at' column")
    else:
        print("✅ 'updated_at' column exists")
    
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎉 Schema fixed!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("Now test again:")
    print("  curl -X POST http://localhost:8000/api/smart-rules/seed -H 'Authorization: Bearer TOKEN'")

