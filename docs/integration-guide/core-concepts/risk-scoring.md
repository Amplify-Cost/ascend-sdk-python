---
title: Risk Scoring
sidebar_position: 1
---

# Risk Scoring

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-CORE-005 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Ascend's Enterprise Hybrid Multi-Factor Risk Scoring Engine (v2.0.0) evaluates every agent action and assigns a risk score from 0-100. This score determines how the action is routed through your governance workflows.

**Source:** `services/enterprise_risk_calculator_v2.py`

## Risk Score Ranges

**Source:** `enterprise_risk_calculator_v2.py:595-605`

| Range | Level | Routing |
|-------|-------|---------|
| 0-24 | Minimal | Auto-approve |
| 25-44 | Low | Quick approval or auto-approve |
| 45-69 | Medium | Single approval required |
| 70-84 | High | Senior approval required |
| 85-100 | Critical | Block and alert security team |

## Algorithm Overview

**Source:** `enterprise_risk_calculator_v2.py:1-42`

The risk engine combines 5 components:

1. **Environment Risk** (35% weight, 0-35 points)
2. **Data Sensitivity** (30% weight, 0-30 points)
3. **Action Type Risk** (25% weight, 0-25 points)
4. **Operational Context** (10% weight, 0-10 points)
5. **Resource Type Multiplier** (0.8x - 1.2x scaling)

## Component 1: Environment Risk (0-35 points)

**Source:** `enterprise_risk_calculator_v2.py:72-84`

Different environments carry inherent risk levels:

```python
# Source: enterprise_risk_calculator_v2.py:72-82
ENVIRONMENT_SCORES = {
    'production': 35,      # Maximum environmental risk
    'prod': 35,            # Alias
    'staging': 18,         # Medium environmental risk
    'stage': 18,           # Alias
    'development': 5,      # Low environmental risk
    'dev': 5,              # Alias
    'sandbox': 2,          # Minimal environmental risk
    'test': 3,             # Minimal environmental risk
    'unknown': 35          # Fail-safe: assume production
}
```

| Environment | Score | Rationale |
|-------------|-------|-----------|
| Production | 35 | Live data, customer impact, business continuity |
| Staging | 18 | Pre-production testing, isolated from customers |
| Development | 5 | Development environment, synthetic data |
| Sandbox | 2 | Isolated test environment |
| Unknown | 35 | Conservative fail-safe assumption |

## Component 2: Data Sensitivity (0-30 points)

**Source:** `enterprise_risk_calculator_v2.py:90-186, 319-402`

Enhanced PII detection with keyword matching and regex pattern recognition:

### Keyword Detection

```python
# Source: enterprise_risk_calculator_v2.py:92-108
PII_KEYWORDS = {
    'high_sensitivity': [
        'ssn', 'social_security', 'credit_card', 'card_number', 'cvv', 'cvc',
        'password', 'credential', 'secret', 'api_key', 'private_key', 'token',
        'financial', 'payment', 'billing', 'bank_account', 'routing_number',
        'passport', 'drivers_license', 'national_id', 'tax_id', 'ein'
    ],
    'medium_sensitivity': [
        'email', 'phone', 'address', 'name', 'dob', 'date_of_birth',
        'customer', 'user', 'patient', 'employee', 'personal', 'pii',
        'birthdate', 'zip_code', 'postal_code', 'ip_address'
    ],
    'business_sensitive': [
        'proprietary', 'confidential', 'internal', 'strategic',
        'revenue', 'profit', 'contract', 'trade_secret', 'competitive',
        'acquisition', 'merger', 'salary', 'compensation'
    ]
}
```

### Pattern Detection

**Source:** `enterprise_risk_calculator_v2.py:110-117`

```python
# Regex patterns for actual PII data
PII_PATTERNS = {
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # XXX-XX-XXXX
    'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
}
```

### Scoring Logic

**Source:** `enterprise_risk_calculator_v2.py:370-401`

