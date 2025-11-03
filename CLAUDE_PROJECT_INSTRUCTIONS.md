# CLAUDE PROJECT INSTRUCTIONS: OW-KAI ENTERPRISE SECURITY REMEDIATION

## 🎯 PRIMARY DIRECTIVE

When working on security fixes and improvements for the OW-KAI platform, you MUST follow this methodology:

---

## ⚠️ CRITICAL RULE: AUDIT FIRST, ACT SECOND

**BEFORE making ANY recommendations or changes:**

1. **Perform Complete Impact Analysis**
   - Identify ALL files that will be affected
   - Map ALL dependencies and imports
   - Check ALL code paths that use the affected functionality
   - Search for ALL references (not just obvious ones)
   - Understand full scope of change

2. **Validate Current State**
   - Read and analyze ALL related code
   - Test current behavior (if possible)
   - Document what currently exists
   - Understand WHY code was written this way
   - Check for existing workarounds or compensating controls

3. **Assess Alternatives**
   - Research multiple solution approaches
   - Compare enterprise-grade options
   - Evaluate trade-offs of each approach
   - Consider backward compatibility
   - Plan for rollback scenarios

4. **Create Evidence-Based Recommendation**
   - Only AFTER completing full audit
   - Provide detailed rationale
   - Show pros/cons of alternatives considered
   - Explain why recommended approach is best
   - Document potential risks and mitigations

**❌ NEVER:**
- Make recommendations based on partial analysis
- Suggest changes without understanding full impact
- Assume you know all the code paths
- Skip the audit phase to "save time"

**✅ ALWAYS:**
- Complete audit FIRST
- Show your analysis work
- Explain your reasoning
- Provide evidence for recommendations

---

## 🛠️ IMPLEMENTATION REQUIREMENTS

### 1. Terminal-Based Fixes ONLY
- **All changes MUST be implementable via terminal commands**
- Provide complete bash scripts for every fix
- Include verification steps after each change
- No manual UI-based configuration (unless absolutely necessary)

**Example Format:**
```bash
# Step 1: Description of what we're doing
cd ~/project
command1

# Step 2: Description of next action
command2

# Verification: How to confirm it worked
verification_command
# Expected output: what success looks like
```

### 2. Enterprise-Grade Solutions ONLY
- **NO quick hacks or temporary workarounds**
- Solutions MUST be production-ready
- Follow industry best practices (OWASP, NIST, CIS benchmarks)
- Implement proper error handling
- Add comprehensive logging
- Consider scalability and performance
- Plan for monitoring and alerting

**Examples:**
- ✅ AWS Secrets Manager for secret management
- ❌ Hardcoded secrets in environment variables
- ✅ Proper authentication middleware with JWT validation
- ❌ "Quick fix" authentication bypass
- ✅ Parameterized SQL queries with SQLAlchemy ORM
- ❌ String concatenation in SQL

### 3. NO Feature Removal
- **NEVER remove functionality to fix security issues**
- Find secure alternatives that preserve features
- Enhance security WITHOUT breaking existing workflows
- Maintain backward compatibility where possible
- If feature must change, provide migration path

**Examples:**
- ✅ Add authentication to WebSocket (feature still works)
- ❌ Delete WebSocket endpoint (removes feature)
- ✅ Fix CSRF protection (requests still work with token)
- ❌ Disable CSRF-vulnerable endpoints (breaks feature)

### 4. Work in BOTH Dev AND Production
- **All fixes MUST work in both environments**
- Provide environment-specific configurations
- Test in dev BEFORE production deployment
- Use feature flags for gradual rollout when appropriate
- Document environment differences

**Environment Handling:**
```bash
# Detect environment
if [ "$NODE_ENV" = "production" ]; then
    # Production-specific config
else
    # Development-specific config
fi
```

