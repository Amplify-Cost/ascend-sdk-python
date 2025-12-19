# Code Analysis

Enterprise-grade code pattern detection for AI agent actions.

## Overview

ASCEND provides real-time detection of dangerous code patterns in AI agent actions. The service analyzes SQL queries, shell commands, Python scripts, and JavaScript code for security vulnerabilities with compliance mappings to CWE, MITRE ATT&CK, and CVSS.

## Architecture

```
Action Submission
       │
       ▼
┌─────────────────────────┐
│ CodeAnalysisService     │
├─────────────────────────┤
│ 1. Extract code         │  ← query, script, command params
│ 2. Detect language      │  ← SQL, Python, Shell, JS
│ 3. Load patterns        │  ← global + org custom
│ 4. Match patterns       │  ← regex analysis
│ 5. Calculate risk       │  ← severity_scores from config
│ 6. Block/allow          │  ← block_threshold from config
└─────────────────────────┘
       │
       ▼
   Governance Decision
```

## Supported Languages

| Language | Detection | Example Patterns |
|----------|-----------|------------------|
| SQL | `SELECT`, `INSERT`, `DROP`, `WHERE` | SQL injection, destructive DDL |
| Python | `def`, `class`, `import` | eval/exec, subprocess, file access |
| Shell | `echo`, `rm`, `cat`, pipes | Command injection, privilege escalation |
| JavaScript | `function`, `const`, arrow functions | eval, DOM manipulation |

## Global Patterns (20 patterns)

ASCEND ships with 20 vendor-managed patterns stored in `global_code_patterns`. Categories:

| Category | Description | Severity Range |
|----------|-------------|----------------|
| `injection` | SQL injection, command injection | Critical-High |
| `code_execution` | Dynamic code execution (eval, exec) | Critical |
| `code_injection` | Script injection attempts | Critical |
| `file_access` | Unauthorized file operations | High-Medium |
| `network_access` | Outbound connections, data exfil | High |
| `data_destruction` | DROP TABLE, rm -rf, etc. | Critical |
| `data_exfiltration` | Data export, external transmission | High |
| `credential_exposure` | Password/key/token patterns | Critical-High |
| `privilege_escalation` | sudo, chmod, chown operations | High |
| `sandbox_escape` | Breakout attempts, dunder access | Critical |

### Key Patterns

| Pattern ID | Language | Category | Severity | CVSS |
|------------|----------|----------|----------|------|
| SQL-001 | sql | injection | critical | 9.8 |
| SQL-002 | sql | data_destruction | critical | 9.1 |
| PY-001 | python | code_execution | critical | 9.8 |
| PY-002 | python | code_execution | critical | 9.1 |
| PY-004 | python | code_injection | critical | 9.5 |
| SHELL-001 | shell | code_injection | critical | 9.8 |
| SHELL-002 | shell | data_destruction | critical | 9.5 |

## Configuration

All configuration is stored in `org_code_analysis_config`. No hardcoded values.

### Default Settings

```sql
-- Default configuration created per-organization
enabled = true
mode = 'monitor'              -- 'enforce', 'monitor', 'off'
block_threshold = 90          -- Block if risk >= 90
alert_threshold = 50          -- Alert if risk >= 50
escalate_threshold = 70       -- Escalate if risk >= 70

-- Severity scores (configurable per-org)
severity_scores = {
  "critical": 95,
  "high": 75,
  "medium": 50,
  "low": 25,
  "info": 10
}

-- Language/category filters (empty = all enabled)
enabled_languages = []
enabled_categories = []
disabled_pattern_ids = []
```

### Modes

| Mode | Behavior |
|------|----------|
| `enforce` | Detect AND block when critical findings exceed threshold |
| `monitor` | Detect and log, but never block |
| `off` | Disabled - no analysis performed |

## Pipeline Integration

Code analysis runs at **Step 1.5** in the action submission pipeline:

```
POST /api/v1/actions/submit
├── Step 1:   Risk Enrichment
├── Step 1.5: CODE ANALYSIS ← Here
├── Step 1.6: Prompt Security (Phase 10)
├── Step 2:   CVSS Calculation
├── Step 3:   Policy Evaluation
└── ...
```

## Usage

### Direct Service Usage

