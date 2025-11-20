/**
 * EmptyCard Component
 * Empty state display for enterprise cards
 *
 * Created: 2025-11-12
 * Purpose: Consistent empty state with optional action
 */

import React from 'react';
import ENTERPRISE_THEME from './EnterpriseTheme';

const EmptyCard = ({
  title = 'No Data Available',
  message = 'There is currently no data to display.',
  icon,
  action,
  actionLabel,
  variant = 'info', // info, success, warning
  className = '',
}) => {
  // Variant styles
  const variantStyles = {
    info: {
      iconBg: 'bg-blue-50',
      iconColor: ENTERPRISE_THEME.status.info,
    },
    success: {
      iconBg: 'bg-green-50',
      iconColor: ENTERPRISE_THEME.status.success,
    },
    warning: {
      iconBg: 'bg-amber-50',
      iconColor: ENTERPRISE_THEME.status.warning,
    },
  };

  const styles = variantStyles[variant] || variantStyles.info;

  // Default icon if none provided
  const defaultIcon = (
    <svg
      className="w-8 h-8"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
      />
    </svg>
  );

  return (
    <div
      className={`
        bg-white rounded-lg border border-gray-200
        shadow-sm p-8 py-12 text-center
        ${className}
      `}
      style={{
        borderRadius: ENTERPRISE_THEME.radius.lg,
        boxShadow: ENTERPRISE_THEME.shadows.base,
      }}
    >
      {/* Icon */}
      <div className="flex justify-center mb-4">
        <div
          className={`${styles.iconBg} rounded-full p-3`}
          style={{ borderRadius: ENTERPRISE_THEME.radius.full }}
        >
          <div style={{ color: styles.iconColor }}>
            {icon || defaultIcon}
          </div>
        </div>
      </div>

      {/* Title */}
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

      {/* Message */}
      <p
        className="mb-6 max-w-md mx-auto"
        style={{
          color: ENTERPRISE_THEME.ui.textSecondary,
          fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
        }}
      >
        {message}
      </p>

      {/* Action Button */}
      {action && actionLabel && (
        <button
          onClick={action}
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
          {actionLabel}
        </button>
      )}
    </div>
  );
};

/**
 * Inline Empty State (smaller, for inline use)
 */
export const InlineEmpty = ({ message, icon, className = '' }) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 ${className}`}
      style={{ color: ENTERPRISE_THEME.ui.textMuted }}
    >
      {icon && (
        <div className="mb-3" style={{ color: ENTERPRISE_THEME.ui.textLight }}>
          {icon}
        </div>
      )}
      <p
        className="text-sm text-center"
        style={{
          color: ENTERPRISE_THEME.ui.textMuted,
          fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
        }}
      >
        {message}
      </p>
    </div>
  );
};

/**
 * Success Empty State (for successful actions with no data)
 */
export const SuccessEmpty = ({ title, message, className = '' }) => {
  return (
    <EmptyCard
      title={title}
      message={message}
      variant="success"
      icon={
        <svg
          className="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      }
      className={className}
    />
  );
};

export default EmptyCard;
