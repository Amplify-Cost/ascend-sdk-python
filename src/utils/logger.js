/**
 * Enterprise Production Logger
 * 
 * Security Features:
 * - Sanitizes sensitive data (tokens, passwords, emails)
 * - Configurable log levels
 * - Production mode strips debug logs
 * - No console.log in production builds
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4
};

// Get log level from environment (default to INFO in production)
const ENV = import.meta.env.MODE || 'development';
const IS_PRODUCTION = ENV === 'production';
const CURRENT_LEVEL = IS_PRODUCTION ? LOG_LEVELS.INFO : LOG_LEVELS.DEBUG;

// Sensitive fields to redact
const SENSITIVE_KEYS = [
  'password',
  'token',
  'access_token',
  'refresh_token',
  'secret',
  'apiKey',
  'authorization',
  'cookie'
];

/**
 * Sanitize object to remove sensitive data
 */
function sanitize(obj) {
  if (!obj || typeof obj !== 'object') return obj;
  
  if (Array.isArray(obj)) {
    return obj.map(item => sanitize(item));
  }
  
  const sanitized = {};
  for (const [key, value] of Object.entries(obj)) {
    const lowerKey = key.toLowerCase();
    
    // Redact sensitive fields
    if (SENSITIVE_KEYS.some(sensitive => lowerKey.includes(sensitive))) {
      sanitized[key] = '[REDACTED]';
    }
    // Redact emails (partially)
    else if (lowerKey.includes('email') && typeof value === 'string') {
      const parts = value.split('@');
      if (parts.length === 2) {
        const masked = parts[0].substring(0, 2) + '***';
        sanitized[key] = `${masked}@${parts[1]}`;
      } else {
        sanitized[key] = value;
      }
    }
    // Recursively sanitize nested objects
    else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitize(value);
    }
    else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
}

/**
 * Format log message
 */
function formatMessage(level, message, data) {
  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}] [${level}]`;
  
  if (data) {
    const sanitizedData = sanitize(data);
    return `${prefix} ${message}`, sanitizedData;
  }
  
  return `${prefix} ${message}`;
}

/**
 * Logger class
 */
class Logger {
  debug(message, data) {
    if (CURRENT_LEVEL <= LOG_LEVELS.DEBUG) {
      const formatted = formatMessage('DEBUG', message, data);
      if (data) {
        console.debug(formatted[0], formatted[1]);
      } else {
        console.debug(formatted);
      }
    }
  }
  
  info(message, data) {
    if (CURRENT_LEVEL <= LOG_LEVELS.INFO) {
      const formatted = formatMessage('INFO', message, data);
      if (data) {
        console.info(formatted[0], formatted[1]);
      } else {
        console.info(formatted);
      }
    }
  }
  
  warn(message, data) {
    if (CURRENT_LEVEL <= LOG_LEVELS.WARN) {
      const formatted = formatMessage('WARN', message, data);
      if (data) {
        console.warn(formatted[0], formatted[1]);
      } else {
        console.warn(formatted);
      }
    }
  }
  
  error(message, error) {
    if (CURRENT_LEVEL <= LOG_LEVELS.ERROR) {
      const formatted = formatMessage('ERROR', message);
      console.error(formatted, error);
      
      // In production, could send to error monitoring service
      if (IS_PRODUCTION) {
        // TODO: Send to Sentry/DataDog/etc
      }
    }
  }
}

// Export singleton instance
const logger = new Logger();
export default logger;
