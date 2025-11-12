# Risk Assessment System Audit Report

**Date:** 2025-11-11
**Engineer:** OW-KAI Platform Engineering Team
**Scope:** Dynamic Risk Scoring, MITRE/NIST Mappings, AI Recommendations
**Status:** 🔴 CRITICAL ISSUES IDENTIFIED

---

## Executive Summary

The current risk assessment system has **6 critical enterprise issues** causing:
- 80% of actions receiving identical risk scores (82, 68, 49, 38)
- MITRE/NIST database with 619 mappings completely unused
- Static recommendations instead of AI-generated context-aware guidance
- Payment processing scored as LOW risk (38) instead of HIGH
- Database writes to production scored as MEDIUM (49) instead of CRITICAL

**Impact:** High-risk financial and production actions are not triggering proper approval workflows.

---

## Issue #1: Static CVSS Scores (CRITICAL)

### Current Behavior
All actions of the same type receive identical CVSS scores:

| Action Type | Example Actions | CVSS Score | Risk Score |
|-------------|----------------|------------|------------|
| system_modification | Firewall updates, ML deployments, Admin user creation | 8.2 | 82 |
| data_export | PII exports, Customer data downloads | 6.8 | 68 |
| database_write | Production schema changes, Data updates | 4.9 | 49 |
| api_call | Payment processing, API key rotation | 3.8 | 38 |

### Root Cause
**File:** `services/cvss_auto_mapper.py:119-132`

The `_normalize_action_type()` function uses broad keyword matching:
```python
def _normalize_action_type(self, action_type: str) -> str:
    action_lower = action_type.lower()
    if any(x in action_lower for x in ["system", "admin", "config", "root"]):
        return "system_modification"  # All get 8.2
    elif any(x in action_lower for x in ["exfil", "export", "download", "copy"]):
        return "data_exfiltration"  # All get 6.8
    elif any(x in action_lower for x in ["write", "update", "modify", "database"]):
        return "database_write"  # All get 4.9
    else:
        return "api_call"  # All get 3.8
```

### Evidence from Simulator
```
Action: "Deploying ML model to production" → 82
Action: "Updating firewall rules" → 82
Action: "Creating admin user" → 82
Action: "Processing payment via Stripe" → 38 ❌ (Should be HIGH)
Action: "Executing database schema changes" → 49 ❌ (Should be CRITICAL)
```

### Enterprise Impact
- Payment processing actions bypass approval (38 < 70 threshold)
- Production database changes bypass approval (49 < 70 threshold)
- All system modifications trigger alerts regardless of actual risk

---

## Issue #2: MITRE/NIST Database Unused (CRITICAL)

### Current Behavior
Code returns hardcoded MITRE/NIST values for all actions:

**File:** `enrichment.py:256-282`
```python
if "exfiltrat" in action_lower:
    result = {"mitre_technique": "T1041", "nist_control": "SI-4", ...}
elif "privilege" in action_lower:
    result = {"mitre_technique": "T1068", "nist_control": "AC-6", ...}
else:
    result = {"mitre_technique": "T1059", "nist_control": "SI-3", ...}
```

### Database Population Status
- `mitre_techniques`: 31 techniques ✅
- `mitre_technique_mappings`: 303 mappings ✅
- `nist_controls`: 44 controls ✅
- `nist_control_mappings`: 316 mappings ✅

**Total: 619 mappings in database, 0 used by code**

### Evidence from Simulator
All `system_modification` actions return:
- MITRE Technique: `T1059 - Command and Scripting Interpreter`
- NIST Control: `SI-3`

Should return:
- Firewall changes → `T1562.004 - Disable System Firewall`, `SC-7`
- Admin user creation → `T1136 - Create Account`, `AC-2`
- ML deployment → `T1055 - Process Injection`, `CM-3`

---

## Issue #3: Static Recommendations (HIGH)

### Current Behavior
**File:** `enrichment.py:263, 272, 281, 293, 302, 311, 322`

All actions of same type get identical recommendations:
```python
"recommendation": "Immediately investigate potential data exfiltration..."
"recommendation": "Monitor execution activities and validate legitimacy..."
"recommendation": "Review user permissions and investigate unauthorized..."
```

### What's Missing
- No context awareness (production vs dev, PII vs regular data)
- No AI-generated natural language
- No specific action guidance

### Example
**Current:**
> "Monitor execution activities and validate legitimacy of commands."

**Should be:**
> "Review firewall rule changes for production environment. Verify no unauthorized ports (22, 3389, 445) are exposed to public internet. Validate change follows CAB approval process per NIST SC-7."

---

## Issue #4: Context Elevation Not Updating CVSS (HIGH)

### Root Cause
**File:** `enrichment.py:390-436`

CVSS score calculated BEFORE context elevation:
1. Calculate CVSS with base metrics → 8.2
2. Detect production/PII/financial context
3. Elevate `risk_level` from "medium" to "high"
4. **But `cvss_score` stays 8.2** (not recalculated)

### Flow Issue
```
enrichment.py:412-419 → Calculate CVSS (8.2)
enrichment.py:422 → Set result["cvss_score"] = 8.2
enrichment.py:329-377 → Context elevation changes risk_level
enrichment.py:422 → cvss_score still 8.2 (not updated)
authorization_routes.py:2185 → risk_score = 8.2 * 10 = 82
```

---

## Issue #5: Database Writes Underscored (CRITICAL)

### Root Cause
**File:** `services/cvss_auto_mapper.py:34-43`

