/**
 * OW-AI SDK Client
 * ================
 *
 * Enterprise-grade HTTP client for OW-AI Authorization API.
 *
 * SEC-054 Enhancements:
 * - Batch action submission
 * - Metrics collection and telemetry
 * - Request/response interceptors
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import {
  AgentAction,
  AuthorizationDecision,
  ActionDetails,
  ActionListResponse,
  DecisionStatus,
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
} from './errors';
import { MetricsCollector, MetricsSnapshot, MetricEvent, MetricsCallback } from './metrics';
import {
  InterceptorManager,
  RequestConfig,
  ResponseData,
  generateRequestId,
} from './interceptors';

/**
 * Client configuration options
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
        const retryAfter = parseInt(error.response.headers['retry-after'] || '60', 10);
        if (retryCount < this.maxRetries) {
          this.log(`Rate limited. Retrying in ${retryAfter}s...`);
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
