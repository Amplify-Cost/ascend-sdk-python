/**
 * New Password Required Component - Enterprise Grade
 * SEC-030: Handles NEW_REDACTED-CREDENTIAL_REQUIRED Cognito challenge
 *
 * This component is displayed when a user logs in with a temporary password
 * and must set a new permanent password.
 *
 * Security Features:
 * - Password strength validation (12+ chars, uppercase, lowercase, number, symbol)
 * - Password confirmation matching
 * - Session-based challenge response (not stored in localStorage)
 * - Audit logging of password change
 *
 * Compliance: NIST 800-63B, PCI-DSS 8.2.3, SOC 2 CC6.1
 * Engineer: OW-AI Enterprise
 * Date: 2025-11-30
 */

import React, { useState } from 'react';
import {
  CognitoIdentityProviderClient,
  RespondToAuthChallengeCommand
} from '@aws-sdk/client-cognito-identity-provider';
import { validatePassword } from '../services/cognitoAuth';

// SEC-027: Import CSRF token storage for immediate use after password change
import { storeCsrfToken } from '../utils/fetchWithAuth';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const NewPasswordRequired = ({
  session,
  poolConfig,
  username,
  challengeParameters,
  onPasswordChanged,
  onCancel
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [passwordStrength, setPasswordStrength] = useState(null);

  /**
   * Handle password input change with strength validation
   */
  const handlePasswordChange = (value) => {
    setNewPassword(value);
    if (value.length > 0) {
      const validation = validatePassword(value);
      setPasswordStrength(validation);
    } else {
      setPasswordStrength(null);
    }
  };

  /**
   * Submit new password to Cognito
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate password strength
    const validation = validatePassword(newPassword);
    if (!validation.valid) {
      setError(validation.errors.join('. '));
      return;
    }

    // Validate password confirmation
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      setLoading(true);
      console.log('SEC-030: Responding to NEW_REDACTED-CREDENTIAL_REQUIRED challenge');

      const client = new CognitoIdentityProviderClient({
        region: poolConfig.region
        // NO credentials - Cognito User Pools don't require them for auth operations
      });

      // Build challenge responses
      const challengeResponses = {
        USERNAME: username,
        NEW_REDACTED-CREDENTIAL: newPassword
      };

      // Include any required attributes from challenge parameters
      const requiredAttributes = challengeParameters?.requiredAttributes || [];
      if (typeof requiredAttributes === 'string') {
        try {
          const attrs = JSON.parse(requiredAttributes);
          attrs.forEach(attr => {
            // For now, we only handle email (which should already be set)
            if (attr === 'email') {
              challengeResponses['userAttributes.email'] = username;
            }
          });
        } catch (e) {
          console.warn('SEC-030: Could not parse requiredAttributes:', e);
        }
      }

      const command = new RespondToAuthChallengeCommand({
        ChallengeName: 'NEW_REDACTED-CREDENTIAL_REQUIRED',
        ClientId: poolConfig.app_client_id,
        Session: session,
        ChallengeResponses: challengeResponses
      });

      const response = await client.send(command);
      console.log('SEC-030: Password change response:', response);

      // Check for additional challenges (e.g., MFA setup after password change)
      if (response.ChallengeName) {
        // Return the new challenge to be handled by parent component
        console.log('SEC-030: Additional challenge required:', response.ChallengeName);
        onPasswordChanged({
          success: false,
          challengeName: response.ChallengeName,
          session: response.Session,
          challengeParameters: response.ChallengeParameters,
          poolConfig
        });
        return;
      }

      // Password change successful - get tokens
      const tokens = response.AuthenticationResult;

      if (!tokens) {
        throw new Error('Password changed but no tokens received');
      }

      // Exchange Cognito tokens for server session (banking-level security)
      console.log('SEC-030: Exchanging Cognito tokens for server session...');
      const sessionResponse = await fetch(`${API_BASE_URL}/api/auth/cognito-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          accessToken: tokens.AccessToken,
          idToken: tokens.IdToken,
          refreshToken: tokens.RefreshToken
        })
      });

      if (!sessionResponse.ok) {
        const errorData = await sessionResponse.json();
        throw new Error(errorData.detail || 'Session creation failed');
      }

      const sessionData = await sessionResponse.json();
      console.log('SEC-030: Server session created successfully');

      // Store CSRF token for immediate use
      if (sessionData.csrf_token) {
        storeCsrfToken(sessionData.csrf_token);
        console.log('SEC-030: CSRF token stored');
      }

      // Complete the password change flow
      onPasswordChanged({
        success: true,
        user: sessionData.user,
        tokens,
        poolConfig
      });

    } catch (err) {
      console.error('SEC-030: Password change error:', err);

      if (err.name === 'InvalidPasswordException') {
        setError('Password does not meet requirements. Please use at least 12 characters with uppercase, lowercase, numbers, and symbols.');
      } else if (err.name === 'NotAuthorizedException') {
        setError('Session expired. Please log in again.');
        setTimeout(() => onCancel(), 3000);
      } else {
        setError(`Password change failed: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get password strength color
   */
  const getStrengthColor = () => {
    if (!passwordStrength) return 'bg-gray-200';
    if (passwordStrength.strength < 40) return 'bg-red-500';
    if (passwordStrength.strength < 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-2xl p-8">
        <h2 className="text-2xl font-bold mb-2 text-center text-gray-900">Set Your Password</h2>
        <p className="text-gray-600 text-center mb-6">
          Your account requires a new password. Please create a secure password to continue.
        </p>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* New Password */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => handlePasswordChange(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-12"
                placeholder="Enter new password"
                disabled={loading}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                disabled={loading}
              >
                {showPassword ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>

            {/* Password Strength Indicator */}
            {passwordStrength && (
              <div className="mt-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getStrengthColor()} transition-all duration-300`}
                      style={{ width: `${passwordStrength.strength}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500">
                    {passwordStrength.strength < 40 ? 'Weak' : passwordStrength.strength < 70 ? 'Medium' : 'Strong'}
                  </span>
                </div>
                {passwordStrength.errors.length > 0 && (
                  <ul className="mt-2 text-xs text-red-600 space-y-1">
                    {passwordStrength.errors.map((err, i) => (
                      <li key={i} className="flex items-center gap-1">
                        <span>•</span> {err}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                confirmPassword && newPassword !== confirmPassword
                  ? 'border-red-300'
                  : 'border-gray-300'
              }`}
              placeholder="Confirm new password"
              disabled={loading}
              required
            />
            {confirmPassword && newPassword !== confirmPassword && (
              <p className="mt-1 text-xs text-red-600">Passwords do not match</p>
            )}
          </div>

          {/* Password Requirements */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-sm font-semibold text-blue-800 mb-2">Password Requirements:</h3>
            <ul className="text-xs text-blue-700 space-y-1">
              <li className="flex items-center gap-2">
                <span className={newPassword.length >= 12 ? 'text-green-600' : ''}>
                  {newPassword.length >= 12 ? '✓' : '○'}
                </span>
                At least 12 characters
              </li>
              <li className="flex items-center gap-2">
                <span className={/[A-Z]/.test(newPassword) ? 'text-green-600' : ''}>
                  {/[A-Z]/.test(newPassword) ? '✓' : '○'}
                </span>
                One uppercase letter
              </li>
              <li className="flex items-center gap-2">
                <span className={/[a-z]/.test(newPassword) ? 'text-green-600' : ''}>
                  {/[a-z]/.test(newPassword) ? '✓' : '○'}
                </span>
                One lowercase letter
              </li>
              <li className="flex items-center gap-2">
                <span className={/[0-9]/.test(newPassword) ? 'text-green-600' : ''}>
                  {/[0-9]/.test(newPassword) ? '✓' : '○'}
                </span>
                One number
              </li>
              <li className="flex items-center gap-2">
                <span className={/[^A-Za-z0-9]/.test(newPassword) ? 'text-green-600' : ''}>
                  {/[^A-Za-z0-9]/.test(newPassword) ? '✓' : '○'}
                </span>
                One special character (!@#$%^&*)
              </li>
            </ul>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !newPassword || !confirmPassword || newPassword !== confirmPassword}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Setting Password...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Set Password & Continue
              </>
            )}
          </button>

          {/* Cancel Button */}
          <button
            type="button"
            onClick={onCancel}
            className="w-full mt-3 text-gray-600 hover:text-gray-800 py-2 text-sm"
            disabled={loading}
          >
            Cancel
          </button>
        </form>

        {/* Security Notice */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-start gap-2 text-xs text-gray-600">
            <svg className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
            <p>
              Your password is encrypted using industry-standard algorithms.
              Choose a strong, unique password that you don't use elsewhere.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewPasswordRequired;
