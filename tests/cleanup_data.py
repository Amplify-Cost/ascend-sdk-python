#!/usr/bin/env python3
"""
OW-KAI Test Data Cleanup Script
Uses ACTUAL table names discovered by Database Agent
"""
import os
import psycopg2
from psycopg2 import sql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
PRESERVE_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@owkai.com")

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BLUE = '\033[94m'

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{RESET}")

def cleanup_database():
    """Clean test data from database"""
    print_info(f"Starting cleanup at {datetime.now()}")
    
    if not DATABASE_URL:
        print_error("DATABASE_URL not set in environment")
        return False
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print_success("Connected to database")
        
        # Tables in order (respecting foreign keys)
        cleanup_order = [
            ("rule_feedback", "DELETE FROM rule_feedback"),
            ("log_audit_trails", "DELETE FROM log_audit_trails"),
            ("audit_logs", f"DELETE FROM audit_logs WHERE user_id NOT IN (SELECT id FROM users WHERE email = '{PRESERVE_ADMIN_EMAIL}')"),
            ("pending_agent_actions", "DELETE FROM pending_agent_actions"),
            ("workflow_executions", "DELETE FROM workflow_executions"),
            ("workflow_steps", "DELETE FROM workflow_steps WHERE workflow_id NOT IN ('risk_0_49', 'risk_50_69', 'risk_70_89', 'risk_90_100')"),
            ("agent_actions", "DELETE FROM agent_actions"),
            ("alerts", "DELETE FROM alerts"),
            ("logs", f"DELETE FROM logs WHERE user_id NOT IN (SELECT id FROM users WHERE email = '{PRESERVE_ADMIN_EMAIL}')"),
            ("smart_rules", "DELETE FROM smart_rules"),
            ("rules", "DELETE FROM rules"),
            ("mcp_server_actions", "DELETE FROM mcp_server_actions"),
            ("mcp_sessions", "DELETE FROM mcp_sessions"),
            ("enterprise_policies", "DELETE FROM enterprise_policies WHERE created_by != 'system'"),
            ("integration_endpoints", "DELETE FROM integration_endpoints"),
            ("system_configurations", "DELETE FROM system_configurations WHERE key LIKE 'test_%'"),
        ]
        
        total_deleted = 0
        print_info("\nCleaning tables...")
        
        for table_name, query in cleanup_order:
            try:
                cur.execute(query)
                deleted = cur.rowcount
                total_deleted += deleted
                if deleted > 0:
                    print_success(f"  {table_name:30} → {deleted:4} rows deleted")
                else:
                    print_info(f"  {table_name:30} → no rows to delete")
            except Exception as e:
                print_warning(f"  {table_name:30} → {str(e)[:50]}")
                conn.rollback()
                continue
        
        conn.commit()
        
        print(f"\n{GREEN}{'='*60}")
        print(f"✅ CLEANUP COMPLETE")
        print(f"{'='*60}{RESET}")
        print_info(f"Total rows deleted: {total_deleted}")
        print_info(f"Admin user preserved: {PRESERVE_ADMIN_EMAIL}")
        print_info(f"System workflows preserved\n")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Cleanup failed: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"\n{BLUE}{'='*60}")
    print("OW-KAI TEST DATA CLEANUP")
    print(f"{'='*60}{RESET}\n")
    
    success = cleanup_database()
    
    if success:
        print_success("Database ready for testing! 🎉\n")
        exit(0)
    else:
        print_error("Cleanup failed\n")
        exit(1)
