/**
 * Ascend AI Governance Platform - Client
 * Enterprise-grade API client with banking-level security
 *
 * @module client
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import https from 'https';
import {
  ClientConfig,
  AgentAction,
  ActionResult,
  ListParams,
  ListResult,
  ConnectionStatus,
  ActionStatus,
} from './types';
import {
  DEFAULT_API_URL,
  DEFAULT_TIMEOUT_MS,
  DEFAULT_MAX_RETRIES,
  DEFAULT_PAGE_LIMIT,
  ENDPOINTS,
  HEADERS,
  SDK_USER_AGENT,
  ENV_VARS,
  POLLING_CONFIG,
} from './constants';
import {
  AuthenticationError,
  AuthorizationDeniedError,
  handleApiError,
  TimeoutError,
} from './errors';
import {
  generateCorrelationId,
  maskString,
  withRetry,
  pollUntil,
  validateApiKey,
  validateAgentAction,
  validateListParams,
  validateActionId,
  validateClientConfig,
  getEnv,
} from './utils';

/**
 * Main client for Ascend AI Governance Platform
 *
 * @example
 * ```typescript
 * const client = new AscendClient({
 *   apiKey: 'owkai_admin_...',
 *   baseUrl: 'https://pilot.owkai.app'
 * });
 *
 * const result = await client.submitAction({
 *   agent_id: 'gpt-4',
 *   agent_name: 'Customer Support Bot',
 *   action_type: 'data_access',
 *   resource: 'customer_database',
 *   resource_id: 'user_12345'
 * });
 * ```
 */
