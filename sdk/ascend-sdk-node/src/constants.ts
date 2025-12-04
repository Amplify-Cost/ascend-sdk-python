/**
 * Ascend AI Governance Platform - Constants
 * Enterprise configuration and defaults
 *
 * @module constants
 */

/**
 * Default API configuration
 */
export const DEFAULT_API_URL = 'https://pilot.owkai.app';
export const DEFAULT_TIMEOUT_MS = 30000; // 30 seconds
export const DEFAULT_MAX_RETRIES = 3;
export const DEFAULT_PAGE_LIMIT = 50;
export const MAX_PAGE_LIMIT = 100;

/**
 * API endpoints
 */
export const ENDPOINTS = {
  SUBMIT_ACTION: '/api/v1/actions/submit',
  GET_ACTION: '/api/v1/actions',
  LIST_ACTIONS: '/api/v1/actions',
  HEALTH_CHECK: '/health',
} as const;

/**
 * Retry configuration for transient failures
 * Implements exponential backoff with jitter
 */
export const RETRY_CONFIG = {
  INITIAL_DELAY_MS: 1000,      // 1 second
  MAX_DELAY_MS: 30000,         // 30 seconds
  BACKOFF_MULTIPLIER: 2,       // Exponential backoff
  JITTER_FACTOR: 0.1,          // 10% random jitter
  RETRYABLE_STATUS_CODES: [
    429, // Rate Limit
    500, // Internal Server Error
    502, // Bad Gateway
    503, // Service Unavailable
    504, // Gateway Timeout
  ],
} as const;

/**
 * Polling configuration for waiting for decisions
 */
export const POLLING_CONFIG = {
  INITIAL_DELAY_MS: 1000,      // Start polling after 1 second
  MAX_DELAY_MS: 5000,          // Max 5 seconds between polls
  DEFAULT_TIMEOUT_MS: 300000,  // 5 minutes default timeout
} as const;

/**
 * Action type definitions
 */
export const ACTION_TYPES = {
  DATA_ACCESS: 'data_access',
  DATA_MODIFICATION: 'data_modification',
  TRANSACTION: 'transaction',
  RECOMMENDATION: 'recommendation',
  COMMUNICATION: 'communication',
  SYSTEM_OPERATION: 'system_operation',
} as const;

/**
 * Risk level thresholds
 */
export const RISK_LEVELS = {
  MINIMAL: 'minimal',   // 0-20
  LOW: 'low',           // 21-40
  MEDIUM: 'medium',     // 41-60
  HIGH: 'high',         // 61-80
  CRITICAL: 'critical', // 81-100
} as const;

/**
 * Action status values
 */
export const ACTION_STATUS = {
  APPROVED: 'approved',
  PENDING_APPROVAL: 'pending_approval',
  DENIED: 'denied',
  TIMEOUT: 'timeout',
} as const;

/**
 * HTTP headers used by the SDK
 */
export const HEADERS = {
  AUTHORIZATION: 'Authorization',
  API_KEY: 'X-API-Key',
  CORRELATION_ID: 'X-Correlation-ID',
  CONTENT_TYPE: 'Content-Type',
  USER_AGENT: 'User-Agent',
} as const;

/**
 * SDK metadata
 */
export const SDK_VERSION = '1.0.0';
export const SDK_USER_AGENT = `ascend-sdk-node/${SDK_VERSION}`;

/**
 * Environment variable names
 */
export const ENV_VARS = {
  API_KEY: 'ASCEND_API_KEY',
  API_URL: 'ASCEND_API_URL',
} as const;

/**
 * Security constants
 */
export const SECURITY = {
  /** Number of characters to show when masking API keys */
  API_KEY_VISIBLE_CHARS: 4,
  /** Minimum API key length for validation */
  MIN_API_KEY_LENGTH: 32,
  /** API key prefix */
  API_KEY_PREFIX: 'owkai_',
} as const;
