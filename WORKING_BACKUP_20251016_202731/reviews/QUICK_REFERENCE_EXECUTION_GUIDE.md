# OW AI Remediation - Quick Reference Execution Guide

**For:** Development Team
**Timeline:** 4 Weeks
**Team:** 2 Full-time Developers

---

## Week 1: Security & Cleanup (Days 1-5)

### Backend Developer - Daily Tasks

**Monday (8h)**
```bash
# Morning: Rate Limiting (4h)
1. Install slowapi: pip install slowapi
2. Create limiter in main.py
3. Add @limiter.limit("5/minute") to /auth/login
4. Add @limiter.limit("5/minute") to /auth/register
5. Test with brute force script
6. Add account lockout logic (10 failed attempts)

# Afternoon: Dead Code Cleanup Part 1 (4h)
7. Create backup: ./scripts/backup_dead_code.sh
8. Delete backup files: find . -name "*.backup*" -delete
9. Delete broken files: find . -name "*_broken.*" -delete
10. Delete fix scripts: find . -name "fix_*.py" -not -path "*/alembic/*" -delete
```

**Tuesday (8h)**
```bash
# Dead Code Cleanup Part 2
1. Delete main_baseline.py, main_clean_original.py
2. Delete route backup files in /routes/
3. Update .dockerignore with exclusion patterns
4. Test application startup
5. Run test suite: pytest tests/
6. Create deployment validation script
```

**Wednesday (8h)**
```bash
# Morning: Remove Duplicate Code (2h)
1. Open dependencies.py
2. Delete lines 231-336 (exact duplicate)
3. Verify imports: python -c "from dependencies import *"
4. Run tests: pytest tests/test_dependencies.py

# Afternoon: Validate Production Secrets (2h)
5. Add production secret validation to config.py
6. Create environment variable checklist
7. Test with production-like env vars
8. Document required secrets in README

# Buffer time for fixes (4h)
```

**Thursday-Friday (16h)**
```bash
# Code review, testing, documentation
1. Security penetration testing
2. Rate limiting validation
3. Dead code verification
4. Documentation updates
5. Week 1 retrospective prep
```

---

### Frontend Developer - Daily Tasks

**Monday (8h)**
```bash
# Morning: Dead Code Cleanup (3h)
1. Delete src/components/AppContent.jsx
2. Delete src/context/AlertContext.jsx
3. Delete src/components/ToastAlert.jsx
4. Delete src/components/BannerAlert.jsx
5. Delete src/components/AgentAuthorizationDashboard.jsx.backup
6. Test application: npm run dev

# Afternoon: Fix Profile Duplication (2h)
7. Open src/App.jsx
8. Delete lines 71-242 (Profile component)
9. Verify import: import Profile from './components/Profile'
10. Test profile page loads correctly

# Fix localStorage Security (2h)
11. Search for localStorage.setItem("access_token")
12. Remove all token storage in localStorage
13. Verify cookie-only authentication works
14. Update auth components
```

**Tuesday (8h)**
```bash
# Centralize API Configuration (3h)
1. Create src/config/api.js
2. Export API_BASE_URL constant
3. Find/replace 108 API_BASE_URL declarations
4. Update all component imports
5. Test all API calls work

# Testing and validation (5h)
6. Run test suite: npm test
7. Test authentication flows
8. Verify all components render
9. Integration testing
```

**Wednesday-Friday (24h)**
```bash
# Code review, testing, documentation
1. Component integration testing
2. Security validation
3. Bundle size baseline measurement
4. Documentation updates
5. Code review with backend dev
6. Week 1 retrospective
```

---

## Week 2: Performance Optimization (Days 6-10)

### Backend Developer - Daily Tasks

**Monday-Tuesday (16h)**
```bash
# Add Database Eager Loading (8h)
1. Import joinedload, selectinload from sqlalchemy.orm
2. Update get_pending_actions:
   actions = db.query(AgentAction)\
       .options(joinedload(AgentAction.user))\
       .options(joinedload(AgentAction.risk_assessment))\
       .options(selectinload(AgentAction.approvers))\
       .all()
3. Update get_dashboard_data with eager loading
4. Update analytics endpoints with eager loading
5. Test query performance
6. Run query counter tests
```

