import React, { useState } from 'react';

/*
 * OW-AI Enterprise Login Portal
 * Professional enterprise-grade design with authentication fix
 * Cookie-only authentication (Master Prompt compliant)
 */

const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!onLogin || typeof onLogin !== 'function') {
      setError('Authentication system not available');
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      console.log('🔐 Enterprise authentication attempt...');
      console.log('📝 Sending credentials:', { username: credentials.username, password: '***' });
      
      const result = await onLogin(credentials);
      
      if (!result || !result.success) {
        setError(result?.error || 'Authentication failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Network error - please try again');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 75%, #64748b 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      padding: '1rem'
    }}>
      {/* Professional Background Pattern */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        opacity: 0.5
      }} />
      
      <div style={{
        position: 'relative',
        width: '100%',
        maxWidth: '440px',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '16px',
        padding: '3rem 2.5rem',
        boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15), 0 20px 40px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(255, 255, 255, 0.2)'
      }}>
        {/* Enterprise Header */}
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <div style={{
            width: '80px',
            height: '80px',
            background: 'linear-gradient(135deg, #0f172a 0%, #334155 50%, #64748b 100%)',
            borderRadius: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.5rem',
            fontSize: '2rem',
            color: 'white',
            boxShadow: '0 8px 16px rgba(15, 23, 42, 0.3)'
          }}>
            🏢
          </div>
          <h1 style={{ 
            margin: '0 0 0.5rem 0', 
            color: '#0f172a',
            fontSize: '1.75rem',
            fontWeight: '700',
            letterSpacing: '-0.025em'
          }}>
            OW-AI Enterprise
          </h1>
          <p style={{ 
            margin: 0, 
            color: '#64748b', 
            fontSize: '0.95rem',
            fontWeight: '500'
          }}>
            Secure Enterprise Authentication Portal
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ marginBottom: '1.5rem' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              marginBottom: '0.75rem',
              fontWeight: '600',
              color: '#374151',
              fontSize: '0.9rem',
              letterSpacing: '0.025em'
            }}>
              Enterprise Email
            </label>
            <input
              type="text"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              placeholder="admin@example.com"
              required
              style={{
                width: '100%',
                padding: '0.875rem 1rem',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '1rem',
                boxSizing: 'border-box',
                transition: 'all 0.2s ease',
                background: 'rgba(249, 250, 251, 0.8)',
                outline: 'none'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#64748b';
                e.target.style.boxShadow = '0 0 0 3px rgba(100, 116, 139, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label style={{
              display: 'block',
              marginBottom: '0.75rem',
              fontWeight: '600',
              color: '#374151',
              fontSize: '0.9rem',
              letterSpacing: '0.025em'
            }}>
              Secure Password
            </label>
            <input
              type="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              style={{
                width: '100%',
                padding: '0.875rem 1rem',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '1rem',
                boxSizing: 'border-box',
                transition: 'all 0.2s ease',
                background: 'rgba(249, 250, 251, 0.8)',
                outline: 'none'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#64748b';
                e.target.style.boxShadow = '0 0 0 3px rgba(100, 116, 139, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          {error && (
            <div style={{
              padding: '0.875rem 1rem',
              marginBottom: '1.5rem',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '8px',
              color: '#dc2626',
              fontSize: '0.9rem',
              fontWeight: '500'
            }}>
              <span style={{ marginRight: '0.5rem' }}>⚠️</span>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.875rem 1rem',
              background: loading 
                ? 'linear-gradient(135deg, #9ca3af 0%, #6b7280 100%)' 
                : 'linear-gradient(135deg, #0f172a 0%, #334155 50%, #64748b 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: loading 
                ? 'none' 
                : '0 4px 12px rgba(15, 23, 42, 0.3)',
              letterSpacing: '0.025em'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = '0 6px 16px rgba(15, 23, 42, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 12px rgba(15, 23, 42, 0.3)';
              }
            }}
          >
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>🔄</span>
                Authenticating...
              </span>
            ) : (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                🔐 Enterprise Login
              </span>
            )}
          </button>
        </form>

        {/* Enterprise Security Features */}
        <div style={{
          padding: '1.25rem',
          background: 'rgba(34, 197, 94, 0.05)',
          border: '1px solid rgba(34, 197, 94, 0.1)',
          borderRadius: '8px',
          fontSize: '0.85rem'
        }}>
          <div style={{ 
            fontWeight: '600', 
            color: '#059669', 
            marginBottom: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            🛡️ Enterprise Security Features
          </div>
          <div style={{ color: '#047857', lineHeight: '1.5' }}>
            <div style={{ marginBottom: '0.25rem' }}>✓ Advanced cookie-based authentication</div>
            <div style={{ marginBottom: '0.25rem' }}>✓ Enterprise-grade encryption</div>
            <div style={{ marginBottom: '0.25rem' }}>✓ SOC 2 Type II certified infrastructure</div>
            <div>✓ Multi-layer security protocols</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
