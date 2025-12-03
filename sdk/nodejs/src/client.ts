/**
 * ASCEND SDK Client v2.0
 * ======================
 *
 * Enterprise-grade HTTP client for ASCEND AI Governance API.
 *
 * Features:
 * - Fail mode configuration (closed/open)
 * - Circuit breaker pattern
 * - HMAC-SHA256 request signing
 * - Agent registration and lifecycle
 * - Action completion/failure logging
 * - Approval workflow support
 * - Webhook configuration
 * - Structured JSON logging
 *
 * Compliance: SOC 2 CC6.1, HIPAA 164.312(e), PCI-DSS 8.2, NIST AI RMF
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import * as crypto from 'crypto';
import {
  AgentAction,
  AuthorizationDecision,
  ActionDetails,
  ActionListResponse,
  DecisionStatus,
  Decision,
  BatchOptions,
  BatchResponse,
  BatchActionResult,
  toApiPayload,
  parseDecision,
} from './models';
import {
  OWKAIError,
  AuthenticationError,
  AuthorizationError,
  TimeoutError,
  RateLimitError,
  ValidationError,
  ConnectionError,
  CircuitBreakerOpenError,
} from './errors';
import { MetricsCollector, MetricsSnapshot, MetricEvent, MetricsCallback } from './metrics';
import {
  InterceptorManager,
  RequestConfig,
  ResponseData,
  generateRequestId,
} from './interceptors';

// ============================================================
// Fail Mode Configuration
// ============================================================

/**
 * Fail mode determines behavior when ASCEND is unreachable.
 *
 * CLOSED: Block all actions when ASCEND is down (secure default)
 * OPEN: Allow actions when ASCEND is down (fail-open for availability)
 */
export enum FailMode {
  /** Block actions when ASCEND is unreachable (recommended for production) */
  CLOSED = 'closed',
  /** Allow actions when ASCEND is unreachable (use with caution) */
  OPEN = 'open',
}

// ============================================================
// Circuit Breaker Pattern
// ============================================================

export enum CircuitState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open',
}

export interface CircuitBreakerOptions {
  /** Number of failures before opening circuit */
  failureThreshold?: number;
  /** Seconds to wait before attempting recovery */
  recoveryTimeout?: number;
  /** Number of test requests in half-open state */
  halfOpenMaxCalls?: number;
}

/**
 * Circuit breaker for resilient API communication.
 *
 * Prevents cascading failures by failing fast when ASCEND is down.
 */
export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failures: number = 0;
  private lastFailureTime: number = 0;
  private halfOpenCalls: number = 0;

  private readonly failureThreshold: number;
  private readonly recoveryTimeout: number;
  private readonly halfOpenMaxCalls: number;

  constructor(options: CircuitBreakerOptions = {}) {
    this.failureThreshold = options.failureThreshold ?? 5;
    this.recoveryTimeout = options.recoveryTimeout ?? 30;
    this.halfOpenMaxCalls = options.halfOpenMaxCalls ?? 3;
  }

  getState(): CircuitState {
    return this.state;
  }

  getFailures(): number {
    return this.failures;
  }

  recordSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      // Successful call in half-open state closes the circuit
      this.state = CircuitState.CLOSED;
      this.failures = 0;
      this.halfOpenCalls = 0;
    } else if (this.state === CircuitState.CLOSED) {
      this.failures = Math.max(0, this.failures - 1);
    }
  }

  recordFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitState.HALF_OPEN) {
      // Failure in half-open state reopens the circuit
      this.state = CircuitState.OPEN;
      this.halfOpenCalls = 0;
    } else if (this.failures >= this.failureThreshold) {
      this.state = CircuitState.OPEN;
    }
  }

  allowRequest(): boolean {
    if (this.state === CircuitState.CLOSED) {
      return true;
    }

    if (this.state === CircuitState.OPEN) {
      const elapsed = (Date.now() - this.lastFailureTime) / 1000;
      if (elapsed >= this.recoveryTimeout) {
        // Transition to half-open state
        this.state = CircuitState.HALF_OPEN;
        this.halfOpenCalls = 0;
        return true;
      }
      return false;
    }

    // Half-open: allow limited test requests
    if (this.halfOpenCalls < this.halfOpenMaxCalls) {
      this.halfOpenCalls++;
      return true;
    }
    return false;
  }

  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failures = 0;
    this.lastFailureTime = 0;
    this.halfOpenCalls = 0;
  }
}

// ============================================================
// Structured Logger
// ============================================================

export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';

export interface AscendLoggerOptions {
  level?: LogLevel;
  jsonFormat?: boolean;
  maskApiKeys?: boolean;
}

/**
 * Structured JSON logger with API key masking.
 */
export class AscendLogger {
  private readonly level: LogLevel;
  private readonly jsonFormat: boolean;
  private readonly maskApiKeys: boolean;
  private readonly levels: Record<LogLevel, number> = {
    DEBUG: 10,
    INFO: 20,
    WARNING: 30,
    ERROR: 40,
  };

  constructor(options: AscendLoggerOptions = {}) {
    this.level = options.level ?? 'INFO';
    this.jsonFormat = options.jsonFormat ?? true;
    this.maskApiKeys = options.maskApiKeys ?? true;
  }

  private shouldLog(level: LogLevel): boolean {
    return this.levels[level] >= this.levels[this.level];
  }

  private maskSensitive(data: unknown): unknown {
    if (!this.maskApiKeys) return data;

    if (typeof data === 'string') {
      // Mask API keys
      return data.replace(/owkai_[a-zA-Z0-9_]+/g, 'owkai_****');
    }

    if (Array.isArray(data)) {
      return data.map((item) => this.maskSensitive(item));
    }

    if (data && typeof data === 'object') {
      const masked: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(data)) {
        if (['api_key', 'apiKey', 'authorization', 'secret', 'password', 'token'].includes(key.toLowerCase())) {
          masked[key] = '****';
        } else {
          masked[key] = this.maskSensitive(value);
        }
      }
      return masked;
    }

