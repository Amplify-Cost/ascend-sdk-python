#!/usr/bin/env python3
"""
COMPLETE Enterprise MITRE & NIST Mapping Expansion
Covers all 13 current action types + common enterprise scenarios
"""

# ALL 13 CURRENT ACTION TYPES + 7 COMMON ENTERPRISE TYPES
NEW_MITRE_MAPPINGS = '''
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
'''

NEW_NIST_MAPPINGS = '''
        # === CURRENT SYSTEM ACTION TYPES (13) ===
        "database_query": [
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("AC-6", "PRIMARY"),   # Least Privilege
            ("AU-2", "SECONDARY"), # Event Logging
            ("IA-2", "SUPPORTING") # User Identification
        ],
        "forensic_analysis": [
            ("AU-6", "PRIMARY"),   # Audit Review and Analysis
            ("AU-7", "PRIMARY"),   # Audit Reduction and Report Generation
            ("IR-4", "SECONDARY"), # Incident Handling
            ("SI-4", "SUPPORTING") # System Monitoring
        ],
        "threat_analysis": [
            ("SI-4", "PRIMARY"),   # Information System Monitoring
            ("RA-5", "PRIMARY"),   # Vulnerability Monitoring
            ("IR-4", "SECONDARY"), # Incident Handling
            ("AU-6", "SUPPORTING") # Audit Review
        ],
        "access_review": [
            ("AC-2", "PRIMARY"),   # Account Management
            ("AC-6", "PRIMARY"),   # Least Privilege
            ("AU-2", "SECONDARY"), # Event Logging
            ("IA-4", "SUPPORTING") # Identifier Management
        ],
        "network_monitoring": [
            ("SI-4", "PRIMARY"),   # Information System Monitoring
            ("SC-7", "PRIMARY"),   # Boundary Protection
            ("AU-2", "SECONDARY"), # Event Logging
            ("IR-4", "SUPPORTING") # Incident Handling
        ],
        "financial_transaction": [
            ("AU-2", "PRIMARY"),   # Event Logging
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("SI-7", "SECONDARY"), # Software and Information Integrity
            ("AU-10", "SUPPORTING") # Non-Repudiation
        ],
        "firewall_modification": [
            ("SC-7", "PRIMARY"),   # Boundary Protection
            ("CM-3", "PRIMARY"),   # Configuration Change Control
            ("AC-3", "SECONDARY"), # Access Enforcement
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        "anomaly_detection": [
            ("SI-4", "PRIMARY"),   # Information System Monitoring
            ("IR-4", "PRIMARY"),   # Incident Handling
            ("AU-6", "SECONDARY"), # Audit Review
            ("RA-5", "SUPPORTING") # Vulnerability Monitoring
        ],
        "code_deployment": [
            ("CM-3", "PRIMARY"),   # Configuration Change Control
            ("SA-10", "PRIMARY"),  # Developer Configuration Management
            ("CM-2", "SECONDARY"), # Baseline Configuration
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        "compliance_check": [
            ("CA-2", "PRIMARY"),   # Control Assessments
            ("CA-7", "PRIMARY"),   # Continuous Monitoring
            ("AU-6", "SECONDARY"), # Audit Review
            ("PM-6", "SUPPORTING") # Measures of Performance
        ],
        "delete_files": [
            ("MP-6", "PRIMARY"),   # Media Sanitization
            ("AU-2", "PRIMARY"),   # Event Logging
            ("AC-3", "SECONDARY"), # Access Enforcement
            ("SI-7", "SUPPORTING") # Software and Information Integrity
        ],
        "send_email": [
            ("SC-8", "PRIMARY"),   # Transmission Confidentiality
            ("AC-4", "PRIMARY"),   # Information Flow Enforcement
            ("AU-2", "SECONDARY"), # Event Logging
            ("AT-2", "SUPPORTING") # Literacy Training and Awareness
        ],
        "vulnerability_scan": [
            ("RA-5", "PRIMARY"),   # Vulnerability Monitoring and Scanning
            ("SI-2", "PRIMARY"),   # Flaw Remediation
            ("CA-7", "SECONDARY"), # Continuous Monitoring
            ("AU-2", "SUPPORTING") # Event Logging
        ],
        # === COMMON ENTERPRISE ACTION TYPES (7) ===
        "api_call": [
            ("SC-8", "PRIMARY"),   # Transmission Confidentiality
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("AU-2", "SECONDARY"), # Event Logging
            ("IA-2", "SUPPORTING") # User Authentication
        ],
        "file_read": [
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("AC-6", "PRIMARY"),   # Least Privilege
            ("AU-2", "SECONDARY"), # Event Logging
            ("MP-2", "SUPPORTING") # Media Access
        ],
        "file_write": [
            ("AC-3", "PRIMARY"),   # Access Enforcement
            ("SI-7", "PRIMARY"),   # Software and Information Integrity
            ("AU-2", "SECONDARY"), # Event Logging
            ("MP-2", "SUPPORTING") # Media Access
        ],
        "authentication": [
            ("IA-2", "PRIMARY"),   # User Identification and Authentication
            ("AC-7", "PRIMARY"),   # Unsuccessful Logon Attempts
            ("AU-2", "SECONDARY"), # Event Logging
            ("IA-5", "SUPPORTING") # Authenticator Management
        ],
        "backup_operation": [
            ("CP-9", "PRIMARY"),   # Information System Backup
            ("MP-4", "PRIMARY"),   # Media Storage
            ("AU-2", "SECONDARY"), # Event Logging
            ("SC-28", "SUPPORTING") # Protection of Information at Rest
        ],
        "log_analysis": [
            ("AU-6", "PRIMARY"),   # Audit Review and Analysis
            ("AU-7", "PRIMARY"),   # Audit Reduction and Report Generation
            ("SI-4", "SECONDARY"), # System Monitoring
            ("IR-4", "SUPPORTING") # Incident Handling
        ],
        "user_management": [
            ("AC-2", "PRIMARY"),   # Account Management
            ("IA-4", "PRIMARY"),   # Identifier Management
            ("AU-2", "SECONDARY"), # Event Logging
            ("AC-6", "SUPPORTING") # Least Privilege
        ],
'''

