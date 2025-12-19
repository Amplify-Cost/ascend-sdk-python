---
title: LLM-to-LLM Governance
sidebar_position: 1
---

# LLM-to-LLM Governance

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SEC-002 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Enterprise-grade governance for AI agent-to-agent communication.

## Overview

ASCEND provides LLM-to-LLM governance to control and monitor when one AI agent passes prompts to another. This prevents injection propagation, enforces chain depth limits, and maintains audit trails for compliance.

## Architecture

```
Agent A (source)
    │
    ├── prompt_content
    │
    ▼
┌─────────────────────────────┐
│ PromptSecurityService       │
│   .analyze_llm_chain()      │
├─────────────────────────────┤
│ 1. Check chain depth        │  ← llm_chain_depth_limit (default: 5)
│ 2. Analyze prompt           │  ← Same as prompt injection detection
│ 3. Log to llm_chain_audit   │  ← SHA-256 hash, no raw content
│ 4. Return decision          │
└─────────────────────────────┘
    │
    ▼
Agent B (target)
```

## Configuration

LLM-to-LLM settings are part of `org_prompt_security_config`:

```sql
-- Default settings
scan_llm_to_llm = true           -- Enable chain scanning
llm_chain_depth_limit = 5        -- Max nested agent calls
require_chain_approval = false   -- Require approval for high-risk chains
```

### Chain Depth Limits

| Depth | Description | Default Behavior |
|-------|-------------|------------------|
| 1 | Direct agent call | Allowed |
| 2-5 | Nested calls | Allowed (scanned) |
| >5 | Deep nesting | Blocked |

## API Usage

### Analyze Chain Communication

```python
from services.prompt_security_service import PromptSecurityService

service = PromptSecurityService(db, org_id=1)
result = service.analyze_llm_chain(
    source_agent_id="agent-orchestrator",
    target_agent_id="agent-executor",
    prompt_content="Execute the following task...",
    parent_chain_id=None,  # UUID if nested
    source_action_id=12345
)

if result["allowed"]:
    # Proceed with agent communication
    pass
else:
    # Block and log
    print(f"Blocked: {result['reason']}")
```

### Response Format

```json
{
    "allowed": true,
    "chain_id": "550e8400-e29b-41d4-a716-446655440000",
    "depth": 1,
    "injection_detected": false,
    "risk_score": 0,
    "patterns_matched": [],
    "reason": null
}
```

### Blocked Response

```json
{
    "allowed": false,
    "chain_id": "550e8400-e29b-41d4-a716-446655440001",
    "depth": 6,
    "reason": "Chain depth limit exceeded (6 > 5)"
}
```

## Audit Trail

All chain communications are logged to `llm_chain_audit_log`:

| Column | Description |
|--------|-------------|
| `chain_id` | Unique UUID for this chain |
| `parent_chain_id` | Parent chain for nested calls |
| `depth` | Nesting level (1 = direct) |
| `source_agent_id` | Agent sending the prompt |
| `target_agent_id` | Agent receiving the prompt |
| `prompt_content_hash` | SHA-256 hash (no raw content stored) |
| `prompt_length` | Character count |
| `injection_detected` | Boolean detection result |
| `risk_score` | 0-100 risk score |
| `patterns_matched` | Array of matched pattern IDs |
| `status` | allowed, blocked, escalated |
| `block_reason` | Reason if blocked |

### Query Chain Log

```bash
# Via API
GET /api/v1/admin/prompt-security/chain-log?status_filter=blocked

# Response
{
    "total": 5,
    "chains": [
        {
            "chain_id": "...",
            "depth": 6,
            "source_agent_id": "orchestrator",
            "target_agent_id": "executor",
            "status": "blocked",
            "block_reason": "Chain depth limit exceeded (6 > 5)"
        }
    ]
}
```

## Detection Patterns

The same patterns used for prompt injection apply to LLM-to-LLM communication. Key patterns for chain attacks:

| Pattern ID | Description | Severity |
|------------|-------------|----------|
| PROMPT-020 | Chain injection propagation | Critical |
| PROMPT-001 | Direct instruction override | Critical |
| PROMPT-004 | Jailbreak mode attempts | Critical |

### PROMPT-020 Pattern

Detects when an agent is instructed to propagate malicious prompts:

```regex
\b(pass|forward|relay|send|propagate)\s+(this|these|the\s+following)\s+(instructions?|commands?|prompts?|messages?)\s+(to|for)\s+(the\s+)?(next|other|downstream|target|receiving)\s*(agent|AI|model|LLM|assistant)?\b
```

## Use Cases

### 1. Orchestrator-Worker Pattern

```
User Request
    │
    ▼
[Orchestrator Agent]──┬──► [Worker Agent 1]
    chain_id: A       │
                      ├──► [Worker Agent 2]
                      │    chain_id: B, parent: A
                      │
                      └──► [Worker Agent 3]
                           chain_id: C, parent: A
```

### 2. Recursive Agent Calls

```
[Research Agent]
    │ depth=1
    ▼
[Search Agent]
    │ depth=2
    ▼
[Summarize Agent]
    │ depth=3
    ▼
[Verify Agent]
    │ depth=4
    ▼
[Format Agent]
    │ depth=5 ← At limit
    ▼
[Export Agent]  ← BLOCKED (depth=6)
```

### 3. Cross-Tenant Prevention

Chain governance ensures agents from one tenant cannot inject prompts into agents of another tenant through the `organization_id` filter.

## Integration Points

### MCP Governance

When using MCP (Model Context Protocol) servers, chain governance integrates automatically:

```python
# In mcp_governance_service.py
if action_type == "llm_call":
    chain_result = prompt_service.analyze_llm_chain(
        source_agent_id=current_agent,
        target_agent_id=target_agent,
        prompt_content=mcp_request.prompt
    )
    if not chain_result["allowed"]:
        return MCPDenied(reason=chain_result["reason"])
```

### Action Submission

Chain analysis is part of the standard `/api/v1/actions/submit` flow when `action_type` indicates inter-agent communication.

## Compliance

- **SOC 2 CC6.1**: Access control and monitoring
- **NIST 800-53 SI-10**: Information Input Validation
- **OWASP LLM Top 10**: LLM01 (Prompt Injection), LLM07 (Insecure Plugin Design)

## Best Practices

1. **Set reasonable depth limits** - Default of 5 is sufficient for most architectures
2. **Monitor blocked chains** - Review `/chain-log` regularly for anomalies
3. **Use unique agent IDs** - Helps with audit trail analysis
4. **Hash sensitive content** - Only hashes stored, never raw prompts
5. **Enable in monitor mode first** - Evaluate before enforcing blocks