    return data;
  }

  private formatMessage(level: LogLevel, message: string, extra: Record<string, unknown> = {}): string {
    const timestamp = new Date().toISOString();
    const maskedExtra = this.maskSensitive(extra) as Record<string, unknown>;

    if (this.jsonFormat) {
      return JSON.stringify({
        timestamp,
        level,
        logger: 'ascend_sdk',
        message,
        ...maskedExtra,
      });
    }

    const extraStr = Object.keys(extra).length > 0 ? ` ${JSON.stringify(maskedExtra)}` : '';
    return `${timestamp} [${level}] ascend_sdk: ${message}${extraStr}`;
  }

  debug(message: string, extra: Record<string, unknown> = {}): void {
    if (this.shouldLog('DEBUG')) {
      console.log(this.formatMessage('DEBUG', message, extra));
    }
  }

  info(message: string, extra: Record<string, unknown> = {}): void {
    if (this.shouldLog('INFO')) {
      console.log(this.formatMessage('INFO', message, extra));
    }
  }

  warning(message: string, extra: Record<string, unknown> = {}): void {
    if (this.shouldLog('WARNING')) {
      console.warn(this.formatMessage('WARNING', message, extra));
    }
  }

  error(message: string, extra: Record<string, unknown> = {}): void {
    if (this.shouldLog('ERROR')) {
      console.error(this.formatMessage('ERROR', message, extra));
    }
  }
}

// ============================================================
// Client Configuration
// ============================================================

/**
 * Legacy client configuration options (v1.0)
 */
export interface OWKAIClientOptions {
  /** API endpoint URL */
  apiUrl?: string;
  /** Organization API key */
  apiKey?: string;
  /** Organization identifier */
  organizationSlug?: string;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Maximum retry attempts */
  maxRetries?: number;
  /** Enable debug logging */
  debug?: boolean;
  /** SEC-054: Enable metrics collection */
  enableMetrics?: boolean;
  /** SEC-054: Metrics window in milliseconds (default: 5 minutes) */
  metricsWindow?: number;
  /** SEC-054: Max metrics events to store (default: 10000) */
  maxMetricsEvents?: number;
}

/**
 * AscendClient configuration options (v2.0)
 */
export interface AscendClientOptions {
  /** API endpoint URL */
  apiUrl?: string;
  /** Organization API key */
  apiKey: string;
  /** Unique agent identifier */
  agentId: string;
  /** Human-readable agent name */
  agentName: string;
  /** Environment (production/staging/development) */
  environment?: string;
  /** Fail mode when ASCEND is unreachable */
  failMode?: FailMode;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Maximum retry attempts */
  maxRetries?: number;
  /** Enable debug logging */
  debug?: boolean;
  /** Log level */
  logLevel?: LogLevel;
  /** Use JSON format for logs */
  jsonLogs?: boolean;
  /** Enable metrics collection */
  enableMetrics?: boolean;
  /** Circuit breaker options */
  circuitBreakerOptions?: CircuitBreakerOptions;
  /** Secret for HMAC signing (optional) */
  signingSecret?: string;
}

const DEFAULT_API_URL = 'https://pilot.owkai.app';
const DEFAULT_TIMEOUT = 30000;
const DEFAULT_MAX_RETRIES = 3;

/**
 * OW-AI Authorization Center SDK Client
 *
 * Enterprise-grade client for submitting agent actions
 * for authorization and policy enforcement.
 *
 * @example
 * ```typescript
 * const client = new OWKAIClient({ apiKey: 'your-api-key' });
 *
 * // Test connection
 * const status = await client.testConnection();
 *
 * // Submit action
 * const decision = await client.submitAction({
 *   agentId: 'agent-001',
 *   agentName: 'My Agent',
 *   actionType: ActionType.DATA_ACCESS,
 *   resource: 'customer_data'
 * });
 * ```
 */
export class OWKAIClient {
  private readonly apiUrl: string;
  private readonly apiKey: string;
  private readonly organizationSlug?: string;
  private readonly timeout: number;
  private readonly maxRetries: number;
  private readonly debug: boolean;
  private readonly client: AxiosInstance;

  /** SEC-054: Metrics collector instance */
  private readonly metricsCollector: MetricsCollector | null;

  /** SEC-054: Request/response interceptors */
  readonly interceptors: InterceptorManager;

  /**
   * Initialize the OW-AI client
   *
   * @param options - Client configuration options
   * @throws Error if API key is not provided
   */
  constructor(options: OWKAIClientOptions = {}) {
    this.apiUrl = options.apiUrl || process.env.OWKAI_API_URL || DEFAULT_API_URL;
    this.apiKey = options.apiKey || process.env.OWKAI_API_KEY || '';
    this.organizationSlug = options.organizationSlug || process.env.OWKAI_ORG_SLUG;
    this.timeout = options.timeout || DEFAULT_TIMEOUT;
    this.maxRetries = options.maxRetries || DEFAULT_MAX_RETRIES;
    this.debug = options.debug || process.env.DEBUG === 'true';

    if (!this.apiKey) {
      throw new Error(
        'API key is required. Pass apiKey option or set OWKAI_API_KEY environment variable.'
      );
    }

    // SEC-054: Initialize metrics collector
    const enableMetrics = options.enableMetrics !== false; // Enabled by default
    this.metricsCollector = enableMetrics
      ? new MetricsCollector({
          maxEvents: options.maxMetricsEvents || 10000,
          windowMs: options.metricsWindow || 300000,
        })
      : null;

    // SEC-054: Initialize interceptors
    this.interceptors = new InterceptorManager();

    this.client = axios.create({
      baseURL: this.apiUrl,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        Authorization: `Bearer ${this.apiKey}`,
        'User-Agent': 'owkai-sdk/1.0.0 NodeJS',
      },
    });