**Wednesday (8h)**
```bash
# Create Missing Indexes (4h)
1. Create Alembic migration:
   alembic revision -m "add_performance_indexes"
2. Add indexes:
   Index('idx_agent_action_status_time', 'status', 'created_at')
   Index('idx_alert_severity_time', 'severity', 'timestamp')
   Index('idx_user_role_active', 'role', 'is_active')
3. Run migration: alembic upgrade head
4. Test query performance

# Increase Connection Pool (1h)
5. Update database.py:
   pool_size=20, max_overflow=50, pool_recycle=3600
6. Test under load

# Performance Testing (3h)
7. Run load test script
8. Measure P50, P95, P99 latency
```

**Thursday-Friday (16h)**
```bash
# Load testing and optimization
1. Test with 100 concurrent users
2. Monitor database connections
3. Optimize slow queries
4. Documentation updates
```

---

### Frontend Developer - Daily Tasks

**Monday-Tuesday (16h)**
```bash
# Monday Morning: Remove Unused Dependencies (1h)
1. npm uninstall @clerk/clerk-react react-router-dom
2. npm run build
3. Test application

# Implement Code Splitting (4h)
4. Update App.jsx:
   const Dashboard = lazy(() => import('./components/Dashboard'));
   const Authorization = lazy(() => import('./components/AgentAuthorizationDashboard'));
   const Analytics = lazy(() => import('./components/RealTimeAnalyticsDashboard'));
5. Wrap with Suspense:
   <Suspense fallback={<LoadingScreen />}>
     {activeTab === 'dashboard' && <Dashboard />}
   </Suspense>
6. Test lazy loading works
7. Measure bundle size

# Optimize Icon Imports (2h)
8. Replace: import { Activity, Users, ... } from 'lucide-react'
9. With: import Activity from 'lucide-react/dist/esm/icons/activity'
10. Test all icons render
```

**Wednesday (8h)**
```bash
# Production Logger Utility (2h)
1. Create src/utils/logger.js:
   const logger = {
     log: (...args) => import.meta.env.DEV && console.log(...args),
     error: (...args) => console.error(...args),
     warn: (...args) => import.meta.env.DEV && console.warn(...args),
   };
2. Find/replace console.log with logger.log
3. Find/replace console.error with logger.error
4. Test production build

# Bundle Optimization Testing (6h)
5. Run: npm run build
6. Measure bundle size: du -sh dist/assets/*.js
7. Run Lighthouse: npx lighthouse http://localhost:5173
8. Verify targets met
```

**Thursday-Friday (16h)**
```bash
# Performance validation
1. Lighthouse testing
2. Bundle size verification
3. Integration testing
4. Documentation
```

---

## Week 3: Architecture Improvements (Days 11-15)

### Backend Developer - Daily Tasks

**Monday-Tuesday (16h)**
```bash
# Implement API Versioning (4h)
1. Update main.py route registration:
   app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
   app.include_router(authorization_router, prefix="/api/v1/authorization")
   app.include_router(analytics_router, prefix="/api/v1/analytics")
2. Update all route files with /api/v1/ prefix
3. Test all endpoints
4. Update OpenAPI docs

# Consolidate Route Registration (4h)
5. Create route lists in main.py:
   CORE_ROUTES = [(router, prefix, tags), ...]
   ENTERPRISE_ROUTES = [...]
6. Loop through and register
7. Remove all commented imports
8. Add feature flags for enterprise routes
9. Test all routes accessible
```

**Wednesday-Friday (24h)**
```bash
# Integration testing
1. API contract tests
2. Route validation
3. OpenAPI schema verification
4. Documentation
5. Code review
```

---

### Frontend Developer - Daily Tasks

**Monday-Tuesday (16h)**
```bash
# Create AuthContext (3h)
1. Create src/contexts/AuthContext.jsx:
   export const AuthProvider = ({ children }) => {
     const getAuthHeaders = () => {
       const token = localStorage.getItem("access_token");
       return token ? { Authorization: `Bearer ${token}` } : {};
     };
     return <AuthContext.Provider value={{ getAuthHeaders }}>...
   }
2. Update App.jsx to wrap with AuthProvider
3. Update all components to use useAuth() instead of props
4. Remove getAuthHeaders from all component props
5. Test authentication flows

# Add Error Boundaries (2h)
6. Create src/components/ErrorBoundary.jsx
7. Wrap Dashboard: <ErrorBoundary><Dashboard /></ErrorBoundary>
8. Wrap Authorization Center
9. Wrap Analytics
10. Create error fallback UI
11. Test error scenarios
```

