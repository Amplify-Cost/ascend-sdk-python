/**
 * SEC-021: Email Verification Component
 *
 * Handles email verification for self-service signup flow.
 * Reads token from URL query parameter and verifies with backend.
 *
 * Security:
 * - Token is single-use
 * - Token expires in 24 hours
 * - Verification logged for audit trail
 */

import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { API_BASE_URL } from '../config/api';
import logger from '../utils/logger.js';

const VerifyEmail = ({ onVerified, switchToLogin }) => {
  const { isDarkMode } = useTheme();
  const [status, setStatus] = useState('verifying'); // verifying, success, error, expired
  const [message, setMessage] = useState('Verifying your email...');
  const [organizationName, setOrganizationName] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      try {
        // Get token from URL query parameters
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
          setStatus('error');
          setMessage('Invalid verification link. No token provided.');
          return;
        }

        logger.debug('SEC-021: Verifying email with token');

        const response = await fetch(`${API_BASE_URL}/api/signup/verify-email`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ token })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          setStatus('success');
          setOrganizationName(data.organization_name || 'your organization');
          setMessage('Your email has been verified successfully!');
          logger.debug('SEC-021: Email verified successfully');
        } else if (response.status === 400 && data.detail?.includes('expired')) {
          setStatus('expired');
          setMessage('This verification link has expired. Please request a new one.');
        } else if (response.status === 400 && data.detail?.includes('already verified')) {
          setStatus('success');
          setMessage('This email has already been verified. You can proceed to login.');
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed. Please try again or contact support.');
        }
      } catch (error) {
        logger.error('SEC-021: Email verification error:', error);
        setStatus('error');
        setMessage('An error occurred during verification. Please try again.');
      }
    };

    verifyEmail();
  }, []);

  const handleContinue = () => {
    if (onVerified) {
      onVerified();
    } else if (switchToLogin) {
      switchToLogin();
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-900' : 'bg-gray-50'
    }`}>
      <div className={`max-w-md w-full mx-4 p-8 rounded-xl shadow-xl transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-white'
      }`}>
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className={`text-2xl font-bold mb-2 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            ASCEND
          </h1>
          <p className={`text-sm ${
            isDarkMode ? 'text-slate-400' : 'text-gray-500'
          }`}>
            Email Verification
          </p>
        </div>

        {/* Status Icon */}
        <div className="flex justify-center mb-6">
          {status === 'verifying' && (
            <div className="w-16 h-16 border-4 border-t-transparent border-blue-500 rounded-full animate-spin" />
          )}
          {status === 'success' && (
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          )}
          {status === 'error' && (
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          )}
          {status === 'expired' && (
            <div className="w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          )}
        </div>

        {/* Message */}
        <div className="text-center mb-8">
          <p className={`text-lg ${
            isDarkMode ? 'text-slate-300' : 'text-gray-700'
          }`}>
            {message}
          </p>

          {status === 'success' && organizationName && (
            <p className={`mt-4 text-sm ${
              isDarkMode ? 'text-slate-400' : 'text-gray-500'
            }`}>
              Welcome to {organizationName}! You can now proceed to set up your account.
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="space-y-4">
          {status === 'success' && (
            <button
              onClick={handleContinue}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Continue to Login
            </button>
          )}

          {status === 'error' && (
            <>
              <button
                onClick={switchToLogin}
                className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Back to Login
              </button>
              <p className={`text-sm text-center ${
                isDarkMode ? 'text-slate-400' : 'text-gray-500'
              }`}>
                Need help? Contact{' '}
                <a href="mailto:support@ascendowkai.com" className="text-blue-500 hover:text-blue-600">
                  support@ascendowkai.com
                </a>
              </p>
            </>
          )}

          {status === 'expired' && (
            <>
              <button
                onClick={switchToLogin}
                className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Request New Verification Email
              </button>
              <p className={`text-sm text-center ${
                isDarkMode ? 'text-slate-400' : 'text-gray-500'
              }`}>
                Verification links expire after 24 hours for security.
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        <div className={`mt-8 pt-6 border-t text-center text-xs ${
          isDarkMode ? 'border-slate-700 text-slate-500' : 'border-gray-200 text-gray-400'
        }`}>
          <p>ASCEND AI Governance Platform</p>
          <p className="mt-1">Ascend Technologies, Inc.</p>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
