# Prompt Injection Detection

Enterprise-grade prompt injection detection for AI governance.

## Overview

ASCEND provides real-time detection and blocking of prompt injection attacks targeting AI agents. The service uses pattern-based detection with compliance mappings to CWE, MITRE ATT&CK, NIST 800-53, and OWASP LLM Top 10.

## Architecture

```
User/Agent Prompt
       │
       ▼
┌─────────────────────────┐
│ PromptSecurityService   │
├─────────────────────────┤
│ 1. Load org config      │  ← org_prompt_security_config
│ 2. Recursive decode     │  ← base64, unicode, HTML
│ 3. Match patterns       │  ← global + custom patterns
│ 4. Calculate risk       │  ← severity_scores from config
│ 5. Block/allow          │  ← block_threshold from config
└─────────────────────────┘
       │
       ▼
   Governance Decision
```

## Detection Categories

| Category | Description | Severity Range |
|----------|-------------|----------------|
| `prompt_injection` | Direct instruction override attempts | Critical-High |
| `jailbreak` | DAN mode, developer mode bypasses | Critical-High |
| `role_manipulation` | Identity hijacking, fake system messages | Critical-High |
| `encoding_attack` | Base64, unicode, HTML entity evasion | High-Medium |
| `delimiter_attack` | Code block, markdown manipulation | High |
| `data_exfiltration` | System prompt extraction, external transmission | Critical-High |
| `chain_attack` | LLM-to-LLM injection propagation | Critical |

## Global Patterns (21 patterns)

ASCEND ships with 21 vendor-managed patterns stored in `global_prompt_patterns`. Key patterns:

| Pattern ID | Category | Severity | CVSS | OWASP LLM |
|------------|----------|----------|------|-----------|
| PROMPT-001 | prompt_injection | critical | 9.8 | LLM01 |
| PROMPT-004 | jailbreak | critical | 9.8 | LLM01 |
| PROMPT-005 | jailbreak | critical | 9.1 | LLM01 |
| PROMPT-008 | role_manipulation | critical | 9.1 | LLM01, LLM08 |
| PROMPT-010 | role_manipulation | high | 8.8 | LLM01 |
| PROMPT-011 | encoding_attack | high | 7.5 | LLM01 |
| PROMPT-018 | data_exfiltration | critical | 9.1 | LLM06 |
| PROMPT-020 | chain_attack | critical | 9.5 | LLM01, LLM07 |

## Configuration

All configuration is stored in `org_prompt_security_config`. No hardcoded values.

### Default Settings

```sql
-- Default configuration created per-organization
enabled = true
mode = 'monitor'              -- 'enforce', 'monitor', 'off'
block_threshold = 90          -- Block if risk >= 90
escalate_threshold = 70       -- Escalate if risk >= 70
alert_threshold = 50          -- Alert if risk >= 50

-- Severity scores (configurable per-org)
severity_scores = {
  "critical": 95,
  "high": 75,
  "medium": 50,
  "low": 25,
  "info": 10
}

-- Scan settings
scan_system_prompts = true
scan_user_prompts = true
scan_agent_responses = true
scan_llm_to_llm = true

-- Encoding detection
detect_base64 = true
detect_unicode_smuggling = true
detect_html_entities = true
max_decode_depth = 3
```

### Modes

| Mode | Behavior |
|------|----------|
| `enforce` | Detect AND block when threshold exceeded |
| `monitor` | Detect and log, but never block |
| `off` | Disabled - no analysis performed |

## API Endpoints

