-- Load MITRE ATT&CK Tactics (14 tactics in Enterprise matrix)
INSERT INTO mitre_tactics (tactic_id, name, description) VALUES
('TA0001', 'Initial Access', 'Adversary trying to get into your network'),
('TA0002', 'Execution', 'Adversary trying to run malicious code'),
('TA0003', 'Persistence', 'Adversary trying to maintain their foothold'),
('TA0004', 'Privilege Escalation', 'Adversary trying to gain higher-level permissions'),
('TA0005', 'Defense Evasion', 'Adversary trying to avoid being detected'),
('TA0006', 'Credential Access', 'Adversary trying to steal account names and passwords'),
('TA0007', 'Discovery', 'Adversary trying to figure out your environment'),
('TA0008', 'Lateral Movement', 'Adversary trying to move through your environment'),
('TA0009', 'Collection', 'Adversary trying to gather data of interest'),
('TA0010', 'Exfiltration', 'Adversary trying to steal data'),
('TA0011', 'Command and Control', 'Adversary trying to communicate with compromised systems'),
('TA0040', 'Impact', 'Adversary trying to manipulate, interrupt, or destroy systems and data'),
('TA0042', 'Resource Development', 'Adversary trying to establish resources for operations'),
('TA0043', 'Reconnaissance', 'Adversary trying to gather information for planning')
ON CONFLICT (tactic_id) DO NOTHING;

-- Load critical MITRE ATT&CK Techniques
INSERT INTO mitre_techniques (technique_id, name, description, tactic_id, detection_methods, mitigation_strategies) VALUES
-- Initial Access
('T1078', 'Valid Accounts', 'Adversaries may obtain and abuse credentials of existing accounts', 'TA0001', 'Monitor for unusual account behavior, login patterns', 'Multi-factor authentication, least privilege'),
('T1190', 'Exploit Public-Facing Application', 'Adversaries may attempt to exploit software vulnerabilities', 'TA0001', 'Network intrusion detection, application logs', 'Patch management, WAF'),
('T1133', 'External Remote Services', 'Adversaries may leverage external remote services', 'TA0001', 'Monitor authentication logs', 'MFA, network segmentation'),

-- Execution
('T1059', 'Command and Scripting Interpreter', 'Adversaries may abuse command interpreters to execute commands', 'TA0002', 'Command-line logging, process monitoring', 'Restrict script execution, application whitelisting'),
('T1203', 'Exploitation for Client Execution', 'Adversaries may exploit software vulnerabilities', 'TA0002', 'Behavior analysis, endpoint detection', 'Patch management, sandbox analysis'),

-- Persistence
('T1053', 'Scheduled Task/Job', 'Adversaries may abuse task scheduling to execute code', 'TA0003', 'Monitor scheduled task creation', 'Least privilege, task monitoring'),
('T1098', 'Account Manipulation', 'Adversaries may manipulate accounts to maintain access', 'TA0003', 'Account modification monitoring', 'MFA, privileged account management'),
('T1136', 'Create Account', 'Adversaries may create an account to maintain access', 'TA0003', 'Account creation monitoring', 'Centralized account management'),

-- Privilege Escalation
('T1068', 'Exploitation for Privilege Escalation', 'Adversaries may exploit vulnerabilities to elevate privileges', 'TA0004', 'System call monitoring, integrity checks', 'Patch management, least privilege'),
('T1134', 'Access Token Manipulation', 'Adversaries may modify access tokens', 'TA0004', 'API call monitoring, token use analysis', 'Restrict token creation, audit policies'),

-- Defense Evasion
('T1070', 'Indicator Removal', 'Adversaries may delete or modify artifacts to remove evidence', 'TA0005', 'File deletion monitoring, log analysis', 'Centralized logging, file integrity monitoring'),
('T1112', 'Modify Registry', 'Adversaries may modify registry to hide configuration', 'TA0005', 'Registry monitoring', 'Registry permissions, monitoring tools'),
('T1027', 'Obfuscated Files or Information', 'Adversaries may obfuscate files or information', 'TA0005', 'File analysis, entropy detection', 'Content inspection, behavioral analysis'),

-- Credential Access
('T1110', 'Brute Force', 'Adversaries may use brute force techniques to gain access', 'TA0006', 'Failed authentication monitoring', 'Account lockout policies, MFA'),
('T1003', 'OS Credential Dumping', 'Adversaries may dump credentials from OS', 'TA0006', 'Process monitoring, API call monitoring', 'Credential guard, least privilege'),
('T1555', 'Credentials from Password Stores', 'Adversaries may search for passwords in stores', 'TA0006', 'File access monitoring', 'Encrypt password stores'),

-- Discovery
('T1087', 'Account Discovery', 'Adversaries may attempt to get account lists', 'TA0007', 'Command execution monitoring', 'Restrict account enumeration'),
('T1083', 'File and Directory Discovery', 'Adversaries may enumerate files and directories', 'TA0007', 'Process monitoring, file access logs', 'Least privilege'),
('T1082', 'System Information Discovery', 'Adversaries may gather system information', 'TA0007', 'Command monitoring', 'Restrict system information access'),

-- Lateral Movement
('T1021', 'Remote Services', 'Adversaries may use valid accounts to access remote systems', 'TA0008', 'Network traffic analysis, authentication logs', 'MFA, network segmentation'),
('T1570', 'Lateral Tool Transfer', 'Adversaries may transfer tools between systems', 'TA0008', 'File transfer monitoring', 'Network segmentation, allowlist'),

-- Collection
('T1005', 'Data from Local System', 'Adversaries may search local system for files', 'TA0009', 'File access monitoring', 'Data loss prevention'),
('T1560', 'Archive Collected Data', 'Adversaries may compress or encrypt data before exfiltration', 'TA0009', 'Process monitoring, file creation', 'Monitor archiving tools'),

-- Exfiltration
('T1041', 'Exfiltration Over C2 Channel', 'Adversaries may steal data over existing command channel', 'TA0010', 'Network traffic analysis', 'Data loss prevention, network monitoring'),
('T1048', 'Exfiltration Over Alternative Protocol', 'Adversaries may steal data over different protocol', 'TA0010', 'Network protocol analysis', 'Network segmentation, filtering'),
('T1567', 'Exfiltration Over Web Service', 'Adversaries may use web services to exfiltrate data', 'TA0010', 'Web proxy logs, SSL inspection', 'Web filtering, DLP'),

-- Command and Control
('T1071', 'Application Layer Protocol', 'Adversaries may communicate using application protocols', 'TA0011', 'Network traffic analysis', 'Network intrusion prevention'),
('T1105', 'Ingress Tool Transfer', 'Adversaries may transfer tools into compromised environment', 'TA0011', 'File monitoring, network traffic', 'Application whitelisting'),

-- Impact
('T1486', 'Data Encrypted for Impact', 'Adversaries may encrypt data to disrupt operations', 'TA0040', 'File modification monitoring', 'Data backup, behavior analysis'),
('T1490', 'Inhibit System Recovery', 'Adversaries may delete or remove backup data', 'TA0040', 'Backup monitoring', 'Restrict backup access'),
('T1498', 'Network Denial of Service', 'Adversaries may perform DoS attacks', 'TA0040', 'Network traffic monitoring', 'Rate limiting, DDoS mitigation')

ON CONFLICT (technique_id) DO NOTHING;
