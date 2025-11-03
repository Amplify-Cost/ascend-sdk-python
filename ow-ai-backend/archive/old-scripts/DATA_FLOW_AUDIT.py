"""
Analyze data flow between components
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=" * 80)
print("🔄 DATA FLOW ANALYSIS")
print("=" * 80)

with engine.connect() as conn:
    # Check if workflows reference playbooks
    print("\n1. Do workflow_executions reference automation_playbooks?")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions'
        ORDER BY ordinal_position
    """))
    we_columns = [row[0] for row in result.fetchall()]
    print(f"   workflow_executions columns: {', '.join(we_columns)}")
    has_playbook_ref = 'playbook_id' in we_columns
    print(f"   Has playbook_id? {has_playbook_ref}")
    
    # Check if policies reference workflows
    print("\n2. Do enterprise_policies reference workflows?")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'enterprise_policies'
        ORDER BY ordinal_position
    """))
    ep_columns = [row[0] for row in result.fetchall()]
    print(f"   enterprise_policies columns: {', '.join(ep_columns)}")
    
    # Check smart_rules
    print("\n3. Smart rules structure:")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'smart_rules'
        ORDER BY ordinal_position
    """))
    sr_columns = [row[0] for row in result.fetchall()]
    print(f"   smart_rules columns: {', '.join(sr_columns)}")
    
    # Check actual data relationships
    print("\n4. Actual data in tables:")
    
    tables_to_check = [
        'workflows',
        'workflow_executions', 
        'automation_playbooks',
        'enterprise_policies',
        'smart_rules',
        'agent_actions'
    ]
    
    for table in tables_to_check:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            
            # Get sample row if exists
            if count > 0:
                result = conn.execute(text(f"SELECT * FROM {table} LIMIT 1"))
                sample = result.fetchone()
                print(f"\n   {table}: {count} rows")
                print(f"   Sample ID: {sample[0] if sample else 'N/A'}")
            else:
                print(f"\n   {table}: 0 rows (EMPTY)")
        except Exception as e:
            print(f"\n   {table}: ERROR - {str(e)}")

print("\n" + "=" * 80)
