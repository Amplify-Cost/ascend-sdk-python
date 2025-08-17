# llm_utils.py - Enterprise Security Compliant Version
from typing import List, Dict, Optional, Any
import os
import random
import logging

# Import config first to ensure proper secret loading
from config import OPENAI_API_KEY

# Initialize OpenAI client with enterprise secret
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized with enterprise secrets")
except Exception as e:
    print(f"⚠️  OpenAI client initialization failed: {e}")
    client = None

logger = logging.getLogger(__name__)

def generate_summary(agent_id: str, action_type: str, description: str | None) -> str:
    """
    Generate security-aware summary of agent actions.
    Implements enterprise logging and fallback for compliance.
    """
    # Input validation for enterprise security
    if not agent_id or not action_type:
        logger.warning("Invalid input for summary generation")
        return "[SECURITY] Invalid agent action data provided."
    
    prompt = f"""
    Summarize the following agent action in 1-2 concise security-aware sentences.
    
    Agent ID: {agent_id}
    Action Type: {action_type}
    Description: {description or "No description provided."}
    
    Focus on security implications and risk assessment.
    """
    
    try:
        if not client:
            raise Exception("OpenAI client not available")
            
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst focused on agent behavior assessment."},
                {"role": "user", "content": prompt.strip()}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Enterprise logging for audit trail
        logger.info(f"Summary generated for agent {agent_id}, action {action_type}")
        
        return summary
        
    except Exception as e:
        logger.error(f"OpenAI summary generation failed: {e}")
        
        # Enterprise-grade fallback with security context
        risk_indicators = {
            "file_access": "HIGH",
            "network_request": "MEDIUM", 
            "system_command": "HIGH",
            "data_access": "HIGH",
            "api_call": "MEDIUM"
        }
        
        risk_level = "UNKNOWN"
        for indicator, level in risk_indicators.items():
            if indicator.lower() in action_type.lower():
                risk_level = level
                break
        
        return f"[ENTERPRISE FALLBACK] Agent '{agent_id}' performed '{action_type}' (Risk: {risk_level}). Manual security review required."

def generate_rule(agent_actions: List[Dict]) -> Dict[str, Any]:
    """
    Generate enterprise security rules based on agent behavior patterns.
    Implements SOC 2 compliant rule generation with audit trails.
    """
    if not agent_actions:
        logger.warning("No agent actions provided for rule generation")
        return {
            "rule": "No agent actions available to generate security rule.",
            "condition": {},
            "action": "none",
            "confidence": 0.0,
            "compliance_notes": "Insufficient data for rule generation"
        }
    
    # Enterprise security analysis
    action_types = [a.get("action_type", "") for a in agent_actions if a.get("action_type")]
    type_counts = {t: action_types.count(t) for t in set(action_types)}
    
    if not type_counts:
        return {
            "rule": "Invalid action data provided.",
            "condition": {},
            "action": "escalate",
            "confidence": 0.0
        }
    
    most_common_type = max(type_counts, key=type_counts.get)
    frequency = type_counts[most_common_type]
    confidence = min(frequency / len(agent_actions), 1.0)
    
    # Find representative action
    selected = None
    for a in agent_actions:
        if a.get("action_type") == most_common_type:
            selected = a
            break
    
    # Enterprise rule generation with security context
    rule_text = f"Enterprise Security Rule: If an agent performs '{most_common_type}'"
    condition = {
        "action_type": most_common_type,
        "frequency_threshold": frequency,
        "confidence_score": confidence
    }
    
    # Enhanced security conditions
    if selected and selected.get("tool_name"):
        condition["tool_name"] = selected["tool_name"]
        rule_text += f" using {selected['tool_name']}"
    
    # Risk-based action determination
    if confidence > 0.8:
        action = "auto_block"
        rule_text += ", automatically block and alert security team."
    elif confidence > 0.5:
        action = "flag_high_risk"
        rule_text += ", flag as high risk and require approval."
    else:
        action = "monitor"
        rule_text += ", increase monitoring and log for analysis."
    
    # Enterprise logging
    logger.info(f"Security rule generated with confidence {confidence:.2f}")
    
    return {
        "rule": rule_text,
        "condition": condition,
        "action": action,
        "confidence": confidence,
        "compliance_notes": f"Generated from {len(agent_actions)} agent actions with {confidence:.1%} confidence",
        "security_classification": "INTERNAL",
        "created_by": "Enterprise AI Governance System"
    }

def generate_smart_rule(agent_id: str, action_type: str, description: str) -> Dict[str, Any]:
    """
    Generate smart security rules with enterprise compliance features.
    """
    # Input validation
    if not agent_id or not action_type:
        logger.error("Invalid parameters for smart rule generation")
        return {
            "error": "Invalid input parameters",
            "compliance_status": "FAILED_VALIDATION"
        }
    
    # Enterprise rule generation
    rule_id = f"ESR-{agent_id}-{action_type}".replace(" ", "_").upper()
    
    # Risk assessment based on action type
    high_risk_actions = ["system_command", "file_delete", "network_scan", "privilege_escalation"]
    medium_risk_actions = ["file_access", "api_call", "data_query"]
    
    if any(risk in action_type.lower() for risk in high_risk_actions):
        risk_level = "HIGH"
        recommendation = "Immediate security review required. Consider blocking until approved."
    elif any(risk in action_type.lower() for risk in medium_risk_actions):
        risk_level = "MEDIUM" 
        recommendation = "Enhanced monitoring required. Log all activities."
    else:
        risk_level = "LOW"
        recommendation = "Standard monitoring sufficient."
    
    logger.info(f"Smart rule generated: {rule_id} with risk level {risk_level}")
    
    return {
        "id": rule_id,
        "agent_id": agent_id,
        "action_type": action_type,
        "description": description or "Enterprise security rule",
        "condition": f"agent_id == '{agent_id}' AND action_type == '{action_type}'",
        "action": "security_assessment",
        "risk_level": risk_level,
        "recommendation": recommendation,
        "compliance_framework": "SOC 2 Type II",
        "security_classification": "INTERNAL",
        "auto_generated": True,
        "requires_approval": risk_level in ["HIGH", "CRITICAL"]
    }

def validate_enterprise_compliance(rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate rules against enterprise compliance requirements.
    """
    compliance_checks = {
        "has_risk_assessment": "risk_level" in rule_data,
        "has_security_classification": "security_classification" in rule_data,
        "has_audit_trail": "created_by" in rule_data or "auto_generated" in rule_data,
        "has_approval_workflow": "requires_approval" in rule_data
    }
    
    passed_checks = sum(compliance_checks.values())
    compliance_score = passed_checks / len(compliance_checks)
    
    return {
        "compliance_score": compliance_score,
        "passed_checks": compliance_checks,
        "enterprise_ready": compliance_score >= 0.75,
        "recommendations": [
            check for check, passed in compliance_checks.items() if not passed
        ]
    }