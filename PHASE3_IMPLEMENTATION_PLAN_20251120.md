# Phase 3 AWS Cognito Frontend Integration - IMPLEMENTATION PLAN

**Date**: November 20, 2025
**Engineer**: OW-KAI Engineer
**Status**: 🚧 **IN PROGRESS**
**Phase**: Frontend AWS Cognito Integration
**Duration Estimate**: 6-8 hours

---

## 📊 EXECUTIVE SUMMARY

Phase 3 focuses on migrating the frontend from cookie-based authentication to AWS Cognito JWT authentication, aligning with the completed Phase 2 backend implementation.

### Current State:
- ✅ Phase 2 backend complete with AWS Cognito JWT validation
- ✅ 3 test users created across 3 organizations
- ✅ Backend endpoints operational and tested
- ⚠️ Frontend still using legacy cookie authentication
- ⚠️ JWT tokens not being sent from frontend to backend

### Target State:
- ✅ Frontend uses AWS Cognito SDK for authentication
- ✅ JWT ID tokens sent with all API requests
- ✅ Seamless login/logout experience
- ✅ Secure token storage and management
- ✅ Token refresh handling
- ✅ End-to-end authentication working

---

## 🎯 OBJECTIVES

### Primary Objectives:
1. **Replace cookie authentication with Cognito JWT authentication**
2. **Implement AWS Cognito SDK integration**
3. **Update all API calls to send Cognito ID tokens**
4. **Implement secure token storage**
5. **Create smooth user experience for login/logout**

### Secondary Objectives:
1. Token refresh handling
2. Error handling for expired tokens
3. Organization context from JWT claims
4. Session management

---

## 🏗️ ARCHITECTURE OVERVIEW

### Authentication Flow:

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │
       │ 1. Login credentials
       ▼
┌─────────────────────────┐
│   Login.jsx             │
│   (React Component)     │
└──────┬──────────────────┘
       │
       │ 2. Authenticate
       ▼
┌─────────────────────────┐
│   Cognito Auth Service  │
│   (cognitoAuth.js)      │
└──────┬──────────────────┘
       │
       │ 3. Cognito authentication
       ▼
┌─────────────────────────┐
│   AWS Cognito           │
│   (User Pool)           │
│   us-east-2_HPew14Rbn   │
└──────┬──────────────────┘
       │
       │ 4. JWT tokens (ID, Access, Refresh)
       ▼
┌─────────────────────────┐
│   AuthContext           │
│   (Global State)        │
└──────┬──────────────────┘
       │
       │ 5. Store tokens
       ▼
┌─────────────────────────┐
│   sessionStorage        │
│   (Secure Storage)      │
└─────────────────────────┘

API Request Flow:
┌──────────────┐
│  Component   │
└──────┬───────┘
       │
       │ 1. API call
       ▼
┌──────────────────┐
│  fetchWithAuth   │
└──────┬───────────┘
       │
       │ 2. Get ID token
       ▼
┌──────────────────┐
│  AuthContext     │
└──────┬───────────┘
       │
       │ 3. Add Authorization header
       ▼
┌──────────────────────────┐
│  Backend API             │
│  (Cognito middleware)    │
└──────────────────────────┘
```

---

## 📋 IMPLEMENTATION TASKS

### Task 1: Install AWS Cognito SDK
**Duration**: 15 minutes
**Priority**: CRITICAL

```bash
cd owkai-pilot-frontend
npm install amazon-cognito-identity-js
```

**Why amazon-cognito-identity-js**:
- ✅ Lightweight (no AWS Amplify bloat)
- ✅ Direct Cognito SDK support
- ✅ Better control over authentication flow
- ✅ No UI components (we have our own)

**Alternative**: AWS Amplify (heavier, but includes UI components)
```bash
npm install aws-amplify @aws-amplify/ui-react
```

**Decision**: Use `amazon-cognito-identity-js` for enterprise control

---

### Task 2: Create Cognito Authentication Service
**Duration**: 1-2 hours
**Priority**: CRITICAL
**File**: `src/services/cognitoAuth.js`

```javascript
// src/services/cognitoAuth.js
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserSession
} from 'amazon-cognito-identity-js';
import logger from '../utils/logger';

