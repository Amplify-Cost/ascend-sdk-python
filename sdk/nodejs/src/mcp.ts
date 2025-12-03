/**
 * ASCEND MCP Governance Integration
 * ==================================
 *
 * Enterprise-grade wrapper for integrating ASCEND governance
 * with MCP (Model Context Protocol) server tools.
 *
 * @example
 * ```typescript
 * import { AscendClient } from './client';
 * import { mcpGovernance, MCPGovernanceMiddleware } from './mcp';
 *
 * const client = new AscendClient({ ... });
 *
 * // Using decorator pattern
 * const queryDatabase = mcpGovernance(client, {
 *   actionType: 'database.query',
 *   resource: 'production_db',
 * })(async (sql: string) => {
 *   return db.execute(sql);
 * });
 *
 * // Using middleware pattern
 * const middleware = new MCPGovernanceMiddleware(client);
 *
 * const tools = {
 *   queryDatabase: middleware.wrap('database.query', 'prod_db', queryFn),
 *   writeFile: middleware.wrap('file.write', '/etc/config', writeFn),
 * };
 * ```
 *
 * Compliance: SOC 2 CC6.1, HIPAA 164.312(e), PCI-DSS 8.2, NIST AI RMF
 */

import {
  AscendClient,
  EvaluateActionResult,
} from './client';
import { Decision } from './models';
import {
  AuthorizationError,
  TimeoutError,
  ConnectionError,
  CircuitBreakerOpenError,
} from './errors';

/**
 * Configuration for MCP governance behavior
 */
export interface MCPGovernanceConfig {
  /** Whether to wait for approval if action is pending (default: true) */
  waitForApproval?: boolean;
  /** Approval timeout in milliseconds (default: 300000 = 5 minutes) */
  approvalTimeoutMs?: number;
  /** Polling interval for approval status in milliseconds (default: 5000) */
  approvalPollIntervalMs?: number;

  /** Include tool name in context (default: true) */
  includeToolName?: boolean;
  /** Include arguments in context (default: true) */
  includeArguments?: boolean;

  /** Throw error on denial (default: true) */
  raiseOnDenial?: boolean;
  /** Log all decisions (default: true) */
  logAllDecisions?: boolean;

  /** Callback when approval is required */
  onApprovalRequired?: (decision: EvaluateActionResult, toolName: string) => void | Promise<void>;
  /** Callback when action is denied */
  onDenied?: (decision: EvaluateActionResult, toolName: string) => void | Promise<void>;
  /** Callback when action is allowed */
  onAllowed?: (decision: EvaluateActionResult, toolName: string) => void | Promise<void>;
  /** Callback on approval timeout */
  onTimeout?: (decision: EvaluateActionResult, toolName: string) => void | Promise<void>;
}

/**
 * Options for the governance wrapper
 */
export interface GovernanceOptions {
  actionType: string;
  resource: string;
  config?: MCPGovernanceConfig;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  metadata?: Record<string, unknown>;
  requireHumanApproval?: boolean;
}

const DEFAULT_CONFIG: Required<Omit<MCPGovernanceConfig, 'onApprovalRequired' | 'onDenied' | 'onAllowed' | 'onTimeout'>> = {
  waitForApproval: true,
  approvalTimeoutMs: 300000,
  approvalPollIntervalMs: 5000,
  includeToolName: true,
  includeArguments: true,
  raiseOnDenial: true,
  logAllDecisions: true,
};

/**
 * Create a governance-wrapped function using higher-order function pattern.
 *
 * @param client - AscendClient instance
 * @param options - Governance options
 * @returns Function that wraps the original with governance checks
 *
 * @example
 * ```typescript
 * const govQueryDatabase = mcpGovernance(client, {
 *   actionType: 'database.query',
 *   resource: 'production_db',
 * })(async (sql: string) => {
 *   return db.execute(sql);
 * });
 *
 * // Usage
 * const result = await govQueryDatabase('SELECT * FROM users');
 * ```
 */