### 5. Follow Best Practices
- **Adhere to established security standards**
- Use industry-standard libraries and tools
- Implement defense in depth (multiple layers)
- Follow principle of least privilege
- Apply secure by default configurations
- Use established patterns (don't reinvent)

**Standards to Follow:**
- OWASP Top 10
- NIST Cybersecurity Framework
- CIS Benchmarks
- SANS Top 25
- PCI-DSS requirements (if applicable)
- SOC 2 controls

---

## 📚 EXPLANATION REQUIREMENTS

### For EVERY recommendation, provide:

1. **What We're Doing** (The Fix)
   - Clear description of the change
   - Specific files/lines affected
   - Terminal commands to execute

2. **Why This Is Necessary** (The Problem)
   - Explain the vulnerability or issue
   - Show the security risk with examples
   - Demonstrate potential attack scenarios
   - Reference CVE/CWE numbers if applicable

3. **How It Works** (The Solution)
   - Explain the mechanism of the fix
   - Describe how it prevents the vulnerability
   - Show code examples (before/after)
   - Explain key concepts (e.g., "JWT tokens", "CSRF double-submit")

4. **Why This Is Best Practice** (The Justification)
   - Reference industry standards (OWASP, NIST, etc.)
   - Compare to alternative approaches
   - Explain trade-offs considered
   - Show why this approach is optimal

5. **Impact Analysis** (The Consequences)
   - What will change for users?
   - What will change for developers?
   - Performance implications?
   - Compatibility considerations?

6. **Verification** (The Proof)
   - How to test that it works
   - What success looks like
   - How to confirm security improvement
   - Monitoring/alerting recommendations

**Example Explanation Format:**

```markdown
## Fix: Add WebSocket Authentication (SEC-008)

### 1. What We're Doing
We're implementing JWT token validation for WebSocket connections by:
- Creating a new `verify_websocket_token()` dependency
- Adding authentication to WebSocket endpoint decorators
- Requiring clients to send JWT tokens via query parameters

### 2. Why This Is Necessary
**Current Problem:**
WebSocket endpoints at `/ws/realtime` accept connections from ANYONE:
```python
@router.websocket("/ws/realtime")
async def websocket(websocket: WebSocket):
    await websocket.accept()  # ← No auth check!
```

**Security Risk:**
- Attackers can monitor real-time system metrics
- Governance data exposed publicly (pending actions count)
- Reconnaissance for planning attacks
- OWASP A01:2021 - Broken Access Control
- CWE-306: Missing Authentication

### 3. How It Works
**JWT Token Flow:**
1. Client authenticates normally (POST /auth/token) → receives JWT
2. Client opens WebSocket with JWT in query param: `ws://host/ws?token=<jwt>`
3. Server validates JWT signature using SECRET_KEY
4. If valid → connection accepted, user_id/role extracted
5. If invalid → connection rejected with 1008 policy violation

**Code Implementation:**
```python
# New dependency validates token before connection
async def verify_websocket_token(websocket: WebSocket) -> dict:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Auth required")
        raise HTTPException(401)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return {"user_id": payload["sub"], "email": payload["email"]}

# Apply to endpoint
@router.websocket("/ws/realtime")
async def websocket(
    websocket: WebSocket,
    current_user: dict = Depends(verify_websocket_token)  # ✅ Auth required!
):
    # Only authenticated users reach here
```

### 4. Why This Is Best Practice
**Industry Standards:**
- **OWASP:** Authentication required for all sensitive endpoints
- **NIST SP 800-63B:** Multi-factor token validation recommended
- **RFC 6455 (WebSocket):** Security considerations require authentication
- **SOC 2 CC6.1:** Logical access controls must be implemented

**Why JWT for WebSockets:**
- ✅ Stateless authentication (scalable)
- ✅ Standard approach used by AWS API Gateway, Socket.io, etc.
- ✅ No session storage required
- ✅ Works across load balancers
- ✅ Short expiration times possible (security)

**Alternatives Considered:**
1. ❌ Cookie-based auth: Doesn't work well with WebSocket query params
2. ❌ API key in header: WebSocket handshake limited header support
3. ✅ JWT in query param: Standard practice, widely supported
4. ❌ No auth + IP whitelist: Not scalable, bypassable

### 5. Impact Analysis
**User Impact:**
- Minimal: Frontend already has JWT from login
- Change: Must include `?token=<jwt>` in WebSocket URL
- Benefit: Protected real-time data

**Developer Impact:**
- Frontend update required: Add token to WebSocket URL
- Backend: New dependency file (~50 lines)
- Testing: WebSocket tests must include auth

**Performance:**
- Overhead: ~2ms JWT validation per connection
- Scalability: No session storage = infinitely scalable
- Network: +~200 bytes for JWT in URL (negligible)

**Compatibility:**
- ✅ Works with all WebSocket clients
- ✅ Works in dev (localhost) and production
- ✅ No breaking changes to existing authenticated endpoints

### 6. Verification
**Test 1: Unauthenticated Access Denied**
```bash
# Should FAIL with 1008 policy violation
python3 << 'EOF'
import asyncio
import websockets

async def test():
    try:
        uri = "wss://pilot.owkai.app/ws/realtime"
        async with websockets.connect(uri) as ws:
            print("❌ FAIL: No auth required!")
    except Exception as e:
        print(f"✅ PASS: {e}")

asyncio.run(test())
