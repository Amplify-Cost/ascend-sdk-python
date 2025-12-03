/**
 * OW-AI SDK Error Classes
 * =======================
 *
 * Enterprise-grade exception handling with detailed error context.
 */

/**
 * Base error class for all OW-AI SDK errors
 */
export class OWKAIError extends Error {
  /** Error code for programmatic handling */
  readonly code: string;
  /** Additional error details */
  readonly details: Record<string, unknown>;

  constructor(
    message: string,
    code: string = 'OWKAI_ERROR',
    details: Record<string, unknown> = {}
  ) {
    super(message);
    this.name = 'OWKAIError';
    this.code = code;
    this.details = details;

    // Maintains proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Convert error to JSON-serializable object
   */
  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      details: this.details,
    };
  }
}

/**
 * Raised when authentication fails
 *
 * Possible causes:
 * - Invalid API key
 * - Expired credentials
 * - API key not authorized for organization
 */
export class AuthenticationError extends OWKAIError {
  constructor(
    message: string = 'Authentication failed',
    details: Record<string, unknown> = {}
  ) {
    super(message, 'AUTH_ERROR', details);
    this.name = 'AuthenticationError';
  }
}

/**
 * Raised when an action is denied
 *
 * Contains details about why the action was denied
 * and any policy violations.
 */
export class AuthorizationError extends OWKAIError {
  /** List of policy violations */
  readonly policyViolations: string[];
  /** Risk score that triggered denial */
  readonly riskScore?: number;

  constructor(
    message: string = 'Action not authorized',
    policyViolations: string[] = [],
    riskScore?: number,
    details: Record<string, unknown> = {}
  ) {
    super(message, 'AUTHZ_DENIED', {
      ...details,
      policyViolations,
      riskScore,
    });
    this.name = 'AuthorizationError';
    this.policyViolations = policyViolations;
    this.riskScore = riskScore;
  }
}

/**
 * Raised when an operation times out
 *
 * This can occur when:
 * - API request exceeds timeout
 * - Waiting for approval decision exceeds timeout
 */
export class TimeoutError extends OWKAIError {
  /** Timeout duration in milliseconds */
  readonly timeoutMs: number;

  constructor(
    message: string = 'Operation timed out',
    timeoutMs: number = 0,
    details: Record<string, unknown> = {}
  ) {
    super(message, 'TIMEOUT', { ...details, timeoutMs });
    this.name = 'TimeoutError';
    this.timeoutMs = timeoutMs;
  }
}

/**
 * Raised when rate limit is exceeded
 *
 * Contains information about when to retry.
 */
export class RateLimitError extends OWKAIError {
  /** Seconds until rate limit resets */
  readonly retryAfter: number;

  constructor(
    message: string = 'Rate limit exceeded',
    retryAfter: number = 60,
    details: Record<string, unknown> = {}
  ) {
    super(message, 'RATE_LIMIT', { ...details, retryAfter });
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

/**
 * Raised when input validation fails
 *
 * Contains details about which fields failed validation.
 */
export class ValidationError extends OWKAIError {
  /** Field-specific error messages */
  readonly fieldErrors: Record<string, string>;

  constructor(
    message: string = 'Validation failed',
    fieldErrors: Record<string, string> = {},
    details: Record<string, unknown> = {}
  ) {
    super(message, 'VALIDATION_ERROR', { ...details, fieldErrors });
    this.name = 'ValidationError';
    this.fieldErrors = fieldErrors;
  }
}

/**
 * Raised when connection to API fails
 */
export class ConnectionError extends OWKAIError {
  constructor(
    message: string = 'Failed to connect to OW-AI API',
    details: Record<string, unknown> = {}
  ) {
    super(message, 'CONNECTION_ERROR', details);
    this.name = 'ConnectionError';
  }
}

/**
 * Raised when circuit breaker is open due to repeated failures.
 *
 * The circuit breaker prevents cascading failures by failing fast
 * when the ASCEND service appears to be down.
 */
export class CircuitBreakerOpenError extends OWKAIError {
  /** Estimated time until circuit recovery attempt */
  readonly recoveryTimeSeconds: number;

  constructor(
    message: string = 'Circuit breaker is open - service appears to be down',
    recoveryTimeSeconds: number = 0,
    details: Record<string, unknown> = {}
  ) {
    super(message, 'CIRCUIT_OPEN', { ...details, recoveryTimeSeconds });
    this.name = 'CircuitBreakerOpenError';
    this.recoveryTimeSeconds = recoveryTimeSeconds;
  }
}