export function mcpGovernance<T extends (...args: unknown[]) => unknown>(
  client: AscendClient,
  options: GovernanceOptions
): (fn: T) => (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
  const config = { ...DEFAULT_CONFIG, ...options.config };

  return (fn: T) => {
    const toolName = fn.name || 'anonymous';

    return async (...args: Parameters<T>): Promise<Awaited<ReturnType<T>>> => {
      const startTime = Date.now();
      let actionId: string | undefined;

      try {
        // Build context
        const context = buildContext(toolName, args, config, options.metadata);

        // Build parameters
        const parameters = extractParameters(args, fn);

        // Evaluate action
        console.log(`[MCP Governance] Evaluating ${options.actionType} on ${options.resource}`);

        const decision = await client.evaluateAction({
          actionType: options.actionType,
          resource: options.resource,
          parameters,
          context,
          waitForApproval: false, // We handle waiting ourselves
          riskLevel: options.riskLevel,
          requireHumanApproval: options.requireHumanApproval,
        });

        actionId = decision.actionId;

        if (config.logAllDecisions) {
          console.log(
            `[MCP Governance] Decision=${decision.decision}, ` +
            `actionId=${actionId}, riskScore=${decision.riskScore}`
          );
        }

        // Handle decision
        if (decision.decision === Decision.DENIED) {
          return handleDenied(decision, config, options, toolName) as Awaited<ReturnType<T>>;
        }

        if (decision.decision === Decision.PENDING) {
          const finalDecision = await handlePending(
            client,
            decision,
            config,
            options,
            toolName
          );

          if (finalDecision.decision === Decision.DENIED) {
            return handleDenied(finalDecision, config, options, toolName) as Awaited<ReturnType<T>>;
          }

          if (finalDecision.decision === Decision.PENDING) {
            await handleApprovalTimeout(finalDecision, config, options, toolName);
          }
        }

        // ALLOWED - Execute the function
        if (config.onAllowed) {
          await config.onAllowed(decision, toolName);
        }

        try {
          const result = await fn(...args);
          const durationMs = Date.now() - startTime;

          // Log completion
          if (actionId) {
            try {
              await client.logActionCompleted(
                actionId,
                { success: true, hasResult: result !== undefined },
                durationMs
              );
            } catch (logError) {
              console.warn(`[MCP Governance] Failed to log completion: ${logError}`);
            }
          }

          return result as Awaited<ReturnType<T>>;
        } catch (execError) {
          const durationMs = Date.now() - startTime;

          // Log failure
          if (actionId) {
            try {
              await client.logActionFailed(actionId, execError as Error, durationMs);
            } catch (logError) {
              console.warn(`[MCP Governance] Failed to log failure: ${logError}`);
            }
          }

          throw execError;
        }
      } catch (error) {
        if (error instanceof ConnectionError ||
            error instanceof TimeoutError ||
            error instanceof CircuitBreakerOpenError) {
          console.error(`[MCP Governance] ASCEND unavailable: ${error.message}`);
          throw new AuthorizationError(
            `ASCEND governance service unavailable: ${error.message}`,
            [],
            undefined,
            {
              actionType: options.actionType,
              resource: options.resource,
              toolName,
              originalError: error.message,
            }
          );
        }

        throw error;
      }
    };
  };
}

/**
 * Handle denied decision
 */
async function handleDenied<T>(
  decision: EvaluateActionResult,
  config: MCPGovernanceConfig,
  options: GovernanceOptions,
  toolName: string
): Promise<T> {
  console.warn(
    `[MCP Governance] DENIED - ${options.actionType} on ${options.resource} ` +
    `(tool: ${toolName}, reason: ${decision.reason})`
  );

  if (config.onDenied) {
    await config.onDenied(decision, toolName);
  }

  if (config.raiseOnDenial) {
    throw new AuthorizationError(
      `Action denied: ${decision.reason}`,
      decision.policyViolations,
      decision.riskScore,
      {
        actionType: options.actionType,
        resource: options.resource,
        toolName,
        actionId: decision.actionId,
        requiredApprovers: decision.requiredApprovers,
      }
    );
  }

  return undefined as T;
}

/**
 * Handle pending approval decision
 */