// Cognito User Pool Configuration
const POOL_DATA = {
  UserPoolId: 'us-east-2_HPew14Rbn',
  ClientId: '2t9sms0kmd85huog79fqpslc2u'
};

const userPool = new CognitoUserPool(POOL_DATA);

/**
 * Enterprise Cognito Authentication Service
 *
 * Features:
 * - JWT-based authentication with RS256 validation
 * - Organization context from custom attributes
 * - Secure token management
 * - Token refresh handling
 */

/**
 * Authenticate user with email and password
 * Returns JWT tokens and user attributes
 */
export const cognitoLogin = (email, password) => {
  return new Promise((resolve, reject) => {
    const authenticationData = {
      Username: email.toLowerCase(),
      Password: password,
    };

    const authenticationDetails = new AuthenticationDetails(authenticationData);

    const userData = {
      Username: email.toLowerCase(),
      Pool: userPool,
    };

    const cognitoUser = new CognitoUser(userData);

    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (session) => {
        logger.debug('✅ Cognito authentication successful');

        // Extract tokens
        const idToken = session.getIdToken().getJwtToken();
        const accessToken = session.getAccessToken().getJwtToken();
        const refreshToken = session.getRefreshToken().getToken();

        // Extract user attributes from ID token
        const idTokenPayload = session.getIdToken().decodePayload();

        const user = {
          id: idTokenPayload['sub'],
          email: idTokenPayload['email'],
          organization_id: parseInt(idTokenPayload['custom:organization_id']),
          organization_slug: idTokenPayload['custom:organization_slug'],
          role: idTokenPayload['custom:role'],
          is_org_admin: idTokenPayload['custom:is_org_admin'] === 'true'
        };

        resolve({
          idToken,
          accessToken,
          refreshToken,
          user,
          session
        });
      },

      onFailure: (err) => {
        logger.error('❌ Cognito authentication failed:', err);
        reject(err);
      },

      newPasswordRequired: (userAttributes, requiredAttributes) => {
        logger.warn('⚠️ New password required');
        reject({
          code: 'NewPasswordRequired',
          message: 'Please set a new password',
          userAttributes,
          requiredAttributes
        });
      }
    });
  });
};

/**
 * Logout current user
 */
export const cognitoLogout = () => {
  const cognitoUser = userPool.getCurrentUser();
  if (cognitoUser) {
    cognitoUser.signOut();
    logger.debug('✅ Cognito logout successful');
  }
};

/**
 * Get current authenticated session
 */
export const getCurrentSession = () => {
  return new Promise((resolve, reject) => {
    const cognitoUser = userPool.getCurrentUser();

    if (!cognitoUser) {
      reject(new Error('No current user'));
      return;
    }

    cognitoUser.getSession((err, session) => {
      if (err) {
        reject(err);
        return;
      }

      if (!session.isValid()) {
        reject(new Error('Session is not valid'));
        return;
      }

      resolve(session);
    });
  });
};

/**
 * Get ID token from current session
 */
export const getIdToken = async () => {
  try {
    const session = await getCurrentSession();
    return session.getIdToken().getJwtToken();
  } catch (error) {
    logger.error('❌ Failed to get ID token:', error);
    throw error;
  }
};

/**
 * Get current user attributes
 */
export const getCurrentUserAttributes = () => {
  return new Promise((resolve, reject) => {
    const cognitoUser = userPool.getCurrentUser();

    if (!cognitoUser) {
      reject(new Error('No current user'));
      return;
    }

    cognitoUser.getSession((err, session) => {
      if (err) {
        reject(err);
        return;
      }

      cognitoUser.getUserAttributes((err, attributes) => {
        if (err) {
          reject(err);
          return;
        }

        const userAttributes = {};
        attributes.forEach(attr => {
          userAttributes[attr.Name] = attr.Value;
        });

        resolve(userAttributes);
      });
    });
  });
};

