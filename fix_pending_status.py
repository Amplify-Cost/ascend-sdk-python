from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Update status to match what dashboard expects
with engine.connect() as conn:
    # First, let's see what statuses exist
    result = conn.execute(text("SELECT DISTINCT status FROM agent_actions"))
    statuses = result.fetchall()
    print("Current statuses:", statuses)
    
    # Update pending_approval to pending
    result = conn.execute(text("""
        UPDATE agent_actions 
        SET status = 'pending' 
        WHERE status = 'pending_approval'
        RETURNING id
    """))
    updated = result.fetchall()
    conn.commit()
    print(f"✅ Updated {len(updated)} actions from 'pending_approval' to 'pending'")
    
    # Verify the change
    result = conn.execute(text("SELECT COUNT(*) FROM agent_actions WHERE status = 'pending'"))
    count = result.scalar()
    print(f"📊 Total pending actions now: {count}")