    this.log(`OW-AI Client initialized for ${this.apiUrl}`);
  }

  private log(message: string, ...args: unknown[]): void {
    if (this.debug) {
      console.log(`[OWKAI] ${message}`, ...args);
    }
  }

  /**
   * Make authenticated request with retry logic, metrics, and interceptors
   */
  private async request<T = Record<string, unknown>>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    data?: Record<string, unknown>,
    params?: Record<string, unknown>,
    retryCount: number = 0
  ): Promise<T> {
    const startTime = Date.now();
    const requestId = generateRequestId();

    this.log(`${method.toUpperCase()} ${endpoint} [${requestId}]`);

    // SEC-054: Build request config for interceptors
    let requestConfig: RequestConfig = {
      method: method.toUpperCase(),
      url: endpoint,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        Authorization: `Bearer ${this.apiKey}`,
        'User-Agent': 'owkai-sdk/1.0.0 NodeJS',
        'X-Request-ID': requestId,
      },
      data,
      params,
      timestamp: new Date(),
      requestId,
    };

    try {
      // SEC-054: Run request interceptors
      requestConfig = await this.interceptors.runRequestInterceptors(requestConfig);

      const response = await this.client.request<T>({
        method,
        url: requestConfig.url,
        data: requestConfig.data,
        params: requestConfig.params,
        headers: requestConfig.headers,
      });

      const duration = Date.now() - startTime;

      // SEC-054: Record metrics
      if (this.metricsCollector) {
        this.metricsCollector.recordRequest(method, endpoint, duration, response.status);
      }

      // SEC-054: Run response interceptors
      const responseData: ResponseData = {
        status: response.status,
        headers: response.headers as Record<string, string>,
        data: response.data as Record<string, unknown>,
        config: requestConfig,
        duration,
      };
      await this.interceptors.runResponseInterceptors(responseData);

      return response.data;
    } catch (error) {
      const duration = Date.now() - startTime;
      return this.handleError(error as AxiosError, method, endpoint, data, params, retryCount, duration, requestConfig);
    }
  }

  /**
   * Handle API errors with retries and metrics tracking
   */
  private async handleError<T>(
    error: AxiosError,
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    data?: Record<string, unknown>,
    params?: Record<string, unknown>,
    retryCount: number = 0,
    duration: number = 0,
    requestConfig?: RequestConfig
  ): Promise<T> {
    if (error.response) {
      const status = error.response.status;
      const responseData = error.response.data as Record<string, unknown>;

      // SEC-054: Record error metrics
      if (this.metricsCollector) {
        this.metricsCollector.recordError(method, endpoint, duration, error.message, status);
      }

      if (status === 401) {
        throw new AuthenticationError('Invalid or expired API key', { status });
      }

      if (status === 403) {
        throw new AuthorizationError(
          String(responseData.detail || 'Access denied'),
          responseData.policy_violations as string[] | undefined,
          responseData.risk_score as number | undefined
        );
      }

      if (status === 429) {
        const MAX_RETRY_AFTER_SECONDS = 300; // Cap at 5 minutes to prevent DoS
        const retryAfterRaw = parseInt(error.response.headers['retry-after'] || '60', 10);
        const retryAfter = Math.min(retryAfterRaw, MAX_RETRY_AFTER_SECONDS);
        if (retryCount < this.maxRetries) {
          this.log(`Rate limited. Retrying in ${retryAfter}s (requested: ${retryAfterRaw}s)...`);
          // SEC-054: Record retry metrics
          if (this.metricsCollector) {
            this.metricsCollector.recordRetry(method, endpoint, retryCount + 1, 'rate_limited');
          }
          await this.sleep(retryAfter * 1000);
          return this.request<T>(method, endpoint, data, params, retryCount + 1);
        }
        throw new RateLimitError('Rate limit exceeded', retryAfter);
      }

      if (status === 400 || status === 422) {
        throw new ValidationError(
          String(responseData.detail || 'Validation failed'),
          responseData.errors as Record<string, string> | undefined
        );
      }

      if (status >= 500) {
        if (retryCount < this.maxRetries) {
          const waitTime = Math.pow(2, retryCount) * 1000;
          this.log(`Server error. Retrying in ${waitTime}ms...`);
          // SEC-054: Record retry metrics
          if (this.metricsCollector) {
            this.metricsCollector.recordRetry(method, endpoint, retryCount + 1, 'server_error');
          }
          await this.sleep(waitTime);
          return this.request<T>(method, endpoint, data, params, retryCount + 1);
        }
        throw new OWKAIError('Server error', 'SERVER_ERROR', { status });
      }
    }

    if (error.code === 'ECONNABORTED') {
      // SEC-054: Record timeout metrics
      if (this.metricsCollector) {
        this.metricsCollector.recordTimeout(method, endpoint, duration);
      }
      throw new TimeoutError(`Request timed out after ${this.timeout}ms`, this.timeout);
    }

    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      if (retryCount < this.maxRetries) {
        const waitTime = Math.pow(2, retryCount) * 1000;
        this.log(`Connection failed. Retrying in ${waitTime}ms...`);
        // SEC-054: Record retry metrics
        if (this.metricsCollector) {
          this.metricsCollector.recordRetry(method, endpoint, retryCount + 1, 'connection_failed');
        }
        await this.sleep(waitTime);
        return this.request<T>(method, endpoint, data, params, retryCount + 1);
      }
      // SEC-054: Record error metrics
      if (this.metricsCollector) {
        this.metricsCollector.recordError(method, endpoint, duration, 'connection_failed');
      }
      throw new ConnectionError(`Failed to connect to ${this.apiUrl}`);
    }

    // SEC-054: Record generic error metrics
    if (this.metricsCollector) {
      this.metricsCollector.recordError(method, endpoint, duration, error.message);
    }
    throw new OWKAIError(error.message, 'REQUEST_ERROR', { originalError: error.message });
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Test API connectivity and authentication
   *
   * @returns Connection status and API info
   */
  async testConnection(): Promise<{
    status: 'connected' | 'error';
    apiVersion?: string;
    environment?: string;
    organization?: string;
    error?: string;
  }> {
    try {
      await this.request('get', '/health');
      const deployment = await this.request<Record<string, unknown>>('get', '/api/deployment-info');

      return {
        status: 'connected',
        apiVersion: String(deployment.version || 'unknown'),
        environment: String(deployment.environment || 'unknown'),
        organization: this.organizationSlug,
      };
    } catch (error) {
      return {
        status: 'error',
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Submit an agent action for authorization
   *
   * @param action - Agent action to submit
   * @returns Authorization decision
   */
  async submitAction(action: AgentAction): Promise<AuthorizationDecision> {
    this.log(`Submitting action: ${action.actionType} on ${action.resource}`);

    const response = await this.request<Record<string, unknown>>(
      'post',
      '/api/authorization/agent-action',
      toApiPayload(action)
    );

    const decision = parseDecision(response);
    this.log(`Action submitted: ${decision.actionId} - Status: ${decision.decision}`);

    return decision;
  }

  /**
   * Get the current status of an action
   *
   * @param actionId - Action ID to check
   * @returns Current authorization decision
   */
  async getActionStatus(actionId: string): Promise<AuthorizationDecision> {
    const response = await this.request<Record<string, unknown>>(
      'get',
      `/api/agent-action/status/${actionId}`
    );
    return parseDecision(response);
  }

  /**
   * Wait for an authorization decision
   *
   * @param actionId - Action ID to wait for
   * @param timeout - Maximum wait time in milliseconds
   * @param pollInterval - Polling interval in milliseconds
   * @returns Final authorization decision
   * @throws TimeoutError if decision not received within timeout
   */
  async waitForDecision(
    actionId: string,
    timeout: number = 60000,
    pollInterval: number = 2000
  ): Promise<AuthorizationDecision> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const decision = await this.getActionStatus(actionId);

      if (decision.decision !== DecisionStatus.PENDING) {
        return decision;
      }

      this.log(`Action ${actionId} still pending...`);
      await this.sleep(pollInterval);
    }

    throw new TimeoutError(`Decision not received within ${timeout}ms`, timeout);
  }

  /**
   * Get detailed information about an action
   *
   * @param actionId - Action ID
   * @returns Full action details
   */
  async getActionDetails(actionId: string): Promise<ActionDetails> {
    const response = await this.request<Record<string, unknown>>(
      'get',
      `/api/agent-action/${actionId}`
    );

    return {
      actionId: String(response.id || response.action_id || ''),
      agentId: String(response.agent_id || ''),
      agentName: String(response.agent_name || ''),
      actionType: String(response.action_type || ''),
      resource: String(response.resource || ''),
      resourceId: response.resource_id as string | undefined,
      status: (response.status || 'pending') as DecisionStatus,
      riskScore: response.risk_score as number | undefined,
      createdAt: response.created_at as string | undefined,
      updatedAt: response.updated_at as string | undefined,
      auditTrail: response.audit_trail as ActionDetails['auditTrail'],
    };
  }

  /**
   * List recent agent actions
   *
   * @param options - Query options
   * @returns List of actions with pagination
   */
  async listActions(options: {
    limit?: number;
    offset?: number;
    status?: string;
    agentId?: string;
  } = {}): Promise<ActionListResponse> {
    const params: Record<string, unknown> = {
      limit: options.limit || 50,
      offset: options.offset || 0,
    };

    if (options.status) params.status = options.status;
    if (options.agentId) params.agent_id = options.agentId;

    return this.request<ActionListResponse>('get', '/api/agent-activity', undefined, params);
  }

  /**
   * Approve a pending action (requires admin privileges)
   *
   * @param actionId - Action ID to approve
   * @param comments - Optional approval comments
   * @returns Updated authorization decision
   */
  async approveAction(actionId: string, comments?: string): Promise<AuthorizationDecision> {
    const response = await this.request<Record<string, unknown>>(
      'post',
      `/api/authorization/authorize/${actionId}`,
      {
        approved: true,
        comments: comments || 'Approved via SDK',
      }
    );
    return parseDecision(response);
  }

  /**
   * Deny a pending action (requires admin privileges)
   *
   * @param actionId - Action ID to deny
   * @param reason - Reason for denial
   * @returns Updated authorization decision
   */
  async denyAction(actionId: string, reason: string): Promise<AuthorizationDecision> {
    const response = await this.request<Record<string, unknown>>(
      'post',
      `/api/authorization/authorize/${actionId}`,
      {
        approved: false,
        comments: reason,
      }
    );
    return parseDecision(response);
  }

  // ============================================================
  // SEC-054: Batch Action Submission
  // ============================================================

  /**
   * Submit multiple actions for authorization in a single batch
   *
   * Supports parallel or sequential processing with error handling options.
   *
   * @param actions - Array of agent actions to submit
   * @param options - Batch processing options
   * @returns Batch response with results for each action
   *
   * @example
   * ```typescript
   * const results = await client.submitActionBatch([
   *   { agentId: 'agent-1', agentName: 'Agent 1', actionType: 'data_access', resource: 'db1' },
   *   { agentId: 'agent-2', agentName: 'Agent 2', actionType: 'transaction', resource: 'payments' }
   * ], { parallel: true, continueOnError: true });
   *
   * console.log(`Success: ${results.successCount}/${results.totalSubmitted}`);
   * ```
   */
  async submitActionBatch(
    actions: AgentAction[],
    options: BatchOptions = {}
  ): Promise<BatchResponse> {
    const startTime = Date.now();
    const {
      parallel = true,
      timeout = this.timeout * actions.length,
      continueOnError = true,
      waitForDecisions = false,
    } = options;

    this.log(`Submitting batch of ${actions.length} actions (parallel: ${parallel})`);

    const results: BatchActionResult[] = [];

    if (parallel) {
      // Process all actions in parallel
      const promises = actions.map(async (action, index) => {
        try {
          const decision = await this.submitAction(action);

          // Optionally wait for decision
          let finalDecision = decision;
          if (waitForDecisions && decision.decision === DecisionStatus.PENDING) {
            finalDecision = await this.waitForDecision(decision.actionId, timeout / actions.length);
          }

          return {
            index,
            actionId: finalDecision.actionId,
            decision: finalDecision,
            success: true,
          } as BatchActionResult;
        } catch (error) {
          const err = error as Error;
          return {
            index,
            success: false,
            error: {
              code: (err as OWKAIError).code || 'UNKNOWN_ERROR',
              message: err.message,
            },
          } as BatchActionResult;
        }
      });

      const settledResults = await Promise.all(promises);
      results.push(...settledResults);
    } else {
      // Process actions sequentially
      for (let i = 0; i < actions.length; i++) {
        try {
          const decision = await this.submitAction(actions[i]);

          // Optionally wait for decision
          let finalDecision = decision;
          if (waitForDecisions && decision.decision === DecisionStatus.PENDING) {
            finalDecision = await this.waitForDecision(decision.actionId, timeout / actions.length);
          }

          results.push({
            index: i,
            actionId: finalDecision.actionId,
            decision: finalDecision,
            success: true,
          });
        } catch (error) {
          const err = error as Error;
          results.push({
            index: i,
            success: false,
            error: {
              code: (err as OWKAIError).code || 'UNKNOWN_ERROR',
              message: err.message,
            },
          });

          if (!continueOnError) {
            break;
          }
        }
      }
    }

    const duration = Date.now() - startTime;
    const successCount = results.filter((r) => r.success).length;
    const errorCount = results.filter((r) => !r.success).length;

    this.log(`Batch complete: ${successCount}/${actions.length} succeeded in ${duration}ms`);

    return {
      results,
      totalSubmitted: actions.length,
      successCount,
      errorCount,
      duration,
      allSucceeded: errorCount === 0,
    };
  }

  // ============================================================
  // SEC-054: Metrics API
  // ============================================================

  /**
   * Get current metrics snapshot
   *
   * Returns aggregated metrics for the current time window including
   * request counts, latency percentiles, error rates, and more.
   *
   * @returns Metrics snapshot
   *
   * @example
   * ```typescript
   * const metrics = client.getMetrics();
   * console.log(`Success rate: ${(metrics.successRate * 100).toFixed(1)}%`);
   * console.log(`P95 latency: ${metrics.p95Latency}ms`);
   * console.log(`Requests/min: ${metrics.requestsPerMinute}`);
   * ```
   */
  getMetrics(): MetricsSnapshot | null {
    if (!this.metricsCollector) {
      return null;
    }
    return this.metricsCollector.getSnapshot();
  }

  /**
   * Register callback for real-time metrics events
   *
   * Useful for integrating with external monitoring systems like
   * Datadog, Prometheus, or custom dashboards.
   *
   * @param callback - Function to call on each metric event
   * @returns Unsubscribe function
   *
   * @example
   * ```typescript
   * // Send metrics to Datadog
   * const unsubscribe = client.onMetricEvent((event) => {
   *   datadogClient.gauge('owkai.sdk.latency', event.duration, {
   *     endpoint: event.endpoint,
   *     method: event.method,
   *   });
   * });
   *
   * // Later: stop sending metrics
   * unsubscribe();
   * ```
   */
  onMetricEvent(callback: MetricsCallback): () => void {
    if (!this.metricsCollector) {
      return () => {}; // No-op if metrics disabled
    }
    return this.metricsCollector.onEvent(callback);
  }

  /**
   * Reset all collected metrics
   *
   * Useful for testing or when starting a new measurement period.
   */
  resetMetrics(): void {
    if (this.metricsCollector) {
      this.metricsCollector.reset();
    }
  }
}

