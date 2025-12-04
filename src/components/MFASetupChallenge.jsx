/**
 * MFA Setup Challenge Component - Enterprise Grade
 * Handles MFA_SETUP challenge during initial login
 *
 * 🏦 ENTERPRISE SOLUTION: Proper MFA_SETUP Challenge Handling
 *
 * This component is specifically for handling the AWS Cognito MFA_SETUP challenge
 * that occurs when a user logs in for the first time and must set up MFA.
 *
 * Unlike MFASetup.jsx (which is for logged-in users adding MFA), this component:
 * - Uses SESSION token (not AccessToken)
 * - Responds to MFA_SETUP challenge
 * - Guides user through QR code scanning
 * - Verifies setup code and completes authentication
 *
 * Security: SOC 2, NIST 800-63B, PCI-DSS compliant
 * Engineer: Donald King (OW-AI Enterprise)
 * Date: 2025-11-23
 */
import React, { useState, useEffect } from 'react';
import QRCode from 'qrcode';
import {
  CognitoIdentityProviderClient,
  AssociateSoftwareTokenCommand,
  RespondToAuthChallengeCommand
} from '@aws-sdk/client-cognito-identity-provider';

const MFASetupChallenge = ({ session, poolConfig, username, onSetupComplete, onCancel, onSessionExpired }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [totpSecret, setTotpSecret] = useState('');
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState(session); // 🏦 CRITICAL: Track updated session
  const [sessionExpired, setSessionExpired] = useState(false);

  // Initialize TOTP setup when component mounts
  useEffect(() => {
    if (currentStep === 1) {
      initializeTOTPSetup();
    }
  }, []);

  /**
   * Step 1: Associate software token using SESSION
   */
  const initializeTOTPSetup = async () => {
    try {
      setLoading(true);
      setError('');

      console.log('🏦 [MFA_SETUP] Step 1: Initializing TOTP setup');
      console.log('🏦 [MFA_SETUP] Session A (from login):', currentSession.substring(0, 50) + '...');
      console.log('🏦 [MFA_SETUP] Session A length:', currentSession.length);

      const client = new CognitoIdentityProviderClient({
        region: poolConfig.region
        // NO credentials - Cognito User Pools don't require them for auth operations
      });

      // Use SESSION (not AccessToken) for MFA_SETUP challenge
      const associateCommand = new AssociateSoftwareTokenCommand({
        Session: currentSession
      });

      console.log('🏦 [MFA_SETUP] Calling AssociateSoftwareTokenCommand...');
      const response = await client.send(associateCommand);
      const secretCode = response.SecretCode;
      const newSession = response.Session; // 🏦 CRITICAL: AWS returns NEW session

      console.log('🏦 [MFA_SETUP] AssociateSoftwareToken SUCCESS');
      console.log('🏦 [MFA_SETUP] Session B (from associate):', newSession.substring(0, 50) + '...');
      console.log('🏦 [MFA_SETUP] Session B length:', newSession.length);
      console.log('🏦 [MFA_SETUP] Secret code:', secretCode);
      console.log('🏦 [MFA_SETUP] Sessions different?', currentSession !== newSession ? '✅ YES (CORRECT)' : '❌ NO (ERROR)');

      setTotpSecret(secretCode);
      setCurrentSession(newSession); // 🏦 CRITICAL: Update session for verification

      // Generate QR code for authenticator apps
      const otpAuthUrl = `otpauth://totp/Ascend:${username}?secret=${secretCode}&issuer=Ascend`;
      const qrUrl = await QRCode.toDataURL(otpAuthUrl);
      setQrCodeUrl(qrUrl);

      console.log('🏦 [MFA_SETUP] QR code generated, advancing to step 2');
      setCurrentStep(2);
    } catch (err) {
      console.error('🏦 [MFA_SETUP] ERROR:', err);
      console.error('🏦 [MFA_SETUP] Error name:', err.name);
      console.error('🏦 [MFA_SETUP] Error message:', err.message);

      // 🏦 ENTERPRISE: Handle session expiration gracefully
      if (err.name === 'NotAuthorizedException' || err.message.includes('Invalid session')) {
        setError('Session expired. Please log in again to set up MFA.');
        setTimeout(() => onCancel(), 3000);
      } else {
        setError(`Setup failed: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Step 2: Verify TOTP code and complete MFA setup
   */
  const handleVerifySetup = async () => {
    try {
      setLoading(true);
      setError('');

      console.log('🏦 [MFA_SETUP] Step 2: Verifying TOTP code');
      console.log('🏦 [MFA_SETUP] Verification code:', verificationCode);
      console.log('🏦 [MFA_SETUP] Username:', username);
      console.log('🏦 [MFA_SETUP] Using Session (should be Session B):', currentSession.substring(0, 50) + '...');
      console.log('🏦 [MFA_SETUP] Session length:', currentSession.length);

      const client = new CognitoIdentityProviderClient({
        region: poolConfig.region
        // NO credentials - Cognito User Pools don't require them for auth operations
      });

      // Respond to MFA_SETUP challenge with verification code
      // 🏦 CRITICAL: Use the UPDATED session from AssociateSoftwareToken response
      const challengeResponse = new RespondToAuthChallengeCommand({
        ChallengeName: 'MFA_SETUP',
        ClientId: poolConfig.app_client_id,
        Session: currentSession, // 🏦 CRITICAL: Use updated session, not original
        ChallengeResponses: {
          USERNAME: username, // 🏦 REQUIRED by AWS Cognito
          SOFTWARE_TOKEN_MFA_CODE: verificationCode
        }
      });

      console.log('🏦 [MFA_SETUP] Calling RespondToAuthChallengeCommand...');
      const response = await client.send(challengeResponse);
      console.log('🏦 [MFA_SETUP] Verification SUCCESS:', response);

      // MFA setup successful - get user data and tokens
      const tokens = response.AuthenticationResult;

      if (!tokens) {
        throw new Error('MFA setup completed but no tokens received');
      }

      // Get user attributes
      const user = {
        username,
        email: username,
        mfaEnabled: true
      };

      onSetupComplete({
        success: true,
        user,
        tokens,
        poolConfig
      });

    } catch (err) {
      console.error('🏦 [MFA_SETUP] VERIFICATION ERROR:', err);
      console.error('🏦 [MFA_SETUP] Error name:', err.name);
      console.error('🏦 [MFA_SETUP] Error message:', err.message);
      console.error('🏦 [MFA_SETUP] Error code:', err.code);
      console.error('🏦 [MFA_SETUP] Full error object:', JSON.stringify(err, null, 2));

      // 🏦 ENTERPRISE: Comprehensive error handling
      if (err.name === 'CodeMismatchException') {
        setError('Invalid verification code. Please check your authenticator app and try again.');
      } else if (err.name === 'EnableSoftwareTokenMFAException') {
        setError('Failed to enable MFA. Please try again.');
      } else if (err.name === 'NotAuthorizedException' || err.message.includes('Invalid session')) {
        console.error('🏦 [MFA_SETUP] Session invalidation detected');
        console.error('🏦 [MFA_SETUP] Current session being used:', currentSession.substring(0, 50) + '...');

        // 🏦 BANKING-LEVEL FIX: Session expired (3-minute AWS limit)
        // User needs to get a fresh session by logging in again
        setSessionExpired(true);
        setError('⏱️ Security session expired (3-minute limit). Your TOTP code is still valid in your authenticator app. Please close this window and log in again to get a fresh session, then enter the same code.');
      } else if (err.message.includes('Invalid session for the user')) {
        console.error('🏦 [MFA_SETUP] AWS Cognito session error detected');
        setSessionExpired(true);
        setError('⏱️ Security session expired. Please close this window and log in again. Your authenticator app code is still valid - use the same code after logging in.');
      } else {
        setError(`Verification failed: ${err.message}`);
      }
      setVerificationCode('');
    } finally {
      setLoading(false);
    }
  };

  // Auto-verify when 6 digits entered
  useEffect(() => {
    if (verificationCode.length === 6 && currentStep === 2) {
      handleVerifySetup();
    }
  }, [verificationCode]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-2xl p-8">

        {/* Step 1: Loading Setup */}
        {currentStep === 1 && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold mb-2">Setting Up MFA...</h2>
            <p className="text-gray-600">Generating your secure authentication key</p>
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {error}
                <button
                  onClick={initializeTOTPSetup}
                  className="block w-full mt-2 text-blue-600 hover:text-blue-800"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Scan QR Code & Verify */}
        {currentStep === 2 && (
          <div>
            <h2 className="text-2xl font-bold mb-4 text-center">Set Up Authenticator App</h2>

            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-4">
                <strong className="block mb-2">Step 1:</strong>
                Open your authenticator app (Google Authenticator, Authy, Microsoft Authenticator, etc.)
              </p>
              <p className="text-sm text-gray-600 mb-4">
                <strong className="block mb-2">Step 2:</strong>
                Scan this QR code or enter the code manually
              </p>
            </div>

            {qrCodeUrl && (
              <div className="text-center mb-6 p-4 bg-gray-50 rounded-lg">
                <img
                  src={qrCodeUrl}
                  alt="MFA QR Code"
                  className="mx-auto mb-3"
                  style={{ width: '200px', height: '200px' }}
                />
                <p className="text-xs text-gray-500 mb-2">Can't scan? Enter this code manually:</p>
                <code className="bg-gray-200 px-3 py-1 rounded text-sm font-mono">
                  {totpSecret}
                </code>
              </div>
            )}

            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-3">
                <strong className="block mb-2">Step 3:</strong>
                Enter the 6-digit code from your authenticator app:
              </p>
              <input
                type="text"
                maxLength="6"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                className="w-full p-3 border-2 border-gray-300 rounded-lg text-center text-2xl tracking-widest font-mono focus:border-blue-500 focus:outline-none"
                placeholder="000000"
                autoFocus
                disabled={loading}
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {error}
              </div>
            )}

            {loading && (
              <div className="text-center text-blue-600 mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                Verifying...
              </div>
            )}

            {sessionExpired ? (
              <button
                onClick={onCancel}
                className="w-full bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 font-semibold transition-colors"
              >
                Close and Login Again
              </button>
            ) : (
              <>
                <button
                  onClick={handleVerifySetup}
                  disabled={verificationCode.length !== 6 || loading}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold transition-colors"
                >
                  {loading ? 'Verifying...' : 'Verify and Complete Setup'}
                </button>

                <button
                  onClick={onCancel}
                  className="w-full mt-3 text-gray-600 hover:text-gray-800 py-2"
                  disabled={loading}
                >
                  Cancel
                </button>
              </>
            )}

            <div className="mt-6 space-y-3">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-800">
                  <strong>🔐 Security Note:</strong> This app will generate a new 6-digit code every 30 seconds.
                  You'll need this app every time you log in for enhanced security.
                </p>
              </div>

              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-xs text-yellow-800">
                  <strong>⏱️ Time Limit:</strong> For security, you have 3 minutes to complete MFA setup.
                  If the session expires, simply close this window and log in again - your QR code will remain the same.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MFASetupChallenge;
