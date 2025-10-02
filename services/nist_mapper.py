"""
NIST Control Mapper Service
Automatically maps agent actions to relevant NIST SP 800-53 controls
"""
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class NISTMapper:
    """
    Maps agent actions to NIST SP 800-53 controls based on action characteristics
    """
    
    # Action type to NIST control mappings
    ACTION_TO_CONTROLS = {
        "data_exfiltration": [
            ("SC-8", "PRIMARY"),   # Transmission Confidentiality
            ("SC-28", "PRIMARY"),  # Protection of Information at Rest
            ("AC-4", "SECONDARY"), # Information Flow Enforcement
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        "database_write": [
            ("SI-7", "PRIMARY"),   # Software and Information Integrity
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("AU-2", "SECONDARY"), # Event Logging
            ("CM-3", "SUPPORTING") # Configuration Change Control
        ],
        "database_access": [
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("AC-6", "PRIMARY"),   # Least Privilege
            ("AU-2", "SECONDARY"), # Event Logging
            ("IA-2", "SUPPORTING") # User Identification and Authentication
        ],
        "system_modification": [
            ("CM-3", "PRIMARY"),   # Configuration Change Control
            ("AC-5", "PRIMARY"),   # Separation of Duties
            ("CM-6", "SECONDARY"), # Configuration Settings
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        "file_access": [
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("MP-2", "SECONDARY"), # Media Access
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        "authentication": [
            ("IA-2", "PRIMARY"),   # User Identification and Authentication
            ("IA-5", "PRIMARY"),   # Authenticator Management
            ("AC-2", "SECONDARY"), # Account Management
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        "network_access": [
            ("SC-7", "PRIMARY"),   # Boundary Protection
            ("AC-17", "PRIMARY"),  # Remote Access
            ("AC-3", "SECONDARY"), # Access Enforcement
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        "vulnerability_scan": [
            ("RA-5", "PRIMARY"),   # Vulnerability Monitoring and Scanning
            ("SI-2", "SECONDARY"), # Flaw Remediation
            ("CA-7", "SUPPORTING") # Continuous Monitoring
        ],
        "incident_detection": [
            ("SI-4", "PRIMARY"),   # System Monitoring
            ("IR-4", "SECONDARY"), # Incident Handling
            ("IR-5", "SUPPORTING") # Incident Monitoring
        ]
    }
    
    def map_action_to_controls(
        self,
        db: Session,
        action_id: int,
        action_type: str,
        auto_assess: bool = True
    ) -> List[Dict]:
        """
        Map an agent action to relevant NIST controls
        
        Args:
            action_id: Agent action ID
            action_type: Type of action
            auto_assess: Automatically create mappings in database
        
        Returns:
            List of control mappings with relevance
        """
        # Normalize action type
        normalized = self._normalize_action_type(action_type)
        
        # Get control mappings
        control_mappings = self.ACTION_TO_CONTROLS.get(
            normalized,
            [("AU-2", "PRIMARY")]  # Default: at least log it
        )
        
        results = []
        for control_id, relevance in control_mappings:
            # Get control details
            control = self._get_control_details(db, control_id)
            if not control:
                logger.warning(f"Control {control_id} not found in database")
                continue
            
            mapping = {
                "control_id": control_id,
                "family": control["family"],
                "title": control["title"],
                "relevance": relevance,
                "baseline_impact": control["baseline_impact"]
            }
            
            # Store in database if requested
            if auto_assess:
                self._create_mapping(db, action_id, control_id, relevance)
            
            results.append(mapping)
        
        logger.info(
            f"Mapped action {action_id} ({normalized}) to {len(results)} NIST controls"
        )
        
        return results
    
    def _normalize_action_type(self, action_type: str) -> str:
        """Normalize action type to standard categories"""
        action_lower = action_type.lower()
        
        if any(x in action_lower for x in ["exfil", "export", "download", "copy"]):
            return "data_exfiltration"
        elif "database" in action_lower and any(x in action_lower for x in ["write", "update", "modify"]):
            return "database_write"
        elif "database" in action_lower or "sql" in action_lower:
            return "database_access"
        elif any(x in action_lower for x in ["system", "config", "admin"]):
            return "system_modification"
        elif any(x in action_lower for x in ["file", "read", "access"]):
            return "file_access"
        elif any(x in action_lower for x in ["auth", "login", "credential"]):
            return "authentication"
        elif any(x in action_lower for x in ["network", "remote", "ssh", "rdp"]):
            return "network_access"
        elif any(x in action_lower for x in ["scan", "vulnerability", "vuln"]):
            return "vulnerability_scan"
        elif any(x in action_lower for x in ["incident", "alert", "detect", "monitor"]):
            return "incident_detection"
        else:
            return "file_access"  # Safe default
    
    def _get_control_details(self, db: Session, control_id: str) -> Dict:
        """Get control details from database"""
        query = text("""
            SELECT control_id, family, title, baseline_impact, priority
            FROM nist_controls
            WHERE control_id = :control_id
        """)
        
        result = db.execute(query, {"control_id": control_id}).fetchone()
        if not result:
            return None
        
        return {
            "control_id": result[0],
            "family": result[1],
            "title": result[2],
            "baseline_impact": result[3],
            "priority": result[4]
        }
    
    def _create_mapping(
        self,
        db: Session,
        action_id: int,
        control_id: str,
        relevance: str
    ):
        """Create control-to-action mapping in database"""
        # Check if mapping already exists
        check_query = text("""
            SELECT id FROM nist_control_mappings
            WHERE action_id = :action_id AND control_id = :control_id
        """)
        
        existing = db.execute(check_query, {
            "action_id": action_id,
            "control_id": control_id
        }).fetchone()
        
        if existing:
            logger.debug(f"Mapping already exists for action {action_id} -> {control_id}")
            return
        
        # Insert new mapping
        insert_query = text("""
            INSERT INTO nist_control_mappings (action_id, control_id, relevance)
            VALUES (:action_id, :control_id, :relevance)
        """)
        
        db.execute(insert_query, {
            "action_id": action_id,
            "control_id": control_id,
            "relevance": relevance
        })
        db.commit()
    
    def get_compliance_summary(self, db: Session) -> Dict:
        """Get overall NIST compliance summary"""
        query = text("""
            SELECT 
                nc.family,
                COUNT(DISTINCT nc.control_id) as total_controls,
                COUNT(DISTINCT ncm.control_id) as mapped_controls,
                COUNT(DISTINCT CASE WHEN ncm.compliance_status = 'COMPLIANT' 
                      THEN ncm.control_id END) as compliant_controls
            FROM nist_controls nc
            LEFT JOIN nist_control_mappings ncm ON nc.control_id = ncm.control_id
            GROUP BY nc.family
            ORDER BY nc.family
        """)
        
        result = db.execute(query)
        summary = []
        
        for row in result:
            family, total, mapped, compliant = row
            summary.append({
                "family": family,
                "total_controls": total,
                "mapped_controls": mapped or 0,
                "compliant_controls": compliant or 0,
                "coverage_percent": round((mapped or 0) / total * 100, 1) if total > 0 else 0
            })
        
        return summary


# Singleton instance
nist_mapper = NISTMapper()
