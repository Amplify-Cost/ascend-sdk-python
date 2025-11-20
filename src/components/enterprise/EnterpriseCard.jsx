/**
 * EnterpriseCard Component
 * Professional card layout for enterprise analytics dashboards
 *
 * Created: 2025-11-12
 * Purpose: Consistent, accessible card design with header, body, footer
 */

import React from 'react';
import ENTERPRISE_THEME from './EnterpriseTheme';

const EnterpriseCard = ({
  icon,
  title,
  subtitle,
  children,
  footer,
  className = '',
  headerAction,
  variant = 'default', // default, success, warning, danger, info
  loading = false,
}) => {
  // Variant styles
  const variantStyles = {
    default: {
      iconBg: 'bg-blue-50',
      iconColor: 'text-blue-600',
      borderColor: 'border-gray-200',
    },
    success: {
      iconBg: 'bg-green-50',
      iconColor: 'text-green-600',
      borderColor: 'border-green-200',
    },
    warning: {
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
      borderColor: 'border-amber-200',
    },
    danger: {
      iconBg: 'bg-red-50',
      iconColor: 'text-red-600',
      borderColor: 'border-red-200',
    },
    info: {
      iconBg: 'bg-blue-50',
      iconColor: 'text-blue-600',
      borderColor: 'border-blue-200',
    },
  };

  const styles = variantStyles[variant] || variantStyles.default;

  return (
    <div
      className={`
        bg-white rounded-lg border ${styles.borderColor}
        shadow-sm hover:shadow-md
        transition-all duration-200
        overflow-hidden
        ${className}
      `}
      style={{
        borderRadius: ENTERPRISE_THEME.radius.lg,
        boxShadow: ENTERPRISE_THEME.shadows.base,
      }}
    >
      {/* Card Header */}
      {(icon || title || headerAction) && (
        <div
          className="px-6 py-4 border-b border-gray-100"
          style={{ borderColor: ENTERPRISE_THEME.ui.border }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {/* Icon */}
              {icon && (
                <div
                  className={`
                    ${styles.iconBg} ${styles.iconColor}
                    p-2 rounded-lg
                  `}
                  style={{ borderRadius: ENTERPRISE_THEME.radius.md }}
                >
                  {icon}
                </div>
              )}

              {/* Title & Subtitle */}
              <div>
                {title && (
                  <h3
                    className="text-lg font-semibold"
                    style={{
                      color: ENTERPRISE_THEME.ui.text,
                      fontSize: ENTERPRISE_THEME.typography.fontSize.lg,
                      fontWeight: ENTERPRISE_THEME.typography.fontWeight.semibold,
                    }}
                  >
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p
                    className="text-sm mt-0.5"
                    style={{
                      color: ENTERPRISE_THEME.ui.textMuted,
                      fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
                    }}
                  >
                    {subtitle}
                  </p>
                )}
              </div>
            </div>

            {/* Header Action (e.g., dropdown menu) */}
            {headerAction && (
              <div className="flex-shrink-0">
                {headerAction}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Card Body */}
      <div className="px-6 py-5">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          children
        )}
      </div>

      {/* Card Footer */}
      {footer && (
        <div
          className="px-6 py-3 border-t"
          style={{
            backgroundColor: ENTERPRISE_THEME.ui.background,
            borderColor: ENTERPRISE_THEME.ui.border,
          }}
        >
          <div
            className="text-sm"
            style={{
              color: ENTERPRISE_THEME.ui.textSecondary,
              fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
            }}
          >
            {footer}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Compact Card Variant (for smaller widgets)
 */
export const CompactCard = ({
  icon,
  title,
  value,
  change,
  changeType = 'neutral', // positive, negative, neutral
  className = '',
}) => {
  const changeColors = {
    positive: ENTERPRISE_THEME.status.success,
    negative: ENTERPRISE_THEME.status.danger,
    neutral: ENTERPRISE_THEME.ui.textMuted,
  };

  return (
    <div
      className={`
        bg-white rounded-lg border border-gray-200
        shadow-sm hover:shadow-md
        transition-all duration-200
        p-5
        ${className}
      `}
      style={{
        borderRadius: ENTERPRISE_THEME.radius.lg,
        boxShadow: ENTERPRISE_THEME.shadows.base,
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          {/* Title */}
          <p
            className="text-sm font-medium mb-1"
            style={{
              color: ENTERPRISE_THEME.ui.textSecondary,
              fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
            }}
          >
            {title}
          </p>

          {/* Value */}
          <p
            className="text-2xl font-bold"
            style={{
              color: ENTERPRISE_THEME.ui.text,
              fontSize: ENTERPRISE_THEME.typography.fontSize['2xl'],
              fontWeight: ENTERPRISE_THEME.typography.fontWeight.bold,
            }}
          >
            {value}
          </p>

          {/* Change Indicator */}
          {change && (
            <p
              className="text-xs mt-1 flex items-center"
              style={{
                color: changeColors[changeType],
                fontSize: ENTERPRISE_THEME.typography.fontSize.xs,
              }}
            >
              {changeType === 'positive' && '↑'}
              {changeType === 'negative' && '↓'}
              {change}
            </p>
          )}
        </div>

        {/* Icon */}
        {icon && (
          <div
            className="text-gray-400 ml-4"
            style={{ color: ENTERPRISE_THEME.ui.textLight }}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnterpriseCard;
