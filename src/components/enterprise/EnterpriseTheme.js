/**
 * Enterprise Theme Configuration
 * Professional color system for OW AI Enterprise Analytics
 *
 * Created: 2025-11-12
 * Purpose: Consistent, accessible, professional color palette
 */

export const ENTERPRISE_THEME = {
  // Status colors (semantic) - WCAG AA compliant
  status: {
    success: '#10b981',      // Green for safe/approved actions
    warning: '#f59e0b',      // Amber for medium risk
    danger: '#ef4444',       // Red for high risk
    critical: '#dc2626',     // Dark red for critical risk
    info: '#3b82f6',         // Blue for informational
    neutral: '#6b7280',      // Gray for neutral/inactive
  },

  // Risk level colors (mapped to CVSS scores)
  risk: {
    none: '#10b981',         // 0.0 (Green - No risk)
    low: '#84cc16',          // 0.1-3.9 (Lime - Low risk)
    medium: '#f59e0b',       // 4.0-6.9 (Amber - Medium risk)
    high: '#f97316',         // 7.0-8.9 (Orange - High risk)
    critical: '#ef4444',     // 9.0-10.0 (Red - Critical risk)
  },

  // Data visualization palette (professional, accessible)
  chart: {
    primary: '#1e40af',      // Deep blue
    secondary: '#7c3aed',    // Purple
    tertiary: '#059669',     // Teal
    quaternary: '#dc2626',   // Red
    quinary: '#ea580c',      // Orange
    senary: '#0891b2',       // Cyan
    septenary: '#c026d3',    // Magenta
    octonary: '#65a30d',     // Green
  },

  // UI element colors
  ui: {
    background: '#f9fafb',   // Light gray background
    cardBg: '#ffffff',       // White cards
    cardBgHover: '#f3f4f6',  // Light gray on hover
    border: '#e5e7eb',       // Subtle borders
    borderHover: '#d1d5db',  // Darker border on hover
    text: '#111827',         // Dark text (primary)
    textSecondary: '#4b5563', // Medium gray text
    textMuted: '#6b7280',    // Muted text
    textLight: '#9ca3af',    // Light gray text
    shadow: 'rgba(0, 0, 0, 0.1)', // Subtle shadow
    shadowMd: 'rgba(0, 0, 0, 0.15)', // Medium shadow
  },

  // Gradient overlays for visual appeal
  gradients: {
    primary: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
    success: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
    warning: 'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)',
    danger: 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
    info: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
  },

  // Spacing system (8px grid)
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    xxl: '3rem',     // 48px
  },

  // Border radius
  radius: {
    sm: '0.25rem',   // 4px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
    full: '9999px',  // Fully rounded
  },

  // Typography
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontSize: {
      xs: '0.75rem',   // 12px
      sm: '0.875rem',  // 14px
      base: '1rem',    // 16px
      lg: '1.125rem',  // 18px
      xl: '1.25rem',   // 20px
      '2xl': '1.5rem', // 24px
      '3xl': '1.875rem', // 30px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },

  // Shadows (consistent elevation)
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
};

/**
 * Get color by risk score (CVSS 0-10)
 */
export const getRiskColor = (score) => {
  if (score === 0) return ENTERPRISE_THEME.risk.none;
  if (score < 4.0) return ENTERPRISE_THEME.risk.low;
  if (score < 7.0) return ENTERPRISE_THEME.risk.medium;
  if (score < 9.0) return ENTERPRISE_THEME.risk.high;
  return ENTERPRISE_THEME.risk.critical;
};

/**
 * Get risk label by score
 */
export const getRiskLabel = (score) => {
  if (score === 0) return 'None';
  if (score < 4.0) return 'Low';
  if (score < 7.0) return 'Medium';
  if (score < 9.0) return 'High';
  return 'Critical';
};

/**
 * Get status color by status string
 */
export const getStatusColor = (status) => {
  const statusMap = {
    'approved': ENTERPRISE_THEME.status.success,
    'success': ENTERPRISE_THEME.status.success,
    'completed': ENTERPRISE_THEME.status.success,
    'pending': ENTERPRISE_THEME.status.warning,
    'in_progress': ENTERPRISE_THEME.status.info,
    'denied': ENTERPRISE_THEME.status.danger,
    'failed': ENTERPRISE_THEME.status.danger,
    'error': ENTERPRISE_THEME.status.danger,
    'blocked': ENTERPRISE_THEME.status.critical,
  };

  return statusMap[status?.toLowerCase()] || ENTERPRISE_THEME.status.neutral;
};

/**
 * Chart color palette generator (cycles through chart colors)
 */
export const getChartColors = (count = 8) => {
  const colors = Object.values(ENTERPRISE_THEME.chart);
  return Array.from({ length: count }, (_, i) => colors[i % colors.length]);
};

export default ENTERPRISE_THEME;
