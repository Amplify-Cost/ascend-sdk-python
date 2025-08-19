#!/bin/bash

echo "🔧 CRITICAL FRONTEND FIXES"
echo "=========================="
echo "Fixing: API_BASE_URL errors, login freezing, console errors"
echo ""

cd ow-ai-dashboard

# STEP 1: Create centralized API configuration
echo "📁 STEP 1: Creating centralized API config..."
mkdir -p src/config

cat > src/config/api.js << 'EOF'
// Centralized API configuration with fallbacks
const getApiBaseUrl = () => {
  // Try different environment variable approaches
  const viteUrl = import.meta.env.VITE_API_URL;
  const processUrl = typeof process !== 'undefined' && process.env?.VITE_API_URL;
  
  // Fallback chain
  return viteUrl || processUrl || 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

// Debug logging (remove in production)
console.log('🔧 API Configuration:', {
  'import.meta.env.VITE_API_URL': import.meta.env.VITE_API_URL,
  'Final API_BASE_URL': API_BASE_URL
});

export default API_BASE_URL;
EOF

echo "✅ API config created"

# STEP 2: Fix the main App.jsx to resolve login errors
echo "📄 STEP 2: Fixing App.jsx login function..."

# Create backup
cp src/App.jsx src/App.jsx.backup

cat > src/App.jsx << 'EOF'
import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from './config/api.js';
import './App.css';

// Import components
import Dashboard from './components/Dashboard';
import Alerts from './components/Alerts';
import AgentAuthorization from './components/AgentAuthorization';
import AgentActivityFeed from './components/AgentActivityFeed';
import RiskAssessment from './components/RiskAssessment';
import PolicyManagement from './components/PolicyManagement';
import Compliance from './components/Compliance';
import DataManager from './components/DataManager';

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
      
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const userData = await response.json();
        console.log('✅ Enterprise authentication valid:', userData);
        setUser(userData);
      } else {
        console.log('ℹ️ No valid enterprise authentication - showing login');
        setUser(null);
      }
    } catch (error) {
      console.error('❌ Enterprise auth check error:', error);
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

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: loginData.email,
          password: loginData.password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        console.log('✅ Enterprise login successful');
        setUser(data.user);
        setLoginData({ email: '', password: '' });
      } else {
        throw new Error(data.detail || 'Login failed');
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      setLoginError(error.message || 'Login failed');
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      
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
    { id: 'risk', name: 'Risk Assessment', icon: '⚠️' },
    { id: 'policy', name: 'Policy Management', icon: '📋' },
    { id: 'compliance', name: 'Compliance', icon: '✅' },
    { id: 'data', name: 'Data Manager', icon: '🗄️' },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'authorization':
        return <AgentAuthorization />;
      case 'activity':
        return <AgentActivityFeed />;
      case 'alerts':
        return <Alerts />;
      case 'risk':
        return <RiskAssessment />;
      case 'policy':
        return <PolicyManagement />;
      case 'compliance':
        return <Compliance />;
      case 'data':
        return <DataManager />;
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

echo "✅ App.jsx fixed"

# STEP 3: Update environment files
echo "🌍 STEP 3: Updating environment configuration..."

# Update .env file
cat > .env << 'EOF'
VITE_API_URL=https://owai-production.up.railway.app
VITE_APP_NAME=OW-AI Enterprise
VITE_ENVIRONMENT=production
EOF

# Update .env.local (for local development)
cat > .env.local << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=OW-AI Enterprise (Local)
VITE_ENVIRONMENT=development
EOF

echo "✅ Environment files updated"

# STEP 4: Update vite.config.js for proper env variable handling
echo "⚙️ STEP 4: Updating Vite configuration..."

cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    // Make sure all VITE_ variables are available
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL),
    'import.meta.env.VITE_APP_NAME': JSON.stringify(process.env.VITE_APP_NAME),
    'import.meta.env.VITE_ENVIRONMENT': JSON.stringify(process.env.VITE_ENVIRONMENT),
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: undefined
      }
    }
  },
  server: {
    port: 3000,
    host: true
  }
})
EOF

echo "✅ Vite config updated"

# STEP 5: Fix any remaining components that use API_BASE_URL
echo "🔧 STEP 5: Updating components to use centralized API config..."

# Create a script to update all component files
cat > fix_api_imports.sh << 'EOF'
#!/bin/bash

echo "Fixing API imports in all components..."

# Find all JS/JSX files and update API_BASE_URL usage
find src/components -name "*.jsx" -o -name "*.js" | while read file; do
  if grep -q "API_BASE_URL" "$file"; then
    echo "Updating $file..."
    
    # Add import at the top if not present
    if ! grep -q "import.*API_BASE_URL.*from.*config/api" "$file"; then
      # Insert import after existing imports or at the top
      sed -i '1i import { API_BASE_URL } from "../config/api.js";' "$file"
    fi
    
    # Remove any local API_BASE_URL definitions
    sed -i '/const API_BASE_URL = /d' "$file"
  fi
done

echo "✅ All components updated to use centralized API config"
EOF

chmod +x fix_api_imports.sh
./fix_api_imports.sh

echo "✅ Component API imports fixed"

# STEP 6: Clear build cache and test
echo "🧹 STEP 6: Clearing build cache..."

rm -rf node_modules/.vite
rm -rf dist
npm install

echo "✅ Build cache cleared"

# STEP 7: Create test script
cat > test_fixes.sh << 'EOF'
#!/bin/bash

echo "🧪 TESTING FIXES"
echo "==============="
echo ""

echo "1. Testing environment variables..."
echo "VITE_API_URL: $VITE_API_URL"

echo ""
echo "2. Building application..."
npm run build

if [ $? -eq 0 ]; then
  echo "✅ Build successful"
else
  echo "❌ Build failed"
  exit 1
fi

echo ""
echo "3. Starting development server..."
echo "Run: npm run dev"
echo "Then check browser console for errors"
echo ""
echo "4. What to look for:"
echo "- No 'API_BASE_URL is not defined' errors"
echo "- Login form should work without freezing"
echo "- Authentication should complete successfully"
EOF

chmod +x test_fixes.sh

echo ""
echo "🎯 FIXES COMPLETED!"
echo "=================="
echo ""
echo "✅ Fixed API_BASE_URL configuration"
echo "✅ Fixed login function errors"
echo "✅ Updated environment variable handling"
echo "✅ Created enterprise-grade login UI"
echo "✅ Added proper error handling"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Run: ./test_fixes.sh"
echo "2. Run: npm run dev"
echo "3. Test login functionality"
echo "4. Check browser console for remaining errors"
echo ""
echo "If issues persist, share the new console output!"