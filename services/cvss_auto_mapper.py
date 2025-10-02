"""
CVSS Auto-Mapper Service
Automatically assigns CVSS metrics based on agent action characteristics
"""
import logging
from typing import Dict
from sqlalchemy.orm import Session
from services.cvss_calculator import cvss_calculator

logger = logging.getLogger(__name__)


class CVSSAutoMapper:
    """
    Automatically maps agent actions to CVSS v3.1 metrics
    Based on action type, resource, and context
    """
    
    # Action type to CVSS metric mappings
    ACTION_MAPPINGS = {
        # Data exfiltration - high confidentiality impact
        "data_exfiltration": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        
        # Database write - high integrity impact
        "database_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        
        # System modification - all impacts
        "system_modification": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        
        # File read - low confidentiality impact
        "file_read": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        
        # API call - medium risk
        "api_call": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        }
    }
    
    def auto_assess_action(
        self,
        db: Session,
        action_id: int,
        action_type: str,
        context: Dict = None
    ) -> Dict:
        """
        Automatically create CVSS assessment for an agent action
        """
        # Normalize action type
        normalized_type = self._normalize_action_type(action_type)
        
        # Get base metrics for this action type
        base_metrics = self.ACTION_MAPPINGS.get(
            normalized_type,
            self._get_default_metrics()
        )
        
        # Adjust metrics based on context
        adjusted_metrics = self._adjust_for_context(base_metrics, context or {})
        
        # Calculate and store CVSS assessment
        result = cvss_calculator.assess_agent_action(
            db=db,
            action_id=action_id,
            metrics=adjusted_metrics,
            assessed_by="auto_mapper"
        )
        
        logger.info(
            f"Auto-assessed action {action_id} ({normalized_type}): "
            f"CVSS {result['base_score']} ({result['severity']})"
        )
        
        return result
    
    def _normalize_action_type(self, action_type: str) -> str:
        """Normalize action type to standard categories"""
        action_lower = action_type.lower()
        
        if any(x in action_lower for x in ["exfil", "export", "download", "copy"]):
            return "data_exfiltration"
        elif any(x in action_lower for x in ["write", "update", "modify", "database"]):
            return "database_write"
        elif any(x in action_lower for x in ["system", "admin", "config", "root"]):
            return "system_modification"
        elif any(x in action_lower for x in ["read", "view", "list", "get"]):
            return "file_read"
        else:
            return "api_call"
    
    def _get_default_metrics(self) -> Dict[str, str]:
        """Default metrics for unknown action types"""
        return {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "LOW"
        }
    
    def _adjust_for_context(self, metrics: Dict[str, str], context: Dict) -> Dict[str, str]:
        """Adjust CVSS metrics based on action context"""
        adjusted = metrics.copy()
        
        # Production environment = higher impact
        if context.get("environment") == "production":
            if adjusted["confidentiality_impact"] == "LOW":
                adjusted["confidentiality_impact"] = "HIGH"
            if adjusted["integrity_impact"] == "LOW":
                adjusted["integrity_impact"] = "HIGH"
        
        # PII data = changed scope + high confidentiality
        if context.get("contains_pii"):
            adjusted["scope"] = "CHANGED"
            adjusted["confidentiality_impact"] = "HIGH"
        
        # Public resource = network attack vector
        if context.get("public_facing"):
            adjusted["attack_vector"] = "NETWORK"
            adjusted["privileges_required"] = "NONE"
        
        # Requires admin = high privileges
        if context.get("requires_admin"):
            adjusted["privileges_required"] = "HIGH"
        
        return adjusted


# Singleton instance
cvss_auto_mapper = CVSSAutoMapper()
