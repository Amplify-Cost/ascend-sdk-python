/**
 * SkeletonCard Component
 * Loading state skeleton for enterprise cards
 *
 * Created: 2025-11-12
 * Purpose: Provide visual feedback during data loading
 */

import React from 'react';
import ENTERPRISE_THEME from './EnterpriseTheme';

const SkeletonCard = ({ variant = 'default', className = '' }) => {
  return (
    <div
      className={`
        bg-white rounded-lg border border-gray-200
        shadow-sm overflow-hidden animate-pulse
        ${className}
      `}
      style={{
        borderRadius: ENTERPRISE_THEME.radius.lg,
        boxShadow: ENTERPRISE_THEME.shadows.base,
      }}
    >
      {/* Header Skeleton */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-center space-x-3">
          {/* Icon skeleton */}
          <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>

          {/* Title & subtitle skeleton */}
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
            <div className="h-3 bg-gray-100 rounded w-24"></div>
          </div>
        </div>
      </div>

      {/* Body Skeleton */}
      <div className="px-6 py-5 space-y-4">
        {variant === 'chart' && (
          <>
            {/* Chart skeleton */}
            <div className="h-64 bg-gray-100 rounded"></div>
          </>
        )}

        {variant === 'list' && (
          <>
            {/* List skeleton */}
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-2 bg-gray-100 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </>
        )}

        {variant === 'default' && (
          <>
            {/* Generic content skeleton */}
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </>
        )}
      </div>

      {/* Footer Skeleton */}
      <div
        className="px-6 py-3 border-t"
        style={{ backgroundColor: ENTERPRISE_THEME.ui.background }}
      >
        <div className="h-3 bg-gray-200 rounded w-48"></div>
      </div>
    </div>
  );
};

/**
 * Compact Skeleton (for small widgets)
 */
export const CompactSkeleton = ({ className = '' }) => {
  return (
    <div
      className={`
        bg-white rounded-lg border border-gray-200
        shadow-sm p-5 animate-pulse
        ${className}
      `}
      style={{
        borderRadius: ENTERPRISE_THEME.radius.lg,
        boxShadow: ENTERPRISE_THEME.shadows.base,
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 space-y-3">
          <div className="h-3 bg-gray-200 rounded w-24"></div>
          <div className="h-6 bg-gray-300 rounded w-16"></div>
          <div className="h-2 bg-gray-100 rounded w-20"></div>
        </div>
        <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
      </div>
    </div>
  );
};

/**
 * Chart Skeleton (specific for chart loading)
 */
export const ChartSkeleton = ({ height = '300px', className = '' }) => {
  return (
    <div
      className={`bg-gray-100 rounded animate-pulse ${className}`}
      style={{
        height,
        borderRadius: ENTERPRISE_THEME.radius.md,
      }}
    >
      <div className="flex items-end justify-around h-full p-4">
        {[60, 80, 45, 90, 70, 55, 85].map((h, i) => (
          <div
            key={i}
            className="bg-gray-300 rounded-t"
            style={{
              width: '10%',
              height: `${h}%`,
            }}
          ></div>
        ))}
      </div>
    </div>
  );
};

export default SkeletonCard;
