import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("🔍 Checking automation playbook tables...")
print("=" * 70)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name IN ('automation_playbooks', 'playbook_executions')
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    
    if tables:
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = count_result.scalar()
            print(f"  • {table}: {count} rows")
    else:
        print("❌ Tables not found!")

print("=" * 70)