// ============================================================
// ASCEND Client v2.0
// ============================================================

/**
 * Authorization decision result
 */
export interface EvaluateActionResult {
  decision: Decision;
  actionId: string;
  reason?: string;
  riskScore?: number;
  policyViolations: string[];
  conditions: string[];
  approvalRequestId?: string;
  requiredApprovers: string[];
  expiresAt?: string;
  metadata: Record<string, unknown>;
}

/**
 * Agent registration response
 */
export interface RegisterResponse {
  agentId: string;
  status: string;
  registeredAt: string;
  capabilities: string[];
  metadata?: Record<string, unknown>;
}

/**
 * Action completion response
 */
export interface ActionLogResponse {
  actionId: string;
  status: string;
  loggedAt: string;
}

/**
 * Approval status response
 */
export interface ApprovalStatusResponse {
  approvalRequestId: string;
  status: 'pending' | 'approved' | 'rejected';
  approvedBy?: string;
  rejectedBy?: string;
  rejectionReason?: string;
  decidedAt?: string;
}

/**
 * Webhook configuration response
 */
export interface WebhookConfigResponse {
  webhookId: string;
  url: string;
  events: string[];
  status: string;
  createdAt: string;
}

/**
 * ASCEND Enterprise SDK Client v2.0
 *
 * Production-ready client for AI agent governance with enterprise features:
 * - Fail mode configuration (closed/open)
 * - Circuit breaker pattern for resilience
 * - HMAC-SHA256 request signing
 * - Agent registration and lifecycle
 * - Action completion/failure logging
 * - Approval workflow support
 * - Webhook configuration
 *
 * @example
 * ```typescript
 * const client = new AscendClient({
 *   apiKey: 'owkai_...',
 *   agentId: 'agent-001',
 *   agentName: 'My AI Agent',
 *   failMode: FailMode.CLOSED,
 * });
 *
 * // Register agent
 * await client.register({
 *   agentType: 'automation',
 *   capabilities: ['data_access', 'file_operations'],
 * });
 *
 * // Evaluate action
 * const decision = await client.evaluateAction({
 *   actionType: 'database.query',
 *   resource: 'production_db',
 *   parameters: { query: 'SELECT * FROM users' },
 * });
 *
 * if (decision.decision === Decision.ALLOWED) {
 *   const result = await executeQuery();
 *   await client.logActionCompleted(decision.actionId, result);
 * }
 * ```
 *
 * Compliance: SOC 2 CC6.1, HIPAA 164.312(e), PCI-DSS 8.2, NIST AI RMF
 */