**Wednesday-Friday (24h)**
```bash
# Component refactoring
1. Integration testing
2. Error boundary testing
3. Auth context validation
4. Documentation
5. Code review
```

---

## Week 4: Testing & Deployment (Days 16-20)

### Both Developers - Daily Tasks

**Monday-Tuesday (32h combined)**
```bash
# End-to-End Testing
1. Run full E2E test suite
2. Test user registration → approval flow
3. Test policy creation → enforcement
4. Fix any discovered issues

# Security Testing
5. Run OWASP ZAP scan
6. SQL injection tests
7. XSS tests
8. CSRF tests
9. Rate limiting tests

# Performance Testing
10. Load test with 100 concurrent users
11. Stress test to find limits
12. Endurance test (24-hour)
```

**Wednesday (16h combined)**
```bash
# User Acceptance Testing
1. UAT test plan execution
2. Documentation updates
3. Deployment runbook creation
4. Rollback plan documentation

# Staging Deployment
5. Deploy to staging
6. Run smoke tests
7. Validate all features
```

**Thursday (16h combined)**
```bash
# Staging Validation
1. Run full test suite in staging
2. Performance validation
3. Security validation
4. Fix any issues

# Pre-Launch Checklist
5. Review all exit criteria
6. Validate monitoring
7. Review rollback plan
8. Final go/no-go decision
```

**Friday (16h combined)**
```bash
# Production Deployment
Morning (09:00-12:00):
1. Deploy to production
2. Run smoke tests
3. Monitor error rates

Afternoon (13:00-17:00):
4. Performance validation
5. Security validation
6. Monitor user feedback
7. Launch retrospective
```

---

## Daily Standup Template

**Time:** 9:00 AM (15 minutes)

**Format:**
1. What I completed yesterday
2. What I'm working on today
3. Any blockers or dependencies
4. Coordination needed with other dev

**Example:**
```
Backend Dev:
- Yesterday: Implemented rate limiting, deleted 200+ dead files
- Today: Remove duplicate code, validate production secrets
- Blockers: None
- Coordination: Will need frontend to test cookie auth by Wednesday

Frontend Dev:
- Yesterday: Deleted 5 dead files, fixed Profile duplication
- Today: Centralize API config, security testing
- Blockers: Need backend API versioning spec
- Coordination: Can start AuthContext after backend completes H7
```

---

## Weekly Review Template

**Time:** Friday 4:00 PM (1 hour)

**Agenda:**
1. Demo completed features (30 min)
2. Review metrics vs targets (15 min)
3. Discuss blockers and challenges (10 min)
4. Plan next week priorities (5 min)

**Metrics to Review:**

Week 1:
- [ ] Rate limiting active?
- [ ] Dead files = 0?
- [ ] Security audit passed?

Week 2:
- [ ] Bundle size <600 kB?
- [ ] API P95 <500ms?
- [ ] Lighthouse score >85?

Week 3:
- [ ] All routes /api/v1/?
- [ ] AuthContext implemented?
- [ ] Error boundaries active?

Week 4:
- [ ] All tests passing?
- [ ] Production deployed?
- [ ] Monitoring active?

---

## Quick Commands Reference

### Backend

```bash
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_rate_limiting.py -v

# Check test coverage
pytest tests/ --cov=. --cov-report=html

# Run security scan
./scripts/security_scan.sh

# Database migrations
alembic revision -m "description"
alembic upgrade head
alembic downgrade -1

# Start backend
python main.py

# Load testing
python scripts/load_test.py
```

### Frontend

```bash
# Run tests
npm test

# Run specific test
npm test -- Dashboard.test.jsx

# Check coverage
npm test -- --coverage

# Build production
npm run build

# Check bundle size
du -sh dist/assets/*.js

# Run Lighthouse
npx lighthouse http://localhost:5173 --view

# Start frontend
npm run dev
```

