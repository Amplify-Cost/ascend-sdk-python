/**
 * MFA Setup Component - Enterprise Grade
 * Supports TOTP (authenticator apps) and SMS MFA enrollment
 * Engineer: OW-KAI Engineer
 */
import React, { useState, useEffect } from 'react';
import QRCode from 'qrcode';
import { setupTOTP, verifyTOTP } from '../services/cognitoAuth';

const MFASetup = ({ onComplete, onCancel, userEmail, accessToken }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [mfaMethod, setMfaMethod] = useState(null);
  const [totpSecret, setTotpSecret] = useState('');
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Generate QR code when TOTP is selected
  useEffect(() => {
    if (mfaMethod === 'TOTP' && currentStep === 2) {
      initializeTOTP();
    }
  }, [mfaMethod, currentStep]);

  const initializeTOTP = async () => {
    try {
      setLoading(true);
      const result = await setupTOTP(accessToken);
      setTotpSecret(result.secretCode);

      // Generate QR code
      const otpAuthUrl = `otpauth://totp/OW-KAI:${userEmail}?secret=${result.secretCode}&issuer=OW-KAI`;
      const qrUrl = await QRCode.toDataURL(otpAuthUrl);
      setQrCodeUrl(qrUrl);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyTOTP = async () => {
    try {
      setLoading(true);
      setError('');
      await verifyTOTP(accessToken, totpSecret, verificationCode);
      onComplete({ method: 'TOTP', success: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6">Set Up Multi-Factor Authentication</h2>

      {/* Step 1: Choose Method */}
      {currentStep === 1 && (
        <div>
          <p className="mb-4 text-gray-600">Choose your preferred MFA method:</p>
          <div className="space-y-4">
            <button
              onClick={() => { setMfaMethod('TOTP'); setCurrentStep(2); }}
              className="w-full p-4 border-2 border-gray-300 rounded-lg hover:border-blue-500 text-left"
            >
              <div className="font-semibold">Authenticator App (Recommended)</div>
              <div className="text-sm text-gray-600">Use Google Authenticator, Authy, or similar</div>
            </button>
            <button
              onClick={() => { setMfaMethod('SMS'); setCurrentStep(2); }}
              className="w-full p-4 border-2 border-gray-300 rounded-lg hover:border-blue-500 text-left"
            >
              <div className="font-semibold">SMS Text Message</div>
              <div className="text-sm text-gray-600">Receive codes via text message</div>
            </button>
          </div>
        </div>
      )}

      {/* Step 2: TOTP Setup */}
      {currentStep === 2 && mfaMethod === 'TOTP' && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Scan QR Code</h3>
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : (
            <>
              {qrCodeUrl && (
                <div className="text-center mb-4">
                  <img src={qrCodeUrl} alt="QR Code" className="mx-auto mb-4" />
                  <p className="text-sm text-gray-600 mb-2">Or enter this code manually:</p>
                  <code className="bg-gray-100 px-3 py-1 rounded">{totpSecret}</code>
                </div>
              )}
              <button
                onClick={() => setCurrentStep(3)}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
              >
                I've Scanned the Code
              </button>
            </>
          )}
        </div>
      )}

      {/* Step 3: Verify TOTP */}
      {currentStep === 3 && mfaMethod === 'TOTP' && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Verify Code</h3>
          <p className="mb-4 text-gray-600">Enter the 6-digit code from your authenticator app:</p>
          <input
            type="text"
            maxLength="6"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
            className="w-full p-3 border rounded mb-4 text-center text-2xl tracking-widest"
            placeholder="000000"
          />
          {error && <div className="text-red-600 mb-4">{error}</div>}
          <button
            onClick={handleVerifyTOTP}
            disabled={verificationCode.length !== 6 || loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Verifying...' : 'Verify and Enable MFA'}
          </button>
        </div>
      )}

      <button onClick={onCancel} className="mt-4 text-gray-600 hover:text-gray-800">
        Cancel
      </button>
    </div>
  );
};

export default MFASetup;