export class AscendClient {
  private readonly apiUrl: string;
  private readonly apiKey: string;
  private readonly agentId: string;
  private readonly agentName: string;
  private readonly environment: string;
  private readonly failMode: FailMode;
  private readonly timeout: number;
  private readonly maxRetries: number;
  private readonly signingSecret?: string;
  private readonly client: AxiosInstance;
  private readonly logger: AscendLogger;
  private readonly circuitBreaker: CircuitBreaker;
  private readonly metricsCollector: MetricsCollector | null;

  constructor(options: AscendClientOptions) {
    this.apiUrl = options.apiUrl || process.env.ASCEND_API_URL || DEFAULT_API_URL;
    this.apiKey = options.apiKey;
    this.agentId = options.agentId;
    this.agentName = options.agentName;
    this.environment = options.environment || 'production';
    this.failMode = options.failMode ?? FailMode.CLOSED;
    this.timeout = options.timeout || DEFAULT_TIMEOUT;
    this.maxRetries = options.maxRetries || DEFAULT_MAX_RETRIES;
    this.signingSecret = options.signingSecret;

    // Initialize logger
    this.logger = new AscendLogger({
      level: options.logLevel ?? (options.debug ? 'DEBUG' : 'INFO'),
      jsonFormat: options.jsonLogs ?? true,
      maskApiKeys: true,
    });

    // Initialize circuit breaker
    this.circuitBreaker = new CircuitBreaker(options.circuitBreakerOptions);

    // Initialize metrics
    this.metricsCollector = options.enableMetrics !== false
      ? new MetricsCollector({ maxEvents: 10000, windowMs: 300000 })
      : null;

    // Create HTTP client
    this.client = axios.create({
      baseURL: this.apiUrl,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        Authorization: `Bearer ${this.apiKey}`,
        'User-Agent': 'ascend-sdk/2.0.0 NodeJS',
      },
    });

