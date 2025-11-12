# Risk Assessment Enhancement - Implementation Plan

**Date:** 2025-11-11
**Engineer:** OW-KAI Platform Engineering Team
**Architecture Version:** ARCH-003
**Status:** 📋 PLANNING COMPLETE

---

## Overview

This document outlines the enterprise-grade implementation plan for fixing 6 critical issues in the risk assessment system identified in the audit.

---

## Implementation Phases

### Phase 1: Enhanced CVSS Auto-Mapper (CRITICAL - Priority 1)

**File:** `services/cvss_auto_mapper.py`

#### Changes Required

1. **Fix Database Write Metrics** (Lines 34-43)
   ```python
   "database_write": {
       "scope": "CHANGED",  # Was: UNCHANGED
       "confidentiality_impact": "HIGH",  # Was: NONE
       "integrity_impact": "HIGH",
       "availability_impact": "HIGH"  # Was: NONE
   }
   ```
   - Result: CVSS 4.9 → 9.0+ (CRITICAL)

2. **Enhance Context Adjustment** (Lines 147-end)
   - Add production system detection → Scope: CHANGED, A: HIGH
   - Add PII detection → C: HIGH
   - Add financial detection → I: HIGH, A: HIGH
   - Add privilege escalation detection → PR: HIGH, Scope: CHANGED

3. **Add Financial Action Type** (New mapping)
   ```python
   "financial_transaction": {
       "attack_vector": "NETWORK",
       "attack_complexity": "LOW",
       "privileges_required": "LOW",
       "user_interaction": "NONE",
       "scope": "CHANGED",
       "confidentiality_impact": "HIGH",
       "integrity_impact": "HIGH",
       "availability_impact": "HIGH"
   }
   ```

4. **Improve Normalization** (Lines 119-132)
   - Add financial keywords: payment, transaction, billing, stripe, paypal
   - Add privilege keywords: admin, root, sudo, privilege
   - Check description in addition to action_type

#### Enterprise Features
- Comprehensive error handling with try/except
- Detailed logging of metric adjustments
- Backward compatibility (all existing code works)
- Performance optimization (cache normalized types)

#### Testing
- Test Case 1: "Processing payment" → CVSS 8.5+, not 3.8
- Test Case 2: "Database write to production" → CVSS 9.0+, not 4.9
- Test Case 3: "Creating admin user" → CVSS 8.5+
- Test Case 4: "Deploying ML to dev" → CVSS 6.5, not 8.2

---

### Phase 2: Database-Driven MITRE/NIST Mapping (CRITICAL - Priority 2)

**File:** `enrichment.py`

#### Changes Required

1. **Add Database Query Function** (New function after line 65)
   ```python
   def query_mitre_mappings(db: Session, action_type: str, keywords: List[str]) -> Dict:
       """Query database for best MITRE/NIST mappings"""
       # Join tables to find mappings
       # Filter by action_type and keywords
       # Order by relevance DESC
       # Return top result
   ```

2. **Add Fallback Logic** (Lines 254-323)
   - Try database query FIRST
   - If found, use database mappings
   - If not found, use keyword matching (existing logic)
   - Log whether DB or fallback was used

3. **Add Mapping Cache** (Performance optimization)
   - Cache mappings by (action_type, keyword_hash)
   - TTL: 1 hour
   - Reduces database queries by 90%

#### Enterprise Features
- Graceful degradation (if DB fails, use static mappings)
- Connection pool reuse (no new connections)
- Query optimization (indexed lookups)
- Comprehensive logging (DB hit/miss rates)

#### Testing
- Test Case 1: "Firewall update" → T1562.004 (from DB), not T1059
- Test Case 2: "Admin user" → T1136 (from DB), not T1059
- Test Case 3: Unknown action → Fallback to static mapping
- Test Case 4: DB connection failure → Graceful fallback

---

### Phase 3: AI-Generated Recommendations (HIGH - Priority 3)

**File:** `services/ai_recommendation_generator.py` (NEW)

#### Implementation

1. **Create New Service** (New file)
   ```python
   class AIRecommendationGenerator:
       def generate_recommendation(
           self,
           action_type: str,
           description: str,
           risk_level: str,
           mitre_tactic: str,
           nist_control: str,
           context_flags: Dict
       ) -> str:
           """Generate context-aware security recommendation using LLM"""
   ```

