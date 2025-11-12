# ARCH-004: Enterprise Compliance Mapping - Quick Reference

## TL;DR

ARCH-004 replaces generic NIST/MITRE mappings with **action-specific** and **context-aware** enterprise-grade compliance controls.

---

## Key Improvements

| Aspect | Old Behavior | New Behavior |
|--------|--------------|--------------|
| Payment API calls | SI-3 (Malicious Code) | **AU-9 (Audit Protection)** |
| Credential operations | SI-3 (Generic) | **IA-5 (Authenticator Management)** |
| Schema changes | AC-3 (Wrong tactic) | **CM-3 (Configuration Change)** |
| Privilege operations | Generic | **AC-6 (Least Privilege)** |
| Data exfiltration | SI-4 (Generic) | **AC-4 (Information Flow)** |

---

## Context Override Keywords

### Financial Transactions → AU-9 (Audit) + TA0040 (Impact)
```
payment, financial, transaction, billing, stripe, paypal, invoice, charge, refund
```

### Credential Access → IA-5 (Authenticator) + TA0006 (Credential Access)
```
credential, password, secret, token, api key, private key, auth
```

### Privilege Escalation → AC-6 (Least Privilege) + TA0004 (Privilege Escalation)
```
privilege, admin, administrator, sudo, root, superuser, elevated, escalate
```

### Data Exfiltration → AC-4 (Information Flow) + TA0010 (Exfiltration)
```
exfiltrate, exfil, leak, steal, copy sensitive, export
```

### Schema Changes → CM-3 (Configuration Change) + TA0040 (Impact)
```
schema, alter table, drop table, create table, truncate
```

---

## Action Type Mappings

| Action Type | NIST Control | MITRE Tactic | Use Case |
|-------------|--------------|--------------|----------|
| database_write | AC-3 | TA0006 | Database modifications |
| database_read | AU-2 | TA0009 | Database queries |
| database_delete | AC-3 | TA0040 | Data deletion |
| api_call | SI-3 | TA0002 | Generic API calls |
| financial_transaction | AU-9 | TA0040 | Payment processing |
| credentials_access | IA-5 | TA0006 | Secret/credential access |
| system_modification | CM-3 | TA0005 | System config changes |
| file_access | AC-4 | TA0009 | File operations |
| privilege_escalation | AC-6 | TA0004 | Permission elevation |
| data_export | AC-4 | TA0010 | Data extraction |
| schema_change | CM-3 | TA0040 | Database schema changes |
| user_create | AC-2 | TA0003 | User provisioning |
| permission_grant | AC-6 | TA0004 | Permission changes |

---

## Priority Order

```
1. Context Keywords (highest priority)
   └─> Detects: financial, credential, privilege, exfiltration, schema keywords

2. Action Type
   └─> Uses predefined mapping for 20+ action types

3. Default Fallback
   └─> SI-3 (Malicious Code Protection) + TA0002 (Execution)
```

---

## Example Usage

### Python API
```python
from enrichment import evaluate_action_enrichment

# Example 1: Payment processing
result = evaluate_action_enrichment(
    action_type="api_call",
    description="Process payment via Stripe for $49.99",
    db=db_session,
    action_id=123
)
# Returns: AU-9 (Audit Protection) + TA0040 (Impact)

# Example 2: Schema change
result = evaluate_action_enrichment(
    action_type="database_write",
    description="ALTER TABLE users ADD COLUMN email",
    db=db_session,
    action_id=124
)
# Returns: CM-3 (Configuration Change) + TA0040 (Impact)

# Example 3: Generic API call
result = evaluate_action_enrichment(
    action_type="api_call",
    description="Fetch weather data from OpenWeather API",
    db=db_session,
    action_id=125
)
# Returns: SI-3 (Malicious Code Protection) + TA0002 (Execution)
```

---

## Log Output Examples

### Context Override
```
INFO - ARCH-004 ENTERPRISE COMPLIANCE: Context override 'financial_transaction' detected
       - action_type=api_call, NIST=AU-9, MITRE=TA0040
```

