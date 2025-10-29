"""
Workflow Configuration
Shared configuration for authorization workflows
"""

workflow_config = {
    "risk_90_100": {
        "name": "Critical Risk (90-100)",
        "approval_levels": 3,
        "approvers": ["security@company.com", "senior@company.com", "executive@company.com"],
        "timeout_hours": 2,
        "emergency_override": True,
        "escalation_minutes": 30
    },
    "risk_70_89": {
        "name": "High Risk (70-89)", 
        "approval_levels": 2,
        "approvers": ["security@company.com", "senior@company.com"],
        "timeout_hours": 4,
        "emergency_override": False,
        "escalation_minutes": 60
    },
    "risk_50_69": {
        "name": "Medium Risk (50-69)",
        "approval_levels": 2,
        "approvers": ["security@company.com", "security2@company.com"],
        "timeout_hours": 8,
        "emergency_override": False,
        "escalation_minutes": 120
    },
    "risk_0_49": {
        "name": "Low Risk (0-49)",
        "approval_levels": 1,
        "approvers": ["security@company.com"],
        "timeout_hours": 24,
        "emergency_override": False,
        "escalation_minutes": 480
    }
}