```python
from services.code_analysis_service import CodeAnalysisService

service = CodeAnalysisService(db, org_id=1)
result = service.analyze_for_action(
    action_type="execute_sql",
    parameters={"query": "SELECT * FROM users WHERE id = 1; DROP TABLE users;"},
    agent_id="agent-123"  # Optional: for agent-specific thresholds
)

if result.blocked:
    print(f"Blocked: {result.block_reason}")
else:
    print(f"Risk score: {result.max_risk_score}")
    for finding in result.findings:
        print(f"  - {finding.pattern_id}: {finding.description}")
```

### Response Format

```json
{
  "code_analysis": {
    "analyzed": true,
    "language": "sql",
    "findings_count": 2,
    "max_severity": "critical",
    "max_risk_score": 98,
    "patterns_matched": ["SQL-001", "SQL-002"],
    "blocked": true,
    "block_reason": "Critical code pattern detected: SQL-001 - SQL injection vulnerability",
    "config_mode": "enforce",
    "scan_duration_ms": 12,
    "findings": [
      {
        "pattern_id": "SQL-001",
        "severity": "critical",
        "category": "injection",
        "description": "SQL injection vulnerability",
        "matched_text": "'; DROP TABLE users;--",
        "line_number": 1,
        "cwe_ids": ["CWE-89"],
        "mitre_techniques": ["T1190"],
        "cvss_base_score": 9.8,
        "risk_score": 98
      }
    ]
  }
}
```

## Code Parameter Detection

The service automatically extracts code from these parameter names:

| Parameter | Description |
|-----------|-------------|
| `query` | SQL queries |
| `sql` | SQL statements |
| `code` | Generic code |
| `script` | Script content |
| `command` | Shell commands |
| `cmd` | Command aliases |
| `statement` | SQL/code statements |
| `expression` | Expressions to evaluate |
| `source` | Source code |
| `shell` | Shell scripts |
| `bash` | Bash commands |
| `description` | May contain code snippets |

## Custom Patterns

Organizations can add custom patterns with IDs prefixed `CUSTOM-`:

```python
# Create custom pattern
pattern = OrgCustomPattern(
    organization_id=1,
    pattern_id="CUSTOM-PII-001",
    language="any",
    category="data_exfiltration",
    severity="high",
    pattern_type="regex",
    pattern_value=r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
    pattern_flags="IGNORECASE",
    description="Social Security Number detected",
    cwe_ids=["CWE-200"],
    mitre_techniques=["T1530"],
    cvss_base_score=7.5
)
```

## Pattern Overrides

Disable or adjust global patterns for your organization:

```python
# Create override
override = OrgPatternOverride(
    organization_id=1,
    pattern_id="SQL-003",
    is_disabled=False,
    severity_override="medium",
    risk_score_override=50,
    modified_by=user_id,
    modification_reason="False positives for our ORM-generated queries"
)
```

## Agent-Specific Thresholds

Registered agents can have their own risk thresholds via `RegisteredAgent.max_risk_threshold`. The service uses the **minimum** of:

1. `org_code_analysis_config.block_threshold`
2. `RegisteredAgent.max_risk_threshold`

This allows restricting high-risk agents more than the org default.

## Compliance

- **CWE-78**: OS Command Injection
- **CWE-89**: SQL Injection
- **CWE-94**: Code Injection
- **CWE-95**: Eval Injection
- **CWE-200**: Information Exposure
- **MITRE ATT&CK**: T1059, T1190, T1071, T1530
- **NIST 800-53**: SI-10 (Information Input Validation)
- **SOC 2**: CC6.1 (Access Control)

## Troubleshooting

### Code Not Being Analyzed

```sql
-- Check org config
SELECT enabled, mode
FROM org_code_analysis_config
WHERE organization_id = X;
```

### Pattern Not Matching

```sql
-- Check if pattern is disabled
SELECT is_disabled
FROM org_pattern_overrides
WHERE organization_id = X AND pattern_id = 'SQL-001';

-- Check language filtering
SELECT enabled_languages
FROM org_code_analysis_config
WHERE organization_id = X;
```

### Performance Issues

- Normal scan duration: <50ms
- If >100ms, check pattern count and complexity
- Consider disabling unused languages/categories
