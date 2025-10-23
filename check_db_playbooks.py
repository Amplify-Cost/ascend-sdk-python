from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=" * 80)
print("DATABASE PLAYBOOK CHECK")
print("=" * 80)

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, status, created_at FROM automation_playbooks ORDER BY created_at DESC"))
    rows = result.fetchall()
    
    print(f"\nPlaybooks in database: {len(rows)}")
    for row in rows:
        print(f"  • {row[0]}: {row[1]} (status: {row[2]}, created: {row[3]})")
    
    if len(rows) == 1 and rows[0][0] == 'pb-001':
        print("\n❌ ONLY DEMO DATA - No real playbooks created!")
    elif len(rows) > 1:
        print("\n✅ Real playbooks exist in database")
    else:
        print("\n⚠️  No playbooks in database")

print("=" * 80)
