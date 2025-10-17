"""
MCP Data Population Service
Generates realistic MCP actions for dashboard demonstration
"""

import asyncio
import json
from datetime import datetime, UTC, timedelta
import uuid
import random

# Sample realistic MCP actions for enterprise demo
SAMPLE_ACTIONS = [
    {
        "agent_id": "security-scanner-01",
        "action_type": "file_read",
        "resource": "/logs/security.log",
        "risk_score": 25,
        "status": "approved",
        "timestamp": datetime.now(UTC) - timedelta(minutes=5)
    },
    {
        "agent_id": "vulnerability-scanner",
        "action_type": "network_scan", 
        "resource": "192.168.1.0/24",
        "risk_score": 45,
        "status": "pending",
        "timestamp": datetime.now(UTC) - timedelta(minutes=2)
    },
    {
        "agent_id": "database-maintenance",
        "action_type": "database_query",
        "resource": "SELECT * FROM user_activity",
        "risk_score": 35,
        "status": "approved", 
        "timestamp": datetime.now(UTC) - timedelta(minutes=8)
    },
    {
        "agent_id": "file-analyzer-03",
        "action_type": "file_delete",
        "resource": "/tmp/suspicious_file.exe",
        "risk_score": 70,
        "status": "requires_approval",
        "timestamp": datetime.now(UTC) - timedelta(minutes=1)
    },
    {
        "agent_id": "network-monitor", 
        "action_type": "network_request",
        "resource": "https://api.threat-intel.com/check",
        "risk_score": 40,
        "status": "approved",
        "timestamp": datetime.now(UTC) - timedelta(minutes=12)
    }
]

def generate_mcp_actions():
    """Generate realistic MCP actions for dashboard"""
    actions = []
    
    for i, sample in enumerate(SAMPLE_ACTIONS):
        action = {
            "id": str(uuid.uuid4()),
            "action_id": f"action_{i+1:03d}",
            "agent_id": sample["agent_id"],
            "action_type": sample["action_type"],
            "resource": sample["resource"],
            "risk_score": sample["risk_score"],
            "status": sample["status"],
            "timestamp": sample["timestamp"].isoformat(),
            "enterprise_risk_assessment": {
                "risk_score": sample["risk_score"],
                "methodology": "CVSS v3.1 + NIST 800-30 + MITRE ATT&CK",
                "framework_version": "enterprise_v1.0",
                "cvss_base_score": 5.0,
                "nist_risk_level": "MODERATE" if sample["risk_score"] < 50 else "HIGH",
                "mitre_tactic_id": "T1005",
                "compliance_frameworks": ["SOC2", "NIST CSF", "ISO 27001"]
            },
            "requires_approval": sample["risk_score"] > 60,
            "metadata": {
                "source": "enterprise_demo",
                "environment": "production"
            }
        }
        actions.append(action)
    
    return actions

if __name__ == "__main__":
    actions = generate_mcp_actions()
    print(f"Generated {len(actions)} MCP actions")
    for action in actions:
        print(f"- {action['agent_id']}: {action['action_type']} (risk: {action['risk_score']})")