/**
 * Refresh session tokens
 */
export const refreshSession = () => {
  return new Promise((resolve, reject) => {
    const cognitoUser = userPool.getCurrentUser();

    if (!cognitoUser) {
      reject(new Error('No current user'));
      return;
    }

    cognitoUser.getSession((err, session) => {
      if (err) {
        reject(err);
        return;
      }

      const refreshToken = session.getRefreshToken();

      cognitoUser.refreshSession(refreshToken, (err, newSession) => {
        if (err) {
          reject(err);
          return;
        }

        logger.debug('✅ Session refreshed successfully');
        resolve(newSession);
      });
    });
  });
};
```

---

### Task 3: Create AuthContext for Global State
**Duration**: 1 hour
**Priority**: CRITICAL
**File**: `src/contexts/AuthContext.jsx`

```javascript
// src/contexts/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { cognitoLogin, cognitoLogout, getCurrentSession, getIdToken } from '../services/cognitoAuth';
import logger from '../utils/logger';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [idToken, setIdToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const session = await getCurrentSession();

      if (session.isValid()) {
        const idTokenPayload = session.getIdToken().decodePayload();
        const token = session.getIdToken().getJwtToken();

        const userData = {
          id: idTokenPayload['sub'],
          email: idTokenPayload['email'],
          organization_id: parseInt(idTokenPayload['custom:organization_id']),
          organization_slug: idTokenPayload['custom:organization_slug'],
          role: idTokenPayload['custom:role'],
          is_org_admin: idTokenPayload['custom:is_org_admin'] === 'true'
        };

        setUser(userData);
        setIdToken(token);
        setIsAuthenticated(true);
        logger.debug('✅ Session restored from Cognito');
      }
    } catch (error) {
      logger.debug('No valid session found');
      setUser(null);
      setIdToken(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const result = await cognitoLogin(email, password);

      setUser(result.user);
      setIdToken(result.idToken);
      setIsAuthenticated(true);

      logger.debug('✅ Login successful:', result.user.email);
      return result;
    } catch (error) {
      logger.error('❌ Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    cognitoLogout();
    setUser(null);
    setIdToken(null);
    setIsAuthenticated(false);
    logger.debug('✅ Logout successful');
  };

  const getAuthToken = async () => {
    try {
      // Try to get fresh token
      const token = await getIdToken();
      setIdToken(token);
      return token;
    } catch (error) {
      // Session expired, logout
      await logout();
      throw error;
    }
  };

  const value = {
    user,
    idToken,
    isAuthenticated,
    loading,
    login,
    logout,
    getAuthToken
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

---

### Task 4: Update Login.jsx Component
**Duration**: 1 hour
**Priority**: CRITICAL
**File**: `src/components/Login.jsx`

**Changes Required**:
1. Remove cookie authentication logic
2. Use `useAuth()` hook from AuthContext
3. Call `auth.login(email, password)` instead of fetch
4. Handle Cognito-specific errors

---

### Task 5: Update App.jsx
**Duration**: 1 hour
**Priority**: CRITICAL
**File**: `src/App.jsx`

**Changes Required**:
1. Wrap app with `<AuthProvider>`
2. Use `useAuth()` hook instead of local state
3. Remove cookie authentication checks
4. Use `auth.user` and `auth.isAuthenticated`

---

### Task 6: Update fetchWithAuth.js
**Duration**: 1 hour
**Priority**: CRITICAL
**File**: `src/utils/fetchWithAuth.js`

**Changes Required**:
1. Remove CSRF token logic (not needed for JWT)
2. Get ID token from AuthContext
3. Add `Authorization: Bearer <idToken>` header
4. Remove cookie credentials

---

### Task 7: Environment Variables
**Duration**: 15 minutes
**Priority**: HIGH
**File**: `.env` and `.env.local`

```bash
# .env
VITE_COGNITO_USER_POOL_ID=us-east-2_HPew14Rbn
VITE_COGNITO_APP_CLIENT_ID=2t9sms0kmd85huog79fqpslc2u
VITE_COGNITO_REGION=us-east-2
VITE_API_URL=https://pilot.owkai.app
```

---

### Task 8: Testing
**Duration**: 2 hours
**Priority**: CRITICAL

**Test Cases**:
1. Login with platform-admin@owkai.com
2. Login with test-pilot-admin@example.com
3. Login with test-growth-admin@example.com
4. Verify JWT tokens in API requests
5. Test organization isolation
6. Test token expiration handling
7. Test logout flow
8. Test protected routes

---

## 🔐 SECURITY CONSIDERATIONS

### Token Storage:
- ✅ Use `sessionStorage` for ID tokens (not localStorage)
- ✅ Tokens cleared on browser close
- ✅ No sensitive data in cookies
- ✅ JWT validation on backend

### Error Handling:
- ✅ Graceful token expiration
- ✅ Automatic session refresh
- ✅ Clear error messages
- ✅ Audit logging

---

## 📝 SUCCESS CRITERIA

### Must Have:
- [x] AWS Cognito SDK installed
- [ ] Cognito authentication service created
- [ ] AuthContext implemented
- [ ] Login.jsx updated to use Cognito
- [ ] App.jsx updated to use AuthContext
- [ ] fetchWithAuth.js updated for JWT tokens
- [ ] All test users can login successfully
- [ ] JWT tokens sent with API requests
- [ ] Backend validates JWT tokens correctly
- [ ] Organization isolation working

### Nice to Have:
- [ ] Token refresh handling
- [ ] Error boundary for auth errors
- [ ] Loading states during authentication
- [ ] Password reset flow
- [ ] MFA support (future)

---

## 📊 RISK ASSESSMENT

### High Risk:
- ❌ **Token storage security** → Use sessionStorage, not localStorage
- ❌ **Token expiration handling** → Implement auto-refresh
- ❌ **Breaking existing functionality** → Test thoroughly

### Medium Risk:
- ⚠️ **User experience during migration** → Clear error messages
- ⚠️ **Third-party SDK updates** → Pin SDK version

### Low Risk:
- ✅ **Performance impact** → JWT validation is fast
- ✅ **Browser compatibility** → Modern browsers support JWT

---

## 🎓 IMPLEMENTATION BEST PRACTICES

### Enterprise Standards:
1. **No Quick Fixes** - Proper Cognito integration
2. **Real Data Testing** - Use actual test users
3. **Comprehensive Error Handling** - Handle all edge cases
4. **Audit Logging** - Log all authentication events
5. **Documentation** - Complete documentation of changes

### Code Quality:
1. Follow existing code patterns
2. Add JSDoc comments
3. Use TypeScript-style prop validation
4. Test all authentication paths
5. Handle loading states

---

## 📞 PRODUCTION READINESS

### Pre-Deployment Checklist:
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Cognito service tested locally
- [ ] AuthContext tested
- [ ] Login flow tested
- [ ] Logout flow tested
- [ ] API calls sending JWT tokens
- [ ] Backend validating tokens
- [ ] Error handling working
- [ ] Loading states implemented
- [ ] Code reviewed
- [ ] Documentation complete

---

## 🚀 DEPLOYMENT PLAN

### Local Development:
```bash
cd owkai-pilot-frontend
npm install amazon-cognito-identity-js
npm run dev:local
```

### Production Deployment:
```bash
npm run build:prod
# Deploy to Railway or hosting platform
```

---

## ✅ NEXT STEPS

After Phase 3 completion, proceed to:
1. **Phase 4**: Organization admin dashboard
2. **Phase 5**: User invitation workflows
3. **Phase 6**: Stripe billing integration

---

**Engineer**: OW-KAI Engineer
**Date**: November 20, 2025
**Status**: 🚧 **IN PROGRESS**

*Ready to implement Phase 3 frontend integration with enterprise-grade quality*
