#!/usr/bin/env python3
"""Clean Demo Data Setup for OW-KAI"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Enterprise test scenarios
DEMO_ACTIONS = [
    {'id': 2001, 'agent_id': 'DataAnalyzer_AI', 'tool_name': 'PandasAI', 
     'action_type': 'database_query', 'risk_level': 'low',
     'description': 'Query customer purchase history for Q4 analytics report'},
    
    {'id': 2002, 'agent_id': 'EmailBot_AI', 'tool_name': 'SendGrid',
     'action_type': 'send_email', 'risk_level': 'low',
     'description': 'Send automated welcome emails to 50 new enterprise customers'},
    
    {'id': 2003, 'agent_id': 'CodeReviewer_AI', 'tool_name': 'GitHub Actions',
     'action_type': 'code_deployment', 'risk_level': 'medium',
     'description': 'Deploy hotfix to production API gateway'},
    
    {'id': 2004, 'agent_id': 'SecurityScanner_AI', 'tool_name': 'Nessus',
     'action_type': 'firewall_modification', 'risk_level': 'high',
     'description': 'Modify production firewall rules for new microservice deployment'},
    
    {'id': 2005, 'agent_id': 'BackupManager_AI', 'tool_name': 'AWS S3',
     'action_type': 'delete_files', 'risk_level': 'high',
     'description': 'Delete production database backups older than 90 days (2.5TB)'},
    
    {'id': 2006, 'agent_id': 'PaymentProcessor_AI', 'tool_name': 'Stripe API',
     'action_type': 'financial_transaction', 'risk_level': 'high',
     'description': 'Process bulk vendor payments: 200 transactions totaling $2.5M'}
]

def main():
    print("\n" + "="*60)
    print("OW-KAI DEMO DATA SETUP")
    print("="*60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Step 1: Clean up old data (correct order!)
        print("\n🧹 Cleaning old test data...")
        cur.execute("DELETE FROM nist_control_mappings WHERE action_id BETWEEN 2001 AND 2006")
	cur.execute("DELETE FROM cvss_assessments WHERE action_id BETWEEN 2001 AND 2006")
        cur.execute("DELETE FROM agent_actions WHERE id BETWEEN 2001 AND 2006")
        
        # Step 2: Insert fresh demo data
        print("\n📝 Creating demo scenarios...")
        for action in DEMO_ACTIONS:
            cur.execute("""
                INSERT INTO agent_actions (
                    id, agent_id, tool_name, action_type, 
                    description, risk_level, status, approved
                ) VALUES (%s, %s, %s, %s, %s, %s, 'pending', false)
            """, (action['id'], action['agent_id'], action['tool_name'],
                  action['action_type'], action['description'], action['risk_level']))
            
            emoji = "🟢" if action['risk_level'] == 'low' else "🟡" if action['risk_level'] == 'medium' else "🔴"
            print(f"  {emoji} {action['agent_id']}: {action['action_type']}")
        
        conn.commit()
        
        # Step 3: Verify
        cur.execute("SELECT COUNT(*) FROM agent_actions WHERE status = 'pending'")
        total = cur.fetchone()[0]
        
        print(f"\n✅ SUCCESS! Created {len(DEMO_ACTIONS)} demo actions")
        print(f"📊 Total pending actions: {total}")
        print("\n" + "="*60)
        print("🎯 READY FOR DEMO!")
        print("="*60)
        print("\nNext: Open https://pilot.owkai.app")
        print("Go to Authorization Center to see your demo data\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
