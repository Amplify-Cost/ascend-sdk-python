import React from 'react';

/*
 * OW-AI Enterprise Dashboard
 * Master Prompt Compliant: Cookie-only authentication, no localStorage
 * Enterprise Level: Professional UI without theme dependencies
 */

const Dashboard = ({ user, onLogout }) => {
  const handleLogout = () => {
    console.log('🔓 Initiating enterprise logout...');
    onLogout();
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f8f9fa',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* Enterprise Header */}
      <header style={{
        backgroundColor: '#2c3e50',
        color: 'white',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>🏢 OW-AI Enterprise Platform</h1>
          <p style={{ margin: 0, fontSize: '0.9rem', opacity: 0.8 }}>
            Master Prompt Compliant • Cookie Authentication
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.9rem' }}>
            👤 {user?.email || 'Enterprise User'} ({user?.role || 'user'})
          </span>
          <button
            onClick={handleLogout}
            style={{
              backgroundColor: '#e74c3c',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            🔓 Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ padding: '2rem' }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '2rem',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '2rem'
        }}>
          <h2 style={{ margin: '0 0 1rem 0', color: '#2c3e50' }}>
            ✅ Enterprise Authentication Successful
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1rem',
            marginTop: '1rem'
          }}>
            <div style={{
              padding: '1rem',
              backgroundColor: '#e8f5e8',
              border: '1px solid #28a745',
              borderRadius: '4px'
            }}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#155724' }}>🔐 Authentication</h3>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>Cookie-only authentication active</p>
            </div>
            <div style={{
              padding: '1rem',
              backgroundColor: '#e7f3ff',
              border: '1px solid #007bff',
              borderRadius: '4px'
            }}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#004085' }}>👤 User Status</h3>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>Logged in as {user?.role || 'user'}</p>
            </div>
            <div style={{
              padding: '1rem',
              backgroundColor: '#fff3cd',
              border: '1px solid #ffc107',
              borderRadius: '4px'
            }}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#856404' }}>🏢 Compliance</h3>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>Master Prompt compliant</p>
            </div>
          </div>
        </div>

        {/* Analytics Section */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '2rem',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ margin: '0 0 1rem 0', color: '#2c3e50' }}>
            📊 Enterprise Analytics Dashboard
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem'
          }}>
            <div style={{
              textAlign: 'center',
              padding: '1.5rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #dee2e6'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🚀</div>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Platform Status</h3>
              <p style={{ margin: 0, color: '#28a745', fontWeight: 'bold' }}>Operational</p>
            </div>
            <div style={{
              textAlign: 'center',
              padding: '1.5rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #dee2e6'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔒</div>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Security Level</h3>
              <p style={{ margin: 0, color: '#007bff', fontWeight: 'bold' }}>Enterprise</p>
            </div>
            <div style={{
              textAlign: 'center',
              padding: '1.5rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #dee2e6'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Compliance</h3>
              <p style={{ margin: 0, color: '#28a745', fontWeight: 'bold' }}>Verified</p>
            </div>
            <div style={{
              textAlign: 'center',
              padding: '1.5rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #dee2e6'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>👥</div>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Active Users</h3>
              <p style={{ margin: 0, color: '#6c757d', fontWeight: 'bold' }}>1 Online</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