2. **LLM Integration**
   - Use existing `llm_utils.py`
   - Prompt engineering for security recommendations
   - Include context: production, PII, financial, admin
   - 1-2 sentence actionable recommendations

3. **Caching Strategy**
   - Cache by (action_type, risk_level, flags_hash)
   - TTL: 24 hours
   - Reduces LLM API calls by 95%

4. **Fallback Logic**
   - If LLM fails → use static recommendation
   - If API rate limited → use cached similar recommendation
   - Never block on LLM response

#### Enterprise Features
- Async LLM calls (non-blocking)
- Request timeout (2 seconds)
- Retry logic (exponential backoff)
- Cost tracking (token usage logging)
- A/B testing support (compare static vs AI)

#### Testing
- Test Case 1: Firewall update → Mentions specific ports, CAB process
- Test Case 2: Payment processing → Mentions PCI-DSS, encryption
- Test Case 3: PII export → Mentions GDPR, data minimization
- Test Case 4: LLM failure → Returns static fallback

---

### Phase 4: Enhanced Context Detection (HIGH - Priority 4)

**File:** `enrichment.py`

#### Changes Required

1. **Move Context Detection Earlier** (Before CVSS calculation)
   - Current: Calculate CVSS → Detect context → Elevate risk_level
   - New: Detect context → Adjust CVSS metrics → Calculate CVSS

2. **Add Financial Detection** (New function)
   ```python
   def detect_financial_context(description: str, tool_name: str = None) -> bool:
       financial_keywords = ["payment", "transaction", "billing", "stripe",
                            "paypal", "invoice", "charge", "refund", "credit card"]
       financial_tools = ["stripe_api", "paypal_api", "payment_gateway"]
       # Check both description and tool_name
   ```

3. **Enhanced Production Detection**
   - Check tool_name for "prod", "production"
   - Check target_system for production indicators
   - Check description for deployment keywords

#### Enterprise Features
- Multi-factor detection (description + tool + target)
- Confidence scoring (weak/strong signal)
- Detailed logging of detection reasons
- Support for custom indicators via config

#### Testing
- Test Case 1: "payment" in description → Financial detected
- Test Case 2: tool_name="stripe_api" → Financial detected
- Test Case 3: target_system="prod-db" → Production detected
- Test Case 4: All flags combined → Highest risk

---

### Phase 5: CVSS Recalculation Flow (HIGH - Priority 5)

**File:** `enrichment.py` (Lines 390-436)

#### Changes Required

1. **Restructure Flow**
   ```
   OLD FLOW:
   1. Get base CVSS metrics
   2. Calculate CVSS → 8.2
   3. Detect context flags
   4. Elevate risk_level (but cvss_score stays 8.2)

   NEW FLOW:
   1. Detect context flags FIRST
   2. Get base CVSS metrics
   3. Adjust metrics based on context flags
   4. Calculate CVSS with adjusted metrics → 9.2
   5. Return result
   ```

2. **Add Adjustment Logic**
   ```python
   if context_flags["production"]:
       cvss_context["production_system"] = True
       # cvss_auto_mapper will adjust Scope → CHANGED

   if context_flags["financial"]:
       cvss_context["financial_transaction"] = True
       # cvss_auto_mapper will adjust I:HIGH, A:HIGH
   ```

#### Enterprise Features
- Clear separation of concerns
- Adjustment reasons logged
- Before/after CVSS comparison logged
- Audit trail of score changes

#### Testing
- Test Case 1: Production flag → CVSS increases by 1-2 points
- Test Case 2: Financial flag → CVSS increases by 2-3 points
- Test Case 3: All flags → CVSS reaches 9.0+
- Test Case 4: No flags → CVSS unchanged

---

### Phase 6: Frontend Enhancements (MEDIUM - Priority 6)

**Files:** Frontend components displaying MITRE/NIST/recommendations

#### Changes Required

1. **Authorization Center Dashboard**
   - Display dynamic MITRE techniques (not just T1059)
   - Display dynamic NIST controls (not just SI-3)
   - Display AI-generated recommendations
   - Show "AI Generated" badge for recommendations

2. **Action Detail Modal**
   - Show CVSS vector string
   - Show context flags (production, PII, financial)
   - Show adjustment reasons
   - Show before/after risk scores

3. **Analytics Dashboard**
   - Add CVSS score distribution chart
   - Add top MITRE techniques chart
   - Add top NIST controls chart
   - Add recommendation effectiveness tracking

