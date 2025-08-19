import React, { useState, useEffect } from 'react';
import { fetchWithAuth, getCurrentUser, logout } from './utils/fetchWithAuth.js';
import { ThemeProvider } from './contexts/ThemeContext.jsx';

// Import ALL your original components
import Dashboard from './components/Dashboard.jsx';
import Alerts from './components/Alerts.jsx';
import AgentAuthorizationDashboard from './components/AgentAuthorizationDashboard.jsx';
import AgentActivityFeed from './components/AgentActivityFeed.jsx';
import RiskAssessment from './components/RiskAssessment.jsx';
import PolicyManagement from './components/PolicyManagement.jsx';
import Compliance from './components/Compliance.jsx';
import DataManager from './components/DataManager.jsx';
import Analytics from './components/Analytics.jsx';
import SecurityReports from './components/SecurityReports.jsx';
import EnterpriseUserManagement from './components/EnterpriseUserManagement.jsx';
import SecurityInsights from './components/SecurityInsights.jsx';
import SmartRuleGen from './components/SmartRuleGen.jsx';

// Keep the working error boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Component Error</h2>
            <p className="text-gray-600 mb-4">A component failed to load.</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [loginError, setLoginError] = useState('');

  // Working authentication check
  useEffect(() => {
    console.log('🏢 Enterprise cookie auth check...');
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const userData = await getCurrentUser();
      if (userData && typeof userData === 'object' && userData.email) {
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // Working login function (KEEP THIS - IT WORKS!)
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    
    try {
      if (!loginData.email || !loginData.password) {
        throw new Error('Email and password are required');
      }

      // This is the working auth format for your backend
      const data = await fetchWithAuth('/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: loginData.email,
          password: loginData.password
        }),
      });

      if (data && data.user) {
        setUser(data.user);
        setLoginData({ email: '', password: '' });
      } else if (data && data.access_token) {
        setUser({ 
          email: loginData.email, 
          role: 'user',
          authenticated: true
        });
        setLoginData({ email: '', password: '' });
      }
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
    } catch (error) {
      setUser(null);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({ ...prev, [name]: value }));
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
                  className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Sign In
            </button>
          </form>
        </div>
      </div>
    );
  }

  // RESTORE ALL YOUR ORIGINAL NAVIGATION TABS
  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'authorization', name: 'Agent Authorization', icon: '🤖' },
    { id: 'activity', name: 'Activity Feed', icon: '📈' },
    { id: 'alerts', name: 'Alerts', icon: '🚨' },
    { id: 'risk', name: 'Risk Assessment', icon: '⚠️' },
    { id: 'policy', name: 'Policy Management', icon: '📋' },
    { id: 'compliance', name: 'Compliance', icon: '✅' },
    { id: 'data', name: 'Data Manager', icon: '🗄️' },
    { id: 'analytics', name: 'Analytics', icon: '📈' },
    { id: 'security', name: 'Security Reports', icon: '🔒' },
    { id: 'users', name: 'User Management', icon: '👥' },
    { id: 'insights', name: 'Security Insights', icon: '💡' },
    { id: 'rules', name: 'Smart Rules', icon: '🧠' }
  ];

  // RESTORE ALL YOUR ORIGINAL COMPONENTS
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <ErrorBoundary>
            <Dashboard />
          </ErrorBoundary>
        );
      case 'authorization':
        return (
          <ErrorBoundary>
            <AgentAuthorizationDashboard user={user} />
          </ErrorBoundary>
        );
      case 'activity':
        return (
          <ErrorBoundary>
            <AgentActivityFeed />
          </ErrorBoundary>
        );
      case 'alerts':
        return (
          <ErrorBoundary>
            <Alerts />
          </ErrorBoundary>
        );
      case 'risk':
        return (
          <ErrorBoundary>
            <RiskAssessment />
          </ErrorBoundary>
        );
      case 'policy':
        return (
          <ErrorBoundary>
            <PolicyManagement />
          </ErrorBoundary>
        );
      case 'compliance':
        return (
          <ErrorBoundary>
            <Compliance />
          </ErrorBoundary>
        );
      case 'data':
        return (
          <ErrorBoundary>
            <DataManager />
          </ErrorBoundary>
        );
      case 'analytics':
        return (
          <ErrorBoundary>
            <Analytics />
          </ErrorBoundary>
        );
      case 'security':
        return (
          <ErrorBoundary>
            <SecurityReports />
          </ErrorBoundary>
        );
      case 'users':
        return (
          <ErrorBoundary>
            <EnterpriseUserManagement />
          </ErrorBoundary>
        );
      case 'insights':
        return (
          <ErrorBoundary>
            <SecurityInsights />
          </ErrorBoundary>
        );
      case 'rules':
        return (
          <ErrorBoundary>
            <SmartRuleGen />
          </ErrorBoundary>
        );
      default:
        return (
          <ErrorBoundary>
            <Dashboard />
          </ErrorBoundary>
        );
    }
  };

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-100">
        {/* Original Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-gray-900">OW-AI Dashboard</h1>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-700">
                  {user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="flex">
          {/* Original Sidebar with ALL tabs */}
          <nav className="w-64 bg-white shadow-lg h-screen overflow-y-auto">
            <div className="p-4">
              <ul className="space-y-2">
                {navigation.map((item) => (
                  <li key={item.id}>
                    <button
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center space-x-3 px-4 py-2 rounded-md text-left transition-colors ${
                        activeTab === item.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <span>{item.icon}</span>
                      <span>{item.name}</span>
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
    </ThemeProvider>
  );
}

export default App;
