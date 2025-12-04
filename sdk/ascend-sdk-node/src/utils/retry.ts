/**
 * Ascend AI Governance Platform - Retry Logic
 * Enterprise-grade exponential backoff with jitter
 *
 * @module utils/retry
 */

import { RETRY_CONFIG } from '../constants';
import { RateLimitError, TimeoutError, NetworkError } from '../errors';

/**
 * Configuration for retry behavior
 */
export interface RetryOptions {
  maxRetries: number;
  initialDelayMs: number;
  maxDelayMs: number;
  retryableStatusCodes: number[];
}

/**
 * Determines if an error is retryable
 */
export function isRetryableError(error: any, retryableStatusCodes: number[]): boolean {
  // Rate limit errors are always retryable
  if (error instanceof RateLimitError) {
    return true;
  }

  // Timeout errors are not retryable (already waited)
  if (error instanceof TimeoutError) {
    return false;
  }

  // Network errors with retryable status codes
  if (error instanceof NetworkError && error.statusCode) {
    return retryableStatusCodes.includes(error.statusCode);
  }

  // Axios errors
  if (error.response?.status) {
    return retryableStatusCodes.includes(error.response.status);
  }

  // Network connection errors (ECONNREFUSED, ENOTFOUND, etc.)
  if (error.code && ['ECONNREFUSED', 'ENOTFOUND', 'ETIMEDOUT', 'ECONNRESET'].includes(error.code)) {
    return true;
  }

  return false;
}

/**
 * Calculates delay for next retry using exponential backoff with jitter
 *
 * Formula: min(maxDelay, initialDelay * 2^attempt) * (1 ± jitter)
 */
export function calculateRetryDelay(
  attempt: number,
  initialDelayMs: number = RETRY_CONFIG.INITIAL_DELAY_MS,
  maxDelayMs: number = RETRY_CONFIG.MAX_DELAY_MS
): number {
  // Exponential backoff: initialDelay * 2^attempt
  const exponentialDelay = initialDelayMs * Math.pow(RETRY_CONFIG.BACKOFF_MULTIPLIER, attempt);

  // Cap at maximum delay
  const cappedDelay = Math.min(exponentialDelay, maxDelayMs);

  // Add jitter (±10% random variation)
  const jitterFactor = 1 + (Math.random() - 0.5) * 2 * RETRY_CONFIG.JITTER_FACTOR;
  const delayWithJitter = Math.floor(cappedDelay * jitterFactor);

  return delayWithJitter;
}

/**
 * Sleeps for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Executes a function with retry logic
 *
 * @param fn Function to execute
 * @param options Retry configuration
 * @param onRetry Optional callback for retry events
 * @returns Result of the function
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {},
  onRetry?: (attempt: number, error: any, delayMs: number) => void
): Promise<T> {
  const config: RetryOptions = {
    maxRetries: options.maxRetries ?? RETRY_CONFIG.INITIAL_DELAY_MS / 1000,
    initialDelayMs: options.initialDelayMs ?? RETRY_CONFIG.INITIAL_DELAY_MS,
    maxDelayMs: options.maxDelayMs ?? RETRY_CONFIG.MAX_DELAY_MS,
    retryableStatusCodes: options.retryableStatusCodes ?? RETRY_CONFIG.RETRYABLE_STATUS_CODES,
  };

  let lastError: any;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry if it's the last attempt
      if (attempt >= config.maxRetries) {
        break;
      }

      // Check if error is retryable
      if (!isRetryableError(error, config.retryableStatusCodes)) {
        throw error;
      }

      // Calculate delay (with special handling for rate limits)
      let delayMs: number;

      if (error instanceof RateLimitError && error.retryAfter) {
        // Use server-provided retry-after value
        delayMs = error.retryAfter * 1000;
      } else {
        delayMs = calculateRetryDelay(attempt, config.initialDelayMs, config.maxDelayMs);
      }

      // Notify caller of retry
      if (onRetry) {
        onRetry(attempt + 1, error, delayMs);
      }

      // Wait before retrying
      await sleep(delayMs);
    }
  }

  // All retries exhausted
  throw lastError;
}

/**
 * Polls a function until it returns a truthy value or timeout
 *
 * @param fn Function to poll (should return null/undefined while waiting)
 * @param options Polling configuration
 * @returns Result when available
 */
export async function pollUntil<T>(
  fn: () => Promise<T | null | undefined>,
  options: {
    timeoutMs: number;
    initialDelayMs?: number;
    maxDelayMs?: number;
    onPoll?: (attempt: number) => void;
  }
): Promise<T> {
  const startTime = Date.now();
  const initialDelay = options.initialDelayMs ?? RETRY_CONFIG.INITIAL_DELAY_MS;
  const maxDelay = options.maxDelayMs ?? RETRY_CONFIG.MAX_DELAY_MS;

  let attempt = 0;

  while (true) {
    // Check timeout
    const elapsed = Date.now() - startTime;
    if (elapsed >= options.timeoutMs) {
      throw new TimeoutError(
        `Polling timeout after ${options.timeoutMs}ms`,
        options.timeoutMs
      );
    }

    // Try to get result
    const result = await fn();
    if (result !== null && result !== undefined) {
      return result;
    }

    // Notify caller
    if (options.onPoll) {
      options.onPoll(attempt);
    }

    // Calculate next delay with exponential backoff
    const delayMs = Math.min(
      initialDelay * Math.pow(1.5, attempt),
      maxDelay
    );

    // Don't sleep longer than remaining time
    const remainingTime = options.timeoutMs - elapsed;
    const actualDelay = Math.min(delayMs, remainingTime);

    if (actualDelay > 0) {
      await sleep(actualDelay);
    }

    attempt++;
  }
}
