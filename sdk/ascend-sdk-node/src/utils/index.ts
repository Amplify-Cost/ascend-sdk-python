/**
 * Ascend AI Governance Platform - Utility Functions
 * @module utils
 */

import { randomBytes } from 'crypto';

export * from './retry';
export * from './validation';

/**
 * Generates a unique correlation ID for request tracking
 * Format: ascend-{timestamp}-{random}
 */
export function generateCorrelationId(): string {
  const timestamp = Date.now().toString(36);
  const random = randomBytes(8).toString('hex');
  return `ascend-${timestamp}-${random}`;
}

/**
 * Masks sensitive data for logging
 * Shows first and last N characters
 */
export function maskString(value: string, visibleChars: number = 4): string {
  if (!value || value.length <= visibleChars * 2) {
    return '***';
  }

  const start = value.substring(0, visibleChars);
  const end = value.substring(value.length - visibleChars);
  return `${start}...${end}`;
}

/**
 * Formats bytes to human-readable string
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Formats milliseconds to human-readable duration
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  return `${(ms / 3600000).toFixed(1)}h`;
}

/**
 * Deep clones an object (safe for JSON-serializable objects)
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Checks if running in Node.js environment
 */
export function isNode(): boolean {
  return typeof process !== 'undefined' && process.versions?.node !== undefined;
}

/**
 * Gets environment variable safely
 */
export function getEnv(key: string, defaultValue?: string): string | undefined {
  if (isNode()) {
    return process.env[key] || defaultValue;
  }
  return defaultValue;
}