| Condition | Score | Explanation |
|-----------|-------|-------------|
| PII + High Keywords + Pattern | 30 | Triple threat detection |
| PII + Pattern Match | 28 | PII flag with actual data detected |
| PII + High Keywords | 27 | PII flag with financial/credential terms |
| PII Flag Only | 25 | PII flagged without additional indicators |
| Pattern Match Only | 22 | Actual PII data detected without flag |
| High Sensitivity Keywords | 20 | Financial/credential terms |
| Customer Data Keywords | 18 | Customer/user data references |
| Business Sensitive | 12 | Internal/strategic data |
| Test/Synthetic Data | 0 | Explicitly marked as test data |
| Generic Data | 5 | Default for unclassified data |

## Component 3: Action Type Risk (0-25 points)

**Source:** `enterprise_risk_calculator_v2.py:123-145`

Action types ranked by inherent risk:

```python
# Source: enterprise_risk_calculator_v2.py:123-145
ACTION_TYPE_BASE_SCORES = {
    'delete': 25,          # Highest risk (destructive, irreversible)
    'drop': 25,
    'destroy': 25,
    'terminate': 25,
    'write': 23,           # High risk (modifies state)
    'create': 21,          # High risk (creates resources)
    'update': 21,
    'modify': 19,          # Medium-high risk
    'put': 23,
    'post': 21,
    'patch': 19,
    'execute': 16,         # Medium risk (runs code)
    'run': 16,
    'invoke': 16,
    'read': 10,            # Low risk (read-only)
    'list': 7,
    'describe': 7,
    'get': 10,
    'query': 10,
    'scan': 12,            # Low-medium risk (reads all data)
    'unknown': 19          # Fail-safe: assume moderate risk
}
```

### CVSS Integration

**Source:** `enterprise_risk_calculator_v2.py:541-552`

If CVSS score is provided, it overrides action type lookup:

```python
# CVSS score 0-10, normalize to 0-25
if cvss_score is not None:
    action_score = min(int(cvss_score * 2.5), 25)
else:
    # Fallback to action type lookup
    action_score = ACTION_TYPE_BASE_SCORES.get(action_type.lower(), 19)
```

## Component 4: Operational Context (0-10 points)

**Source:** `enterprise_risk_calculator_v2.py:408-445`

Contextual factors that affect risk:

```python
# Source: enterprise_risk_calculator_v2.py:423-444
def _calculate_operational_context_score(
    self,
    action_metadata: Optional[Dict] = None
) -> int:
    """Calculate operational context risk score (0-10 points)"""

    score = 8  # Baseline: conservative default

    if action_metadata:
        # Maintenance window detection
        if action_metadata.get('maintenance_window'):
            score = max(3, score - 5)  # Reduce risk during maintenance
            return score

        # Peak hours detection
        if action_metadata.get('peak_hours'):
            score = min(10, score + 2)  # Increase risk during peak hours
            return score

    return score
```

| Factor | Risk Modifier | Example |
|--------|---------------|---------|
| Baseline | 8/10 points | Conservative default |
| Maintenance Window | -5 points (min 3) | Approved change window |
| Peak Hours | +2 points (max 10) | Business hours with high traffic |

**Future Enhancements:**
- User risk profile integration
- Anomaly detection (unusual action for agent)
- Recent action frequency analysis

## Component 5: Resource Type Multiplier

**Source:** `enterprise_risk_calculator_v2.py:151-186`

Different AWS resource types carry different risk profiles:

```python
# Source: enterprise_risk_calculator_v2.py:153-186
RESOURCE_TYPE_MULTIPLIERS = {
    # Critical Infrastructure (Higher Risk)
    'rds': 1.2,            # Relational databases
    'database': 1.2,
    'dynamodb': 1.15,      # NoSQL database
    'aurora': 1.2,
    'redshift': 1.15,      # Data warehouse

    # Storage (Standard Risk)
    's3': 1.0,             # Object storage
    'ebs': 1.05,           # Block storage
    'efs': 1.05,           # File storage
    'glacier': 0.95,       # Archive (less critical)

    # Compute (Lower Risk - Stateless)
    'lambda': 0.8,         # Serverless functions
    'ec2': 1.0,            # Virtual machines
    'ecs': 0.9,            # Container service
    'fargate': 0.85,       # Serverless containers

    # Networking & Security
    'vpc': 1.1,            # Network infrastructure
    'security_group': 1.15,# Security rules
    'iam': 1.2,            # Identity & access (critical)
    'kms': 1.2,            # Encryption keys (critical)

    # Other Services
    'sns': 0.9,            # Notifications
    'sqs': 0.9,            # Message queues
    'cloudwatch': 0.85,    # Monitoring

    'unknown': 1.0         # No adjustment
}
```