export class AscendClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly timeout: number;
  private readonly maxRetries: number;
  private readonly debug: boolean;
  private readonly httpClient: AxiosInstance;

  /**
   * Creates a new Ascend client
   *
   * @param config Client configuration options
   */
  constructor(config: ClientConfig = {}) {
    // Validate configuration
    validateClientConfig(config);

    // Get API key from config or environment
    this.apiKey = config.apiKey || getEnv(ENV_VARS.API_KEY) || '';
    if (!this.apiKey) {
      throw AuthenticationError.missingApiKey();
    }
    validateApiKey(this.apiKey);

    // Set configuration
    this.baseUrl = config.baseUrl || getEnv(ENV_VARS.API_URL) || DEFAULT_API_URL;
    this.timeout = config.timeout || DEFAULT_TIMEOUT_MS;
    this.maxRetries = config.maxRetries ?? DEFAULT_MAX_RETRIES;
    this.debug = config.debug || false;

    // Create Axios instance with TLS/HTTPS agent
    this.httpClient = axios.create({
      baseURL: this.baseUrl,
      timeout: this.timeout,
      headers: {
        [HEADERS.CONTENT_TYPE]: 'application/json',
        [HEADERS.USER_AGENT]: SDK_USER_AGENT,
      },
      httpsAgent: new https.Agent({
        rejectUnauthorized: true, // Enforce valid SSL certificates
        minVersion: 'TLSv1.2',    // Minimum TLS 1.2
      }),
    });

    this.log('Client initialized', {
      baseUrl: this.baseUrl,
      timeout: this.timeout,
      maxRetries: this.maxRetries,
      apiKey: maskString(this.apiKey),
    });
  }

  /**
   * Submits an agent action for authorization
   *
   * @param action Agent action details
   * @returns Action result with decision
   *
   * @example
   * ```typescript
   * const result = await client.submitAction({
   *   agent_id: 'gpt-4',
   *   agent_name: 'Financial Advisor Bot',
   *   action_type: 'transaction',
   *   resource: 'trading_system',
   *   action_details: { amount: 10000, symbol: 'AAPL' },
   *   risk_indicators: { unusual_amount: true }
   * });
   *
   * if (result.status === 'approved') {
   *   // Execute action
   * }
   * ```
   */
  async submitAction(action: AgentAction): Promise<ActionResult> {
    // Validate input
    validateAgentAction(action);

    const correlationId = generateCorrelationId();
    this.log('Submitting action', { action, correlationId });

    try {
      const result = await withRetry(
        async () => {
          const response = await this.request<ActionResult>({
            method: 'POST',
            url: ENDPOINTS.SUBMIT_ACTION,
            data: action,
            headers: {
              [HEADERS.CORRELATION_ID]: correlationId,
            },
          });
          return response;
        },
        { maxRetries: this.maxRetries },
        (attempt, error, delayMs) => {
          this.log(`Retry attempt ${attempt} after ${delayMs}ms`, { error: error.message });
        }
      );

      this.log('Action submitted successfully', { result });
      return result;
    } catch (error) {
      this.log('Failed to submit action', { error });
      throw handleApiError(error, correlationId);
    }
  }

  /**
   * Gets an action by ID
   *
   * @param actionId Action ID
   * @returns Action result
   */
  async getAction(actionId: number): Promise<ActionResult> {
    validateActionId(actionId);

    const correlationId = generateCorrelationId();
    this.log('Getting action', { actionId, correlationId });

    try {
      const result = await withRetry(
        async () => {
          const response = await this.request<ActionResult>({
            method: 'GET',
            url: `${ENDPOINTS.GET_ACTION}/${actionId}`,
            headers: {
              [HEADERS.CORRELATION_ID]: correlationId,
            },
          });
          return response;
        },
        { maxRetries: this.maxRetries }
      );

      return result;
    } catch (error) {
      throw handleApiError(error, correlationId);
    }
  }

  /**
   * Gets the current status of an action
   * Alias for getAction() for semantic clarity
   *
   * @param actionId Action ID
   * @returns Action result
   */
  async getActionStatus(actionId: number): Promise<ActionResult> {
    return this.getAction(actionId);
  }

  /**
   * Waits for a decision on an action (polls until approved/denied)
   *
   * @param actionId Action ID
   * @param timeoutMs Timeout in milliseconds (default: 5 minutes)
   * @returns Final action result
   *
   * @example
   * ```typescript
   * const submitted = await client.submitAction(action);
   *
   * if (submitted.requires_approval) {
   *   const final = await client.waitForDecision(submitted.id, 60000); // 1 minute
   *   console.log('Decision:', final.status);
   * }
   * ```
   */
  async waitForDecision(
    actionId: number,
    timeoutMs: number = POLLING_CONFIG.DEFAULT_TIMEOUT_MS
  ): Promise<ActionResult> {
    validateActionId(actionId);

    this.log('Waiting for decision', { actionId, timeoutMs });

    try {
      const result = await pollUntil(
        async () => {
          const current = await this.getAction(actionId);

          // Check if decision is final
          const finalStatuses: ActionStatus[] = ['approved', 'denied', 'timeout'];
          if (finalStatuses.includes(current.status)) {
            return current;
          }

          return null; // Still pending
        },
        {
          timeoutMs,
          initialDelayMs: POLLING_CONFIG.INITIAL_DELAY_MS,
          maxDelayMs: POLLING_CONFIG.MAX_DELAY_MS,
          onPoll: (attempt) => {
            this.log(`Polling attempt ${attempt}`, { actionId });
          },
        }
      );

      this.log('Decision received', { actionId, status: result.status });

      // Throw error if denied
      if (result.status === 'denied') {
        throw new AuthorizationDeniedError(
          result.reason || 'Action was denied by governance policy',
          result.id,
          result.reason
        );
      }

      return result;
    } catch (error) {
      if (error instanceof TimeoutError) {
        throw TimeoutError.pollingTimeout(timeoutMs, actionId);
      }
      throw error;
    }
  }

  /**
   * Lists actions with optional filters
   *
   * @param params Query parameters
   * @returns List of actions with pagination
   *
   * @example
   * ```typescript
   * const result = await client.listActions({
   *   status: 'approved',
   *   risk_level: 'high',
   *   page: 1,
   *   limit: 50
   * });
   *
   * console.log(`Found ${result.total} actions`);
   * result.actions.forEach(action => {
   *   console.log(`Action ${action.id}: ${action.status}`);
   * });
   * ```
   */
  async listActions(params: ListParams = {}): Promise<ListResult> {
    validateListParams(params);

    const correlationId = generateCorrelationId();
    this.log('Listing actions', { params, correlationId });

    // Build query parameters
    const queryParams: Record<string, string> = {
      page: String(params.page || 1),
      limit: String(params.limit || DEFAULT_PAGE_LIMIT),
    };

    if (params.status) queryParams.status = params.status;
    if (params.risk_level) queryParams.risk_level = params.risk_level;
    if (params.agent_id) queryParams.agent_id = params.agent_id;
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;

    try {
      const result = await withRetry(
        async () => {
          const response = await this.request<ListResult>({
            method: 'GET',
            url: ENDPOINTS.LIST_ACTIONS,
            params: queryParams,
            headers: {
              [HEADERS.CORRELATION_ID]: correlationId,
            },
          });
          return response;
        },
        { maxRetries: this.maxRetries }
      );

      return result;
    } catch (error) {
      throw handleApiError(error, correlationId);
    }
  }

  /**
   * Tests connection to Ascend API
   *
   * @returns Connection status
   *
   * @example
   * ```typescript
   * const status = await client.testConnection();
   * if (status.connected) {
   *   console.log(`Connected in ${status.latency_ms}ms`);
   * }
   * ```
   */
  async testConnection(): Promise<ConnectionStatus> {
    const correlationId = generateCorrelationId();
    const startTime = Date.now();

    try {
      await this.request({
        method: 'GET',
        url: ENDPOINTS.HEALTH_CHECK,
        headers: {
          [HEADERS.CORRELATION_ID]: correlationId,
        },
      });

      const latency = Date.now() - startTime;

      return {
        connected: true,
        latency_ms: latency,
      };
    } catch (error) {
      return {
        connected: false,
        latency_ms: Date.now() - startTime,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Internal method for making HTTP requests with dual authentication
   * SECURITY: Uses both Authorization header AND X-API-Key header
   */
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    // Add dual authentication headers (banking-level security)
    const headers = {
      ...config.headers,
      [HEADERS.AUTHORIZATION]: `Bearer ${this.apiKey}`,
      [HEADERS.API_KEY]: this.apiKey,
    };

    try {
      const response = await this.httpClient.request<T>({
        ...config,
        headers,
      });

      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Internal logging method
   */
  private log(message: string, data?: Record<string, unknown>): void {
    if (!this.debug) return;

    console.log(`[AscendClient] ${message}`, data || '');
  }
}
