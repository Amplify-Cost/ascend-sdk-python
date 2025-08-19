# security_mappings.py

MITRE_MAP = {
    "data_exfiltration": {"tactic": "Exfiltration", "technique": "T1041"},
    "privilege_escalation": {"tactic": "Privilege Escalation", "technique": "T1068"},
    "unauthorized_api_call": {"tactic": "Command and Control", "technique": "T1071"},
}

NIST_MAP = {
    "data_exfiltration": {
        "control": "PR.DS-5",
        "description": "Protect against unauthorized data exfiltration."
    },
    "privilege_escalation": {
        "control": "PR.AC-4",
        "description": "Access permissions should be managed to enforce least privilege."
    },
    "unauthorized_api_call": {
        "control": "DE.CM-7",
        "description": "Monitor for unauthorized system activity."
    },
}

RECOMMENDATIONS = {
    "data_exfiltration": "Enable outbound data flow monitoring and alerts.",
    "privilege_escalation": "Review IAM role assignments regularly.",
    "unauthorized_api_call": "Add API Gateway throttling and strict auth."
}

RISK_LEVELS = {
    "data_exfiltration": "high",
    "privilege_escalation": "high",
    "unauthorized_api_call": "medium",
}
