# 🚨 PHASE 2 CRITICAL ISSUE - Routing Configuration Blocker

**Date**: November 20, 2025
**Engineer**: OW-KAI Engineer
**Severity**: CRITICAL - Blocks all Phase 2 functionality
**Status**: IDENTIFIED - Solution in progress

---

## 🔍 ISSUE SUMMARY

**Problem**: Phase 2 backend routes (`/organizations/*` and `/platform/*`) are deployed to production (Task Definition 513) but **NOT ACCESSIBLE** via the frontend URL `https://pilot.owkai.app`.

**Root Cause**: Web server (likely Nginx or ALB) routing configuration serves React frontend for ALL requests, including API routes that should go to the FastAPI backend.

---

## 📊 EVIDENCE

### Test Results:
```
✅ 3 Cognito users created successfully
✅ Authentication working (got valid ID tokens)
❌ All API requests return HTML (React app) instead of JSON
❌ Backend routes not reachable from https://pilot.owkai.app
```

### Example Request/Response:
```bash
Request:
  GET https://pilot.owkai.app/organizations/users
  Authorization: Bearer eyJraWQi... (valid Cognito ID token)

Expected Response:
  HTTP 200 JSON
  {"users": [...], "total": 3}

Actual Response:
  HTTP 200 HTML
  <!DOCTYPE html><html>... (React frontend index.html)
```

### Backend Verification:
```bash
# Backend is running healthy
aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service
→ Task Definition: 513 ✅ RUNNING
→ Container Status: HEALTHY
→ Startup logs: "✅ PHASE 2: Organization admin routes registered"
```

**Conclusion**: Backend has the routes, but requests never reach it.

---

## 🏗️ ARCHITECTURE ANALYSIS

### Current Production Setup (Assumed):

```
User Request
   ↓
   ↓ https://pilot.owkai.app/organizations/users
   ↓
[Application Load Balancer or CloudFront]
   ↓
   ↓ (Routing Rules?)
   ↓
   ├─→ Frontend (React) ✅ Serving on ALL paths
   │   └─ Returns: index.html for /organizations/*
   │
   └─→ Backend (FastAPI) ❌ NOT REACHABLE
       └─ Should handle: /organizations/*, /platform/*, /api/*
```

### Required Production Setup:

```
User Request
   ↓
[Application Load Balancer / Nginx / CloudFront]
   ↓
   ├─ Path: /api/*          → Backend (ECS: owkai-pilot-backend:8000)
   ├─ Path: /organizations/* → Backend (ECS: owkai-pilot-backend:8000)
   ├─ Path: /platform/*      → Backend (ECS: owkai-pilot-backend:8000)
   ├─ Path: /health          → Backend (ECS: owkai-pilot-backend:8000)
   └─ Path: /*               → Frontend (React SPA)
```

---

## 🔧 ENTERPRISE SOLUTION OPTIONS

### **Option 1: Add API Prefix to All Backend Routes** (RECOMMENDED)
**Pros**:
- Single routing rule: `/api/*` → Backend
- Clear separation between API and frontend
- Standard enterprise pattern
- Easiest to configure in ALB/CloudFront

**Implementation**:
1. Update `main.py`:
   ```python
   app = FastAPI(root_path="/api")
   # OR
   app.include_router(org_admin_router, prefix="/api")
   app.include_router(platform_admin_router, prefix="/api")
   ```

2. Update ALB/CloudFront routing:
   ```
   /api/*    → Target Group: owkai-pilot-backend (port 8000)
   /*        → Target Group: owkai-pilot-frontend (or S3/CloudFront)
   ```

3. Update frontend API calls to use `/api` prefix

**Timeline**: 2-3 hours (backend update + ALB config + frontend update)

---

### **Option 2: Multiple Path Rules in Load Balancer**
**Pros**:
- No code changes needed
- Routes work as designed

**Implementation**:
1. Add ALB Path-based routing rules (priority order matters):
   ```
   Priority 1: /organizations/* → owkai-pilot-backend:8000
   Priority 2: /platform/*      → owkai-pilot-backend:8000
   Priority 3: /health          → owkai-pilot-backend:8000
   Priority 4: /*               → owkai-pilot-frontend
   ```