Base path: `/api/v1/admin/prompt-security`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/config` | Get organization configuration |
| PUT | `/config` | Update organization configuration |
| GET | `/patterns` | List all effective patterns |
| POST | `/patterns/override` | Add/update pattern override |
| DELETE | `/patterns/override/{pattern_id}` | Remove pattern override |
| GET | `/custom-patterns` | List custom patterns |
| POST | `/custom-patterns` | Create custom pattern |
| GET | `/audit-log` | Query detection audit log |
| GET | `/chain-log` | Query LLM chain audit log |
| GET | `/stats` | Get detection statistics |

## Integration

### Pipeline Position

Prompt security runs at **Step 1.6** in the action submission pipeline:

```
POST /api/v1/actions/submit
├── Step 1:   Risk Enrichment
├── Step 1.5: Code Analysis (Phase 9)
├── Step 1.6: PROMPT SECURITY ← Here
├── Step 2:   CVSS Calculation
├── Step 3:   Policy Evaluation
└── ...
```

### Response Format

```json
{
  "prompt_security": {
    "analyzed": true,
    "findings_count": 2,
    "max_severity": "critical",
    "patterns_matched": ["PROMPT-001", "PROMPT-004"],
    "blocked": true,
    "block_reason": "Prompt injection detected: PROMPT-001 - Direct instruction override",
    "encoding_detected": true,
    "decoded_layers": 1,
    "config_mode": "enforce"
  }
}
```

## Encoding Detection

The service recursively decodes obfuscated content up to `max_decode_depth` layers:

| Encoding | Detection | Example |
|----------|-----------|---------|
| Base64 | Strings 40+ chars matching `[A-Za-z0-9+/]+={0,2}` | `aWdub3JlIGFsbA==` |
| Unicode | `\uXXXX` escape sequences | `\u0069\u0067\u006e` |
| HTML Entities | `&#NNN;` or `&#xHH;` numeric references | `&#105;&#103;` |
| Zero-width | Invisible Unicode characters | `U+200B`, `U+FEFF` |

## Custom Patterns

Organizations can add custom patterns with IDs prefixed `CUSTOM-PROMPT-`:

```python
# POST /api/v1/admin/prompt-security/custom-patterns
{
    "pattern_id": "CUSTOM-PROMPT-COMPANY-001",
    "category": "prompt_injection",
    "attack_vector": "direct",
    "severity": "high",
    "pattern_type": "regex",
    "pattern_value": "\\b(company-specific-keyword)\\b",
    "pattern_flags": "IGNORECASE",
    "applies_to": ["user_prompt", "agent_response"],
    "description": "Company-specific injection attempt",
    "cwe_ids": ["CWE-77"],
    "mitre_techniques": ["T1059"]
}
```

## Pattern Overrides

Disable or adjust global patterns for your organization:

```python
# POST /api/v1/admin/prompt-security/patterns/override
{
    "pattern_id": "PROMPT-007",
    "is_disabled": false,
    "severity_override": "medium",
    "risk_score_override": 60,
    "modification_reason": "False positives in our environment"
}
```

All overrides require justification and are logged for SOC 2 compliance.

## Compliance

- **CWE-77**: Command Injection
- **CWE-94**: Code Injection
- **CWE-863**: Incorrect Authorization
- **MITRE ATT&CK**: T1059, T1190, T1036, T1548
- **NIST 800-53**: SI-10 (Information Input Validation)
- **OWASP LLM Top 10**: LLM01 (Prompt Injection), LLM06 (Sensitive Info Disclosure)

## Troubleshooting

### Prompt Not Being Scanned

```sql
-- Check org config
SELECT enabled, mode, scan_user_prompts
FROM org_prompt_security_config
WHERE organization_id = X;
```

### Pattern Not Matching

```sql
-- Check if pattern is disabled
SELECT is_disabled, severity_override
FROM org_prompt_pattern_overrides
WHERE organization_id = X AND pattern_id = 'PROMPT-XXX';

-- Check if category is filtered
SELECT enabled_categories, disabled_pattern_ids
FROM org_prompt_security_config
WHERE organization_id = X;
```

### High False Positive Rate

1. Switch to `monitor` mode to evaluate without blocking
2. Review detection audit log: `GET /api/v1/admin/prompt-security/audit-log`
3. Create pattern overrides to adjust severity or disable
4. Contact ASCEND support for pattern tuning assistance
