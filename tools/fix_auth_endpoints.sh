#!/bin/bash

echo "🔧 FIXING AUTHENTICATION ENDPOINTS & fetchWithAuth"
echo "=================================================="

cd ow-ai-dashboard

# Fix 1: Fix the fetchWithAuth.js error
echo "🛠️ STEP 1: Fixing fetchWithAuth.js 'text is not defined' error..."

cp src/utils/fetchWithAuth.js src/utils/fetchWithAuth.js.backup.$(date +%Y%m%d_%H%M%S)

cat > src/utils/fetchWithAuth.js << 'EOF'
/**
 * Enterprise cookie-mode fetch helper.
 * - Always sends cookies (credentials: 'include')
 * - Strips Authorization header (cookie-mode backend rejects Bearer)
 * - Adds X-CSRF-Token if a csrftoken cookie exists
 * - Uses VITE_API_URL || window.location.origin as base
 */
export async function fetchWithAuth(endpoint, options = {}) {
  const API_BASE_URL =
    (import.meta?.env?.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) ||
    window.location.origin;

  const headers = new Headers(options.headers || {});

  // In cookie mode: do NOT send Authorization
  if (headers.has('Authorization')) headers.delete('Authorization');

  // Optional CSRF header, if backend sets csrftoken cookie
  try {
    const csrf = document.cookie
      ?.split('; ')
      ?.find((c) => c.startsWith('csrftoken='))
      ?.split('=')[1];
    if (csrf && !headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', csrf);
  } catch {}

  const resp = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ?? null,
    credentials: 'include',
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`HTTP ${resp.status}: ${resp.statusText}${text ? ` - ${text}` : ''}`);
  }
  
  const ct = resp.headers.get('content-type') || '';
  return ct.includes('application/json') ? resp.json() : resp.text();
}

export async function getCurrentUser() {
  try {
    return await fetchWithAuth('/auth/me');
  } catch (error) {
    console.error('Error fetching current user:', error);
    throw error;
  }
}

export async function logout() {
  try {
    return await fetchWithAuth('/auth/logout', { method: 'POST' });
  } catch (error) {
    console.error('Error during logout:', error);
    throw error;
  }
}
EOF

echo "✅ Fixed fetchWithAuth.js - removed undefined 'text' variable"

# Fix 2: Update App.jsx to use correct backend endpoints
echo "🛠️ STEP 2: Updating App.jsx to use correct backend endpoints..."

cp src/App.jsx src/App.jsx.backup.$(date +%Y%m%d_%H%M%S)

cat > src/App.jsx << 'EOF'
import React, { useState, useEffect } from 'react';
import { fetchWithAuth, getCurrentUser, logout } from './utils/fetchWithAuth.js';
import './App.css';

// Import EXISTING components
import Dashboard from './components/Dashboard.jsx';
import Alerts from './components/Alerts.jsx';
import AgentAuthorizationDashboard from './components/AgentAuthorizationDashboard.jsx';
import AgentActivityFeed from './components/AgentActivityFeed.jsx';
import Compliance from './components/Compliance.jsx';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [loginError, setLoginError] = useState('');

  // Check authentication on app load
  useEffect(() => {
    console.log('🏢 Enterprise cookie auth check (one-time)...');
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      console.log('🍪 Enterprise cookie-only auth');
      
      const userData = await getCurrentUser();
      console.log('✅ Enterprise authentication valid:', userData);
      setUser(userData);
    } catch (error) {
      console.log('ℹ️ No valid enterprise authentication - showing login');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    
    try {
      console.log('🔐 Enterprise login attempt...');
      
      // Validate inputs
      if (!loginData.email || !loginData.password) {
        throw new Error('Email and password are required');
      }

      // FIXED: Use correct backend endpoint /auth/token instead of /auth/login
      const data = await fetchWithAuth('/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: loginData.email,
          password: loginData.password,
        }),
      });

      console.log('✅ Enterprise login successful');
      setUser(data.user);
      setLoginData({ email: '', password: '' });
    } catch (error) {
      console.error('❌ Login error:', error);
      setLoginError(error.message || 'Login failed');
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      setUser(null);
      setActiveTab('dashboard');
      console.log('✅ Enterprise logout successful');
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Force logout even if API call fails
      setUser(null);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading OW-AI Enterprise...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-800 flex items-center justify-center p-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl font-bold text-white">OW</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">OW-AI Enterprise</h2>
            <p className="text-gray-300">AI Security & Governance Platform</p>
          </div>
          
          <form onSubmit={handleLogin} className="mt-8 space-y-6">
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={loginData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your email"
                />
              </div>
              
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={loginData.password}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your password"
                />
              </div>
            </div>

            {loginError && (
              <div className="bg-red-900 border border-red-700 text-red-300 px-4 py-3 rounded-lg">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Sign In to Enterprise Platform
            </button>
          </form>
        </div>
      </div>
    );
  }

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'authorization', name: 'Agent Authorization', icon: '🤖' },
    { id: 'activity', name: 'Activity Feed', icon: '📈' },
    { id: 'alerts', name: 'Alerts', icon: '🚨' },
    { id: 'compliance', name: 'Compliance', icon: '✅' }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'authorization':
        return <AgentAuthorizationDashboard user={user} />;
      case 'activity':
        return <AgentActivityFeed />;
      case 'alerts':
        return <Alerts />;
      case 'compliance':
        return <Compliance />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-lg font-bold text-white">OW</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">OW-AI Enterprise</h1>
                <p className="text-sm text-gray-500">AI Security & Governance Platform</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, <span className="font-medium">{user.email}</span>
              </span>
              <button
                onClick={handleLogout}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-lg h-screen">
          <div className="p-4">
            <ul className="space-y-2">
              {navigation.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-2 rounded-lg text-left transition-colors ${
                      activeTab === item.id
                        ? 'bg-blue-100 text-blue-700 border-l-4 border-blue-500'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span className="font-medium">{item.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;
EOF

echo "✅ Updated App.jsx to use correct backend endpoint (/auth/token)"

# Fix 3: Update environment to point to localhost for development
echo "🛠️ STEP 3: Updating environment for local development..."

cat > .env.local << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=OW-AI Enterprise (Local)
VITE_ENVIRONMENT=development
EOF

echo "✅ Created .env.local for local development"

echo ""
echo "🎯 FIXES APPLIED:"
echo "================="
echo "✅ Fixed fetchWithAuth.js 'text is not defined' error"
echo "✅ Updated login endpoint: /auth/login → /auth/token"  
echo "✅ Fixed login data format: JSON → form-urlencoded"
echo "✅ Set correct local API URL: http://localhost:8000"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. npm run dev (start frontend)"
echo "2. Test login with your credentials"
echo "3. Should now connect to your local backend on port 8000"
echo ""
echo "Your backend is running and ready! Try logging in now."