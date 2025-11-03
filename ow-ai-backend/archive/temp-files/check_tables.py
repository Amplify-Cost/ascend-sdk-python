import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

print("🔍 CURRENT DATABASE TABLES:")
print("=" * 70)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    
    tables = result.fetchall()
    
    if tables:
        for table_name, col_count in tables:
            print(f"  ✅ {table_name} ({col_count} columns)")
    else:
        print("  ⚠️  No tables found!")
    
    print("")
    print(f"Total tables: {len(tables)}")
    print("=" * 70)