    this.logger.info('AscendClient initialized', {
      apiUrl: this.apiUrl,
      agentId: this.agentId,
      failMode: this.failMode,
      environment: this.environment,
    });
  }

  // ============================================================
  // HMAC Signing
  // ============================================================

  private generateSignature(payload: string, timestamp: string): string {
    if (!this.signingSecret) {
      return '';
    }

    const signatureBase = `${timestamp}.${payload}`;
    return crypto
      .createHmac('sha256', this.signingSecret)
      .update(signatureBase)
      .digest('hex');
  }

  private generateCorrelationId(): string {
    return `${this.agentId}-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
  }

  // ============================================================
  // Core Request Method
  // ============================================================

  private async request<T = Record<string, unknown>>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    data?: Record<string, unknown>,
    params?: Record<string, unknown>,
    retryCount: number = 0
  ): Promise<T> {
    const startTime = Date.now();
    const correlationId = this.generateCorrelationId();

    // Check circuit breaker
    if (!this.circuitBreaker.allowRequest()) {
      const error = new CircuitBreakerOpenError(
        'Circuit breaker is open - service appears to be down',
        Math.max(0, this.circuitBreaker['recoveryTimeout'] -
          (Date.now() - this.circuitBreaker['lastFailureTime']) / 1000)
      );

      this.logger.warning('Circuit breaker open', {
        endpoint,
        correlationId,
        circuitState: this.circuitBreaker.getState(),
      });

      throw error;
    }

    // Prepare headers
    const timestamp = new Date().toISOString();
    const payloadStr = data ? JSON.stringify(data) : '';
    const signature = this.generateSignature(payloadStr, timestamp);

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      Authorization: `Bearer ${this.apiKey}`,
      'User-Agent': 'ascend-sdk/2.0.0 NodeJS',
      'X-Correlation-ID': correlationId,
      'X-Timestamp': timestamp,
    };

    if (signature) {
      headers['X-Signature'] = signature;
    }

    this.logger.debug(`${method.toUpperCase()} ${endpoint}`, {
      correlationId,
      hasData: !!data,
    });

    try {
      const response = await this.client.request<T>({
        method,
        url: endpoint,
        data,
        params,
        headers,
      });

      const duration = Date.now() - startTime;
      this.circuitBreaker.recordSuccess();

      if (this.metricsCollector) {
        this.metricsCollector.recordRequest(method, endpoint, duration, response.status);
      }

      this.logger.debug(`Response received`, {
        correlationId,
        status: response.status,
        duration,
      });

      return response.data;
    } catch (error) {
      const duration = Date.now() - startTime;
      return this.handleError(error as AxiosError, method, endpoint, data, params, retryCount, duration, correlationId);
    }
  }

  private async handleError<T>(
    error: AxiosError,
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    data?: Record<string, unknown>,
    params?: Record<string, unknown>,
    retryCount: number = 0,
    duration: number = 0,
    correlationId: string = ''
  ): Promise<T> {
    this.circuitBreaker.recordFailure();

    if (error.response) {
      const status = error.response.status;
      const responseData = error.response.data as Record<string, unknown>;

      if (this.metricsCollector) {
        this.metricsCollector.recordError(method, endpoint, duration, error.message, status);
      }

      this.logger.error(`API error`, {
        correlationId,
        status,
        endpoint,
        message: responseData.detail || error.message,
      });

      if (status === 401) {
        throw new AuthenticationError('Invalid or expired API key', { status });
      }

      if (status === 403) {
        throw new AuthorizationError(
          String(responseData.detail || 'Access denied'),
          responseData.policy_violations as string[] | undefined,
          responseData.risk_score as number | undefined
        );
      }

      if (status === 429) {
        const MAX_RETRY_AFTER_SECONDS = 300; // Cap at 5 minutes to prevent DoS
        const retryAfterRaw = parseInt(error.response.headers['retry-after'] || '60', 10);
        const retryAfter = Math.min(retryAfterRaw, MAX_RETRY_AFTER_SECONDS);
        if (retryCount < this.maxRetries) {
          this.logger.warning(`Rate limited, retrying in ${retryAfter}s (requested: ${retryAfterRaw}s)`, { correlationId });
          await this.sleep(retryAfter * 1000);
          return this.request<T>(method, endpoint, data, params, retryCount + 1);
        }
        throw new RateLimitError('Rate limit exceeded', retryAfter);
      }

      if (status >= 500 && retryCount < this.maxRetries) {
        const waitTime = Math.pow(2, retryCount) * 1000;
        this.logger.warning(`Server error, retrying in ${waitTime}ms`, { correlationId });
        await this.sleep(waitTime);
        return this.request<T>(method, endpoint, data, params, retryCount + 1);
      }
    }

    if (error.code === 'ECONNABORTED') {
      throw new TimeoutError(`Request timed out after ${this.timeout}ms`, this.timeout);
    }

    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      if (retryCount < this.maxRetries) {
        const waitTime = Math.pow(2, retryCount) * 1000;
        this.logger.warning(`Connection failed, retrying in ${waitTime}ms`, { correlationId });
        await this.sleep(waitTime);
        return this.request<T>(method, endpoint, data, params, retryCount + 1);
      }
      throw new ConnectionError(`Failed to connect to ${this.apiUrl}`);
    }

    throw new OWKAIError(error.message, 'REQUEST_ERROR', { originalError: error.message });
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // ============================================================
  // Fail Mode Handling
  // ============================================================

  private handleFailMode(error: Error, actionType: string): EvaluateActionResult {
    if (this.failMode === FailMode.OPEN) {
      this.logger.warning('Fail-open: allowing action due to ASCEND unavailability', {
        actionType,
        error: error.message,
      });

      return {
        decision: Decision.ALLOWED,
        actionId: `failopen-${Date.now()}`,
        reason: 'Allowed due to ASCEND service unavailability (fail-open mode)',
        riskScore: undefined,
        policyViolations: [],
        conditions: ['fail_open_mode'],
        requiredApprovers: [],
        metadata: {
          failOpen: true,
          originalError: error.message,
        },
      };
    }

    // Fail closed - re-throw the error
    throw error;
  }

  // ============================================================
  // Agent Registration
  // ============================================================

  /**
   * Register this agent with ASCEND.
   *
   * Should be called on agent startup to establish presence.
   *
   * @param options - Registration options
   * @returns Registration response
   */
  async register(options: {
    agentType: string;
    capabilities: string[];
    allowedResources?: string[];
    metadata?: Record<string, unknown>;
  }): Promise<RegisterResponse> {
    this.logger.info('Registering agent', {
      agentId: this.agentId,
      agentType: options.agentType,
    });

    const response = await this.request<Record<string, unknown>>(
      'post',
      '/api/sdk/agent/register',
      {
        agent_id: this.agentId,
        agent_name: this.agentName,
        agent_type: options.agentType,
        capabilities: options.capabilities,
        allowed_resources: options.allowedResources,
        environment: this.environment,
        metadata: options.metadata,
      }
    );

    return {
      agentId: String(response.agent_id || this.agentId),
      status: String(response.status || 'registered'),
      registeredAt: String(response.registered_at || new Date().toISOString()),
      capabilities: (response.capabilities as string[]) || options.capabilities,
      metadata: response.metadata as Record<string, unknown>,
    };
  }

  // ============================================================
  // Action Evaluation
  // ============================================================

  /**
   * Evaluate an action for authorization.
   *
   * @param options - Action evaluation options
   * @returns Authorization decision
   */
  async evaluateAction(options: {
    actionType: string;
    resource: string;
    parameters?: Record<string, unknown>;
    context?: Record<string, unknown>;
    waitForApproval?: boolean;
    approvalTimeout?: number;
    riskLevel?: string;
    requireHumanApproval?: boolean;
  }): Promise<EvaluateActionResult> {
    const correlationId = this.generateCorrelationId();

    this.logger.info('Evaluating action', {
      correlationId,
      actionType: options.actionType,
      resource: options.resource,
    });

    try {
      const response = await this.request<Record<string, unknown>>(
        'post',
        '/api/authorization/agent-action',
        {
          agent_id: this.agentId,
          agent_name: this.agentName,
          action_type: options.actionType,
          resource: options.resource,
          action_details: options.parameters,
          context: {
            ...options.context,
            correlation_id: correlationId,
            environment: this.environment,
          },
          risk_level: options.riskLevel,
          require_human_approval: options.requireHumanApproval,
        }
      );

      // Map API response to v2.0 format
      const rawDecision = String(response.decision || response.status || 'pending');
      let decision: Decision;

      if (rawDecision === 'approved' || rawDecision === 'allowed') {
        decision = Decision.ALLOWED;
      } else if (rawDecision === 'denied') {
        decision = Decision.DENIED;
      } else {
        decision = Decision.PENDING;
      }

      const result: EvaluateActionResult = {
        decision,
        actionId: String(response.action_id || response.id || ''),
        reason: response.reason as string | undefined,
        riskScore: response.risk_score as number | undefined,
        policyViolations: (response.policy_violations as string[]) || [],
        conditions: (response.conditions as string[]) || [],
        approvalRequestId: response.approval_request_id as string | undefined,
        requiredApprovers: (response.required_approvers as string[]) || [],
        expiresAt: response.expires_at as string | undefined,
        metadata: (response.metadata as Record<string, unknown>) || {},
      };

      this.logger.info('Action evaluated', {
        correlationId,
        decision: result.decision,
        actionId: result.actionId,
        riskScore: result.riskScore,
      });

      // Handle pending with wait
      if (result.decision === Decision.PENDING && options.waitForApproval) {
        return this.waitForApprovalDecision(
          result.approvalRequestId!,
          options.approvalTimeout || 300000,
          result
        );
      }

      return result;
    } catch (error) {
      if (error instanceof ConnectionError ||
          error instanceof TimeoutError ||
          error instanceof CircuitBreakerOpenError) {
        return this.handleFailMode(error, options.actionType);
      }
      throw error;
    }
  }

  private async waitForApprovalDecision(
    approvalRequestId: string,
    timeout: number,
    initialResult: EvaluateActionResult
  ): Promise<EvaluateActionResult> {
    const startTime = Date.now();
    const pollInterval = 5000;

    this.logger.info('Waiting for approval decision', {
      approvalRequestId,
      timeout,
    });

    while (Date.now() - startTime < timeout) {
      await this.sleep(pollInterval);

      try {
        const status = await this.checkApproval(approvalRequestId);

        if (status.status === 'approved') {
          return {
            ...initialResult,
            decision: Decision.ALLOWED,
            reason: 'Approved by human reviewer',
            metadata: {
              ...initialResult.metadata,
              approvedBy: status.approvedBy,
            },
          };
        }

        if (status.status === 'rejected') {
          return {
            ...initialResult,
            decision: Decision.DENIED,
            reason: status.rejectionReason || 'Rejected by human reviewer',
            metadata: {
              ...initialResult.metadata,
              rejectedBy: status.rejectedBy,
            },
          };
        }
      } catch (error) {
        this.logger.warning('Error checking approval status', {
          approvalRequestId,
          error: (error as Error).message,
        });
      }
    }

    throw new TimeoutError(`Approval decision not received within ${timeout}ms`, timeout);
  }

  // ============================================================
  // Action Completion Logging
  // ============================================================

  /**
   * Log successful action completion.
   *
   * @param actionId - Action ID from evaluateAction
   * @param result - Action result/output
   * @param durationMs - Optional execution duration
   * @returns Log response
   */
  async logActionCompleted(
    actionId: string,
    result?: Record<string, unknown>,
    durationMs?: number
  ): Promise<ActionLogResponse> {
    this.logger.info('Logging action completion', {
      actionId,
      durationMs,
    });

    const response = await this.request<Record<string, unknown>>(
      'post',
      `/api/sdk/action/${actionId}/completed`,
      {
        status: 'completed',
        result: result ? { success: true, data: result } : { success: true },
        duration_ms: durationMs,
        completed_at: new Date().toISOString(),
      }
    );

    return {
      actionId,
      status: 'completed',
      loggedAt: String(response.logged_at || new Date().toISOString()),
    };
  }

  /**
   * Log action failure.
   *
   * @param actionId - Action ID from evaluateAction
   * @param error - Error message or object
   * @param durationMs - Optional execution duration
   * @returns Log response
   */
  async logActionFailed(
    actionId: string,
    error: string | Error,
    durationMs?: number
  ): Promise<ActionLogResponse> {
    const errorMessage = typeof error === 'string' ? error : error.message;

    this.logger.warning('Logging action failure', {
      actionId,
      error: errorMessage,
      durationMs,
    });

    const response = await this.request<Record<string, unknown>>(
      'post',
      `/api/sdk/action/${actionId}/failed`,
      {
        status: 'failed',
        error: errorMessage,
        duration_ms: durationMs,
        failed_at: new Date().toISOString(),
      }
    );

    return {
      actionId,
      status: 'failed',
      loggedAt: String(response.logged_at || new Date().toISOString()),
    };
  }

  // ============================================================
  // Approval Workflow
  // ============================================================

  /**
   * Check approval status.
   *
   * @param approvalRequestId - Approval request ID
   * @returns Approval status
   */
  async checkApproval(approvalRequestId: string): Promise<ApprovalStatusResponse> {
    const response = await this.request<Record<string, unknown>>(
      'get',
      `/api/sdk/approval/${approvalRequestId}`
    );

    return {
      approvalRequestId,
      status: (response.status as 'pending' | 'approved' | 'rejected') || 'pending',
      approvedBy: response.approved_by as string | undefined,
      rejectedBy: response.rejected_by as string | undefined,
      rejectionReason: response.rejection_reason as string | undefined,
      decidedAt: response.decided_at as string | undefined,
    };
  }

  // ============================================================
  // Webhook Configuration
  // ============================================================

  /**
   * Configure webhook for event notifications.
   *
   * @param options - Webhook configuration
   * @returns Webhook configuration response
   */
  async configureWebhook(options: {
    url: string;
    events: string[];
    secret?: string;
  }): Promise<WebhookConfigResponse> {
    this.logger.info('Configuring webhook', {
      url: options.url,
      events: options.events,
    });

    const response = await this.request<Record<string, unknown>>(
      'post',
      '/api/sdk/webhooks/configure',
      {
        agent_id: this.agentId,
        url: options.url,
        events: options.events,
        secret: options.secret,
      }
    );

    return {
      webhookId: String(response.webhook_id || ''),
      url: options.url,
      events: options.events,
      status: String(response.status || 'active'),
      createdAt: String(response.created_at || new Date().toISOString()),
    };
  }

  // ============================================================
  // Health & Diagnostics
  // ============================================================

  /**
   * Test connection to ASCEND API.
   *
   * @returns Connection status
   */
  async testConnection(): Promise<{
    status: 'connected' | 'error';
    apiVersion?: string;
    latency?: number;
    error?: string;
  }> {
    const startTime = Date.now();

    try {
      await this.request('get', '/health');
      const latency = Date.now() - startTime;

      return {
        status: 'connected',
        latency,
      };
    } catch (error) {
      return {
        status: 'error',
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Get current circuit breaker state.
   */
  getCircuitBreakerState(): {
    state: CircuitState;
    failures: number;
  } {
    return {
      state: this.circuitBreaker.getState(),
      failures: this.circuitBreaker.getFailures(),
    };
  }

  /**
   * Reset circuit breaker.
   */
  resetCircuitBreaker(): void {
    this.circuitBreaker.reset();
    this.logger.info('Circuit breaker reset');
  }

  /**
   * Get metrics snapshot.
   */
  getMetrics(): MetricsSnapshot | null {
    return this.metricsCollector?.getSnapshot() || null;
  }
}
