# risk_engine.py
def evaluate_risk(agent_action: dict) -> dict:
    action_type = agent_action.get("action_type", "").lower()

    # Example rules (can expand)
    if "delete" in action_type or "disable" in action_type:
        risk_level = "High"
        nist = "AC-6"
        mitre = "TA0001"
        technique = "T1078"
        recommendation = "Alert security team, verify the user intent."
    elif "update" in action_type:
        risk_level = "Medium"
        nist = "CM-5"
        mitre = "TA0002"
        technique = "T1059"
        recommendation = "Log this activity and notify the admin for review."
    else:
        risk_level = "Low"
        nist = "AU-6"
        mitre = "TA0003"
        technique = "T1203"
        recommendation = "Monitor for repeated activity or anomalies."

    return {
        "risk_level": risk_level,
        "nist_control": nist,
        "nist_description": "Refer to NIST 800-53 for details",
        "mitre_tactic": mitre,
        "mitre_technique": technique,
        "recommended_action": recommendation
    }

def evaluate_agent_action(action_type, description, tool_name):
    # Fallback enrichment logic for individual agent actions
    enrichment = {
        "risk_level": "low",
        "nist_control": "AU-6",
        "nist_description": "Refer to NIST 800-53 for details",
        "mitre_tactic": "TA0003",
        "mitre_technique": "T1203",
        "recommended_action": "Monitor for repeated activity or anomalies."
    }

    if "delete" in action_type.lower() or "exfiltrate" in description.lower():
        enrichment["risk_level"] = "high"
        enrichment["nist_control"] = "SI-4"
        enrichment["nist_description"] = "Information System Monitoring"
        enrichment["mitre_tactic"] = "TA0010"
        enrichment["mitre_technique"] = "T1048"
        enrichment["recommended_action"] = "Investigate user behavior and limit access"
    elif "update" in action_type.lower():
        enrichment["risk_level"] = "medium"
        enrichment["nist_control"] = "CM-5"
        enrichment["nist_description"] = "Access Restrictions for Change"
        enrichment["mitre_tactic"] = "TA0002"
        enrichment["mitre_technique"] = "T1059"
        enrichment["recommended_action"] = "Log and notify for admin review"

    return enrichment
