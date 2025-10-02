"""
CVSS v3.1 Calculator Service
Official CVSS base score calculation following NIST specification
"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

logger = logging.getLogger(__name__)


class CVSSCalculator:
    """
    CVSS v3.1 Base Score Calculator
    Implements official CVSS v3.1 specification from FIRST.org
    """
    
    # Metric value mappings to numeric weights
    ATTACK_VECTOR = {"NETWORK": 0.85, "ADJACENT": 0.62, "LOCAL": 0.55, "PHYSICAL": 0.2}
    ATTACK_COMPLEXITY = {"LOW": 0.77, "HIGH": 0.44}
    PRIVILEGES_REQUIRED = {
        "NONE": {"UNCHANGED": 0.85, "CHANGED": 0.85},
        "LOW": {"UNCHANGED": 0.62, "CHANGED": 0.68},
        "HIGH": {"UNCHANGED": 0.27, "CHANGED": 0.50}
    }
    USER_INTERACTION = {"NONE": 0.85, "REQUIRED": 0.62}
    SCOPE = {"UNCHANGED": 0, "CHANGED": 1}
    IMPACT = {"NONE": 0, "LOW": 0.22, "HIGH": 0.56}
    
    def calculate_base_score(self, metrics: Dict[str, str]) -> Dict:
        """
        Calculate CVSS v3.1 base score from metrics
        
        Args:
            metrics: Dict with keys: attack_vector, attack_complexity,
                    privileges_required, user_interaction, scope,
                    confidentiality_impact, integrity_impact, availability_impact
        
        Returns:
            Dict with base_score, severity, and vector_string
        """
        try:
            # Extract and validate metrics
            av = metrics["attack_vector"].upper()
            ac = metrics["attack_complexity"].upper()
            pr = metrics["privileges_required"].upper()
            ui = metrics["user_interaction"].upper()
            s = metrics["scope"].upper()
            c = metrics["confidentiality_impact"].upper()
            i = metrics["integrity_impact"].upper()
            a = metrics["availability_impact"].upper()
            
            # Calculate exploitability
            pr_value = self.PRIVILEGES_REQUIRED[pr][s]
            exploitability = (
                8.22 * 
                self.ATTACK_VECTOR[av] * 
                self.ATTACK_COMPLEXITY[ac] * 
                pr_value * 
                self.USER_INTERACTION[ui]
            )
            
            # Calculate impact
            isc_base = 1 - (
                (1 - self.IMPACT[c]) * 
                (1 - self.IMPACT[i]) * 
                (1 - self.IMPACT[a])
            )
            
            if s == "UNCHANGED":
                impact = 6.42 * isc_base
            else:
                impact = 7.52 * (isc_base - 0.029) - 3.25 * pow(isc_base - 0.02, 15)
            
            # Calculate base score
            if impact <= 0:
                base_score = 0.0
            elif s == "UNCHANGED":
                base_score = min(impact + exploitability, 10.0)
            else:
                base_score = min(1.08 * (impact + exploitability), 10.0)
            
            # Round up to 1 decimal
            base_score = self._round_up(base_score)
            
            # Determine severity
            severity = self._get_severity(base_score)
            
            # Generate vector string
            vector_string = self._generate_vector_string(metrics)
            
            return {
                "base_score": base_score,
                "severity": severity,
                "vector_string": vector_string,
                "exploitability": round(exploitability, 1),
                "impact": round(impact, 1)
            }
            
        except Exception as e:
            logger.error(f"CVSS calculation error: {e}")
            raise ValueError(f"Invalid CVSS metrics: {e}")
    
    def _round_up(self, score: float) -> float:
        """Round up to 1 decimal place (CVSS specification)"""
        return round(score + 0.05, 1) if score > 0 else 0.0
    
    def _get_severity(self, score: float) -> str:
        """Map score to severity rating"""
        if score == 0.0:
            return "NONE"
        elif score < 4.0:
            return "LOW"
        elif score < 7.0:
            return "MEDIUM"
        elif score < 9.0:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _generate_vector_string(self, metrics: Dict[str, str]) -> str:
        """Generate CVSS v3.1 vector string"""
        abbrev = {
            "attack_vector": "AV",
            "attack_complexity": "AC",
            "privileges_required": "PR",
            "user_interaction": "UI",
            "scope": "S",
            "confidentiality_impact": "C",
            "integrity_impact": "I",
            "availability_impact": "A"
        }
        
        value_abbrev = {
            "NETWORK": "N", "ADJACENT": "A", "LOCAL": "L", "PHYSICAL": "P",
            "LOW": "L", "HIGH": "H",
            "NONE": "N", "REQUIRED": "R",
            "UNCHANGED": "U", "CHANGED": "C"
        }
        
        parts = ["CVSS:3.1"]
        for key, val in metrics.items():
            if key in abbrev:
                metric_abbrev = abbrev[key]
                val_abbrev = value_abbrev.get(val.upper(), val[0].upper())
                parts.append(f"{metric_abbrev}:{val_abbrev}")
        
        return "/".join(parts)
    
    def assess_agent_action(
        self,
        db: Session,
        action_id: int,
        metrics: Dict[str, str],
        assessed_by: str = "system"
    ) -> Dict:
        """
        Create CVSS assessment for an agent action
        Stores in database and returns calculated scores
        """
        # Calculate score
        result = self.calculate_base_score(metrics)
        
        # Store in database
        query = text("""
            INSERT INTO cvss_assessments (
                action_id, attack_vector, attack_complexity,
                privileges_required, user_interaction, scope,
                confidentiality_impact, integrity_impact, availability_impact,
                base_score, severity, vector_string, assessed_by
            ) VALUES (
                :action_id, :av, :ac, :pr, :ui, :s, :c, :i, :a,
                :base_score, :severity, :vector_string, :assessed_by
            )
            RETURNING id
        """)
        
        result_row = db.execute(query, {
            "action_id": action_id,
            "av": metrics["attack_vector"].upper(),
            "ac": metrics["attack_complexity"].upper(),
            "pr": metrics["privileges_required"].upper(),
            "ui": metrics["user_interaction"].upper(),
            "s": metrics["scope"].upper(),
            "c": metrics["confidentiality_impact"].upper(),
            "i": metrics["integrity_impact"].upper(),
            "a": metrics["availability_impact"].upper(),
            "base_score": result["base_score"],
            "severity": result["severity"],
            "vector_string": result["vector_string"],
            "assessed_by": assessed_by
        }).fetchone()
        
        db.commit()
        
        assessment_id = result_row[0]
        result["assessment_id"] = assessment_id
        
        logger.info(
            f"Created CVSS assessment {assessment_id} for action {action_id}: "
            f"Score {result['base_score']} ({result['severity']})"
        )
        
        return result


# Singleton instance
cvss_calculator = CVSSCalculator()