2. Or if using Nginx:
   ```nginx
   location /organizations/ {
       proxy_pass http://backend:8000;
   }
   location /platform/ {
       proxy_pass http://backend:8000;
   }
   location / {
       try_files $uri $uri/ /index.html;
   }
   ```

**Timeline**: 1-2 hours (ALB rule updates only)

---

### **Option 3: Subdomain Separation** (Most Enterprise, but requires DNS)
**Pros**:
- Complete isolation
- Easier to scale independently
- Clear architecture

**Implementation**:
1. Create subdomain: `api.owkai.app`
2. Point to backend ALB target group
3. Update frontend to call `https://api.owkai.app/organizations/*`

**Timeline**: 4-6 hours (DNS setup + SSL cert + ALB config + frontend update)

---

## 🎯 RECOMMENDED PATH FORWARD

### **PHASE 3A: Fix Routing (IMMEDIATE - Option 1)**
**Duration**: 2-3 hours

1. **Backend Changes** (30 min):
   - Add `/api` prefix to FastAPI app or routers
   - Test locally: `http://localhost:8000/api/organizations/users`
   - Commit and deploy new Task Definition

2. **ALB Configuration** (30 min):
   - Add path rule: `/api/*` → `owkai-pilot-backend-tg`
   - Keep existing: `/*` → frontend
   - Test: `https://pilot.owkai.app/api/organizations/users`

3. **Frontend Integration** (1-2 hours):
   - Update API base URL to include `/api`
   - Test all existing endpoints still work
   - Test new Phase 2 endpoints

---

## 📋 CURRENT PRODUCTION STATE

### What's Working:
✅ Phase 1 database migrations (organizations, RLS, encryption)
✅ Phase 2 backend code deployed (Task Def 513)
✅ Phase 2 routes loaded in FastAPI
✅ AWS Cognito infrastructure
✅ 3 test Cognito users created
✅ Token authentication working

### What's Broken:
❌ Phase 2 routes not accessible from frontend URL
❌ All `/organizations/*` requests return React HTML
❌ All `/platform/*` requests return React HTML
❌ Cannot test RLS isolation
❌ Cannot test audit logging
❌ Cannot test organization admin features

---

## 🚨 BLOCKING ISSUES

**Cannot proceed with Phase 2 verification until routing is fixed.**

Blocked tasks:
- ❌ Test organization admin endpoints
- ❌ Test platform admin endpoints
- ❌ Verify RLS policy enforcement
- ❌ Verify audit logging
- ❌ Test token revocation
- ❌ Frontend integration

---

## 📝 DEPLOYMENT INVESTIGATION NEEDED

**Questions to answer**:
1. Is there an Application Load Balancer in front of the application?
2. What's the current ALB target group configuration?
3. Is there a CloudFront distribution?
4. What routing rules exist currently?
5. Where is the frontend deployed? (S3? ECS?)

**Commands to run**:
```bash
# Find the load balancer
aws elbv2 describe-load-balancers --region us-east-2 | grep owkai

# Check target groups
aws elbv2 describe-target-groups --region us-east-2 | grep owkai

# Check listener rules
aws elbv2 describe-rules --listener-arn <arn> --region us-east-2

# Check CloudFront distributions
aws cloudfront list-distributions | grep owkai
```

---

## ✅ NEXT STEPS (In Priority Order)

1. **[IMMEDIATE]** Investigate production routing configuration
2. **[IMMEDIATE]** Choose routing solution (recommend Option 1: `/api` prefix)
3. **[2-3 hours]** Implement routing fix
4. **[1 hour]** Re-run Phase 2 endpoint tests
5. **[2-3 hours]** Continue with Phase 3 verification tests
6. **[ONGOING]** Update master plan with actual status

---

**Engineer**: OW-KAI Engineer
**Status**: Awaiting user decision on routing solution
**Recommendation**: Implement Option 1 (`/api` prefix) for fastest enterprise solution
