/**
 * SEC-108: Enterprise Date Formatting Utility
 *
 * Provides safe date formatting with null/undefined checks to prevent
 * "Invalid Date" display issues across the frontend.
 *
 * SEC-108f: Added Unix epoch support (both seconds and milliseconds)
 *
 * SOC 2 A1.1: Consistent time display for audit compliance
 */

/**
 * SEC-108f: Parse date value handling multiple formats
 * @param {string|number|Date|null|undefined} value - The date to parse
 * @returns {Date|null} Parsed Date object or null if invalid
 */
const parseDate = (value) => {
  if (!value) return null;

  try {
    let date;

    if (typeof value === 'number') {
      // SEC-108f: Handle Unix epoch (seconds vs milliseconds)
      // If value < year 2100 in seconds (~4.1 billion), assume seconds
      // Otherwise assume milliseconds
      date = value < 4102444800
        ? new Date(value * 1000)  // Unix seconds → milliseconds
        : new Date(value);         // Already milliseconds
    } else if (value instanceof Date) {
      date = value;
    } else {
      // String - let Date constructor parse (ISO 8601, etc.)
      date = new Date(value);
    }

    return isNaN(date.getTime()) ? null : date;
  } catch {
    return null;
  }
};

/**
 * Safely format a date value to locale string
 * SEC-108f: Now handles Unix epoch (seconds/ms), ISO 8601 strings, and Date objects
 * @param {string|number|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid (default: 'N/A')
 * @returns {string} Formatted date string or fallback
 */
export const formatDate = (dateValue, fallback = 'N/A') => {
  const date = parseDate(dateValue);
  return date ? date.toLocaleString() : fallback;
};

/**
 * Format date to short format (MM/DD/YYYY)
 * SEC-108f: Now handles Unix epoch (seconds/ms), ISO 8601 strings, and Date objects
 * @param {string|number|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid
 * @returns {string} Formatted date string or fallback
 */
export const formatDateShort = (dateValue, fallback = 'N/A') => {
  const date = parseDate(dateValue);
  return date ? date.toLocaleDateString() : fallback;
};

/**
 * Format date to time only (HH:MM:SS)
 * SEC-108f: Now handles Unix epoch (seconds/ms), ISO 8601 strings, and Date objects
 * @param {string|number|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid
 * @returns {string} Formatted time string or fallback
 */
export const formatTime = (dateValue, fallback = 'N/A') => {
  const date = parseDate(dateValue);
  return date ? date.toLocaleTimeString() : fallback;
};

/**
 * Format date as relative time (e.g., "5 minutes ago")
 * SEC-108f: Now handles Unix epoch (seconds/ms), ISO 8601 strings, and Date objects
 * @param {string|number|Date|null|undefined} dateValue - The date to format
 * @param {string} fallback - Fallback text when date is invalid
 * @returns {string} Relative time string or fallback
 */
export const formatRelativeTime = (dateValue, fallback = 'N/A') => {
  const date = parseDate(dateValue);
  if (!date) return fallback;

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
};

/**
 * Format date for ISO string (useful for API submissions)
 * SEC-108f: Now handles Unix epoch (seconds/ms), ISO 8601 strings, and Date objects
 * @param {string|number|Date|null|undefined} dateValue - The date to format
 * @returns {string|null} ISO string or null
 */
export const formatISODate = (dateValue) => {
  const date = parseDate(dateValue);
  return date ? date.toISOString() : null;
};

export default {
  formatDate,
  formatDateShort,
  formatTime,
  formatRelativeTime,
  formatISODate
};
