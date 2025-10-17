"""
MITRE ATT&CK Mapper Service
Maps agent actions to MITRE ATT&CK techniques for threat intelligence
"""
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class MITREMapper:
    """
    Maps agent actions to MITRE ATT&CK techniques based on observed behavior
    """
    
    # Action patterns to MITRE technique mappings
    ACTION_TO_TECHNIQUES = {
        "credential_access": [
            ("T1110", "HIGH"),  # Brute Force
            ("T1003", "MEDIUM"), # OS Credential Dumping
        ],
        "data_exfiltration": [
            ("T1041", "HIGH"),  # Exfiltration Over C2 Channel
            ("T1567", "HIGH"),  # Exfiltration Over Web Service
            ("T1048", "MEDIUM"), # Exfiltration Over Alternative Protocol
        ],
        "lateral_movement": [
            ("T1021", "HIGH"),  # Remote Services
            ("T1570", "MEDIUM"), # Lateral Tool Transfer
        ],
        "persistence": [
            ("T1053", "HIGH"),  # Scheduled Task/Job
            ("T1136", "MEDIUM"), # Create Account
            ("T1098", "MEDIUM"), # Account Manipulation
        ],
        "privilege_escalation": [
            ("T1068", "HIGH"),  # Exploitation for Privilege Escalation
            ("T1134", "MEDIUM"), # Access Token Manipulation
        ],

        # === CURRENT SYSTEM ACTION TYPES (13) ===
        "database_query": [
            ("T1213", "HIGH"),   # Data from Information Repositories
            ("T1005", "MEDIUM"), # Data from Local System
            ("T1119", "LOW"),    # Automated Collection
        ],
        "forensic_analysis": [
            ("T1074", "HIGH"),   # Data Staged
            ("T1005", "HIGH"),   # Data from Local System
            ("T1119", "MEDIUM"), # Automated Collection
        ],
        "threat_analysis": [
            ("T1595", "HIGH"),   # Active Scanning
            ("T1046", "MEDIUM"), # Network Service Discovery
            ("T1595", "LOW"),    # Vulnerability Scanning
        ],
        "access_review": [
            ("T1078", "HIGH"),   # Valid Accounts
            ("T1087", "MEDIUM"), # Account Discovery
            ("T1069", "LOW"),    # Permission Groups Discovery
        ],
        "network_monitoring": [
            ("T1040", "HIGH"),   # Network Sniffing
            ("T1590", "MEDIUM"), # Gather Victim Network Information
            ("T1046", "LOW"),    # Network Service Discovery
        ],
        "financial_transaction": [
            ("T1565", "HIGH"),   # Data Manipulation
            ("T1491", "HIGH"),   # Defacement
            ("T1486", "MEDIUM"), # Data Encrypted for Impact
        ],
        "firewall_modification": [
            ("T1562", "HIGH"),   # Impair Defenses
            ("T1556", "MEDIUM"), # Modify Authentication Process
            ("T1599", "LOW"),    # Network Boundary Bridging
        ],
        "anomaly_detection": [
            ("T1046", "HIGH"),   # Network Service Discovery
            ("T1040", "MEDIUM"), # Network Sniffing
            ("T1082", "LOW"),    # System Information Discovery
        ],
        "code_deployment": [
            ("T1203", "HIGH"),   # Exploitation for Client Execution
            ("T1059", "HIGH"),   # Command and Scripting Interpreter
            ("T1105", "MEDIUM"), # Ingress Tool Transfer
        ],
        "compliance_check": [
            ("T1087", "MEDIUM"), # Account Discovery
            ("T1069", "MEDIUM"), # Permission Groups Discovery
            ("T1082", "LOW"),    # System Information Discovery
        ],
        "delete_files": [
            ("T1485", "HIGH"),   # Data Destruction
            ("T1070", "HIGH"),   # Indicator Removal
            ("T1565", "MEDIUM"), # Data Manipulation
        ],
        "send_email": [
            ("T1566", "HIGH"),   # Phishing
            ("T1071", "MEDIUM"), # Application Layer Protocol
            ("T1114", "LOW"),    # Email Collection
        ],
        "vulnerability_scan": [
            ("T1595", "HIGH"),   # Active Scanning
            ("T1046", "MEDIUM"), # Network Service Discovery
            ("T1590", "LOW"),    # Gather Victim Network Information
        ],
        # === COMMON ENTERPRISE ACTION TYPES (7) ===
        "api_call": [
            ("T1071", "HIGH"),   # Application Layer Protocol
            ("T1102", "MEDIUM"), # Web Service
            ("T1059", "LOW"),    # Command and Scripting Interpreter
        ],
        "file_read": [
            ("T1005", "HIGH"),   # Data from Local System
            ("T1083", "MEDIUM"), # File and Directory Discovery
            ("T1119", "LOW"),    # Automated Collection
        ],
        "file_write": [
            ("T1565", "HIGH"),   # Data Manipulation
            ("T1105", "MEDIUM"), # Ingress Tool Transfer
            ("T1027", "LOW"),    # Obfuscated Files or Information
        ],
        "authentication": [
            ("T1078", "HIGH"),   # Valid Accounts
            ("T1110", "MEDIUM"), # Brute Force
            ("T1556", "LOW"),    # Modify Authentication Process
        ],
        "backup_operation": [
            ("T1005", "HIGH"),   # Data from Local System
            ("T1074", "MEDIUM"), # Data Staged
            ("T1119", "LOW"),    # Automated Collection
        ],
        "log_analysis": [
            ("T1070", "MEDIUM"), # Indicator Removal
            ("T1083", "MEDIUM"), # File and Directory Discovery
            ("T1082", "LOW"),    # System Information Discovery
        ],
        "user_management": [
            ("T1136", "HIGH"),   # Create Account
            ("T1098", "MEDIUM"), # Account Manipulation
            ("T1087", "LOW"),    # Account Discovery
        ],

        "defense_evasion": [
            ("T1070", "HIGH"),  # Indicator Removal
            ("T1027", "MEDIUM"), # Obfuscated Files
            ("T1112", "MEDIUM"), # Modify Registry
        ],
        "discovery": [
            ("T1087", "HIGH"),  # Account Discovery
            ("T1083", "MEDIUM"), # File and Directory Discovery
            ("T1082", "LOW"),   # System Information Discovery
        ],
        "execution": [
            ("T1059", "HIGH"),  # Command and Scripting Interpreter
            ("T1203", "MEDIUM"), # Exploitation for Client Execution
        ],
        "initial_access": [
            ("T1078", "HIGH"),  # Valid Accounts
            ("T1190", "HIGH"),  # Exploit Public-Facing Application
            ("T1133", "MEDIUM"), # External Remote Services
        ],
        "collection": [
            ("T1005", "HIGH"),  # Data from Local System
            ("T1560", "MEDIUM"), # Archive Collected Data
        ],
        "impact": [
            ("T1486", "HIGH"),  # Data Encrypted for Impact
            ("T1490", "HIGH"),  # Inhibit System Recovery
            ("T1498", "MEDIUM"), # Network Denial of Service
        ]
    }
    
    def map_action_to_techniques(
        self,
        db: Session,
        action_id: int,
        action_type: str,
        context: Dict = None
    ) -> List[Dict]:
        """
        Map an agent action to MITRE ATT&CK techniques
        
        Returns list of techniques with confidence levels
        """
        # Normalize action type
        normalized = self._normalize_action_type(action_type)
        
        # Get technique mappings
        technique_mappings = self.ACTION_TO_TECHNIQUES.get(normalized, [])
        
        results = []
        for technique_id, confidence in technique_mappings:
            # Get technique details
            technique = self._get_technique_details(db, technique_id)
            if not technique:
                logger.warning(f"Technique {technique_id} not found")
                continue
            
            # Create mapping
            self._create_mapping(db, action_id, technique_id, confidence)
            
            results.append({
                "technique_id": technique_id,
                "name": technique["name"],
                "tactic": technique["tactic_name"],
                "confidence": confidence,
                "detection": technique["detection_methods"],
                "mitigation": technique["mitigation_strategies"]
            })
        
        logger.info(
            f"Mapped action {action_id} to {len(results)} MITRE techniques"
        )
        
        return results
    
    def _normalize_action_type(self, action_type: str) -> str:
        """Normalize action type to MITRE categories"""
        action_lower = action_type.lower()
        
        if any(x in action_lower for x in ["credential", "password", "auth", "login"]):
            return "credential_access"
        elif any(x in action_lower for x in ["exfil", "export", "download"]):
            return "data_exfiltration"
        elif any(x in action_lower for x in ["lateral", "remote", "ssh", "rdp"]):
            return "lateral_movement"
        elif any(x in action_lower for x in ["persist", "scheduled", "cron"]):
            return "persistence"
        elif any(x in action_lower for x in ["privilege", "escalat", "sudo", "admin"]):
            return "privilege_escalation"
        elif any(x in action_lower for x in ["evasion", "hide", "obfuscate", "delete"]):
            return "defense_evasion"
        elif any(x in action_lower for x in ["discover", "enum", "list", "scan"]):
            return "discovery"
        elif any(x in action_lower for x in ["execute", "command", "script", "shell"]):
            return "execution"
        elif any(x in action_lower for x in ["initial", "exploit", "vulnerability"]):
            return "initial_access"
        elif any(x in action_lower for x in ["collect", "gather", "archive"]):
            return "collection"
        elif any(x in action_lower for x in ["impact", "encrypt", "ransom", "dos", "destroy"]):
            return "impact"
        else:
            return "discovery"  # Safe default
    
    def _get_technique_details(self, db: Session, technique_id: str) -> Dict:
        """Get technique details from database"""
        query = text("""
            SELECT 
                t.technique_id, t.name, t.detection_methods, 
                t.mitigation_strategies, tac.name as tactic_name
            FROM mitre_techniques t
            JOIN mitre_tactics tac ON t.tactic_id = tac.tactic_id
            WHERE t.technique_id = :technique_id
        """)
        
        result = db.execute(query, {"technique_id": technique_id}).fetchone()
        if not result:
            return None
        
        return {
            "technique_id": result[0],
            "name": result[1],
            "detection_methods": result[2],
            "mitigation_strategies": result[3],
            "tactic_name": result[4]
        }
    
    def _create_mapping(
        self,
        db: Session,
        action_id: int,
        technique_id: str,
        confidence: str
    ):
        """Create technique-to-action mapping"""
        # Check if exists
        check = text("""
            SELECT id FROM mitre_technique_mappings
            WHERE action_id = :action_id AND technique_id = :technique_id
        """)
        
        if db.execute(check, {"action_id": action_id, "technique_id": technique_id}).fetchone():
            return
        
        # Insert
        insert = text("""
            INSERT INTO mitre_technique_mappings (action_id, technique_id, confidence)
            VALUES (:action_id, :technique_id, :confidence)
        """)
        
        db.execute(insert, {
            "action_id": action_id,
            "technique_id": technique_id,
            "confidence": confidence
        })
        db.commit()
    
    def get_threat_landscape(self, db: Session) -> Dict:
        """Get overview of detected MITRE techniques"""
        query = text("""
            SELECT 
                tac.name as tactic,
                COUNT(DISTINCT mtm.technique_id) as detected_techniques,
                COUNT(DISTINCT mtm.action_id) as affected_actions
            FROM mitre_tactics tac
            LEFT JOIN mitre_techniques tech ON tac.tactic_id = tech.tactic_id
            LEFT JOIN mitre_technique_mappings mtm ON tech.technique_id = mtm.technique_id
            GROUP BY tac.name
            ORDER BY detected_techniques DESC
        """)
        
        result = db.execute(query)
        landscape = []
        
        for row in result:
            tactic, techniques, actions = row
            if techniques > 0:
                landscape.append({
                    "tactic": tactic,
                    "detected_techniques": techniques,
                    "affected_actions": actions
                })
        
        return landscape


# Singleton instance
mitre_mapper = MITREMapper()
