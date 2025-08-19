# enrichment.py - Create this file in your backend root directory

def evaluate_action_enrichment(action_type: str, description: str) -> dict:
    """Evaluate and enrich agent actions with security metadata"""
    
    # Convert to lowercase for case-insensitive matching
    action_lower = action_type.lower()
    desc_lower = (description or "").lower()
    
    # High-risk patterns
    high_risk_patterns = [
        "data_exfiltration", "exfiltrate", "leak", "steal", "copy_sensitive",
        "privilege_escalation", "escalate", "admin", "root", "sudo",
        "lateral_movement", "persistence", "backdoor", "malware"
    ]
    
    # Medium-risk patterns  
    medium_risk_patterns = [
        "network_scan", "port_scan", "reconnaissance", "discovery",
        "credential_access", "password", "token", "key",
        "execution", "command", "script", "shell"
    ]
    
    # Check for high-risk indicators
    if any(pattern in action_lower or pattern in desc_lower for pattern in high_risk_patterns):
        if "exfiltrat" in action_lower or "leak" in desc_lower:
            return {
                "risk_level": "high",
                "mitre_tactic": "Exfiltration",
                "mitre_technique": "T1041 - Exfiltration Over C2 Channel",
                "nist_control": "SI-4",
                "nist_description": "Information System Monitoring",
                "recommendation": "Immediately investigate potential data exfiltration and block unauthorized data transfers."
            }
        elif "privilege" in action_lower or "escalat" in desc_lower:
            return {
                "risk_level": "high", 
                "mitre_tactic": "Privilege Escalation",
                "mitre_technique": "T1068 - Exploitation for Privilege Escalation",
                "nist_control": "AC-6",
                "nist_description": "Least Privilege",
                "recommendation": "Review user permissions and investigate unauthorized privilege escalation attempts."
            }
        else:
            return {
                "risk_level": "high",
                "mitre_tactic": "Impact",
                "mitre_technique": "T1485 - Data Destruction",
                "nist_control": "SI-4", 
                "nist_description": "Information System Monitoring",
                "recommendation": "Investigate high-risk activity and implement additional security controls."
            }
    
    # Check for medium-risk indicators
    elif any(pattern in action_lower or pattern in desc_lower for pattern in medium_risk_patterns):
        if "network" in action_lower or "scan" in desc_lower:
            return {
                "risk_level": "medium",
                "mitre_tactic": "Discovery", 
                "mitre_technique": "T1046 - Network Service Scanning",
                "nist_control": "SI-4",
                "nist_description": "Information System Monitoring",
                "recommendation": "Monitor network scanning activities and ensure they are authorized."
            }
        elif "credential" in action_lower or "password" in desc_lower:
            return {
                "risk_level": "medium",
                "mitre_tactic": "Credential Access",
                "mitre_technique": "T1110 - Brute Force", 
                "nist_control": "IA-5",
                "nist_description": "Authenticator Management",
                "recommendation": "Review credential access patterns and strengthen authentication mechanisms."
            }
        else:
            return {
                "risk_level": "medium",
                "mitre_tactic": "Execution",
                "mitre_technique": "T1059 - Command and Scripting Interpreter",
                "nist_control": "SI-3",
                "nist_description": "Malicious Code Protection", 
                "recommendation": "Monitor execution activities and validate legitimacy of commands."
            }
    
    # Default to low risk
    else:
        return {
            "risk_level": "low",
            "mitre_tactic": "Execution",
            "mitre_technique": "T1204 - User Execution",
            "nist_control": "AU-6", 
            "nist_description": "Audit Review, Analysis, and Reporting",
            "recommendation": "Continue monitoring agent activities and maintain audit logs."
        }
    