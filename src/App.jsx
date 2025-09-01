import React from 'react';

function App() {
  console.log('React App component loaded');
  return (
    <div style={{
      padding: '40px',
      backgroundColor: '#f8fafc',
      minHeight: '100vh',
      color: '#1f2937',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        backgroundColor: 'white',
        padding: '32px',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h1 style={{marginBottom: '16px', fontSize: '24px', fontWeight: 'bold'}}>
          OW-AI Enterprise Dashboard
        </h1>
        <p style={{marginBottom: '16px', color: '#6b7280'}}>
          React application successfully loaded and rendering.
        </p>
        <div style={{
          padding: '16px',
          backgroundColor: '#10b981',
          color: 'white',
          borderRadius: '4px',
          marginBottom: '16px'
        }}>
          ✅ Frontend deployment successful
        </div>
        <div style={{
          padding: '16px',
          backgroundColor: '#3b82f6',
          color: 'white',
          borderRadius: '4px'
        }}>
          🚀 Ready for enterprise authentication integration
        </div>
      </div>
    </div>
  );
}

export default App;
