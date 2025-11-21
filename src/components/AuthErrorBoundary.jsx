/**
 * Authentication Error Boundary Component
 * Graceful error handling for auth-related failures
 * Engineer: OW-KAI Engineer
 */
import React, { Component } from 'react';

class AuthErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(err, errorInfo) {
    console.error('Auth Error:', err, errorInfo);
    this.setState({ error: err, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md p-6 bg-white rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h2>
            <p className="mb-4">An error occurred during authentication. Please try again.</p>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default AuthErrorBoundary;