### Action Type Mapping
```
INFO - ARCH-004 ENTERPRISE COMPLIANCE: Action type mapping
       - action_type=database_write, NIST=AC-3 (Access Control),
       MITRE=TA0006 (Credential Access)
```

### Default Fallback
```
INFO - ARCH-004 ENTERPRISE COMPLIANCE: Using default mapping
       for unknown action_type=custom_action, NIST=SI-3, MITRE=TA0002
```

---

## Testing

### Run Test Suite
```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
python test_enterprise_compliance.py
```

### Expected Output
```
================================================================================
TEST SUMMARY: 8/8 passed, 0/8 failed
================================================================================
```

---

## Compliance Coverage

### NIST SP 800-53 Controls
```
AC-2  Account Management
AC-3  Access Enforcement
AC-4  Information Flow Enforcement
AC-6  Least Privilege
AU-2  Audit Events
AU-9  Protection of Audit Information
CM-3  Configuration Change Control
IA-5  Authenticator Management
SC-7  Boundary Protection
SI-3  Malicious Code Protection
SI-12 Information Handling and Retention
```

### MITRE ATT&CK Tactics
```
TA0002  Execution
TA0003  Persistence
TA0004  Privilege Escalation
TA0005  Defense Evasion
TA0006  Credential Access
TA0009  Collection
TA0010  Exfiltration
TA0011  Command and Control
TA0040  Impact
```

---

## Integration Points

### Where It's Used
1. **Risk Assessment** (`evaluate_action_enrichment()`)
   - Called by authorization routes
   - Used in policy evaluation
   - Feeds into CVSS scoring

2. **Audit Logging**
   - All mappings logged with full context
   - Compliance audit trail

3. **Frontend Display**
   - Risk dashboards show NIST/MITRE mappings
   - Authorization center displays compliance info

---

## Maintenance

### Adding New Action Types
```python
# In ENTERPRISE_COMPLIANCE_MAPPINGS dictionary
"new_action_type": {
    "nist_control": "XX-Y",
    "nist_family": "Control Family Name",
    "nist_description": "Control Description",
    "mitre_tactic": "TA00XX",
    "mitre_tactic_name": "Tactic Name",
    "mitre_technique": "T1XXX",
    "mitre_technique_name": "Technique Name"
}
```

### Adding New Context Overrides
```python
# In get_enterprise_compliance_mapping() function
if any(keyword in description_lower for keyword in ["new_keyword", "another_keyword"]):
    mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get("specific_action_type")
    logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Context override 'specific_action_type' detected...")
    return mapping
```

---

## Performance

- **Lookup Time**: O(1) dictionary access
- **Context Matching**: O(n) keyword scan (optimized with `any()`)
- **Database Impact**: None (code-only)
- **Memory Impact**: ~5KB (mapping dictionary)

---

## Backward Compatibility

- ✅ All existing API endpoints work unchanged
- ✅ Response format preserved
- ✅ Risk levels unchanged
- ✅ CVSS integration maintained
- ✅ No database migrations required
- ✅ No configuration changes needed

---

## Resources

### Official Documentation
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [MITRE ATT&CK](https://attack.mitre.org/)

### Implementation Files
- **Main Code**: `/Users/mac_001/OW_AI_Project/ow-ai-backend/enrichment.py`
- **Test Suite**: `/Users/mac_001/OW_AI_Project/ow-ai-backend/test_enterprise_compliance.py`
- **Full Documentation**: `ARCH-004_ENTERPRISE_COMPLIANCE_IMPLEMENTATION.md`
- **Comparison Guide**: `ARCH-004_BEFORE_AFTER_COMPARISON.md`

---

## Support

### Common Issues

**Q: Action type not getting correct mapping?**
A: Check if context override is taking priority. Context keywords override action type.

**Q: Want to add new context keywords?**
A: Update `get_enterprise_compliance_mapping()` function and add to appropriate keyword list.

**Q: Need different NIST control?**
A: Update `ENTERPRISE_COMPLIANCE_MAPPINGS` dictionary for that action type.

**Q: Database queries still running?**
A: Yes, by design. They run as secondary enrichment but don't override enterprise mappings.

---

**Last Updated**: 2025-11-11
**Version**: ARCH-004 (Current)
**Status**: Production Ready
