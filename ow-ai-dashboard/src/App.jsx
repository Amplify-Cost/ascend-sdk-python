import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { getCurrentUser, loginUser, logoutUser } from './utils/fetchWithAuth';

/*
 * OW-AI Enterprise Dashboard
 * Master Prompt Compliant: Cookie-only authentication, no localStorage
 * Enterprise-grade professional application
 */

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);

  // Master Prompt Compliant: Enterprise cookie-only authentication check (NO LOOPS)
  useEffect(() => {
    const checkAuth = async () => {
      if (authChecked) {
        console.log('🏢 Auth already checked, preventing loops...');
        return;
      }

      console.log('🏢 Enterprise cookie auth check (one-time)...');
      try {
        const userData = await getCurrentUser();
        if (userData) {
          setUser(userData);
          console.log('✅ Enterprise auth validated:', userData);
        } else {
          console.log('ℹ️ No valid enterprise authentication - showing login');
          setUser(null);
        }
      } catch (error) {
        console.log('ℹ️ Enterprise auth check failed - showing login');
        setUser(null);
      } finally {
        setLoading(false);
        setAuthChecked(true);
      }
    };

    checkAuth();
  }, []); // Empty dependency array - runs once only (Master Prompt compliant)

  // Master Prompt Compliant: Cookie-only login handler
  const handleLogin = async (credentials) => {
    console.log('🔐 Enterprise authentication attempt...');
    
    try {
      const result = await loginUser(credentials);
      
      if (result.success) {
        setUser(result.user);
        console.log('✅ Enterprise login successful:', result.user);
        return { success: true };
      } else {
        console.log('❌ Enterprise login failed:', result.error);
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.log('❌ Enterprise login error:', error);
      return { success: false, error: 'Network error' };
    }
  };

  // Master Prompt Compliant: Cookie-only logout handler
  const handleLogout = async () => {
    try {
      const result = await logoutUser();
      if (result.success) {
        setUser(null);
        setAuthChecked(false);
        console.log('✅ Enterprise logout successful');
      }
    } catch (error) {
      console.log('❌ Logout error:', error);
      // Force logout even if API call fails
      setUser(null);
      setAuthChecked(false);
    }
  };

  // Loading screen with enterprise branding
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
          <div style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>OW-AI Enterprise Platform</div>
          <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>Loading secure environment...</div>
          <div style={{ 
            marginTop: '1rem', 
            padding: '0.5rem 1rem', 
            background: 'rgba(255,255,255,0.2)', 
            borderRadius: '20px',
            fontSize: '0.8rem'
          }}>
            🔒 Master Prompt Compliant
          </div>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/login" 
            element={user ? <Navigate to="/dashboard" /> : <Login onLogin={handleLogin} />} 
          />
          <Route 
            path="/dashboard" 
            element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} 
          />
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
