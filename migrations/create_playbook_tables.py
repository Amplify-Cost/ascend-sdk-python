"""
🏢 ENTERPRISE MIGRATION: Automation Playbooks System
Create tables using SQLAlchemy ORM (enterprise approach)
Author: Enterprise Security Team
Date: 2025-10-22
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime, timedelta

# Load environment
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found!")
    sys.exit(1)

def create_playbook_tables():
    """Create automation playbook tables"""
    
    print("🏢 ENTERPRISE MIGRATION: Automation Playbooks System")
    print("=" * 70)
    
    db_host = DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else 'unknown'
    db_name = DATABASE_URL.split('/')[-1] if '/' in DATABASE_URL else 'unknown'
    print(f"📍 Target: {db_host}/{db_name}")
    print("")
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user"))
            db, user = result.fetchone()
            print(f"✅ Connected: database='{db}' user='{user}'")
            print("")
        
        metadata = MetaData()
        
        print("🔄 Creating tables...")
        print("")
        
        # Table 1: automation_playbooks
        automation_playbooks = Table(
            'automation_playbooks',
            metadata,
            Column('id', String(255), primary_key=True),
            Column('name', String(255), nullable=False, index=True),
            Column('description', Text),
            Column('status', String(50), default='active', nullable=False, index=True),
            Column('risk_level', String(50), default='medium', nullable=False, index=True),
            Column('approval_required', Boolean, default=False),
            Column('trigger_conditions', JSONB),
            Column('actions', JSONB),
            Column('last_executed', DateTime),
            Column('execution_count', Integer, default=0),
            Column('success_rate', Float, default=0.0),
            Column('created_by', Integer, ForeignKey('users.id', ondelete='SET NULL')),
            Column('created_at', DateTime, default=func.now(), nullable=False, index=True),
            Column('updated_by', Integer, ForeignKey('users.id', ondelete='SET NULL')),
            Column('updated_at', DateTime, default=func.now(), onupdate=func.now(), nullable=False),
            CheckConstraint("status IN ('active', 'inactive', 'disabled', 'maintenance')", name='valid_status'),
            CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", name='valid_risk_level'),
            CheckConstraint("success_rate >= 0 AND success_rate <= 100", name='valid_success_rate')
        )
        
        # Table 2: playbook_executions
        playbook_executions = Table(
            'playbook_executions',
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('playbook_id', String(255), ForeignKey('automation_playbooks.id', ondelete='CASCADE'), nullable=False, index=True),
            Column('executed_by', Integer, ForeignKey('users.id', ondelete='SET NULL')),
            Column('execution_context', String(50), default='manual'),
            Column('input_data', JSONB),
            Column('execution_status', String(50), nullable=False, index=True),
            Column('execution_details', JSONB),
            Column('error_message', Text),
            Column('started_at', DateTime, default=func.now(), nullable=False, index=True),
            Column('completed_at', DateTime),
            Column('duration_seconds', Integer),
            CheckConstraint("execution_status IN ('pending', 'running', 'completed', 'failed', 'cancelled')", name='valid_execution_status'),
            CheckConstraint("execution_context IN ('manual', 'automatic', 'scheduled', 'trigger')", name='valid_execution_context')
        )
        
        # Create tables
        metadata.create_all(engine, checkfirst=True)
        print("  ✅ automation_playbooks table created")
        print("  ✅ playbook_executions table created")
        print("")
        
        # Insert seed data
        print("🌱 Inserting seed data...")
        with engine.begin() as conn:
            # Check if admin user exists
            admin_result = conn.execute(text("SELECT id FROM users WHERE email = 'admin@owkai.com' LIMIT 1"))
            admin_user = admin_result.fetchone()
            admin_id = admin_user[0] if admin_user else None
            
            # Insert demo playbook
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
                ON CONFLICT (id) DO NOTHING
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
        
        print("")
        print("=" * 70)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY")
        print("")
        
        # Verify
        print("🔍 Verification:")
        with engine.connect() as conn:
            for table_name in ['automation_playbooks', 'playbook_executions']:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"  ✅ {table_name}: {count} rows")
        
        print("")
        print("=" * 70)
        return True
        
    except Exception as e:
        print("")
        print("=" * 70)
        print(f"❌ MIGRATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = create_playbook_tables()
    sys.exit(0 if success else 1)
