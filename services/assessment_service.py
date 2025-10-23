"""
Assessment Service
Centralizes all security assessment logic (CVSS, MITRE, NIST)
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Optional
from datetime import datetime
import json

from core.logging import logger


class AssessmentService:
    """Enterprise assessment service for security evaluations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def assess_action(self, action_id: int, action_data: Dict) -> Dict:
        """Run complete security assessment"""
        results = {
            "action_id": action_id,
            "cvss": None,
            "mitre": None,
            "nist": None,
            "risk_level": "medium",
            "risk_score": 50
        }
        
        try:
            cvss = self._calculate_cvss(action_data)
            if cvss:
                results["cvss"] = cvss
                results["risk_score"] = min(int(cvss.get("base_score", 5.0) * 10), 100)
            
            results["mitre"] = self._map_mitre(action_data)
            results["nist"] = self._map_nist(action_data)
            results["risk_level"] = self._calculate_risk_level(results["risk_score"])
            
        except Exception as e:
            logger.error(f"Assessment failed: {e}")
        
        return results
    
    def _calculate_cvss(self, data: Dict) -> Optional[Dict]:
        """Calculate CVSS score"""
        action_type = data.get("action_type", "").lower()
        base_score = 5.0
        
        if any(x in action_type for x in ["delete", "modify", "execute"]):
            base_score += 2.0
        
        return {
            "base_score": min(base_score, 10.0),
            "severity": self._cvss_severity(base_score)
        }
    
    def _cvss_severity(self, score: float) -> str:
        """Map score to severity"""
        if score < 4.0:
            return "Low"
        elif score < 7.0:
            return "Medium"
        elif score < 9.0:
            return "High"
        return "Critical"
    
    def _map_mitre(self, data: Dict) -> Optional[Dict]:
        """Map to MITRE ATT&CK"""
        return {"techniques": ["T1078"], "tactics": ["Initial Access"]}
    
    def _map_nist(self, data: Dict) -> Optional[Dict]:
        """Map to NIST CSF"""
        return {"categories": ["Protect"], "subcategories": ["PR.AC"]}
    
    def _calculate_risk_level(self, score: float) -> str:
        """Calculate risk level"""
        if score < 30:
            return "low"
        elif score < 50:
            return "medium"
        elif score < 70:
            return "high"
        return "critical"


def get_assessment_service(db: Session):
    return AssessmentService(db)
