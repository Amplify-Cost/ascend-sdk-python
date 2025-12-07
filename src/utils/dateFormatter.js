/**
 * SEC-108: Enterprise Date Formatting Utility
 *
 * Provides safe date formatting with null/undefined checks to prevent
 * "Invalid Date" display issues across the frontend.
 *
 * SOC 2 A1.1: Consistent time display for audit compliance
 */

/**
 * Safely format a date string to locale string
 * @param {string|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid (default: 'N/A')
 * @returns {string} Formatted date string or fallback
 */
export const formatDate = (dateValue, fallback = 'N/A') => {
  if (!dateValue) return fallback;

  try {
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return fallback;
    return date.toLocaleString();
  } catch {
    return fallback;
  }
};

/**
 * Format date to short format (MM/DD/YYYY)
 * @param {string|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid
 * @returns {string} Formatted date string or fallback
 */
export const formatDateShort = (dateValue, fallback = 'N/A') => {
  if (!dateValue) return fallback;

  try {
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return fallback;
    return date.toLocaleDateString();
  } catch {
    return fallback;
  }
};

/**
 * Format date to time only (HH:MM:SS)
 * @param {string|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid
 * @returns {string} Formatted time string or fallback
 */
export const formatTime = (dateValue, fallback = 'N/A') => {
  if (!dateValue) return fallback;

  try {
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return fallback;
    return date.toLocaleTimeString();
  } catch {
    return fallback;
  }
};

/**
 * Format date as relative time (e.g., "5 minutes ago")
 * @param {string|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid
 * @returns {string} Relative time string or fallback
 */
export const formatRelativeTime = (dateValue, fallback = 'N/A') => {
  if (!dateValue) return fallback;

  try {
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return fallback;

    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    if (diffHour < 24) return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    if (diffDay < 7) return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;

    return date.toLocaleDateString();
  } catch {
    return fallback;
  }
};

/**
 * Format date for ISO string (useful for API submissions)
 * @param {string|Date|null|undefined} dateValue - The date to format
 * @returns {string|null} ISO string or null
 */
export const formatISODate = (dateValue) => {
  if (!dateValue) return null;

  try {
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return null;
    return date.toISOString();
  } catch {
    return null;
  }
};

export default {
  formatDate,
  formatDateShort,
  formatTime,
  formatRelativeTime,
  formatISODate
};
