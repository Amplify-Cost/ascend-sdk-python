/**
 * Ascend AI Governance Platform - Error Classes
 * Enterprise-grade error handling with security masking
 *
 * @module errors
 */

import { SECURITY } from './constants';

/**
 * Masks sensitive data in error messages
 * Never logs full API keys or tokens
 */
function maskSensitiveData(value: string): string {
  if (!value || value.length < 8) {
    return '***';
  }

  const visibleChars = SECURITY.API_KEY_VISIBLE_CHARS;
  const start = value.substring(0, visibleChars);
  const end = value.substring(value.length - visibleChars);
  return `${start}...${end}`;
}

/**
 * Base error class for all Ascend SDK errors
 */
export class AscendError extends Error {
  public readonly name: string;
  public readonly statusCode?: number;
  public readonly correlationId?: string;

  constructor(message: string, statusCode?: number, correlationId?: string) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
    this.correlationId = correlationId;

    // Maintains proper stack trace for where error was thrown (Node.js only)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Returns a JSON representation safe for logging
   * Automatically masks sensitive data
   */
  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      statusCode: this.statusCode,
      correlationId: this.correlationId,
    };
  }
}

/**
 * Authentication error - invalid or missing API key
 */
export class AuthenticationError extends AscendError {
  constructor(message: string = 'Authentication failed. Invalid or missing API key.', correlationId?: string) {
    super(message, 401, correlationId);
  }

  static missingApiKey(): AuthenticationError {
    return new AuthenticationError(
      'API key is required. Set ASCEND_API_KEY environment variable or pass apiKey to constructor.'
    );
  }

  static invalidApiKey(apiKey: string): AuthenticationError {
    const masked = maskSensitiveData(apiKey);
    return new AuthenticationError(
      `Invalid API key format: ${masked}. Expected format: ${SECURITY.API_KEY_PREFIX}*`
    );
  }
}

/**
 * Authorization error - action was denied by policy
 */
export class AuthorizationDeniedError extends AscendError {
  public readonly actionId?: number;
  public readonly reason?: string;

  constructor(
    message: string = 'Action was denied by governance policy.',
    actionId?: number,
    reason?: string,
    correlationId?: string
  ) {
    super(message, 403, correlationId);
    this.actionId = actionId;
    this.reason = reason;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      actionId: this.actionId,
      reason: this.reason,
    };
  }
}

/**
 * Rate limit error - too many requests
 */
export class RateLimitError extends AscendError {
  public readonly retryAfter?: number;

  constructor(
    message: string = 'Rate limit exceeded. Please retry after the specified delay.',
    retryAfter?: number,
    correlationId?: string
  ) {
    super(message, 429, correlationId);
    this.retryAfter = retryAfter;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      retryAfter: this.retryAfter,
    };
  }
}

/**
 * Timeout error - request or polling exceeded time limit
 */
export class TimeoutError extends AscendError {
  public readonly timeoutMs: number;

  constructor(message: string, timeoutMs: number, correlationId?: string) {
    super(message, 408, correlationId);
    this.timeoutMs = timeoutMs;
  }

  static requestTimeout(timeoutMs: number): TimeoutError {
    return new TimeoutError(
      `Request timeout after ${timeoutMs}ms. Consider increasing the timeout value.`,
      timeoutMs
    );
  }

  static pollingTimeout(timeoutMs: number, actionId: number): TimeoutError {
    return new TimeoutError(
      `Polling timeout after ${timeoutMs}ms waiting for decision on action ${actionId}.`,
      timeoutMs
    );
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      timeoutMs: this.timeoutMs,
    };
  }
}

/**
 * Validation error - invalid input parameters
 */
export class ValidationError extends AscendError {
  public readonly field?: string;
  public readonly value?: unknown;

  constructor(
    message: string,
    field?: string,
    value?: unknown,
    correlationId?: string
  ) {
    super(message, 400, correlationId);
    this.field = field;
    this.value = value;
  }

  static requiredField(field: string): ValidationError {
    return new ValidationError(`Required field missing: ${field}`, field);
  }

  static invalidValue(field: string, value: unknown, expected: string): ValidationError {
    return new ValidationError(
      `Invalid value for ${field}: ${value}. Expected: ${expected}`,
      field,
      value
    );
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      field: this.field,
      value: this.value,
    };
  }
}

/**
 * Network error - connection or HTTP errors
 */
export class NetworkError extends AscendError {
  public readonly cause?: Error;

  constructor(message: string, statusCode?: number, cause?: Error, correlationId?: string) {
    super(message, statusCode, correlationId);
    this.cause = cause;
  }

  static fromAxiosError(error: any, correlationId?: string): NetworkError {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data?.detail || error.response.data?.error || error.message;
      return new NetworkError(
        `HTTP ${status}: ${message}`,
        status,
        error,
        correlationId
      );
    } else if (error.request) {
      // Request made but no response received
      return new NetworkError(
        'No response received from server. Check network connection.',
        undefined,
        error,
        correlationId
      );
    } else {
      // Error setting up request
      return new NetworkError(
        `Request setup failed: ${error.message}`,
        undefined,
        error,
        correlationId
      );
    }
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      cause: this.cause?.message,
    };
  }
}

/**
 * Parses API error response and throws appropriate error
 */
export function handleApiError(
  error: any,
  correlationId?: string
): never {
  // Handle Axios errors
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 401:
        throw new AuthenticationError(
          data?.detail || 'Authentication failed',
          correlationId
        );

      case 403:
        throw new AuthorizationDeniedError(
          data?.detail || 'Authorization denied',
          undefined,
          data?.reason,
          correlationId
        );

      case 429:
        const retryAfter = parseInt(error.response.headers['retry-after'] || '60', 10);
        throw new RateLimitError(
          data?.detail || 'Rate limit exceeded',
          retryAfter,
          correlationId
        );

      case 400:
        throw new ValidationError(
          data?.detail || 'Invalid request parameters',
          data?.field,
          data?.value,
          correlationId
        );

      default:
        throw NetworkError.fromAxiosError(error, correlationId);
    }
  }

  // Handle network errors
  if (error.code === 'ECONNABORTED') {
    throw TimeoutError.requestTimeout(parseInt(error.config?.timeout || '30000', 10));
  }

  if (error.request) {
    throw new NetworkError(
      'No response received from server',
      undefined,
      error,
      correlationId
    );
  }

  // Handle SDK errors (already wrapped)
  if (error instanceof AscendError) {
    throw error;
  }

  // Unknown error
  throw new AscendError(
    `Unexpected error: ${error.message || String(error)}`,
    undefined,
    correlationId
  );
}