### Both

```bash
# Validate dead code
./scripts/validate_dead_code.sh

# Deployment validation
./scripts/deployment_validation.sh

# Full test suite
./scripts/run_all_tests.sh

# Docker build
docker-compose build
docker-compose up
```

---

## Common Issues & Solutions

### Issue: Rate limiting blocks legitimate users

**Symptoms:** Users reporting "too many requests" error

**Solution:**
```python
# Increase rate limit temporarily
@limiter.limit("10/minute")  # From 5 to 10

# Or disable via feature flag
RATE_LIMITING_ENABLED=false
```

### Issue: Bundle size still too large

**Symptoms:** Bundle size >600 kB after optimizations

**Solution:**
```bash
# Analyze bundle
npm run build -- --stats
npx vite-bundle-visualizer

# Find large dependencies
npm ls --depth=0 | sort -k2 -h
```

### Issue: Database queries still slow

**Symptoms:** API P95 >500ms after eager loading

**Solution:**
```python
# Check query plan
from sqlalchemy import text
explain_query = text("EXPLAIN ANALYZE SELECT ...")
result = db.execute(explain_query)

# Add more specific indexes
Index('idx_custom', 'column1', 'column2', 'column3')
```

### Issue: Tests failing after refactor

**Symptoms:** Multiple test failures after code changes

**Solution:**
```bash
# Update test fixtures
# Review breaking changes
# Update mocks and stubs
# Run tests in isolation to identify root cause
pytest tests/test_file.py::test_function -v
```

---

## Emergency Rollback Procedure

**If production deployment fails:**

1. **Immediate (< 5 min):**
   ```bash
   # Rollback to previous version
   git revert HEAD
   git push origin main
   # Or use platform rollback (Heroku, AWS, etc.)
   ```

2. **Verify (5-10 min):**
   ```bash
   # Run smoke tests
   curl https://api.example.com/health
   # Check error rates in monitoring
   ```

3. **Communicate (10-15 min):**
   - Notify stakeholders
   - Update status page
   - Create incident report

4. **Post-Mortem (within 24h):**
   - Identify root cause
   - Document lessons learned
   - Plan fix for next deployment

---

## Success Criteria Checklist

### Week 1 ✓
- [ ] Rate limiting: 5/min on auth endpoints
- [ ] Dead files: 0 backup files
- [ ] Security: localStorage tokens removed
- [ ] Validation: Deployment script passing

### Week 2 ✓
- [ ] Performance: Bundle <600 kB
- [ ] Performance: API P95 <500ms
- [ ] Performance: Lighthouse >85
- [ ] Optimization: Database queries 80% faster

### Week 3 ✓
- [ ] Architecture: All routes /api/v1/
- [ ] Architecture: AuthContext in all components
- [ ] Architecture: Error boundaries active
- [ ] Quality: 0 prop drilling instances

### Week 4 ✓
- [ ] Testing: All test suites passing
- [ ] Testing: Security audit complete
- [ ] Deployment: Production deployed
- [ ] Monitoring: Alerts configured

---

## Contact Information

**Product Manager:** [Name]
**Backend Developer:** [Name]
**Frontend Developer:** [Name]
**DevOps:** [Name]
**Security:** [Name]

**Slack Channels:**
- #owai-remediation (main channel)
- #owai-incidents (emergencies only)
- #owai-deploys (deployment notifications)

**Meeting Links:**
- Daily Standup: [Zoom/Meet Link]
- Weekly Review: [Zoom/Meet Link]
- Emergency: [On-call Rotation]

---

## Resources

**Documentation:**
- Master Remediation Plan: /reviews/MASTER_REMEDIATION_PLAN.md
- Testing Strategy: /reviews/TESTING_VALIDATION_STRATEGY.md
- Code Review Reports: /reviews/*.md

**Tools:**
- GitHub: https://github.com/org/owai
- Jira: https://jira.company.com/owai
- Monitoring: https://monitoring.company.com/owai

**External:**
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev
- SQLAlchemy Docs: https://docs.sqlalchemy.org

---

**Last Updated:** 2025-10-15
**Version:** 1.0
**Status:** Ready for Execution
