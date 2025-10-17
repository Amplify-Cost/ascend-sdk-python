# OW AI Enterprise Authorization Center
## Comprehensive Testing & Validation Strategy

**Document Version:** 1.0
**Date:** 2025-10-15
**Companion to:** Master Remediation Plan
**Status:** Planning Phase

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Phase 1: Security & Cleanup Testing (Week 1)](#phase-1-security--cleanup-testing-week-1)
3. [Phase 2: Performance Testing (Week 2)](#phase-2-performance-testing-week-2)
4. [Phase 3: Architecture Testing (Week 3)](#phase-3-architecture-testing-week-3)
5. [Phase 4: Production Validation (Week 4)](#phase-4-production-validation-week-4)
6. [Automated Testing Suite](#automated-testing-suite)
7. [Deployment Validation Checklist](#deployment-validation-checklist)
8. [Post-Deployment Monitoring](#post-deployment-monitoring)

---

## Testing Philosophy

### Testing Pyramid

```
                  /\
                 /  \
                / E2E \ (10% - Critical user journeys)
               /------\
              /        \
             / Integration \ (30% - API contracts, component integration)
            /------------\
           /              \
          /   Unit Tests   \ (60% - Business logic, utilities, components)
         /------------------\
```

### Coverage Targets

| Test Type | Target Coverage | Priority |
|-----------|-----------------|----------|
| **Unit Tests** | >70% | HIGH |
| **Integration Tests** | >60% | HIGH |
| **E2E Tests** | Critical paths only | MEDIUM |
| **Security Tests** | 100% attack vectors | CRITICAL |
| **Performance Tests** | All critical endpoints | HIGH |

---

## Phase 1: Security & Cleanup Testing (Week 1)

### C1: Rate Limiting Testing

#### Unit Tests

**File:** `tests/test_rate_limiting.py`

```python
import pytest
from fastapi.testclient import TestClient

def test_login_rate_limiting_enforced():
    """Test that login attempts are rate limited"""
    client = TestClient(app)

    # Attempt 6 logins in quick succession
    for i in range(6):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrong_password"
        })

    # 6th attempt should be rate limited
    assert response.status_code == 429
    assert "rate limit exceeded" in response.json()["detail"].lower()

def test_login_rate_limit_resets_after_time():
    """Test that rate limit resets after timeout"""
    client = TestClient(app)

    # Hit rate limit
    for i in range(5):
        client.post("/api/v1/auth/login", json={...})

    # Wait 61 seconds (1 minute + buffer)
    time.sleep(61)

    # Should succeed now
    response = client.post("/api/v1/auth/login", json={...})
    assert response.status_code in [200, 401]  # Not 429

def test_account_lockout_after_failed_attempts():
    """Test that account locks after 10 failed login attempts"""
    client = TestClient(app)

    for i in range(11):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": f"wrong_password_{i}"
        })

        if i < 10:
            assert response.status_code == 401  # Unauthorized
        else:
            assert response.status_code == 423  # Locked
            assert "account locked" in response.json()["detail"].lower()
```

#### Security Tests

**File:** `tests/security/test_brute_force_protection.py`

```python
def test_brute_force_attack_blocked():
    """Simulate brute force attack and verify it's blocked"""
    client = TestClient(app)
    password_list = ["password123", "admin", "letmein", ...]

    successful_attempts = 0
    rate_limited = False

    for password in password_list[:100]:
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@company.com",
            "password": password
        })

        if response.status_code == 429:
            rate_limited = True
            break

    assert rate_limited, "Brute force attack not blocked"
    assert successful_attempts == 0, "Attack succeeded"

def test_distributed_attack_prevention():
    """Test that attacks from multiple IPs are detected"""
    # Simulate attacks from 10 different IPs
    for ip in ["192.168.1.1", "192.168.1.2", ...]:
        client = TestClient(app, headers={"X-Forwarded-For": ip})

        for attempt in range(6):
            response = client.post("/api/v1/auth/login", json={...})

        # Each IP should be rate limited independently
        assert response.status_code == 429
```

#### Manual Testing Checklist

- [ ] Login with correct credentials succeeds
- [ ] 5 failed logins within 1 minute triggers rate limit
- [ ] Rate limit error message is user-friendly
- [ ] 10 failed logins locks account
- [ ] Locked account shows appropriate message
- [ ] Admin can unlock account
- [ ] Rate limiting does not affect other users
- [ ] CAPTCHA appears after 3 failed attempts (if implemented)

---

### C2/C3: Dead Code Cleanup Testing

#### Pre-Deletion Validation

**Script:** `scripts/validate_dead_code_deletion.sh`

```bash
#!/bin/bash

echo "=== Dead Code Cleanup Validation ==="

# 1. Check for backup files
echo "Checking for backup files..."
backup_count=$(find . -name "*.backup*" -o -name "*_broken.*" -o -name "*.bak" | wc -l)
echo "Found $backup_count backup files"

# 2. Check for fix scripts
echo "Checking for fix scripts..."
fix_count=$(find . -name "fix_*.py" -not -path "*/alembic/*" | wc -l)
echo "Found $fix_count fix scripts"

# 3. List all files to be deleted
echo "Files to be deleted:"
find . -name "*.backup*" -o -name "*_broken.*" -o -name "fix_*.py" -not -path "*/alembic/*"

# 4. Create backup before deletion
echo "Creating backup archive..."
tar -czf dead_code_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  $(find . -name "*.backup*" -o -name "*_broken.*" -o -name "fix_*.py" -not -path "*/alembic/*")

# 5. Verify backup created
if [ -f dead_code_backup_*.tar.gz ]; then
    echo "✓ Backup created successfully"
else
    echo "✗ Backup creation failed"
    exit 1
fi
```

#### Post-Deletion Validation

```bash
#!/bin/bash

echo "=== Post-Deletion Validation ==="

# 1. Verify no backup files remain
backup_count=$(find . -name "*.backup*" -o -name "*_broken.*" | wc -l)
if [ $backup_count -eq 0 ]; then
    echo "✓ No backup files found"
else
    echo "✗ Warning: $backup_count backup files still exist"
    exit 1
fi

# 2. Verify application still runs
echo "Testing application startup..."
python -c "from main import app; print('✓ Application imports successfully')"

# 3. Run test suite
echo "Running test suite..."
pytest tests/ --tb=short

# 4. Verify deployment pipeline
echo "Validating deployment configuration..."
if grep -q "*.backup*" .dockerignore; then
    echo "✓ .dockerignore configured correctly"
else
    echo "✗ .dockerignore missing backup exclusion"
    exit 1
fi
```

#### Manual Testing Checklist

- [ ] Backup archive created before deletion
- [ ] All 290+ dead files deleted
- [ ] Application starts successfully
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] .dockerignore excludes backup patterns
- [ ] Docker build succeeds
- [ ] Deployment pipeline validates clean code

---

### C4: Duplicate Code Removal Testing

#### Unit Tests

**File:** `tests/test_dependencies_no_duplicates.py`

```python
def test_dependencies_no_duplicate_functions():
    """Verify dependencies.py has no duplicate functions"""
    import inspect
    from dependencies import *

    # Get all functions
    functions = [name for name, obj in inspect.getmembers(dependencies)
                 if inspect.isfunction(obj)]

    # Check for duplicates
    assert len(functions) == len(set(functions)), \
        f"Duplicate functions found: {[f for f in functions if functions.count(f) > 1]}"

def test_auth_context_singleton():
    """Verify AuthContext is defined only once"""
    # Frontend test equivalent
    # Ensure only one AuthContext.jsx exists
    import os
    auth_contexts = []
    for root, dirs, files in os.walk("src/contexts"):
        if "AuthContext.jsx" in files:
            auth_contexts.append(os.path.join(root, "AuthContext.jsx"))

    assert len(auth_contexts) == 1, \
        f"Multiple AuthContext files found: {auth_contexts}"
```

#### Manual Testing Checklist

- [ ] dependencies.py lines 231-336 deleted
- [ ] No duplicate function definitions remain
- [ ] All imports still work
- [ ] Test suite passes
- [ ] No import errors in production
- [ ] Profile component only in /src/components/Profile.jsx
- [ ] App.jsx does not define Profile

---

### C6: localStorage Security Testing

#### Security Tests

**File:** `tests/security/test_token_storage.py`

```javascript
// Frontend test
describe('Token Storage Security', () => {
  test('No tokens stored in localStorage', () => {
    // Clear storage
    localStorage.clear();

    // Perform login
    const { getByLabelText, getByText } = render(<Login />);
    fireEvent.change(getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(getByText(/login/i));

    // Wait for login to complete
    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  test('Authentication works with cookies only', () => {
    // Mock cookie authentication
    document.cookie = 'access_token=mock_token; path=/';

    const { getByText } = render(<App />);

    // Verify authenticated state
    expect(getByText(/dashboard/i)).toBeInTheDocument();
  });

  test('XSS cannot access tokens', () => {
    // Simulate XSS attack
    const maliciousScript = () => {
      try {
        const token = localStorage.getItem('access_token');
        return token;
      } catch (e) {
        return null;
      }
    };

    expect(maliciousScript()).toBeNull();
  });
});
```

#### Manual Testing Checklist

- [ ] Login succeeds without localStorage
- [ ] Tokens stored in httpOnly cookies
- [ ] Browser DevTools cannot access tokens
- [ ] Authentication persists across page refreshes
- [ ] Logout clears all auth data
- [ ] XSS attack simulation fails to steal tokens

---

### Week 1 Integration Testing

#### Full Authentication Flow

**File:** `tests/integration/test_auth_flow.py`

```python
def test_complete_auth_flow_with_rate_limiting():
    """Test complete authentication flow with all Week 1 fixes"""
    client = TestClient(app)

    # 1. Register new user
    register_response = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "name": "New User"
    })
    assert register_response.status_code == 201

    # 2. Login successfully (should use cookies)
    login_response = client.post("/api/v1/auth/login", json={
        "email": "newuser@example.com",
        "password": "SecurePass123!"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.cookies

    # 3. Access protected endpoint
    cookies = login_response.cookies
    dashboard_response = client.get("/api/v1/dashboard", cookies=cookies)
    assert dashboard_response.status_code == 200

    # 4. Verify rate limiting on failed attempts
    for i in range(6):
        fail_response = client.post("/api/v1/auth/login", json={
            "email": "newuser@example.com",
            "password": "wrong_password"
        })

    assert fail_response.status_code == 429  # Rate limited
```

---

## Phase 2: Performance Testing (Week 2)

### H1: Code Splitting Testing

#### Bundle Size Validation

**Script:** `scripts/validate_bundle_size.sh`

```bash
#!/bin/bash

echo "=== Bundle Size Validation ==="

# Build production bundle
npm run build

# Measure bundle sizes
echo "Measuring bundle sizes..."
du -sh dist/assets/*.js | sort -rh

# Extract main bundle size
main_bundle=$(ls -lh dist/assets/index-*.js | awk '{print $5}')
echo "Main bundle size: $main_bundle"

# Check against target
main_bundle_kb=$(du -k dist/assets/index-*.js | awk '{print $1}')
if [ $main_bundle_kb -lt 600 ]; then
    echo "✓ Bundle size within target (<600 kB)"
else
    echo "✗ Bundle size exceeds target: ${main_bundle_kb}kB"
    exit 1
fi

# Check for code splitting
chunk_count=$(ls dist/assets/*.js | wc -l)
if [ $chunk_count -gt 1 ]; then
    echo "✓ Code splitting implemented ($chunk_count chunks)"
else
    echo "✗ No code splitting detected"
    exit 1
fi
```

#### Lighthouse Performance Testing

```bash
#!/bin/bash

echo "=== Lighthouse Performance Testing ==="

# Start dev server
npm run dev &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Run Lighthouse
npx lighthouse http://localhost:5173 \
  --only-categories=performance \
  --output=json \
  --output-path=lighthouse-report.json

# Extract score
performance_score=$(jq '.categories.performance.score * 100' lighthouse-report.json)

echo "Performance Score: $performance_score"

if [ $(echo "$performance_score >= 85" | bc) -eq 1 ]; then
    echo "✓ Lighthouse score meets target (≥85)"
else
    echo "✗ Lighthouse score below target: $performance_score"
    kill $SERVER_PID
    exit 1
fi

# Cleanup
kill $SERVER_PID
```

#### Manual Testing Checklist

- [ ] Dashboard component lazy loads
- [ ] Authorization component lazy loads
- [ ] Analytics component lazy loads
- [ ] Loading spinner appears during chunk load
- [ ] No flash of unstyled content
- [ ] All lazy-loaded components render correctly
- [ ] Bundle size <600 kB
- [ ] Lighthouse score ≥85

---

### H3: Database Eager Loading Testing

#### Performance Benchmark Tests

**File:** `tests/performance/test_database_queries.py`

```python
import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

@pytest.fixture
def query_counter():
    """Count SQL queries executed during test"""
    queries = []

    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
        queries.append(statement)

    yield queries

    event.remove(Engine, "before_cursor_execute", receive_before_cursor_execute)

def test_pending_actions_query_count(query_counter, db):
    """Test that pending actions loads with minimal queries"""
    from routes.authorization_routes import get_pending_actions

    # Clear query counter
    query_counter.clear()

    # Fetch pending actions (should use eager loading)
    actions = get_pending_actions(db, user_id=1, limit=10)

    # Should be 1-2 queries max (1 for actions, 1 for eager loaded relationships)
    assert len(query_counter) <= 2, \
        f"Too many queries: {len(query_counter)}. Expected ≤2 with eager loading."

def test_dashboard_data_performance(query_counter, db):
    """Test dashboard loads efficiently"""
    from routes.analytics_routes import get_dashboard_data

    query_counter.clear()

    dashboard_data = get_dashboard_data(db, user_id=1)

    # With eager loading, should execute <10 queries
    assert len(query_counter) < 10, \
        f"Dashboard queries not optimized: {len(query_counter)} queries"

def test_n_plus_one_eliminated(db):
    """Verify N+1 query problem is eliminated"""
    # Create test data: 10 actions with users
    for i in range(10):
        action = AgentAction(user_id=i, ...)
        db.add(action)
    db.commit()

    # Query with eager loading
    start_time = time.time()
    actions = db.query(AgentAction)\
        .options(joinedload(AgentAction.user))\
        .limit(10)\
        .all()
    eager_time = time.time() - start_time

    # Access user data (should not trigger additional queries)
    for action in actions:
        _ = action.user.email  # This would trigger N queries without eager loading

    total_time = time.time() - start_time

    # Accessing relationships should add minimal time
    assert (total_time - eager_time) < 0.01, \
        "Accessing relationships triggered additional queries"
```

#### Load Testing Script

**File:** `scripts/load_test_database.py`

```python
import concurrent.futures
import requests
import time

def test_endpoint_under_load(url, num_requests=100):
    """Test endpoint with concurrent requests"""

    def make_request():
        start = time.time()
        response = requests.get(url, headers={"Authorization": "Bearer token"})
        duration = time.time() - start
        return {
            "status": response.status_code,
            "duration": duration
        }

    # Execute concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        results = [f.result() for f in futures]

    # Calculate statistics
    durations = [r["duration"] for r in results]
    p50 = sorted(durations)[len(durations)//2]
    p95 = sorted(durations)[int(len(durations)*0.95)]
    p99 = sorted(durations)[int(len(durations)*0.99)]

    print(f"Performance Results:")
    print(f"  P50: {p50:.3f}s")
    print(f"  P95: {p95:.3f}s")
    print(f"  P99: {p99:.3f}s")

    # Verify performance targets
    assert p95 < 0.5, f"P95 latency too high: {p95}s (target: <0.5s)"

    return {
        "p50": p50,
        "p95": p95,
        "p99": p99
    }

if __name__ == "__main__":
    results = test_endpoint_under_load("http://localhost:8001/api/v1/governance/actions/pending")
    print("✓ Load test passed")
```

#### Manual Testing Checklist

- [ ] Dashboard loads in <100ms
- [ ] Pending actions endpoint <200ms
- [ ] Analytics endpoint <500ms
- [ ] No N+1 query warnings in logs
- [ ] Database connection pool not exhausted
- [ ] Load test with 100 concurrent users passes
- [ ] P95 latency <500ms

---

### H4: Database Index Testing

#### Index Verification Tests

**File:** `tests/test_database_indexes.py`

```python
def test_required_indexes_exist(db):
    """Verify all required indexes are created"""
    from sqlalchemy import inspect

    inspector = inspect(db.bind)

    # Check AgentAction indexes
    agent_action_indexes = inspector.get_indexes("agent_actions")
    index_names = [idx["name"] for idx in agent_action_indexes]

    assert "idx_agent_action_status_time" in index_names, \
        "Missing index: idx_agent_action_status_time"

    # Check Alert indexes
    alert_indexes = inspector.get_indexes("alerts")
    alert_index_names = [idx["name"] for idx in alert_indexes]

    assert "idx_alert_severity_time" in alert_index_names, \
        "Missing index: idx_alert_severity_time"

    # Check User indexes
    user_indexes = inspector.get_indexes("users")
    user_index_names = [idx["name"] for idx in user_indexes]

    assert "idx_user_role_active" in user_index_names, \
        "Missing index: idx_user_role_active"

def test_index_performance_improvement(db):
    """Verify indexes improve query performance"""
    # Create test data
    for i in range(1000):
        action = AgentAction(status="pending", created_at=datetime.now())
        db.add(action)
    db.commit()

    # Query using index
    start_time = time.time()
    results = db.query(AgentAction)\
        .filter(AgentAction.status == "pending")\
        .order_by(AgentAction.created_at.desc())\
        .limit(10)\
        .all()
    indexed_time = time.time() - start_time

    # Should complete quickly with index
    assert indexed_time < 0.1, \
        f"Query too slow even with index: {indexed_time}s"
```

---

## Phase 3: Architecture Testing (Week 3)

### H7: API Versioning Testing

#### Contract Tests

**File:** `tests/integration/test_api_versioning.py`

```python
def test_api_v1_endpoints_accessible():
    """Verify all endpoints available under /api/v1/"""
    client = TestClient(app)

    endpoints = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/governance/actions/pending",
        "/api/v1/analytics/dashboard",
        "/api/v1/alerts",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        # Should not be 404 (may be 401 if auth required)
        assert response.status_code != 404, \
            f"Endpoint not found: {endpoint}"

def test_openapi_schema_versioned():
    """Verify OpenAPI schema reflects v1 versioning"""
    client = TestClient(app)

    response = client.get("/openapi.json")
    schema = response.json()

    # All paths should start with /api/v1/
    for path in schema["paths"].keys():
        assert path.startswith("/api/v1/"), \
            f"Path not versioned: {path}"

def test_backward_compatibility():
    """Test that old endpoints still work during migration"""
    client = TestClient(app)

    # If backward compatibility is implemented
    old_response = client.post("/auth/login", json={...})
    new_response = client.post("/api/v1/auth/login", json={...})

    # Both should work (or old should redirect)
    assert old_response.status_code in [200, 301, 302] or \
           new_response.status_code == 200
```

---

### H5: AuthContext Testing

#### Component Tests

**File:** `tests/components/test_auth_context.jsx`

```javascript
import { render, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

describe('AuthContext', () => {
  test('Provides auth functions to children', () => {
    const TestComponent = () => {
      const { getAuthHeaders, user, login, logout } = useAuth();
      return (
        <div>
          <span data-testid="has-headers">{getAuthHeaders ? 'yes' : 'no'}</span>
          <span data-testid="has-user">{user ? 'yes' : 'no'}</span>
        </div>
      );
    };

    const { getByTestId } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(getByTestId('has-headers').textContent).toBe('yes');
  });

  test('No prop drilling required', () => {
    // Verify components don't receive getAuthHeaders as prop
    const Dashboard = () => {
      const { getAuthHeaders } = useAuth();  // From context, not props
      return <div>Dashboard</div>;
    };

    // Should render without props
    const { getByText } = render(
      <AuthProvider>
        <Dashboard />
      </AuthProvider>
    );

    expect(getByText('Dashboard')).toBeInTheDocument();
  });

  test('Auth state persists across re-renders', () => {
    const { rerender, getByText } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Trigger re-render
    rerender(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Auth state should persist
    expect(getByText('Authenticated')).toBeInTheDocument();
  });
});
```

---

### H6: Error Boundary Testing

#### Error Handling Tests

**File:** `tests/components/test_error_boundary.jsx`

```javascript
describe('ErrorBoundary', () => {
  // Suppress console.error for these tests
  beforeAll(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterAll(() => {
    console.error.mockRestore();
  });

  test('Catches component errors', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    const { getByText } = render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(getByText(/something went wrong/i)).toBeInTheDocument();
  });

  test('Shows error fallback UI', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    const { getByText, getByRole } = render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    // Should show reset button
    expect(getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  test('Resets error state on button click', () => {
    let shouldThrow = true;

    const MaybeThrow = () => {
      if (shouldThrow) {
        throw new Error('Test error');
      }
      return <div>Success</div>;
    };

    const { getByRole, getByText } = render(
      <ErrorBoundary>
        <MaybeThrow />
      </ErrorBoundary>
    );

    // Error shown initially
    expect(getByText(/something went wrong/i)).toBeInTheDocument();

    // Fix the error and click reset
    shouldThrow = false;
    fireEvent.click(getByRole('button', { name: /try again/i }));

    // Should show success
    expect(getByText('Success')).toBeInTheDocument();
  });
});
```

---

## Phase 4: Production Validation (Week 4)

### Comprehensive Test Suite

#### End-to-End User Journeys

**File:** `tests/e2e/test_user_journeys.spec.js`

```javascript
// Using Playwright or Cypress

describe('Complete User Journeys', () => {
  test('User registration to authorization approval', async () => {
    // 1. Register new user
    await page.goto('http://localhost:5173/register');
    await page.fill('[name="email"]', 'newuser@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    // 2. Verify email (mock)
    await waitFor(() => {
      expect(page.url()).toContain('/dashboard');
    });

    // 3. Navigate to Authorization Center
    await page.click('text=Authorization');

    // 4. Request high-risk action
    await page.click('text=Request Action');
    await page.fill('[name="action"]', 'Delete production database');
    await page.click('button[type="submit"]');

    // 5. Verify approval required
    await waitFor(() => {
      expect(page.locator('text=Pending Approval')).toBeVisible();
    });

    // 6. Login as approver
    await page.click('text=Logout');
    await page.goto('http://localhost:5173/login');
    await page.fill('[name="email"]', 'approver@example.com');
    await page.fill('[name="password"]', 'ApproverPass123!');
    await page.click('button[type="submit"]');

    // 7. Approve action
    await page.click('text=Authorization');
    await page.click('text=Pending Actions');
    await page.click('button:has-text("Approve")');

    // 8. Verify approval recorded
    await waitFor(() => {
      expect(page.locator('text=Approved')).toBeVisible();
    });
  });

  test('Policy creation to enforcement', async () => {
    // Login as admin
    await loginAsAdmin(page);

    // Create new policy
    await page.click('text=Policy Management');
    await page.click('text=Create Policy');
    await page.fill('[name="policy_name"]', 'No weekend deployments');
    await page.fill('[name="policy_rule"]', 'If action is deployment and time is weekend, then deny');
    await page.click('button:has-text("Create")');

    // Verify policy created
    await waitFor(() => {
      expect(page.locator('text=No weekend deployments')).toBeVisible();
    });

    // Test policy enforcement
    await page.click('text=Authorization');
    await page.click('text=Request Action');
    await page.selectOption('[name="action_type"]', 'deployment');

    // Mock weekend time
    await page.evaluate(() => {
      Date.now = () => new Date('2025-10-18T14:00:00').getTime(); // Saturday
    });

    await page.click('button[type="submit"]');

    // Verify policy denied action
    await waitFor(() => {
      expect(page.locator('text=Denied by policy: No weekend deployments')).toBeVisible();
    });
  });
});
```

---

### Security Penetration Testing

#### Automated Security Scans

**Script:** `scripts/security_scan.sh`

```bash
#!/bin/bash

echo "=== Security Penetration Testing ==="

# 1. OWASP ZAP Scan
echo "Running OWASP ZAP scan..."
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8001 \
  -r zap-report.html

# 2. SQL Injection Testing
echo "Testing SQL injection vectors..."
python scripts/test_sql_injection.py

# 3. XSS Testing
echo "Testing XSS vectors..."
python scripts/test_xss.py

# 4. CSRF Testing
echo "Testing CSRF protection..."
python scripts/test_csrf.py

# 5. Rate Limiting Testing
echo "Testing rate limiting..."
python scripts/test_rate_limiting.py

# 6. Authentication Bypass Testing
echo "Testing authentication bypass..."
python scripts/test_auth_bypass.py

echo "✓ Security scan complete. Review reports in ./security-reports/"
```

---

## Deployment Validation Checklist

### Pre-Deployment Checklist

```markdown
## Pre-Deployment Validation

### Code Quality
- [ ] All unit tests passing (>70% coverage)
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] No critical or high-severity bugs
- [ ] Code review completed
- [ ] Security audit passed

### Performance
- [ ] Bundle size <600 kB
- [ ] API P95 latency <500ms
- [ ] Lighthouse score >85
- [ ] Load testing passed (100 concurrent users)
- [ ] Database queries optimized

### Security
- [ ] Rate limiting active
- [ ] No tokens in localStorage
- [ ] CSRF protection enabled
- [ ] SQL injection tests passed
- [ ] XSS tests passed
- [ ] Security scan passed

### Configuration
- [ ] Environment variables configured
- [ ] Production secrets validated
- [ ] Database migrations applied
- [ ] Connection pool configured
- [ ] CORS settings correct

### Deployment
- [ ] 0 dead code files
- [ ] .dockerignore configured
- [ ] Docker build succeeds
- [ ] Deployment pipeline validated
- [ ] Rollback plan documented

### Monitoring
- [ ] Health check endpoint working
- [ ] Logging configured
- [ ] Alerts configured
- [ ] Monitoring dashboard ready
```

---

### Post-Deployment Checklist

```markdown
## Post-Deployment Validation

### Smoke Tests (Run immediately after deployment)
- [ ] Application accessible
- [ ] Login works
- [ ] Dashboard loads
- [ ] Authorization Center accessible
- [ ] API endpoints responding
- [ ] Database connection healthy

### Integration Tests (Run within 15 minutes)
- [ ] Full user journey test passed
- [ ] Policy creation/enforcement works
- [ ] Approval workflows functional
- [ ] Analytics data loading
- [ ] Alerts working

### Performance Tests (Run within 1 hour)
- [ ] Response times within targets
- [ ] No memory leaks
- [ ] Database performance acceptable
- [ ] Frontend performance good
- [ ] No errors in logs

### Monitoring (Monitor for 24 hours)
- [ ] Error rate <1%
- [ ] P95 latency <500ms
- [ ] No database connection issues
- [ ] No memory/CPU spikes
- [ ] User feedback positive
```

---

## Post-Deployment Monitoring

### Key Metrics to Monitor

#### Application Metrics

```yaml
Metrics:
  Performance:
    - API P50 Latency: <200ms
    - API P95 Latency: <500ms
    - API P99 Latency: <1000ms
    - Time to First Byte: <100ms
    - Time to Interactive: <2.5s

  Reliability:
    - Error Rate: <1%
    - Success Rate: >99%
    - Uptime: >99.9%

  Security:
    - Failed Login Rate: <5%
    - Rate Limit Triggers: Monitor
    - Account Lockouts: Monitor

  Business:
    - Active Users: Monitor
    - Actions Approved: Monitor
    - Policies Created: Monitor
```

#### Alerting Thresholds

```yaml
Critical Alerts (Page On-Call):
  - Error rate >5%
  - API P95 >2000ms
  - Database connection failure
  - Security breach detected

Warning Alerts (Slack/Email):
  - Error rate >2%
  - API P95 >800ms
  - High memory usage (>80%)
  - Unusual traffic patterns

Info Alerts (Dashboard):
  - Error rate >1%
  - API P95 >600ms
  - Rate limiting triggered
  - New user registrations
```

---

## Automated Testing Suite

### CI/CD Pipeline Configuration

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm install

      - name: Run unit tests
        run: npm test -- --coverage

      - name: Run Lighthouse
        run: npm run lighthouse

      - name: Validate bundle size
        run: npm run build && ./scripts/validate_bundle_size.sh

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run unit tests
        run: pytest tests/ --cov=. --cov-report=xml

      - name: Run security scan
        run: ./scripts/security_scan.sh

      - name: Validate dead code
        run: ./scripts/validate_dead_code.sh

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: [frontend-tests, backend-tests]
    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Run load tests
        run: python scripts/load_test.py

      - name: Shutdown services
        run: docker-compose down
```

---

## Conclusion

This comprehensive testing strategy ensures:

1. **Security hardening validated** (Week 1)
2. **Performance targets met** (Week 2)
3. **Architecture quality verified** (Week 3)
4. **Production readiness confirmed** (Week 4)

**Success depends on:**
- Executing tests at each phase
- Meeting all exit criteria before proceeding
- Continuous monitoring post-deployment
- Quick rollback if issues detected

---

**Document Owner:** QA Lead / Product Manager
**Last Updated:** 2025-10-15
**Next Review:** Weekly during remediation
**Status:** APPROVED - Ready for Execution
