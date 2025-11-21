/**
 * Enterprise Forgot Password Component - Phase 3
 * Complete password reset flow with enterprise security
 * Engineer: OW-KAI Engineer
 */
import React, { useState } from 'react';
import { forgotPassword, confirmForgotPassword, validatePassword } from '../services/cognitoAuth';

const ForgotPassword = ({ switchToLogin }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await forgotPassword(email);
      setMessage('Verification code sent to your email');
      setCurrentStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = (password) => {
    setNewPassword(password);
    const validation = validatePassword(password);
    setPasswordStrength(validation.strength);
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    const validation = validatePassword(newPassword);
    if (!validation.valid) {
      setError(validation.errors.join('. '));
      setLoading(false);
      return;
    }

    try {
      await confirmForgotPassword(email, verificationCode, newPassword);
      setMessage('Password reset successfully!');
      setTimeout(() => switchToLogin(), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Reset Password</h2>

      {currentStep === 1 && (
        <form onSubmit={handleRequestReset}>
          <p className="mb-4 text-gray-600">Enter your email to receive a verification code</p>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 border rounded mb-4"
            placeholder="Email address"
            required
          />
          {error && <div className="text-red-600 mb-4 text-sm">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Sending...' : 'Send Verification Code'}
          </button>
        </form>
      )}

      {currentStep === 2 && (
        <form onSubmit={handleResetPassword}>
          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value)}
            className="w-full p-3 border rounded mb-4"
            placeholder="Verification code"
            maxLength="6"
            required
          />
          <input
            type="password"
            value={newPassword}
            onChange={(e) => handlePasswordChange(e.target.value)}
            className="w-full p-3 border rounded mb-2"
            placeholder="New password"
            required
          />
          <div className="mb-4">
            <div className="h-2 bg-gray-200 rounded overflow-hidden">
              <div
                className={`h-full transition-all ${
                  passwordStrength > 75 ? 'bg-green-500' : passwordStrength > 50 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${passwordStrength}%` }}
              />
            </div>
          </div>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full p-3 border rounded mb-4"
            placeholder="Confirm password"
            required
          />
          {error && <div className="text-red-600 mb-4 text-sm">{error}</div>}
          {message && <div className="text-green-600 mb-4 text-sm">{message}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
      )}

      <button onClick={switchToLogin} className="mt-4 text-blue-600 hover:underline text-sm">
        Back to Login
      </button>
    </div>
  );
};

export default ForgotPassword;