def expand_mitre():
    with open('services/mitre_mapper.py', 'r') as f:
        content = f.read()
    
    marker = '        "defense_evasion": ['
    if marker in content:
        content = content.replace(marker, NEW_MITRE_MAPPINGS + '\n        "defense_evasion": [')
        with open('services/mitre_mapper.py', 'w') as f:
            f.write(content)
        return True
    return False

def expand_nist():
    with open('services/nist_mapper.py', 'r') as f:
        content = f.read()
    
    marker = '        "database_write": ['
    if marker in content:
        content = content.replace(marker, NEW_NIST_MAPPINGS + '\n        "database_write": [')
        with open('services/nist_mapper.py', 'w') as f:
            f.write(content)
        return True
    return False

def main():
    print("\n" + "="*60)
    print("COMPLETE ENTERPRISE FRAMEWORK EXPANSION")
    print("="*60 + "\n")
    
    # Backups
    import shutil
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy('services/mitre_mapper.py', f'services/mitre_mapper.py.backup_{timestamp}')
    shutil.copy('services/nist_mapper.py', f'services/nist_mapper.py.backup_{timestamp}')
    print(f"✅ Backups created with timestamp: {timestamp}\n")
    
    mitre_ok = expand_mitre()
    nist_ok = expand_nist()
    
    if mitre_ok and nist_ok:
        print("✅ MITRE ATT&CK mappings expanded (+20 action types)")
        print("✅ NIST 800-53 mappings expanded (+20 action types)")
        print("\n📊 Coverage:")
        print("  ✓ All 13 current action types")
        print("  ✓ 7 common enterprise action types")
        print("  ✓ Total: 31 action types with full assessments")
        print("\n🚀 Ready to deploy!")
        return 0
    else:
        print("❌ Expansion failed - check backups")
        return 1

if __name__ == "__main__":
    exit(main())