#### Enterprise Features
- Real-time updates via WebSocket
- Accessibility (WCAG 2.1 AA compliant)
- Mobile responsive
- Loading states for async data

#### Testing
- Test Case 1: Action details show correct MITRE from DB
- Test Case 2: Recommendations show AI badge
- Test Case 3: CVSS vector string displayed
- Test Case 4: Charts update dynamically

---

## Implementation Order

### Day 1: Core CVSS Fixes (Phases 1 & 5)
1. Fix database write metrics
2. Enhance context adjustment
3. Restructure CVSS flow
4. Test with simulator

**Expected Impact:** Payment processing 38 → 85+, Database writes 49 → 90+

### Day 2: Database Integration (Phase 2)
1. Create database query function
2. Add fallback logic
3. Implement caching
4. Test with real data

**Expected Impact:** Correct MITRE/NIST mappings for 80%+ actions

### Day 3: AI Recommendations (Phase 3)
1. Create AI service
2. Integrate LLM
3. Implement caching
4. Test generation

**Expected Impact:** Context-aware recommendations for all actions

### Day 4: Context Detection (Phase 4)
1. Add financial detection
2. Enhance production detection
3. Multi-factor detection
4. Test all scenarios

**Expected Impact:** Accurate context detection 95%+

### Day 5: Frontend & Testing (Phase 6)
1. Update frontend components
2. End-to-end testing
3. Load testing
4. Production deployment

**Expected Impact:** Full visibility of dynamic data

---

## Enterprise Standards

### Error Handling
- All functions wrapped in try/except
- Graceful degradation on failures
- Detailed error logging
- User-friendly error messages

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Performance metrics logged
- Audit trail for all decisions

### Backward Compatibility
- All existing API contracts preserved
- New fields added, never removed
- Feature flags for gradual rollout
- Deprecation warnings for old fields

### Performance
- Database query optimization (indexes used)
- Caching strategy (Redis ready)
- Async operations (non-blocking)
- Connection pooling

### Security
- Input validation (all user inputs)
- SQL injection prevention (parameterized queries)
- Rate limiting (LLM API calls)
- Secrets management (environment variables)

---

## Testing Strategy

### Unit Tests
- Each function has 80%+ coverage
- Mock external dependencies
- Test edge cases
- Test error handling

### Integration Tests
- End-to-end workflow tests
- Database integration tests
- LLM integration tests
- Cache integration tests

### Load Tests
- 100 actions/second sustained
- Database query performance < 50ms
- LLM cache hit rate > 90%
- Memory usage < 2GB

### Acceptance Tests
- All 6 critical issues resolved
- Simulator shows varied risk scores
- MITRE/NIST from database
- AI recommendations generated

---

## Rollout Plan

### Phase 1: Local Testing
- Test with local simulator
- Verify all 6 issues fixed
- Document evidence

### Phase 2: Staging Deployment
- Deploy to staging environment
- Run integration tests
- Performance testing

### Phase 3: Canary Deployment
- Deploy to 10% of production traffic
- Monitor error rates
- Monitor performance metrics

### Phase 4: Full Production
- Deploy to 100% of traffic
- Monitor for 24 hours
- Document lessons learned

---

## Success Criteria

### Functional
- ✅ Payment processing risk score 80+ (was 38)
- ✅ Database writes risk score 90+ (was 49)
- ✅ MITRE mappings from database (not hardcoded)
- ✅ AI-generated recommendations (not static)
- ✅ Context-aware CVSS calculation
- ✅ All simulator actions have unique risk scores

### Performance
- ✅ CVSS calculation < 100ms (p95)
- ✅ Database query < 50ms (p95)
- ✅ LLM cache hit rate > 90%
- ✅ End-to-end latency < 500ms (p95)

### Quality
- ✅ Zero critical bugs in production
- ✅ Error rate < 0.1%
- ✅ Unit test coverage > 80%
- ✅ Integration test coverage > 70%

---

## Next Steps

1. ✅ **AUDIT** - Complete
2. ✅ **PLAN** - Complete
3. ⏳ **IMPLEMENT** - Ready to start
4. ⏳ **TEST** - After implementation
5. ⏳ **DEPLOY** - After testing

---

**Plan Generated:** 2025-11-11
**Generated By:** OW-KAI Platform Engineering Team
**Classification:** Internal - Engineering Use
**Architecture Version:** ARCH-003
