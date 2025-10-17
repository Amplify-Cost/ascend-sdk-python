import os
import psycopg2
from datetime import datetime, UTC
import random

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Sample agent actions that match your schema
sample_actions = [
    {
        'agent_id': 'security-scanner-01',
        'action_type': 'file_read',
        'description': 'Reading security log files for threat analysis',
        'risk_level': 'low',
        'risk_score': 25.0,
        'status': 'pending'
    },
    {
        'agent_id': 'vulnerability-scanner',
        'action_type': 'network_scan', 
        'description': 'Scanning network infrastructure for vulnerabilities',
        'risk_level': 'medium',
        'risk_score': 45.0,
        'status': 'pending'
    },
    {
        'agent_id': 'file-analyzer-03',
        'action_type': 'file_delete',
        'description': 'Removing suspected malware file from quarantine',
        'risk_level': 'high', 
        'risk_score': 70.0,
        'status': 'pending'
    }
]

# Insert sample data
for action in sample_actions:
    cur.execute("""
        INSERT INTO agent_actions (agent_id, action_type, description, risk_level, risk_score, status, created_at, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        action['agent_id'],
        action['action_type'], 
        action['description'],
        action['risk_level'],
        action['risk_score'],
        action['status'],
        datetime.now(UTC),
        1  # admin user_id
    ))

conn.commit()
cur.close()
conn.close()
print("Sample agent actions populated successfully")