## Final Score Calculation

**Source:** `enterprise_risk_calculator_v2.py:558-593`

### Step 1: Base Score Calculation

```python
# Source: enterprise_risk_calculator_v2.py:558
base_score = environment_score + sensitivity_score + action_score + context_score
```

### Step 2: Risk Amplification

**Source:** `enterprise_risk_calculator_v2.py:560-577`

```python
amplification_bonus = 0

if environment_score >= 30:  # Production environment
    if sensitivity_score >= 20:  # PII data
        if action_score >= 20:  # Write/Delete action
            amplification_bonus = 10  # +10 for Production + PII + Destructive
        elif action_score >= 15:
            amplification_bonus = 6   # +6 for Production + PII + Moderate
    elif action_score >= 20:  # Destructive action (no PII)
        amplification_bonus = 8       # +8 for Production + Destructive
    elif action_score >= 15:  # Write action (no PII)
        amplification_bonus = 5       # +5 for Production + Write
```

### Step 3: Apply Resource Multiplier

**Source:** `enterprise_risk_calculator_v2.py:579-593`

```python
pre_multiplier_score = min(base_score + amplification_bonus, 100)

# Apply resource type multiplier (0.8x - 1.2x)
final_score = min(int(pre_multiplier_score * resource_multiplier), 100)
```

### Complete Formula

```
final_score = min(
    (environment_score + sensitivity_score + action_score + context_score + amplification_bonus)
    × resource_multiplier,
    100
)
```

## Example Calculations

### Example 1: Dev Read, No PII

```
Environment: development = 5
Sensitivity: generic data = 5
Action: read = 10
Context: baseline = 8
Amplification: 0 (not production)
Resource: s3 = 1.0x

Base = 5 + 5 + 10 + 8 = 28
Final = 28 × 1.0 = 28 (LOW)
```

### Example 2: Production Write, No PII

```
Environment: production = 35
Sensitivity: customer data = 18
Action: write = 23
Context: baseline = 8
Amplification: 5 (production + write)
Resource: rds = 1.2x

Base = 35 + 18 + 23 + 8 + 5 = 89
Final = 89 × 1.2 = 106 → capped at 100 (CRITICAL)
```

### Example 3: Production Delete with PII

```
Environment: production = 35
Sensitivity: PII + pattern = 28
Action: delete = 25
Context: baseline = 8
Amplification: 10 (production + PII + destructive)
Resource: database = 1.2x

Base = 35 + 28 + 25 + 8 + 10 = 106
Final = 106 × 1.2 = 127 → capped at 100 (CRITICAL)
```

## Error Handling & Fallbacks

**Source:** `enterprise_risk_calculator_v2.py:189-313`

### Input Validation

**Source:** `enterprise_risk_calculator_v2.py:192-232`

```python
def _validate_inputs(
    self,
    cvss_score: Optional[float],
    environment: str,
    action_type: str,
    contains_pii: bool,
    resource_name: str,
    description: str
) -> None:
    """Validate all input parameters"""

    # CVSS score range check
    if cvss_score is not None:
        if not (0 <= cvss_score <= 10):
            raise ValueError(f"CVSS score must be 0-10, got: {cvss_score}")

    # Environment validation
    if not environment or not isinstance(environment, str):
        raise ValueError(f"Environment must be non-empty string")

    # Action type validation
    if not action_type or not isinstance(action_type, str):
        raise ValueError(f"Action type must be non-empty string")

    # Boolean validation
    if not isinstance(contains_pii, bool):
        raise ValueError(f"contains_pii must be boolean")
```

### Safe Fallback Score

**Source:** `enterprise_risk_calculator_v2.py:238-286`

If validation fails, return conservative fallback:

```python
def _get_safe_fallback_score(
    self,
    environment: Optional[str] = None,
    action_type: Optional[str] = None
) -> Dict:
    """Return conservative fallback score when inputs are questionable"""

    # Base fallback depends on environment
    if environment in ['development', 'dev']:
        fallback_score = 50  # More permissive for dev
    elif environment in ['staging', 'stage']:
        fallback_score = 65  # Medium for staging
    else:
        fallback_score = 75  # Conservative for production/unknown

    # Adjust for dangerous action types
    if action_type in ['delete', 'drop', 'destroy']:
        fallback_score = min(fallback_score + 10, 95)
    elif action_type in ['write', 'create', 'update']:
        fallback_score = min(fallback_score + 5, 90)

    return {
        "risk_score": fallback_score,
        "risk_level": "high" if fallback_score >= 70 else "medium",
        "fallback_mode": True
    }
```

### Maximum Risk Score

**Source:** `enterprise_risk_calculator_v2.py:288-313`

For critical failures, return near-maximum score:

```python
def _get_maximum_risk_score(self) -> Dict:
    """Return maximum risk score for critical failures"""

    max_score = 95  # Not 100 to allow L3/L4 routing

    return {
        "risk_score": max_score,
        "risk_level": "critical",
        "fallback_mode": True,
        "critical_failure": True
    }
```

## Algorithm Metadata

**Source:** `enterprise_risk_calculator_v2.py:60-66`

Every calculation includes version information for auditability:

```python
ALGORITHM_VERSION = "2.0.0"
ALGORITHM_NAME = "Enterprise Hybrid Multi-Factor Risk Scoring"
ALGORITHM_DATE = "2025-11-14"
ALGORITHM_AUTHOR = "Donald King (OW-kai Enterprise)"
```

## Response Format

**Source:** `enterprise_risk_calculator_v2.py:639-656`

```json
{
    "risk_score": 75,
    "risk_level": "high",
    "breakdown": {
        "environment_score": 35,
        "sensitivity_score": 18,
        "action_score": 23,
        "context_score": 8,
        "amplification_bonus": 5,
        "resource_multiplier": 1.2
    },
    "reasoning": "Production environment (+35); Customer data (+18); Modifying action (+23); Resource type adjustment (×1.2)",
    "formula": "(35 env + 18 data + 23 action + 8 context + 5 amp) × 1.2 = 106 → capped at 100",
    "algorithm_version": "2.0.0",
    "algorithm_name": "Enterprise Hybrid Multi-Factor Risk Scoring",
    "calculation_timestamp": "2025-12-04T10:30:45.123Z",
    "fallback_mode": false
}
```

## Best Practices

### 1. Always Provide Environment

```python
# Good: Explicit environment
risk = calculate_risk(
    environment="production",  # Clear classification
    action_type="write",
    contains_pii=True
)

# Bad: Unknown environment
risk = calculate_risk(
    environment="prod-staging-hybrid",  # Will default to production (35 points)
    action_type="write"
)
```

### 2. Flag PII Explicitly

```python
# Good: PII flagged + descriptive text
risk = calculate_risk(
    resource_name="customer_profiles",
    description="Update customer email and phone",
    contains_pii=True  # Explicit flag
)

# Bad: PII not flagged
risk = calculate_risk(
    resource_name="data",
    description="Update records",
    contains_pii=False  # Will miss PII scoring
)
```

### 3. Use Resource Type for AWS Operations

```python
# Good: Resource type specified
risk = calculate_risk(
    resource_name="customer_rds_instance",
    resource_type="rds",  # 1.2x multiplier applied
    action_type="delete"
)

# Bad: No resource type
risk = calculate_risk(
    resource_name="customer_rds_instance",
    # resource_type not specified (1.0x default)
)
```

### 4. Leverage Operational Context

```python
# Good: Maintenance window flagged
risk = calculate_risk(
    action_type="delete",
    action_metadata={
        "maintenance_window": True  # -5 points reduction
    }
)

# Good: Peak hours awareness
risk = calculate_risk(
    action_type="write",
    action_metadata={
        "peak_hours": True  # +2 points increase
    }
)
```

## Next Steps

- [Approval Workflows](/core-concepts/approval-workflows) - Configure human review based on risk levels
- [How Ascend Works](/core-concepts/how-ascend-works) - Overall architecture
- [Audit Logging](/core-concepts/audit-logging) - Risk score audit trails
