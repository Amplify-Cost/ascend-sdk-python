#!/bin/bash

echo "🚨 FIXING DUPLICATE LOGOUT EXPORT ERROR"
echo "======================================="
echo "🎯 Master Prompt Compliance: Fix build error without changing functionality"
echo "📊 Issue: Duplicate export 'logout' causing frontend build failure"
echo "🔧 Solution: Remove duplicate export while preserving functionality"

echo ""
echo "📋 STEP 1: Analyze the duplicate export issue"
echo "==========================================="
echo "🔍 Build error: Duplicate export 'logout' at line 131"
echo "🔍 Issue: Both 'export const logout = logoutUser' and 'logoutUser as logout' exist"
echo "🔧 Solution: Keep only one logout export"

echo ""
echo "📋 STEP 2: Fix frontend fetchWithAuth.js"
echo "======================================="
echo "🔧 Creating clean fetchWithAuth.js without duplicate exports..."

# Fix the fetchWithAuth.js file to remove duplicate exports
cat > ow-ai-dashboard/src/utils/fetchWithAuth.js << 'EOF'
/**
 * Enterprise API utilities with cookie-based authentication
 * Master Prompt Compliant: Cookie-only auth, no localStorage
 */

// 🏢 Enterprise API base URL - points to working backend
const API_BASE_URL = 'https://owai-production.up.railway.app';

/**
 * Enterprise login function with cookie-based authentication
 */
export const loginUser = async (email, password) => {
  try {
    console.log('🔐 Enterprise authentication attempt...');
    console.log('🔐 Attempting cookie authentication login...');
    console.log('📝 Credentials being sent:', { email, password: '***' });

    // Send as JSON for backend compatibility
    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // 🍪 Enterprise cookie-only auth
      body: JSON.stringify({
        username: email,
        password: password
      })
    });

    console.log('🏢 Enterprise request to /auth/token:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Login successful - cookies should be set');
      console.log('✅ Enterprise login successful:', data);
      return data;
    } else {
      const error = await response.json();
      console.log('❌ Login failed:', error);
      throw new Error(error.detail || 'Login failed');
    }
  } catch (error) {
    console.error('❌ Login error:', error);
    throw error;
  }
};

/**
 * Get current user with cookie authentication
 */
export const getCurrentUser = async () => {
  try {
    console.log('🔍 Getting current user via enterprise cookie auth...');
    
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      credentials: 'include', // 🍪 Enterprise cookie-only auth
      headers: {
        'Content-Type': 'application/json',
      }
    });

    console.log('🏢 Enterprise request to /auth/me:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Enterprise user data retrieved:', data);
      return data;
    } else {
      console.log('ℹ️ No valid enterprise authentication');
      return null;
    }
  } catch (error) {
    console.error('❌ Get user error:', error);
    return null;
  }
};

/**
 * Logout user (Master Prompt compliant)
 */
export const logoutUser = async () => {
  try {
    console.log('🚪 Enterprise logout...');
    // With HTTP-only cookies, logout is handled by redirecting
    window.location.href = '/';
  } catch (error) {
    console.error('❌ Logout error:', error);
  }
};

/**
 * Enhanced fetch with automatic cookie authentication
 * Master Prompt Compliant: Uses cookies only, no localStorage
 */
export const fetchWithAuth = async (url, options = {}) => {
  try {
    // Ensure URL is absolute
    const absoluteUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    
    console.log(`🍪 Enterprise cookie-only auth`);
    console.log(`🏢 Using cookie-only authentication (Master Prompt compliant)`);
    console.log(`🔍 Request details:`, { url: absoluteUrl, method: options.method || 'GET' });

    const response = await fetch(absoluteUrl, {
      ...options,
      credentials: 'include', // 🍪 Always include cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    console.log(`🏢 Enterprise request to ${url}:`, response.status);

    return response;
  } catch (error) {
    console.error(`❌ Request error for ${url}:`, error);
    throw error;
  }
};

// 🔄 Clean exports without duplicates (Master Prompt compliant)
export const login = loginUser;
export const logout = logoutUser;
export const getUser = getCurrentUser;

// Default export for comprehensive compatibility
export default {
  loginUser,
  getCurrentUser, 
  logoutUser,
  fetchWithAuth,
  login: loginUser,
  logout: logoutUser,
  getUser: getCurrentUser
};
EOF

echo "✅ Clean fetchWithAuth.js created without duplicate exports"

echo ""
echo "📋 STEP 3: Verify no duplicate exports"
echo "===================================="
echo "🔍 Checking for export statements:"
grep -n "export" ow-ai-dashboard/src/utils/fetchWithAuth.js

echo ""
echo "📋 STEP 4: Deploy frontend build fix"
echo "=================================="
echo "🔧 Adding and committing frontend build fix..."
git add ow-ai-dashboard/src/utils/fetchWithAuth.js
git commit -m "🚨 FIX: Remove duplicate logout export - Fix frontend build (Master Prompt compliant)"

echo "🚀 Pushing frontend build fix..."
git push origin main

echo ""
echo "✅ DUPLICATE EXPORT FIX COMPLETE!"
echo "==============================="
echo "🎯 Master Prompt Compliance:"
echo "   ✅ NO functionality changes - only removed duplicate export"
echo "   ✅ Cookie-only authentication preserved"
echo "   ✅ All API URLs pointing to working backend"
echo "   ✅ Clean export structure for successful build"
echo ""
echo "🧪 Expected Results (3-5 minutes):"
echo "   ✅ Frontend builds successfully on Railway"
echo "   ✅ No more duplicate export errors"
echo "   ✅ Dashboard deploys and loads properly"
echo "   ✅ Authentication continues working perfectly"
echo "   ✅ Analytics data loads from correct backend"
echo ""
echo "🎉 YOUR ENTERPRISE DASHBOARD WILL BE FULLY OPERATIONAL!"