async function handlePending(
  client: AscendClient,
  decision: EvaluateActionResult,
  config: MCPGovernanceConfig,
  options: GovernanceOptions,
  toolName: string
): Promise<EvaluateActionResult> {
  console.log(
    `[MCP Governance] PENDING approval - ${options.actionType} on ${options.resource} ` +
    `(tool: ${toolName}, approvalId: ${decision.approvalRequestId})`
  );

  if (config.onApprovalRequired) {
    await config.onApprovalRequired(decision, toolName);
  }

  if (!config.waitForApproval) {
    console.log('[MCP Governance] Not waiting for approval (config.waitForApproval=false)');
    return decision;
  }

  const approvalId = decision.approvalRequestId;
  if (!approvalId) {
    console.error('[MCP Governance] No approval_request_id in pending decision');
    return decision;
  }

  const timeout = config.approvalTimeoutMs || 300000;
  const pollInterval = config.approvalPollIntervalMs || 5000;
  const startTime = Date.now();

  console.log(
    `[MCP Governance] Waiting up to ${timeout}ms for approval ` +
    `(polling every ${pollInterval}ms)`
  );

  while (Date.now() - startTime < timeout) {
    await sleep(pollInterval);

    try {
      const status = await client.checkApproval(approvalId);

      if (status.status === 'approved') {
        console.log(`[MCP Governance] Approval GRANTED for ${approvalId}`);
        return {
          ...decision,
          decision: Decision.ALLOWED,
          reason: 'Approved by human reviewer',
          metadata: {
            ...decision.metadata,
            approvedBy: status.approvedBy,
          },
        };
      }

      if (status.status === 'rejected') {
        console.log(`[MCP Governance] Approval REJECTED for ${approvalId}`);
        return {
          ...decision,
          decision: Decision.DENIED,
          reason: status.rejectionReason || 'Rejected by human reviewer',
          metadata: {
            ...decision.metadata,
            rejectedBy: status.rejectedBy,
          },
        };
      }

      // Still pending
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      console.debug(`[MCP Governance] Still pending after ${elapsed}s`);
    } catch (error) {
      console.warn(`[MCP Governance] Error checking approval status: ${error}`);
    }
  }

  // Timeout
  console.warn(`[MCP Governance] Approval timeout (${timeout}ms) for ${approvalId}`);
  return decision;
}

/**
 * Handle approval timeout
 */
async function handleApprovalTimeout(
  decision: EvaluateActionResult,
  config: MCPGovernanceConfig,
  options: GovernanceOptions,
  toolName: string
): Promise<never> {
  if (config.onTimeout) {
    await config.onTimeout(decision, toolName);
  }

  throw new TimeoutError(
    `Approval timeout for action: ${options.actionType} on ${options.resource}`,
    config.approvalTimeoutMs || 300000,
    {
      toolName,
      actionId: decision.actionId,
      approvalRequestId: decision.approvalRequestId,
    }
  );
}

/**
 * Build context for authorization request
 */
function buildContext(
  toolName: string,
  args: unknown[],
  config: MCPGovernanceConfig,
  additionalMetadata?: Record<string, unknown>
): Record<string, unknown> {
  const context: Record<string, unknown> = {
    source: 'mcp_server',
    governance_version: '2.0.0',
  };

  if (config.includeToolName) {
    context.tool_name = toolName;
  }

  if (config.includeArguments) {
    context.arguments = sanitizeArguments(args);
  }

  if (additionalMetadata) {
    context.metadata = additionalMetadata;
  }

  return context;
}

/**
 * Extract parameters from function arguments
 */
function extractParameters(
  args: unknown[],
  fn: (...args: unknown[]) => unknown
): Record<string, unknown> {
  const parameters: Record<string, unknown> = {};

  // Try to get parameter names from function
  const fnStr = fn.toString();
  const paramMatch = fnStr.match(/\(([^)]*)\)/);

  if (paramMatch && paramMatch[1]) {
    const paramNames = paramMatch[1]
      .split(',')
      .map(p => p.trim().split(':')[0].trim().split('=')[0].trim())
      .filter(p => p.length > 0);

    for (let i = 0; i < args.length && i < paramNames.length; i++) {
      parameters[paramNames[i]] = serializeValue(args[i]);
    }
  } else {
    // Fallback: use positional args
    for (let i = 0; i < args.length; i++) {
      parameters[`arg${i}`] = serializeValue(args[i]);
    }
  }

  return parameters;
}

/**
 * Serialize value for JSON
 */
