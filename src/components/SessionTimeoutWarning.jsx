/**
 * Session Timeout Warning Component
 * Shows warning 5 minutes before session expires (SOC 2 requirement)
 * Engineer: OW-KAI Engineer
 */
import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const SessionTimeoutWarning = () => {
  const { showSessionWarning, sessionExpiresIn, extendSession, logout } = useAuth();
  const [timeLeft, setTimeLeft] = useState(sessionExpiresIn);

  useEffect(() => {
    setTimeLeft(sessionExpiresIn);
  }, [sessionExpiresIn]);

  if (!showSessionWarning) return null;

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl max-w-md">
        <h3 className="text-xl font-bold mb-4 text-orange-600">Session Expiring Soon</h3>
        <p className="mb-4">Your session will expire in:</p>
        <div className="text-4xl font-bold text-center mb-6">
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </div>
        <p className="mb-6 text-sm text-gray-600">
          For your security, you will be automatically logged out when the timer reaches zero.
        </p>
        <div className="flex gap-4">
          <button
            onClick={logout}
            className="flex-1 border border-gray-300 py-2 px-4 rounded hover:bg-gray-50"
          >
            Logout Now
          </button>
          <button
            onClick={extendSession}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Stay Logged In
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionTimeoutWarning;
