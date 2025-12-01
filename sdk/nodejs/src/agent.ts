/**
 * OW-AI SDK Authorized Agent
 * ==========================
 *
 * Wrapper for AI agents that require OW-AI authorization.
 */

import { OWKAIClient } from './client';
import {
  AgentAction,
  AuthorizationDecision,
  DecisionStatus,
  ActionType,
  RiskIndicators,
  ActionContext,
  ActionListResponse,
} from './models';
import { AuthorizationError, TimeoutError } from './errors';

/**
 * Options for authorization request
 */
export interface AuthorizationOptions {
  /** Type of action */
  actionType: ActionType | string;
  /** Resource being accessed */
  resource: string;
  /** Specific resource identifier */
  resourceId?: string;
  /** Additional action details */
  details?: Record<string, unknown>;
  /** Contextual information */
  context?: ActionContext;
  /** Risk assessment indicators */
  riskIndicators?: RiskIndicators;
  /** Whether to wait for decision */
  waitForDecision?: boolean;
  /** Decision timeout in milliseconds */
  timeout?: number;
}

/**
 * Wrapper for AI agents that require OW-AI authorization
 *
 * This class wraps your AI agent and automatically submits
 * actions for authorization before execution.
 *
 * @example
 * ```typescript
 * const agent = new AuthorizedAgent(
 *   'financial-advisor-001',
 *   'Financial Advisor AI'
 * );
 *
 * // Simple authorization check
 * const decision = await agent.requestAuthorization({
 *   actionType: ActionType.TRANSACTION,
 *   resource: 'customer_account',
 *   details: { amount: 10000 }
 * });
 *
 * // Execute only if authorized
 * const result = await agent.executeIfAuthorized(
 *   {
 *     actionType: ActionType.DATA_ACCESS,
 *     resource: 'portfolio'
 *   },
 *   () => fetchPortfolioData()
 * );
 * ```
 */
export class AuthorizedAgent {
  /** Unique agent identifier */
  readonly agentId: string;
  /** Human-readable agent name */
  readonly agentName: string;
  /** OW-AI client instance */
  readonly client: OWKAIClient;
  /** Default timeout for decisions */
  readonly defaultTimeout: number;

  /**
   * Initialize an authorized agent
   *
   * @param agentId - Unique identifier for this agent
   * @param agentName - Human-readable agent name
   * @param client - OWKAIClient instance (creates new if not provided)
   * @param defaultTimeout - Default timeout for decisions in milliseconds
   */
  constructor(
    agentId: string,
    agentName: string,
    client?: OWKAIClient,
    defaultTimeout: number = 60000
  ) {
    this.agentId = agentId;
    this.agentName = agentName;
    this.client = client || new OWKAIClient();
    this.defaultTimeout = defaultTimeout;
  }

  /**
   * Request authorization for an action
   *
   * @param options - Authorization options
   * @returns Authorization decision
   *
   * @example
   * ```typescript
   * const decision = await agent.requestAuthorization({
   *   actionType: ActionType.TRANSACTION,
   *   resource: 'customer_account',
   *   resourceId: 'ACC-12345',
   *   details: {
   *     operation: 'transfer',
   *     amount: 50000,
   *     currency: 'USD'
   *   },
   *   riskIndicators: {
   *     financialData: true,
   *     dataSensitivity: 'high'
   *   }
   * });
   * ```
   */
  async requestAuthorization(options: AuthorizationOptions): Promise<AuthorizationDecision> {
    const action: AgentAction = {
      agentId: this.agentId,
      agentName: this.agentName,
      actionType: options.actionType,
      resource: options.resource,
      resourceId: options.resourceId,
      details: options.details,
      context: options.context,
      riskIndicators: options.riskIndicators,
    };

    const decision = await this.client.submitAction(action);

    const waitForDecision = options.waitForDecision !== false;
    if (waitForDecision && decision.decision === DecisionStatus.PENDING) {
      const timeout = options.timeout || this.defaultTimeout;
      return this.client.waitForDecision(decision.actionId, timeout);
    }

    return decision;
  }

  /**
   * Execute a function only if authorized
   *
   * This is the recommended pattern for most use cases. It:
   * 1. Submits the action for authorization
   * 2. Waits for a decision
   * 3. Executes the function if approved
   * 4. Throws AuthorizationError if denied
   *
   * @param options - Authorization options
   * @param executeFn - Function to execute if authorized
   * @param onDenied - Optional callback if action denied
   * @returns Result of executeFn if authorized
   * @throws AuthorizationError if action is denied (and no onDenied callback)
   * @throws TimeoutError if decision times out
   *
   * @example
   * ```typescript
   * const customer = await agent.executeIfAuthorized(
   *   {
   *     actionType: ActionType.DATA_ACCESS,
   *     resource: 'customer_pii',
   *     resourceId: customerId
   *   },
   *   async () => {
   *     return await db.customers.findById(customerId);
   *   }
   * );
   * ```
   */
  async executeIfAuthorized<T>(
    options: Omit<AuthorizationOptions, 'waitForDecision'>,
    executeFn: () => T | Promise<T>,
    onDenied?: (decision: AuthorizationDecision) => T | Promise<T>
  ): Promise<T> {
    const decision = await this.requestAuthorization({
      ...options,
      waitForDecision: true,
    });

    if (decision.decision === DecisionStatus.APPROVED) {
      return executeFn();
    }

    if (decision.decision === DecisionStatus.DENIED) {
      if (onDenied) {
        return onDenied(decision);
      }

      throw new AuthorizationError(
        `Action denied: ${decision.comments || 'No reason provided'}`,
        decision.policyViolations,
        decision.riskScore
      );
    }

    if (decision.decision === DecisionStatus.TIMEOUT) {
      throw new TimeoutError(
        'Authorization decision timed out',
        options.timeout || this.defaultTimeout
      );
    }

    // PENDING, REQUIRES_MODIFICATION, etc.
    throw new AuthorizationError(`Unexpected authorization status: ${decision.decision}`, [], undefined, {
      decision: decision.decision,
    });
  }

  /**
   * Quick permission check without waiting
   *
   * Submits the action and returns immediately with initial decision.
   * Useful for UI permission checks or preflight validation.
   *
   * @param options - Authorization options (without waiting)
   * @returns True if likely to be approved, false otherwise
   *
   * @note This returns the initial auto-decision. Some actions may
   * require manual approval even if this returns true initially.
   */
  async checkPermission(
    options: Omit<AuthorizationOptions, 'waitForDecision' | 'timeout'>
  ): Promise<boolean> {
    const decision = await this.requestAuthorization({
      ...options,
      waitForDecision: false,
    });

    return (
      decision.decision === DecisionStatus.APPROVED ||
      decision.decision === DecisionStatus.AUTO_APPROVED
    );
  }

  /**
   * Get recent actions for this agent
   *
   * @param limit - Maximum number of actions to return
   * @param status - Filter by status
   * @returns List of recent actions
   */
  async getRecentActions(limit: number = 10, status?: string): Promise<ActionListResponse> {
    return this.client.listActions({
      limit,
      agentId: this.agentId,
      status,
    });
  }
}
