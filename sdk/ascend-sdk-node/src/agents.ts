/**
 * Ascend AI Governance Platform - Authorized Agent Wrapper
 * Simplified interface for agent authorization patterns
 *
 * @module agents
 */

import { AscendClient } from './client';
import {
  ActionType,
  ActionResult,
  AuthorizationOptions,
  ExecuteOptions,
} from './types';
import { AuthorizationDeniedError } from './errors';
import { POLLING_CONFIG } from './constants';

/**
 * Wrapper class for AI agents that need authorization
 * Simplifies the common pattern of request -> wait -> execute
 *
 * @example
 * ```typescript
 * const agent = new AuthorizedAgent(
 *   'gpt-4-customer-support',
 *   'Customer Support Bot'
 * );
 *
 * const result = await agent.executeIfAuthorized({
 *   authorization: {
 *     action_type: 'data_access',
 *     resource: 'customer_database',
 *     resource_id: 'user_12345'
 *   },
 *   action: async () => {
 *     return await database.getCustomer('user_12345');
 *   }
 * });
 * ```
 */
export class AuthorizedAgent {
  private readonly agentId: string;
  private readonly agentName: string;
  private readonly client: AscendClient;

  /**
   * Creates a new authorized agent wrapper
   *
   * @param agentId Unique identifier for the agent
   * @param agentName Human-readable agent name
   * @param client Optional AscendClient instance (creates default if not provided)
   */
  constructor(
    agentId: string,
    agentName: string,
    client?: AscendClient
  ) {
    this.agentId = agentId;
    this.agentName = agentName;
    this.client = client || new AscendClient();
  }

  /**
   * Requests authorization for an action
   * Does not wait for approval - use executeIfAuthorized() for automatic waiting
   *
   * @param options Authorization options
   * @returns Action result (may be pending)
   *
   * @example
   * ```typescript
   * const result = await agent.requestAuthorization({
   *   action_type: 'transaction',
   *   resource: 'payment_system',
   *   action_details: { amount: 10000 }
   * });
   *
   * if (result.requires_approval) {
   *   console.log('Waiting for approval...');
   * } else if (result.status === 'approved') {
   *   console.log('Approved immediately');
   * }
   * ```
   */
  async requestAuthorization(
    options: AuthorizationOptions
  ): Promise<ActionResult> {
    return await this.client.submitAction({
      agent_id: this.agentId,
      agent_name: this.agentName,
      action_type: options.action_type,
      resource: options.resource,
      resource_id: options.resource_id,
      action_details: options.action_details,
      context: options.context,
      risk_indicators: options.risk_indicators,
    });
  }

  /**
   * Requests authorization and executes action if approved
   * Automatically waits for approval if required
   *
   * @param options Execute options with action function
   * @returns Result of the action function
   *
   * @example
   * ```typescript
   * // Execute with automatic waiting
   * const customer = await agent.executeIfAuthorized({
   *   authorization: {
   *     action_type: 'data_access',
   *     resource: 'customer_database',
   *     resource_id: 'user_12345'
   *   },
   *   action: async () => {
   *     return await database.getCustomer('user_12345');
   *   },
   *   onDenied: (result) => {
   *     console.log('Access denied:', result.reason);
   *     return null; // Return fallback value
   *   }
   * });
   * ```
   */
  async executeIfAuthorized<T>(
    options: ExecuteOptions<T>
  ): Promise<T> {
    // Request authorization
    let result = await this.requestAuthorization(options.authorization);

    // If requires approval, wait for decision
    if (result.requires_approval) {
      if (options.onPending) {
        options.onPending(result);
      }

      const timeout = options.authorization.wait_timeout || POLLING_CONFIG.DEFAULT_TIMEOUT_MS;
      result = await this.client.waitForDecision(result.id, timeout);
    }

    // Handle denial
    if (result.status === 'denied') {
      if (options.onDenied) {
        return await Promise.resolve(options.onDenied(result));
      }
      throw new AuthorizationDeniedError(
        result.reason || 'Action was denied by governance policy',
        result.id,
        result.reason
      );
    }

    // Execute action if approved
    if (result.status === 'approved') {
      return await options.action();
    }

    // Timeout or unexpected status
    throw new Error(`Unexpected action status: ${result.status}`);
  }

  /**
   * Request authorization for data access
   * Convenience method with pre-filled action_type
   */
  async requestDataAccess(
    resource: string,
    resourceId?: string,
    context?: Record<string, unknown>
  ): Promise<ActionResult> {
    return this.requestAuthorization({
      action_type: 'data_access',
      resource,
      resource_id: resourceId,
      context,
    });
  }

  /**
   * Request authorization for data modification
   * Convenience method with pre-filled action_type
   */
  async requestDataModification(
    resource: string,
    resourceId?: string,
    details?: Record<string, unknown>,
    context?: Record<string, unknown>
  ): Promise<ActionResult> {
    return this.requestAuthorization({
      action_type: 'data_modification',
      resource,
      resource_id: resourceId,
      action_details: details,
      context,
    });
  }

  /**
   * Request authorization for transaction
   * Convenience method with pre-filled action_type
   */
  async requestTransaction(
    resource: string,
    details: Record<string, unknown>,
    resourceId?: string,
    riskIndicators?: Record<string, unknown>
  ): Promise<ActionResult> {
    return this.requestAuthorization({
      action_type: 'transaction',
      resource,
      resource_id: resourceId,
      action_details: details,
      risk_indicators: riskIndicators,
    });
  }

  /**
   * Request authorization for sending communication
   * Convenience method with pre-filled action_type
   */
  async requestCommunication(
    resource: string,
    details: Record<string, unknown>,
    context?: Record<string, unknown>
  ): Promise<ActionResult> {
    return this.requestAuthorization({
      action_type: 'communication',
      resource,
      action_details: details,
      context,
    });
  }

  /**
   * Request authorization for system operation
   * Convenience method with pre-filled action_type
   */
  async requestSystemOperation(
    resource: string,
    details: Record<string, unknown>,
    riskIndicators?: Record<string, unknown>
  ): Promise<ActionResult> {
    return this.requestAuthorization({
      action_type: 'system_operation',
      resource,
      action_details: details,
      risk_indicators: riskIndicators,
    });
  }

  /**
   * Gets the underlying client
   */
  getClient(): AscendClient {
    return this.client;
  }

  /**
   * Gets the agent ID
   */
  getAgentId(): string {
    return this.agentId;
  }

  /**
   * Gets the agent name
   */
  getAgentName(): string {
    return this.agentName;
  }
}
