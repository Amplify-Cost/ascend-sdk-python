/**
 * MFA Verification Component - Enterprise Grade
 * Handles MFA code entry during login
 * Engineer: OW-KAI Engineer
 */
import React, { useState, useEffect } from 'react';
import { respondToMFAChallenge } from '../services/cognitoAuth';

const MFAVerification = ({ challengeName, session, poolConfig, onVerify, onCancel }) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [attemptsRemaining, setAttemptsRemaining] = useState(3);

  // Auto-submit when 6 digits entered
  useEffect(() => {
    if (verificationCode.length === 6) {
      handleVerify();
    }
  }, [verificationCode]);

  const handleVerify = async () => {
    try {
      setLoading(true);
      setError('');

      const result = await respondToMFAChallenge(challengeName, session, verificationCode, poolConfig);

      if (result.success) {
        onVerify(result);
      }
    } catch (err) {
      setError(err.message);
      setAttemptsRemaining(prev => prev - 1);

      if (attemptsRemaining <= 1) {
        setError('Account locked due to too many failed attempts. Please try again later.');
        setTimeout(() => onCancel(), 3000);
      }

      setVerificationCode('');
    } finally {
      setLoading(false);
    }
  };

  const isSMS = challengeName === 'SMS_MFA';

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Verify Your Identity</h2>
      <p className="mb-6 text-gray-600">
        {isSMS
          ? 'Enter the 6-digit code sent to your phone'
          : 'Enter the 6-digit code from your authenticator app'}
      </p>

      <input
        type="text"
        maxLength="6"
        value={verificationCode}
        onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
        className="w-full p-3 border rounded mb-4 text-center text-2xl tracking-widest"
        placeholder="000000"
        autoFocus
        disabled={loading || attemptsRemaining === 0}
      />

      {error && <div className="text-red-600 mb-4 text-sm">{error}</div>}

      {attemptsRemaining < 3 && attemptsRemaining > 0 && (
        <div className="text-orange-600 mb-4 text-sm">
          {attemptsRemaining} attempt{attemptsRemaining !== 1 ? 's' : ''} remaining
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={onCancel}
          className="flex-1 border border-gray-300 py-2 px-4 rounded hover:bg-gray-50"
          disabled={loading}
        >
          Cancel
        </button>
        <button
          onClick={handleVerify}
          disabled={verificationCode.length !== 6 || loading || attemptsRemaining === 0}
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? 'Verifying...' : 'Verify'}
        </button>
      </div>
    </div>
  );
};

export default MFAVerification;
