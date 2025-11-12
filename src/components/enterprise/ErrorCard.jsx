/**
 * ErrorCard Component
 * Error state display for enterprise cards
 *
 * Created: 2025-11-12
 * Purpose: Consistent error handling with retry functionality
 */

import React from 'react';
import ENTERPRISE_THEME from './EnterpriseTheme';

const ErrorCard = ({
  title = 'Error Loading Data',
  message = 'An unexpected error occurred while loading this data.',
  onRetry,
  className = '',
  showDetails = false,
  details = null,
}) => {
  const [showDetailsState, setShowDetailsState] = React.useState(false);

  return (
    <div
      className={`
        bg-white rounded-lg border border-red-200
        shadow-sm p-8 text-center
        ${className}
      `}
      style={{
        borderRadius: ENTERPRISE_THEME.radius.lg,
        boxShadow: ENTERPRISE_THEME.shadows.base,
      }}
    >
      {/* Error Icon */}
      <div className="flex justify-center mb-4">
        <div
          className="bg-red-50 rounded-full p-3"
          style={{ borderRadius: ENTERPRISE_THEME.radius.full }}
        >
          <svg
            className="w-8 h-8"
            style={{ color: ENTERPRISE_THEME.status.danger }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
      </div>

      {/* Error Title */}
      <h3
        className="text-lg font-semibold mb-2"
        style={{
          color: ENTERPRISE_THEME.ui.text,
          fontSize: ENTERPRISE_THEME.typography.fontSize.lg,
          fontWeight: ENTERPRISE_THEME.typography.fontWeight.semibold,
        }}
      >
        {title}
      </h3>

      {/* Error Message */}
      <p
        className="mb-6"
        style={{
          color: ENTERPRISE_THEME.ui.textSecondary,
          fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
        }}
      >
        {message}
      </p>

      {/* Action Buttons */}
      <div className="flex items-center justify-center space-x-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 rounded-md font-medium transition-colors"
            style={{
              backgroundColor: ENTERPRISE_THEME.status.info,
              color: 'white',
              fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
              borderRadius: ENTERPRISE_THEME.radius.md,
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#2563eb';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = ENTERPRISE_THEME.status.info;
            }}
          >
            <span className="flex items-center space-x-2">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span>Try Again</span>
            </span>
          </button>
        )}

        {showDetails && details && (
          <button
            onClick={() => setShowDetailsState(!showDetailsState)}
            className="px-4 py-2 rounded-md font-medium transition-colors"
            style={{
              backgroundColor: ENTERPRISE_THEME.ui.background,
              color: ENTERPRISE_THEME.ui.textSecondary,
              border: `1px solid ${ENTERPRISE_THEME.ui.border}`,
              fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
              borderRadius: ENTERPRISE_THEME.radius.md,
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#f3f4f6';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = ENTERPRISE_THEME.ui.background;
            }}
          >
            {showDetailsState ? 'Hide Details' : 'Show Details'}
          </button>
        )}
      </div>

      {/* Error Details (collapsible) */}
      {showDetailsState && details && (
        <div
          className="mt-6 p-4 rounded-md text-left text-xs overflow-auto max-h-40"
          style={{
            backgroundColor: ENTERPRISE_THEME.ui.background,
            borderRadius: ENTERPRISE_THEME.radius.md,
            fontFamily: 'monospace',
            color: ENTERPRISE_THEME.status.danger,
          }}
        >
          <pre className="whitespace-pre-wrap">{JSON.stringify(details, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

/**
 * Inline Error (smaller, for inline errors)
 */
export const InlineError = ({ message, onRetry, className = '' }) => {
  return (
    <div
      className={`flex items-center justify-between p-4 rounded-md ${className}`}
      style={{
        backgroundColor: '#fef2f2',
        border: `1px solid ${ENTERPRISE_THEME.status.danger}`,
        borderRadius: ENTERPRISE_THEME.radius.md,
      }}
    >
      <div className="flex items-center space-x-3">
        <svg
          className="w-5 h-5 flex-shrink-0"
          style={{ color: ENTERPRISE_THEME.status.danger }}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p
          className="text-sm"
          style={{ color: ENTERPRISE_THEME.status.danger }}
        >
          {message}
        </p>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          className="text-sm font-medium hover:underline"
          style={{ color: ENTERPRISE_THEME.status.danger }}
        >
          Retry
        </button>
      )}
    </div>
  );
};

export default ErrorCard;