function serializeValue(value: unknown): unknown {
  if (value === null || value === undefined) return value;
  if (typeof value === 'boolean' || typeof value === 'number' || typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(serializeValue);
  }
  if (typeof value === 'object') {
    const serialized: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value)) {
      serialized[k] = serializeValue(v);
    }
    return serialized;
  }
  return `<${typeof value}>`;
}

/**
 * Sanitize arguments to remove sensitive data
 */
function sanitizeArguments(args: unknown[]): Record<string, unknown> {
  const SENSITIVE_KEYS = new Set([
    'password', 'secret', 'token', 'api_key', 'apikey',
    'auth', 'credential', 'private_key', 'access_token'
  ]);

  function sanitize(value: unknown): unknown {
    if (typeof value === 'string' && value.length > 100) {
      return `${value.substring(0, 50)}...[truncated]`;
    }

    if (typeof value === 'object' && value !== null) {
      if (Array.isArray(value)) {
        return value.map(sanitize);
      }

      const sanitized: Record<string, unknown> = {};
      for (const [key, val] of Object.entries(value)) {
        const lowerKey = key.toLowerCase();
        if ([...SENSITIVE_KEYS].some(s => lowerKey.includes(s))) {
          sanitized[key] = '[REDACTED]';
        } else {
          sanitized[key] = sanitize(val);
        }
      }
      return sanitized;
    }

    return serializeValue(value);
  }

  return {
    count: args.length,
    values: args.map(sanitize),
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Simplified decorator for common use cases
 *
 * @example
 * ```typescript
 * const secureQuery = requireGovernance(client, 'database.query', 'prod_db')(queryFn);
 * ```
 */
export function requireGovernance<T extends (...args: unknown[]) => unknown>(
  client: AscendClient,
  actionType: string,
  resource: string,
  config?: MCPGovernanceConfig
): (fn: T) => (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
  return mcpGovernance(client, { actionType, resource, config });
}

/**
 * Decorator for high-risk actions requiring human approval
 *
 * @example
 * ```typescript
 * const secureDelete = highRiskAction(client, 'database.delete', 'prod_db')(deleteFn);
 * ```
 */
export function highRiskAction<T extends (...args: unknown[]) => unknown>(
  client: AscendClient,
  actionType: string,
  resource: string,
  config?: MCPGovernanceConfig
): (fn: T) => (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
  return mcpGovernance(client, {
    actionType,
    resource,
    riskLevel: 'high',
    requireHumanApproval: true,
    config,
  });
}

/**
 * Middleware class for applying governance to multiple MCP tools
 *
 * @example
 * ```typescript
 * const middleware = new MCPGovernanceMiddleware(client);
 *
 * const tools = {
 *   query: middleware.wrap('database.query', 'prod_db', queryFn),
 *   write: middleware.wrap('file.write', '/var/log', writeFn),
 * };
 *
 * console.log(`Governed tools: ${middleware.governedTools}`);
 * ```
 */
export class MCPGovernanceMiddleware {
  private readonly client: AscendClient;
  private readonly defaultConfig: MCPGovernanceConfig;
  private readonly _governedTools: string[] = [];

  constructor(client: AscendClient, defaultConfig?: MCPGovernanceConfig) {
    this.client = client;
    this.defaultConfig = defaultConfig || {};
  }

  /**
   * Wrap a function with governance
   */
  wrap<T extends (...args: any[]) => any>(
    actionType: string,
    resource: string,
    fn: T,
    config?: MCPGovernanceConfig
  ): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
    this._governedTools.push(fn.name || 'anonymous');
    return mcpGovernance(this.client, {
      actionType,
      resource,
      config: { ...this.defaultConfig, ...config },
    })(fn) as (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>>;
  }

  /**
   * Wrap a high-risk function requiring human approval
   */
  wrapHighRisk<T extends (...args: any[]) => any>(
    actionType: string,
    resource: string,
    fn: T,
    config?: MCPGovernanceConfig
  ): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
    this._governedTools.push(fn.name || 'anonymous');
    return highRiskAction(this.client, actionType, resource, {
      ...this.defaultConfig,
      ...config,
    })(fn) as (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>>;
  }

  /**
   * Get list of governed tool names
   */
  get governedTools(): string[] {
    return [...this._governedTools];
  }
}

// GovernanceOptions and MCPGovernanceConfig are already exported at definition
