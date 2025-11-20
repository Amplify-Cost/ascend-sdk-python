import React from 'react';
import logger from '../utils/logger';

/**
 * ErrorBoundary - Enterprise-grade error handling component
 * 
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 * 
 * Compliance: SOC2, ISO27001 (proper error handling)
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  /**
   * Update state when an error is caught
   */
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  /**
   * Log error details when caught
   */
  componentDidCatch(error, errorInfo) {
    // Log to our enterprise logger
    logger.error('ErrorBoundary caught an error', {
      error: error.toString(),
      componentStack: errorInfo.componentStack,
      errorMessage: error.message,
      errorStack: error.stack
    });

    // Update state with error details
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // In production, you might want to send this to an error tracking service
    // like Sentry, LogRocket, or Datadog
  }

  /**
   * Reset error boundary state
   */
  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center mb-4">
              <svg
                className="h-8 w-8 text-red-500 mr-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <h2 className="text-xl font-semibold text-gray-900">
                Something went wrong
              </h2>
            </div>
            
            <p className="text-gray-600 mb-4">
              {this.props.fallbackMessage || 
                'We encountered an unexpected error. Please try again or contact support if the problem persists.'}
            </p>

            {/* Show error details in development mode */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-4 p-3 bg-gray-100 rounded text-sm">
                <summary className="cursor-pointer font-semibold text-gray-700 mb-2">
                  Error Details (Development Only)
                </summary>
                <div className="mt-2 space-y-2">
                  <div>
                    <strong className="text-red-600">Error:</strong>
                    <pre className="mt-1 whitespace-pre-wrap text-xs text-gray-800">
                      {this.state.error.toString()}
                    </pre>
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <strong className="text-red-600">Component Stack:</strong>
                      <pre className="mt-1 whitespace-pre-wrap text-xs text-gray-800 max-h-40 overflow-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            <div className="flex gap-3">
              <button
                onClick={this.resetError}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded transition-colors"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    // No error, render children normally
    return this.props.children;
  }
}

export default ErrorBoundary;