CVSS metrics for `database_write`:
```python
"database_write": {
    "scope": "UNCHANGED",  # ❌ Should be CHANGED
    "confidentiality_impact": "NONE",  # ❌ Should be HIGH
    "integrity_impact": "HIGH",  # ✅ Correct
    "availability_impact": "NONE"  # ❌ Should be HIGH
}
```

Result: CVSS 4.9 (MEDIUM) instead of 9.0+ (CRITICAL)

### Impact
Production database writes bypass approval:
- "Executing production database schema changes" → 49 (approved)
- Threshold for approval: 70
- **49 < 70 = Bypasses approval workflow** ❌

---

## Issue #6: Payment Processing Low Risk (CRITICAL)

### Root Cause
**File:** `cvss_auto_mapper.py:119-132`

Action: "Processing customer payment via Stripe API"
- Type: `api_call`
- No keywords matching "system", "export", "database"
- **Defaults to `api_call` category**

**File:** `cvss_auto_mapper.py:69-79`
```python
"api_call": {
    "confidentiality_impact": "LOW",  # ❌ PII involved
    "integrity_impact": "LOW",  # ❌ Financial transaction
    "availability_impact": "NONE"  # ❌ Revenue impact
}
```

Result: CVSS 3.8 → Risk Score 38 (LOW)

### Impact
- Payment processing bypasses approval (38 < 70)
- No alerts triggered (38 < 80)
- PCI-DSS compliance violation
- Financial transactions unmonitored

---

## Summary of Critical Issues

| Issue | Severity | Impact | Affected Actions |
|-------|----------|--------|------------------|
| Static CVSS scores | 🔴 CRITICAL | No differentiation of risk | All actions |
| Unused database mappings | 🔴 CRITICAL | Incorrect MITRE/NIST attribution | All actions |
| Static recommendations | 🟠 HIGH | No context-aware guidance | All actions |
| CVSS not recalculated | 🟠 HIGH | Context elevation ineffective | High-risk actions |
| Database writes underscored | 🔴 CRITICAL | Production changes bypass approval | Database operations |
| Payment processing low risk | 🔴 CRITICAL | Financial transactions unmonitored | API calls |

---

## Recommended Fixes

### Fix #1: Dynamic CVSS with Context Awareness
- Adjust CVSS metrics BEFORE calculation based on context flags
- Production system → Scope: CHANGED, Availability: HIGH
- PII data → Confidentiality: HIGH
- Financial transaction → Integrity: HIGH, Availability: HIGH

### Fix #2: Database-Driven MITRE/NIST Mapping
- Query `mitre_technique_mappings` table for action_type + keywords
- Use `relevance` column to prioritize mappings
- Fall back to static mappings only if no DB match

### Fix #3: AI-Generated Recommendations
- Call LLM with action context to generate recommendations
- Include risk factors, MITRE tactics, NIST controls in prompt
- Cache common patterns to reduce API calls

### Fix #4: Enhanced Database Write Metrics
- Update CVSS base metrics for `database_write`
- Set Scope: CHANGED, C: HIGH, I: HIGH, A: HIGH
- Result: CVSS 9.0+ (CRITICAL)

### Fix #5: Financial Action Detection
- Add financial keywords to context detection
- Adjust CVSS metrics for financial transactions
- Result: Payment processing gets HIGH risk (85+)

### Fix #6: Recalculate CVSS After Context Detection
- Detect context flags FIRST
- Adjust CVSS metrics based on flags
- Calculate CVSS with adjusted metrics
- Return final score

---

## Testing Plan

### Test Case 1: Dynamic CVSS Scores
**Input:**
- Action 1: "Deploying ML model to development"
- Action 2: "Deploying ML model to production"

**Expected:**
- Action 1: CVSS ~6.5 (Scope: UNCHANGED)
- Action 2: CVSS ~8.5 (Scope: CHANGED, production detected)

### Test Case 2: Database-Driven MITRE Mapping
**Input:**
- Action: "Updating production firewall rules"

**Expected:**
- MITRE Technique: T1562.004 (from database)
- NIST Control: SC-7 (from database)
- NOT T1059 (hardcoded fallback)

### Test Case 3: AI-Generated Recommendations
**Input:**
- Action: "Processing customer payment via Stripe API"

**Expected:**
- Recommendation contains: "PCI-DSS", "financial", "payment gateway", specific guidance
- NOT generic "Monitor execution activities..."

### Test Case 4: Payment Processing High Risk
**Input:**
- Action: "Processing customer payment via Stripe API"

**Expected:**
- CVSS: 8.0+ (Financial context detected)
- Risk Score: 80+
- Status: pending_approval
- Alert: Triggered

### Test Case 5: Database Write Critical Risk
**Input:**
- Action: "Executing production database schema changes"

**Expected:**
- CVSS: 9.0+ (Scope: CHANGED, C/I/A: HIGH)
- Risk Score: 90+
- Status: pending_approval
- Alert: Critical severity

---

## Next Steps

1. ✅ **AUDIT COMPLETE** - Issues documented
2. ⏳ **PLAN** - Design enterprise-grade fixes
3. ⏳ **IMPLEMENT** - Code changes with error handling
4. ⏳ **TEST** - Verify with simulator and evidence
5. ⏳ **DEPLOY** - Production deployment after verification

---

**Report Generated:** 2025-11-11
**Generated By:** OW-KAI Platform Engineering Team
**Classification:** Internal - Engineering Use
