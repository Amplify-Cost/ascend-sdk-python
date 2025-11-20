import React, { useState } from 'react';

/**
 * Test component to verify ErrorBoundary functionality
 * This should be removed after testing
 */
function ErrorBoundaryTest() {
  const [shouldThrow, setShouldThrow] = useState(false);

  if (shouldThrow) {
    // Deliberately throw an error to test the boundary
    throw new Error('Test error from ErrorBoundaryTest component');
  }

  return (
    <div className="p-6 max-w-md mx-auto">
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <strong>Error Boundary Test Mode</strong>
            </p>
            <p className="mt-2 text-sm text-yellow-700">
              Click the button below to trigger a test error. The ErrorBoundary should catch it and display a fallback UI.
            </p>
          </div>
        </div>
      </div>

      <button
        onClick={() => setShouldThrow(true)}
        className="mt-4 w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded transition-colors"
      >
        🧪 Trigger Test Error
      </button>

      <p className="mt-4 text-xs text-gray-500 text-center">
        This test component will be removed after verification
      </p>
    </div>
  );
}

export default ErrorBoundaryTest;
