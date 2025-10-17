#!/usr/bin/env python3
"""
OW-KAI Demo Data Clearing Script
Safely removes all data while preserving table structures and admin user
"""

import os
import psycopg2
from datetime import datetime

def clear_demo_data():
    """Clear all data from tables except users table"""
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    # Tables to clear (ALL children of agent_actions first!)
    clear_order = [
        'workflow_executions',       # Child of agent_actions
        'cvss_assessments',          # Child of agent_actions
        'mitre_technique_mappings',  # Child of agent_actions
        'nist_control_mappings',     # Child of agent_actions
        'alerts',                    # Child of agent_actions
        'smart_rules',               # Independent
        'agent_actions',             # Parent table LAST
    ]
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print(f"\n🧹 Clearing demo data...")
        print("=" * 60)
        
        # Start transaction
        conn.autocommit = False
        
        total_deleted = 0
        
        for table in clear_order:
            try:
                # Check if table exists
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """)
                
                if not cur.fetchone()[0]:
                    print(f"⚠️  Table '{table}' does not exist, skipping...")
                    continue
                
                # Get count before deletion
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count_before = cur.fetchone()[0]
                
                # Delete all records
                cur.execute(f"DELETE FROM {table};")
                deleted = cur.rowcount
                total_deleted += deleted
                
                # Reset sequence if exists
                try:
                    cur.execute(f"""
                        SELECT pg_get_serial_sequence('{table}', 'id');
                    """)
                    sequence = cur.fetchone()[0]
                    if sequence:
                        cur.execute(f"ALTER SEQUENCE {sequence} RESTART WITH 1;")
                except:
                    pass
                
                print(f"✅ Cleared '{table}': {deleted} records removed")
                
            except Exception as e:
                print(f"⚠️  Error clearing '{table}': {e}")
                conn.rollback()
                return False
        
        # Commit transaction
        conn.commit()
        
        print("=" * 60)
        print(f"✅ Successfully cleared {total_deleted} total records")
        print("⚠️  Users table preserved (admin account intact)")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OW-KAI DEMO DATA CLEARING UTILITY")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete all agent actions, rules, and alerts")
    print("✅ Your admin account will NOT be deleted")
    
    confirm = input("\n⚠️  Are you sure? Type 'DELETE ALL' to confirm: ")
    
    if confirm == 'DELETE ALL':
        success = clear_demo_data()
        if success:
            print("\n✅ Database cleared and ready for demo\n")
        else:
            print("\n❌ Clearing failed - check errors above\n")
    else:
        print("\n❌ Clearing cancelled\n")
