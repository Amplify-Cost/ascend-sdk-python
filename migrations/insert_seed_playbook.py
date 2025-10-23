"""
Insert seed playbook data
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

print("🌱 Inserting seed playbook data...")
print("=" * 70)

with engine.begin() as conn:
    # Get admin user ID
    admin_result = conn.execute(text("SELECT id FROM users WHERE email = 'admin@owkai.com' LIMIT 1"))
    admin_user = admin_result.fetchone()
    admin_id = admin_user[0] if admin_user else None
    print(f"  • Admin user ID: {admin_id}")
    
    # Insert with proper parameter binding (no ::jsonb casting)
    conn.execute(text("""
        INSERT INTO automation_playbooks (
            id, name, description, status, risk_level, approval_required,
            trigger_conditions, actions, last_executed, execution_count, 
            success_rate, created_by, created_at, updated_at
        ) VALUES (
            :id, :name, :description, :status, :risk_level, :approval_required,
            :trigger_conditions, :actions, :last_executed, :execution_count,
            :success_rate, :created_by, :created_at, :updated_at
        )
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            execution_count = EXCLUDED.execution_count,
            success_rate = EXCLUDED.success_rate
    """), {
        'id': 'pb-001',
        'name': 'High-Risk Action Auto-Review',
        'description': 'Automatically review and escalate high-risk agent actions',
        'status': 'active',
        'risk_level': 'high',
        'approval_required': False,
        'trigger_conditions': '{"risk_score": {"min": 80}, "action_type": ["file_access", "network_scan", "database_query"], "environment": ["production"]}',
        'actions': '[{"type": "risk_assessment", "parameters": {"deep_scan": true}}, {"type": "stakeholder_notification", "recipients": ["security-team@company.com"]}, {"type": "temporary_quarantine", "duration_minutes": 30}, {"type": "escalate_approval", "level": "L4"}]',
        'last_executed': datetime.utcnow() - timedelta(hours=2),
        'execution_count': 156,
        'success_rate': 97.4,
        'created_by': admin_id,
        'created_at': datetime.utcnow() - timedelta(days=30),
        'updated_at': datetime.utcnow() - timedelta(days=30)
    })
    
    print("  ✅ Seed playbook 'pb-001' inserted")
    
    # Verify
    result = conn.execute(text("""
        SELECT id, name, status, risk_level, execution_count, success_rate 
        FROM automation_playbooks 
        WHERE id = 'pb-001'
    """))
    pb = result.fetchone()
    if pb:
        print("")
        print("📋 Verified playbook in database:")
        print(f"  • ID: {pb[0]}")
        print(f"  • Name: {pb[1]}")
        print(f"  • Status: {pb[2]}")
        print(f"  • Risk Level: {pb[3]}")
        print(f"  • Execution Count: {pb[4]}")
        print(f"  • Success Rate: {pb[5]}%")

print("")
print("=" * 70)
print("🎉 SEED DATA INSERTION COMPLETE!")
print("=" * 70)
