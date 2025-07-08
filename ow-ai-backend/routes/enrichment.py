# enrichment.py

def evaluate_action_enrichment(action_type: str, description: str) -> dict:
    if "data_exfiltration" in action_type.lower() or "leak" in description.lower():
        return {
            "risk_level": "high",
            "mitre_tactic": "Exfiltration",
            "mitre_technique": "Exfiltration Over Web Service",
            "nist_control": "SI-4",
            "nist_description": "Information System Monitoring",
            "recommendation": "Immediately investigate potential data leaks and block unauthorized exfiltration paths."
        }
    elif "prompt_injection" in description.lower():
        return {
            "risk_level": "medium",
            "mitre_tactic": "Initial Access",
            "mitre_technique": "Spear Phishing via Service",
            "nist_control": "SI-10",
            "nist_description": "Information Input Validation",
            "recommendation": "Implement strict prompt validation and use context-aware sanitization gateways."
        }
    else:
        return {
            "risk_level": "low",
            "mitre_tactic": "Execution",
            "mitre_technique": "User Execution",
            "nist_control": "AC-6",
            "nist_description": "Least Privilege",
            "recommendation": "Monitor activity and ensure agent operates under least privilege principles."
        }
