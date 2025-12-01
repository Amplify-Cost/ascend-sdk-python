/**
 * OW-AI SDK Client
 * ================
 *
 * Enterprise-grade HTTP client for OW-AI Authorization API.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  AgentAction,
  AuthorizationDecision,
  ActionDetails,
  ActionListResponse,
  DecisionStatus,
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
   * Make authenticated request with retry logic
   */
  private async request<T = Record<string, unknown>>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    data?: Record<string, unknown>,
    params?: Record<string, unknown>,
    retryCount: number = 0
  ): Promise<T> {
    this.log(`${method.toUpperCase()} ${endpoint}`);

    try {
      const response = await this.client.request<T>({
        method,
        url: endpoint,
        data,
        params,
      });

      return response.data;
    } catch (error) {
      return this.handleError(error as AxiosError, method, endpoint, data, params, retryCount);
    }
  }

  /**
   * Handle API errors with retries
   */
  private async handleError<T>(
    error: AxiosError,
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    data?: Record<string, unknown>,
    params?: Record<string, unknown>,
    retryCount: number = 0
  ): Promise<T> {
    if (error.response) {
      const status = error.response.status;
      const responseData = error.response.data as Record<string, unknown>;

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
          await this.sleep(waitTime);
          return this.request<T>(method, endpoint, data, params, retryCount + 1);
        }
        throw new OWKAIError('Server error', 'SERVER_ERROR', { status });
      }
    }

    if (error.code === 'ECONNABORTED') {
      throw new TimeoutError(`Request timed out after ${this.timeout}ms`, this.timeout);
    }

    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      if (retryCount < this.maxRetries) {
        const waitTime = Math.pow(2, retryCount) * 1000;
        this.log(`Connection failed. Retrying in ${waitTime}ms...`);
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
}
