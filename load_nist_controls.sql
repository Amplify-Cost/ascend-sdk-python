-- Load critical NIST SP 800-53 Rev 5 controls
INSERT INTO nist_controls (control_id, family, title, description, baseline_impact, priority) VALUES

-- Access Control (AC)
('AC-1', 'Access Control', 'Policy and Procedures', 'Develop, document, and disseminate access control policy and procedures', 'LOW', 'P1'),
('AC-2', 'Access Control', 'Account Management', 'Manage system accounts including creation, modification, and removal', 'LOW', 'P1'),
('AC-3', 'Access Control', 'Access Enforcement', 'Enforce approved authorizations for logical access', 'LOW', 'P1'),
('AC-4', 'Access Control', 'Information Flow Enforcement', 'Enforce approved authorizations for controlling information flow', 'MODERATE', 'P1'),
('AC-5', 'Access Control', 'Separation of Duties', 'Separate duties of individuals to prevent malevolent activity', 'LOW', 'P1'),
('AC-6', 'Access Control', 'Least Privilege', 'Employ the principle of least privilege', 'LOW', 'P1'),
('AC-17', 'Access Control', 'Remote Access', 'Establish usage restrictions and implementation guidance for remote access', 'LOW', 'P1'),

-- Audit and Accountability (AU)
('AU-2', 'Audit and Accountability', 'Event Logging', 'Identify the types of events that the system is capable of logging', 'LOW', 'P1'),
('AU-3', 'Audit and Accountability', 'Content of Audit Records', 'Ensure audit records contain information that establishes what occurred', 'LOW', 'P1'),
('AU-6', 'Audit and Accountability', 'Audit Record Review', 'Review and analyze system audit records', 'LOW', 'P1'),
('AU-9', 'Audit and Accountability', 'Protection of Audit Information', 'Protect audit information and tools from unauthorized access', 'LOW', 'P1'),
('AU-12', 'Audit and Accountability', 'Audit Record Generation', 'Provide audit record generation capability', 'LOW', 'P1'),

-- Configuration Management (CM)
('CM-2', 'Configuration Management', 'Baseline Configuration', 'Develop, document, and maintain baseline configurations', 'LOW', 'P1'),
('CM-3', 'Configuration Management', 'Configuration Change Control', 'Determine and document types of changes that are configuration-controlled', 'MODERATE', 'P1'),
('CM-6', 'Configuration Management', 'Configuration Settings', 'Establish and document configuration settings', 'LOW', 'P1'),
('CM-7', 'Configuration Management', 'Least Functionality', 'Configure the system to provide only essential capabilities', 'LOW', 'P1'),
('CM-8', 'Configuration Management', 'System Component Inventory', 'Develop and document an inventory of system components', 'LOW', 'P2'),

-- Identification and Authentication (IA)
('IA-2', 'Identification and Authentication', 'User Identification and Authentication', 'Uniquely identify and authenticate organizational users', 'LOW', 'P1'),
('IA-4', 'Identification and Authentication', 'Identifier Management', 'Manage system identifiers', 'LOW', 'P1'),
('IA-5', 'Identification and Authentication', 'Authenticator Management', 'Manage system authenticators', 'LOW', 'P1'),
('IA-8', 'Identification and Authentication', 'Identification and Authentication (Non-Organizational Users)', 'Uniquely identify and authenticate non-organizational users', 'LOW', 'P1'),

-- Incident Response (IR)
('IR-4', 'Incident Response', 'Incident Handling', 'Implement incident handling capability', 'LOW', 'P1'),
('IR-5', 'Incident Response', 'Incident Monitoring', 'Track and document incidents', 'LOW', 'P1'),
('IR-6', 'Incident Response', 'Incident Reporting', 'Require personnel to report suspected incidents', 'LOW', 'P1'),
('IR-8', 'Incident Response', 'Incident Response Plan', 'Develop and implement an incident response plan', 'LOW', 'P2'),

-- Risk Assessment (RA)
('RA-3', 'Risk Assessment', 'Risk Assessment', 'Conduct risk assessments of security and privacy risks', 'LOW', 'P1'),
('RA-5', 'Risk Assessment', 'Vulnerability Monitoring and Scanning', 'Monitor and scan for vulnerabilities', 'LOW', 'P1'),

-- System and Communications Protection (SC)
('SC-7', 'System and Communications Protection', 'Boundary Protection', 'Monitor and control communications at external and key internal boundaries', 'LOW', 'P1'),
('SC-8', 'System and Communications Protection', 'Transmission Confidentiality', 'Protect the confidentiality of transmitted information', 'MODERATE', 'P1'),
('SC-13', 'System and Communications Protection', 'Cryptographic Protection', 'Implement cryptographic mechanisms to protect information', 'LOW', 'P1'),
('SC-28', 'System and Communications Protection', 'Protection of Information at Rest', 'Protect the confidentiality and integrity of information at rest', 'MODERATE', 'P1'),

-- System and Information Integrity (SI)
('SI-2', 'System and Information Integrity', 'Flaw Remediation', 'Identify, report, and correct system flaws', 'LOW', 'P1'),
('SI-3', 'System and Information Integrity', 'Malicious Code Protection', 'Implement malicious code protection mechanisms', 'LOW', 'P1'),
('SI-4', 'System and Information Integrity', 'System Monitoring', 'Monitor the system to detect attacks and unauthorized activity', 'LOW', 'P1'),
('SI-7', 'System and Information Integrity', 'Software and Information Integrity', 'Employ integrity verification tools to detect unauthorized changes', 'MODERATE', 'P1'),

-- Planning (PL)
('PL-2', 'Planning', 'System Security Plan', 'Develop and implement a security plan', 'LOW', 'P2'),

-- Personnel Security (PS)
('PS-3', 'Personnel Security', 'Personnel Screening', 'Screen individuals prior to authorizing access', 'LOW', 'P1'),

-- Physical and Environmental Protection (PE)
('PE-2', 'Physical and Environmental Protection', 'Physical Access Authorizations', 'Develop and maintain authorization credentials', 'LOW', 'P1'),
('PE-3', 'Physical and Environmental Protection', 'Physical Access Control', 'Enforce physical access authorizations', 'LOW', 'P1'),

-- Security Assessment (CA)
('CA-2', 'Security Assessment', 'Control Assessments', 'Develop security and privacy assessment plans', 'LOW', 'P2'),
('CA-7', 'Security Assessment', 'Continuous Monitoring', 'Develop and implement a continuous monitoring strategy', 'LOW', 'P1'),

-- System and Services Acquisition (SA)
('SA-4', 'System and Services Acquisition', 'Acquisition Process', 'Include security and privacy requirements in acquisition contracts', 'LOW', 'P1'),

-- Media Protection (MP)
('MP-2', 'Media Protection', 'Media Access', 'Restrict access to system media to authorized users', 'LOW', 'P1'),
('MP-6', 'Media Protection', 'Media Sanitization', 'Sanitize system media prior to disposal or reuse', 'LOW', 'P1')

ON CONFLICT (control_id) DO NOTHING;
