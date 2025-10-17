#!/usr/bin/env python3
"""Populate OW-KAI with Enterprise Test Data via Database"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Enterprise test scenarios with different risk levels
ENTERPRISE_ACTIONS = [
    {
        'id': 2001,
        'agent_id': 'DataAnalyzer_AI',
        'tool_name': 'PandasAI',
        'action_type': 'database_query',
        'description': 'Query customer purchase history for Q4 analytics report',
        'risk_level': 'low',
        'status': 'pending',
        'approved': False
    },
    {
        'id': 2002,
        'agent_id': 'EmailBot_AI',
        'tool_name': 'SendGrid',
        'action_type': 'send_email',
        'description': 'Send automated welcome emails to 50 new enterprise customers',
        'risk_level': 'low',
        'status': 'pending',
        'approved': False
    },
    {
        'id': 2003,
        'agent_id': 'CodeReviewer_AI',
        'tool_name': 'GitHub Actions',
        'action_type': 'code_deployment',
        'description': 'Deploy hotfix to production API gateway',
        'risk_level': 'medium',
        'status': 'pending',
        'approved': False
    },
    {
        'id': 2004,
        'agent_id': 'SecurityScanner_AI',
        'tool_name': 'Nessus',
        'action_type': 'firewall_modification',
        'description': 'Modify production firewall rules for new microservice deployment',
        'risk_level': 'high',
        'status': 'pending',
        'approved': False
    },
    {
        'id': 2005,
        'agent_id': 'BackupManager_AI',
        'tool_name': 'AWS S3',
        'action_type': 'delete_files',
        'description': 'Delete production database backups older than 90 days (2.5TB)',
        'risk_level': 'high',
        'status': 'pending',
        'approved': False
    },
    {
        'id': 2006,
        'agent_id': 'PaymentProcessor_AI',
        'tool_name': 'Stripe API',
        'action_type': 'financial_transaction',
        'description': 'Process bulk vendor payments: 200 transactions totaling $2.5M',
        'risk_level': 'high',
        'status': 'pending',
        'approved': False
    }
]

def main():
    print("\n" + "="*60)
    print("OW-KAI ENTERPRISE TEST DATA SETUP")
    print("="*60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if actions already exist
        cur.execute("SELECT COUNT(*) FROM agent_actions WHERE id BETWEEN 2001 AND 2006")
        existing = cur.fetchone()[0]
        
        if existing > 0:
            print(f"\n⚠️  Found {existing} existing test actions (IDs 2001-2006)")
            print("Deleting and recreating...")
            cur.execute("DELETE FROM agent_actions WHERE id BETWEEN 2001 AND 2006")
        
        # Insert new enterprise test actions
        print("\n📝 Creating enterprise test scenarios...")
        for action in ENTERPRISE_ACTIONS:
            cur.execute("""
                INSERT INTO agent_actions (
                    id, agent_id, tool_name, action_type, description, 
                    risk_level, status, approved
                ) VALUES (
                    %(id)s, %(agent_id)s, %(tool_name)s, %(action_type)s, 
                    %(description)s, %(risk_level)s, %(status)s, %(approved)s
                )
            """, action)
            
            risk_emoji = "🟢" if action['risk_level'] == 'low' else "🟡" if action['risk_level'] == 'medium' else "🔴"
            print(f"  {risk_emoji} {action['agent_id']}: {action['action_type']} ({action['risk_level']})")
        
        conn.commit()
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM agent_actions WHERE status = 'pending'")
        total = cur.fetchone()[0]
        
        print(f"\n✅ SUCCESS! Created {len(ENTERPRISE_ACTIONS)} enterprise test actions")
        print(f"📊 Total pending actions in system: {total}")
        print("\n" + "="*60)
        print("🎯 NEXT STEPS:")
        print("="*60)
        print("1. Open: https://pilot.owkai.app")
        print("2. Go to: Authorization Center")
        print("3. You should see 9 total actions (3 old + 6 new)")
        print("4. Test the workflow:")
        print("   • View action details")
        print("   • Approve low-risk actions")
        print("   • Review high-risk actions")
        print("   • Test rejection workflow")
        print("="*60 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
