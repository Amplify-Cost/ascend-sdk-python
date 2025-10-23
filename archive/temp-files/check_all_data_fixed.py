from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=== ALL DATA IN SYSTEM ===")
print()

with engine.connect() as conn:
    # Check playbooks
    print("📋 AUTOMATION PLAYBOOKS:")
    result = conn.execute(text("SELECT id, name, status FROM automation_playbooks ORDER BY created_at DESC"))
    playbooks = result.fetchall()
    print(f"   Total: {len(playbooks)}")
    for pb in playbooks:
        print(f"   • {pb[0]}: {pb[1]} ({pb[2]})")
    
    print()
    
    # Check workflows - use actual columns
    print("🔄 WORKFLOW TEMPLATES:")
    result = conn.execute(text("SELECT id, name, status, created_by FROM workflows ORDER BY created_at DESC"))
    workflows = result.fetchall()
    print(f"   Total: {len(workflows)}")
    for wf in workflows:
        print(f"   • {wf[0]}: {wf[1]} ({wf[2]}) by {wf[3]}")

print()
