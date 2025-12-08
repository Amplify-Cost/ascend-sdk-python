---
sidebar_position: 3
title: Glossary
description: Key terms and definitions
---

# Glossary

Definitions of key terms used throughout the Ascend documentation.

---

## A

### Action
A discrete operation performed by an AI agent that is submitted for governance evaluation. Actions have types, descriptions, risk scores, and approval statuses.

### Action Type
A categorization of agent operations (e.g., `database_read`, `email_send`, `file_delete`) that determines base risk scoring and compliance mappings.

### Agent
An AI system registered with Ascend that submits actions for governance evaluation. Agents can be supervised, autonomous, advisory, or MCP servers.

### Agent Registry
The central database of all registered AI agents, including their configurations, capabilities, and governance settings.

### Alert
A notification generated when an action exceeds risk thresholds or triggers smart rules. Alerts can be informational, warning, or critical.

### API Key
A cryptographic token used to authenticate SDK and API requests. Keys are hashed and never stored in plaintext.

### Approval Workflow
A configurable process that routes high-risk actions to designated approvers for human review before execution.

### Audit Log
An immutable record of all actions, decisions, and system events for compliance and forensic analysis.

### Auto-Approve
Automatic approval of actions that fall below the configured risk threshold without human intervention.

---

## B

### Base Score
The CVSS 3.1 base score calculated from action type metrics before context modifiers are applied.

### Block
An action that is denied execution due to policy violation or exceeding maximum risk thresholds.

---

## C

### CVSS (Common Vulnerability Scoring System)
An industry-standard framework (version 3.1) used to assess the severity of security vulnerabilities. Ascend applies CVSS metrics to agent actions.

### Compliance Framework
A set of regulatory requirements (SOC 2, HIPAA, PCI-DSS, NIST) that Ascend maps actions to for compliance tracking.

### Context Modifier
Additional risk adjustments based on operational context like time of day, data sensitivity, or target system.

### Correlation ID
A unique identifier that links related events across the system for tracing and debugging.

---

## D

### Decision
The governance outcome for an action: approved, denied, or pending_approval.

### Dashboard
The web interface for monitoring agent activity, reviewing alerts, and managing governance configurations.

---

## E

### Enrichment
The automatic addition of compliance metadata (NIST controls, MITRE tactics) to actions based on their type and context.

### Escalation
The process of routing a decision to a higher authority when standard approvers are unavailable or risk exceeds their authority.

### Executive Dashboard
A high-level view of platform health, security posture, and key performance indicators for leadership.

---

## G

### Governance Pipeline
The 7-step process that evaluates every action: Risk Assessment → CVSS Calculation → Policy Evaluation → Smart Rules → Alert Generation → Workflow Routing → Audit Logging.

### Governance Policy
A configurable rule that defines conditions and actions for governance decisions (allow, deny, require_approval).

---

## H

### HIPAA (Health Insurance Portability and Accountability Act)
U.S. healthcare privacy law that Ascend supports through PHI access controls and audit trails.

### Human-in-the-Loop
A governance model where certain actions require human approval before execution.

---

## J

### JWT (JSON Web Token)
The authentication token format used for user sessions in the Ascend dashboard.

---

## M

### MCP (Model Context Protocol)
An open protocol for AI systems to interact with external tools and data sources. Ascend provides governance for MCP server operations.

### MFA (Multi-Factor Authentication)
Additional authentication requirement triggered for high-risk actions above the MFA threshold.

### MITRE ATT&CK
A knowledge base of adversary tactics and techniques that Ascend maps actions to for threat detection.

### Multi-Tenant
Architecture where multiple organizations share the platform while maintaining complete data isolation.

---

## N

### NIST 800-53
A catalog of security and privacy controls published by the National Institute of Standards and Technology.

### NIST Control
A specific security control from NIST 800-53 (e.g., AC-3 Access Enforcement) that actions are mapped to.

---

## O

### Organization
A tenant in the Ascend platform representing a company or business unit with isolated data and configurations.

### Organization ID
The unique identifier for a tenant, used to ensure data isolation across all queries.

---

## P

### PCI-DSS (Payment Card Industry Data Security Standard)
Security standards for organizations handling payment card data that Ascend supports.

### Pending Approval
An action status indicating human review is required before the action can proceed.

### PHI (Protected Health Information)
Health information protected under HIPAA that Ascend provides enhanced controls for.

### PII (Personally Identifiable Information)
Data that can identify an individual, requiring enhanced protection under GDPR and other regulations.

### Policy
See Governance Policy.

### Policy Engine
The component that evaluates actions against configured policies to determine governance decisions.

---

## R

### RBAC (Role-Based Access Control)
Access control model where permissions are assigned to roles rather than individual users.

### Risk Level
A categorization (low, medium, high, critical) based on the calculated risk score.

### Risk Score
A numeric value (0-100) representing the assessed risk of an action based on CVSS and context modifiers.

---

## S

### SDK (Software Development Kit)
Client libraries for Python, TypeScript/Node.js, and Go that integrate agent actions with Ascend.

### Session
An authenticated user's active connection to the Ascend platform.

### Smart Rule
An AI-powered security rule that can be generated from natural language descriptions and includes A/B testing capabilities.

### SOC 2 (Service Organization Control 2)
An auditing standard for service organizations covering security, availability, processing integrity, confidentiality, and privacy.

### Supervised Agent
An agent type that requires human oversight for actions above certain risk thresholds.

---

## T

### Tenant
See Organization.

### Threshold
A configurable risk score boundary that triggers different governance behaviors (auto-approve, alert, block).

### Tool
The specific service or capability an agent uses to perform an action (e.g., `email_service`, `postgresql`).

---

## W

### Webhook
HTTP callbacks for real-time notifications of governance events to external systems.

### Workflow
See Approval Workflow.

---

## Compliance Terms

### SOC 2 Type II
SOC 2 report covering a period of time (typically 6-12 months) demonstrating consistent control operation.

### Trust Service Criteria
The five categories of SOC 2: Security (CC), Availability (A), Processing Integrity (PI), Confidentiality (C), Privacy (P).

### Control Objective
A desired outcome of a security control (e.g., "access is restricted to authorized users").

### Evidence
Documentation demonstrating that controls are operating effectively for compliance audits.

---

## Risk Terms

### Attack Vector (AV)
CVSS metric indicating how an attacker could exploit a vulnerability: Network, Adjacent, Local, Physical.

### Attack Complexity (AC)
CVSS metric indicating difficulty of exploitation: Low or High.

### Privileges Required (PR)
CVSS metric indicating access level needed: None, Low, High.

### Scope (S)
CVSS metric indicating whether exploitation affects other components: Unchanged or Changed.

### Impact Metrics
CVSS metrics for Confidentiality (C), Integrity (I), and Availability (A) impacts.

---

## MITRE Terms

### Tactic
A high-level adversary goal in the ATT&CK framework (e.g., TA0006 Credential Access).

### Technique
A specific method adversaries use to achieve a tactic (e.g., T1003 OS Credential Dumping).

### Sub-technique
A more specific variation of a technique (e.g., T1003.001 LSASS Memory).

---

## API Terms

### Endpoint
A specific URL path that accepts API requests.

### Rate Limit
Maximum number of requests allowed per time period.

### Pagination
Breaking large result sets into smaller pages using limit and offset parameters.

### Response Code
HTTP status code indicating request outcome (200 success, 400 error, etc.).

---

*For additional terms, contact support@owkai.app*
