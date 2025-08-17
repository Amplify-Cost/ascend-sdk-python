import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { getCurrentUser } from './utils/fetchWithAuth';
import './index.css';

/**
 * Enterprise OW-AI Application - No Authentication Loops
 * Master Prompt Compliant: Cookie-only authentication, no localStorage
 */
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);

  // Enterprise cookie-only authentication check (NO LOOPS)
  useEffect(() => {
    let mounted = true;
    
    const checkAuth = async () => {
      // Prevent infinite loops
      if (authChecked) {
        console.log('🚨 AUTH CHECK ALREADY COMPLETED - Preventing loop');
        return;
      }
      
      console.log('🏢 Enterprise cookie auth check (one-time)...');
      
      try {
        const userData = await getCurrentUser();
        if (mounted) {
          if (userData) {
            console.log('✅ Enterprise authentication valid:', userData.email || userData.user_id);
            setUser(userData);
          } else {
            console.log('ℹ️ No valid enterprise authentication - showing login');
            setUser(null);
          }
          setLoading(false);
          setAuthChecked(true);
        }
      } catch (error) {
        console.error('❌ Enterprise auth check error:', error);
        if (mounted) {
          setUser(null);
          setLoading(false);
          setAuthChecked(true);
        }
      }
    };

    // Only check auth once
    if (!authChecked) {
      checkAuth();
    }
    
    return () => {
      mounted = false;
    };
  }, [authChecked]); // Depend on authChecked to prevent loops

  // Handle successful login
  const handleLoginSuccess = (userData) => {
    console.log('✅ Enterprise login successful:', userData);
    setUser(userData);
    setAuthChecked(true);
  };

  // Handle logout
  const handleLogout = () => {
    console.log('🔐 Enterprise logout initiated');
    setUser(null);
    setAuthChecked(false);
    // Cookie clearing handled by backend
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">🏢 Loading Enterprise Platform...</div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/" 
            element={
              user ? 
                <Navigate to="/dashboard" replace /> : 
                <Login onLoginSuccess={handleLoginSuccess} />
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              user ? 
                <Dashboard user={user} onLogout={handleLogout} /> : 
                <Navigate to="/" replace />
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
