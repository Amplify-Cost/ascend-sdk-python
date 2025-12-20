/**
 * ASCEND MCP Server Governance Integration
 * =========================================
 *
 * Enterprise-grade governance for Model Context Protocol (MCP) servers.
 * Provides fail-secure authorization for AI agent tool execution.
 *
 * Features:
 * - Wrap MCP tool handlers with governance checks
 * - Automatic risk classification and policy enforcement
 * - Approval workflow integration for high-risk actions
 * - Full audit trail for compliance (SOC 2, HIPAA, PCI-DSS)
 * - Fail-closed security (deny on errors)
 * - Sensitive data redaction in logs
 *
 * @example
 * ```typescript
 * import { Server } from "@modelcontextprotocol/sdk/server/index.js";
 * import { McpGovernance } from "ascend-mcp-server";
 *
 * const governance = new McpGovernance({
 *   apiKey: process.env.ASCEND_API_KEY,
 *   agentId: "mcp-database-server",
 *   agentName: "Database MCP Server"
 * });
 *
 * // Evaluate tool call
 * const decision = await governance.evaluate("query", { sql: "SELECT * FROM users" });
 * if (decision.allowed) {
 *   // Execute tool
 * }
 * ```
 *
 * Compliance: SOC 2 CC6.1, HIPAA 164.312(e), PCI-DSS 8.2, NIST AI RMF
 *
 * @packageDocumentation
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// ============================================================================
// Types & Interfaces
// ============================================================================

/**
 * Risk levels for MCP tool actions
 */
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

/**
 * Agent action for governance evaluation
 */
export interface AgentAction {
  agentId: string;
  agentName: string;
  actionType: string;
  resource: string;
  toolName: string;
  actionDetails?: Record<string, unknown>;
  riskIndicators?: Record<string, unknown>;
  context?: Record<string, unknown>;
}

/**
 * Result from action submission
 */
export interface ActionResult {
  actionId: string;
  status: 'approved' | 'denied' | 'pending';
  decision?: string;
  riskScore?: number;
  riskLevel?: string;
  reason?: string;
  policyMatched?: string;
  timestamp?: string;
}

/**
 * Governance decision from ASCEND
 */
export interface GovernanceDecision {
  /** Whether execution is allowed */
  allowed: boolean;
  /** Unique action ID for audit trail */
  actionId: string;
  /** Reason for decision */
  reason?: string;
  /** Calculated risk score (0-100) */
  riskScore?: number;
  /** Risk level classification */
  riskLevel?: RiskLevel;
  /** Whether action is pending approval */
  pendingApproval?: boolean;
  /** Approval request ID if pending */
  approvalRequestId?: string;
  /** Required approvers if pending */
  requiredApprovers?: string[];
  /** Policies that were violated (if denied) */
  policyViolations?: string[];
}

/**
 * Configuration for MCP server governance
 */
export interface McpGovernanceConfig {
  /** ASCEND API key (or set ASCEND_API_KEY env var) */
  apiKey?: string;
  /** ASCEND API base URL */
  baseUrl?: string;
  /** Unique agent identifier for this MCP server */
  agentId: string;
  /** Human-readable agent name */
  agentName: string;

  // Security Configuration
  /** Fail mode: 'closed' denies on error, 'open' allows (default: 'closed') */
  failMode?: 'closed' | 'open';
  /** Whether to wait for pending approvals (default: true) */
  waitForApproval?: boolean;
  /** Approval timeout in milliseconds (default: 300000 = 5 min) */
  approvalTimeoutMs?: number;
  /** Polling interval for approval status (default: 5000ms) */
  approvalPollIntervalMs?: number;

  // Tool Configuration
  /** Default risk level for tools without explicit classification (default: 'medium') */
  defaultRiskLevel?: RiskLevel;
  /** Map tool names to risk levels */
  toolRiskLevels?: Record<string, RiskLevel>;
  /** Map tool names to action types */
  toolActionTypes?: Record<string, string>;

  // Callbacks
  /** Called when action requires approval */
  onApprovalRequired?: (decision: GovernanceDecision, toolName: string) => void | Promise<void>;
  /** Called when action is denied */
  onDenied?: (decision: GovernanceDecision, toolName: string) => void | Promise<void>;
  /** Called when action is approved */
  onApproved?: (decision: GovernanceDecision, toolName: string) => void | Promise<void>;
  /** Called on governance timeout */
  onTimeout?: (decision: GovernanceDecision, toolName: string) => void | Promise<void>;
}

/**
 * Options for wrapping individual tool handlers
 */
export interface ToolGovernanceOptions {
  /** Action type for this tool */
  actionType: string;
  /** Resource being accessed */
  resource: string;
  /** Risk level classification */
  riskLevel?: RiskLevel;
  /** Always require human approval */
  requireApproval?: boolean;
  /** Additional metadata to include */
  metadata?: Record<string, unknown>;
}

/**
 * MCP tool call request structure
 */
export interface McpToolCallRequest {
  params: {
    name: string;
    arguments?: Record<string, unknown>;
  };
}

/**
 * MCP tool call response structure
 */
export interface McpToolCallResponse {
  content: Array<{
    type: string;
    text: string;
  }>;
  isError?: boolean;
}

/**
 * Governed tool handler function type
 */
export type GovernedToolHandler<T = unknown> = (
  request: McpToolCallRequest,
  governance: GovernanceDecision
) => Promise<T>;

// ============================================================================
// Constants
// ============================================================================

const SDK_VERSION = '1.0.0';
const USER_AGENT = `ascend-mcp-server/${SDK_VERSION}`;
const DEFAULT_TIMEOUT = 30000;

const SENSITIVE_KEYS = new Set([
  'password', 'secret', 'token', 'api_key', 'apikey', 'api-key',
  'auth', 'credential', 'private_key', 'privatekey', 'access_token',
  'accesstoken', 'refresh_token', 'refreshtoken', 'bearer', 'authorization',
  'ssn', 'social_security', 'credit_card', 'creditcard', 'cvv', 'pin'
]);

const DEFAULT_RISK_PATTERNS: Record<string, RiskLevel> = {
  // Low risk - read operations
  'read': 'low', 'get': 'low', 'list': 'low', 'search': 'low',
  'query': 'low', 'fetch': 'low', 'describe': 'low', 'view': 'low',
  // Medium risk - write operations
  'create': 'medium', 'update': 'medium', 'modify': 'medium',
  'write': 'medium', 'put': 'medium', 'insert': 'medium', 'add': 'medium',
  // High risk - destructive operations
  'delete': 'high', 'remove': 'high', 'drop': 'high',
  'truncate': 'high', 'purge': 'high', 'destroy': 'high',
  // Critical risk - administrative operations
  'execute': 'critical', 'exec': 'critical', 'admin': 'critical',
  'sudo': 'critical', 'grant': 'critical', 'revoke': 'critical',
  'transfer': 'critical', 'payment': 'critical', 'withdraw': 'critical',
};

// ============================================================================
// Embedded ASCEND Client (Banking-Level Security)
// ============================================================================

/**
 * Lightweight ASCEND client for MCP governance
 * @internal
 */
class AscendClient {
  private readonly http: AxiosInstance;

  constructor(config: { apiKey: string; baseUrl: string }) {
    this.http = axios.create({
      baseURL: config.baseUrl,
      timeout: DEFAULT_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey}`,
        'X-API-Key': config.apiKey,
        'User-Agent': USER_AGENT,
      },
    });
  }

  /**
   * Submit action for governance evaluation
   */
  async submitAction(action: AgentAction): Promise<ActionResult> {
    try {
      const response = await this.http.post('/api/v1/actions/submit', {
        agent_id: action.agentId,
        agent_name: action.agentName,
        action_type: action.actionType,
        description: action.resource,
        tool_name: action.toolName,
        action_details: action.actionDetails,
        risk_indicators: action.riskIndicators,
        context: action.context,
      });

      const data = response.data;
      return {
        actionId: data.id || data.action_id || `action_${Date.now()}`,
        status: data.status || 'approved',
        decision: data.decision || data.status,
        riskScore: data.risk_score,
        riskLevel: data.risk_level,
        reason: data.reason || data.summary,
        policyMatched: data.policy_matched,
        timestamp: data.timestamp || data.created_at,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        if (axiosError.response?.status === 401 || axiosError.response?.status === 403) {
          throw new Error(`Authentication failed: ${axiosError.message}`);
        }
        throw new Error(`API error: ${axiosError.message}`);
      }
      throw error;
    }
  }

  /**
   * Get action status (for polling pending approvals)
   */
  async getActionStatus(actionId: string): Promise<ActionResult> {
    try {
      const response = await this.http.get(`/api/v1/actions/${actionId}/status`);
      const data = response.data;

      return {
        actionId: data.id || actionId,
        status: data.status || 'pending',
        decision: data.decision || data.status,
        riskScore: data.risk_score,
        riskLevel: data.risk_level,
        reason: data.reason,
        policyMatched: data.policy_matched,
      };
    } catch (error) {
      throw new Error(`Failed to get action status: ${error}`);
    }
  }
}

// ============================================================================
// Main Class
// ============================================================================

/**
 * MCP Server Governance Middleware
 *
 * Provides enterprise-grade governance for MCP server tool execution.
 * Integrates with ASCEND platform for policy evaluation and approval workflows.
 *
 * @example
 * ```typescript
 * const governance = new McpGovernance({
 *   apiKey: process.env.ASCEND_API_KEY,
 *   agentId: "mcp-database-server",
 *   agentName: "Database MCP Server"
 * });
 *
 * // Evaluate tool call
 * const decision = await governance.evaluate("query", { sql: "SELECT * FROM users" });
 *
 * if (decision.allowed) {
 *   const result = await executeQuery(args.sql);
 * } else {
 *   console.log(`Denied: ${decision.reason}`);
 * }
 * ```
 */
export class McpGovernance {
  private readonly client: AscendClient;
  private readonly config: Required<Omit<McpGovernanceConfig, 'onApprovalRequired' | 'onDenied' | 'onApproved' | 'onTimeout'>> & McpGovernanceConfig;
  private readonly governedTools: Set<string> = new Set();

  constructor(config: McpGovernanceConfig) {
    // Resolve API key from env if not provided
    const apiKey = config.apiKey || process.env['ASCEND_API_KEY'];
    if (!apiKey) {
      throw new Error(
        'ASCEND API key required. Set ASCEND_API_KEY environment variable or pass apiKey in config.'
      );
    }

    // Initialize with defaults
    this.config = {
      apiKey,
      baseUrl: config.baseUrl || process.env['ASCEND_API_URL'] || 'https://pilot.owkai.app',
      agentId: config.agentId,
      agentName: config.agentName,
      failMode: config.failMode || 'closed',
      waitForApproval: config.waitForApproval ?? true,
      approvalTimeoutMs: config.approvalTimeoutMs || 300000,
      approvalPollIntervalMs: config.approvalPollIntervalMs || 5000,
      defaultRiskLevel: config.defaultRiskLevel || 'medium',
      toolRiskLevels: config.toolRiskLevels || {},
      toolActionTypes: config.toolActionTypes || {},
      onApprovalRequired: config.onApprovalRequired,
      onDenied: config.onDenied,
      onApproved: config.onApproved,
      onTimeout: config.onTimeout,
    };

    // Initialize ASCEND client
    this.client = new AscendClient({
      apiKey: this.config.apiKey,
      baseUrl: this.config.baseUrl,
    });

    console.log(`[ASCEND MCP] Governance initialized for ${this.config.agentName}`);
  }

  /**
   * Evaluate a tool call against governance policies
   *
   * @param toolName - Name of the MCP tool
   * @param args - Tool arguments
   * @param options - Additional governance options
   * @returns Governance decision
   *
   * @example
   * ```typescript
   * const decision = await governance.evaluate("execute_sql", { sql: "DELETE FROM users" }, {
   *   actionType: "database.delete",
   *   resource: "production_db",
   *   riskLevel: "critical"
   * });
   *
   * if (!decision.allowed) {
   *   return { content: [{ type: "text", text: `Denied: ${decision.reason}` }], isError: true };
   * }
   * ```
   */
  async evaluate(
    toolName: string,
    args: Record<string, unknown> = {},
    options: Partial<ToolGovernanceOptions> = {}
  ): Promise<GovernanceDecision> {
    const startTime = Date.now();

    try {
      // Determine action type and risk level
      const actionType = options.actionType ||
        this.config.toolActionTypes[toolName] ||
        `mcp.${toolName}`;
      const riskLevel = options.riskLevel ||
        this.config.toolRiskLevels[toolName] ||
        this.inferRiskLevel(toolName);
      const resource = options.resource || toolName;

      console.log(`[ASCEND MCP] Evaluating: ${actionType} on ${resource} (risk: ${riskLevel})`);

      // Build action
      const action: AgentAction = {
        agentId: this.config.agentId,
        agentName: this.config.agentName,
        actionType,
        resource: `MCP Tool: ${toolName} - ${resource}`,
        toolName,
        actionDetails: this.sanitizeArguments(args),
        riskIndicators: {
          risk_level: riskLevel,
          mcp_server: true,
          tool_name: toolName,
          ...options.metadata,
        },
        context: {
          source: 'mcp_server',
          governance_version: SDK_VERSION,
          require_approval: options.requireApproval || riskLevel === 'critical',
        },
      };

      // Submit for evaluation
      const result = await this.client.submitAction(action);

      // Handle decision
      if (result.status === 'approved') {
        const decision: GovernanceDecision = {
          allowed: true,
          actionId: result.actionId,
          reason: 'approved',
          riskScore: result.riskScore,
          riskLevel: result.riskLevel as RiskLevel,
        };

        if (this.config.onApproved) {
          await this.config.onApproved(decision, toolName);
        }

        console.log(`[ASCEND MCP] APPROVED: ${toolName} (${Date.now() - startTime}ms)`);
        return decision;
      }

      if (result.status === 'pending') {
        console.log(`[ASCEND MCP] PENDING: ${toolName} requires approval`);

        const decision: GovernanceDecision = {
          allowed: false,
          actionId: result.actionId,
          reason: result.reason || 'Requires approval',
          riskScore: result.riskScore,
          riskLevel: result.riskLevel as RiskLevel,
          pendingApproval: true,
          approvalRequestId: result.actionId,
        };

        if (this.config.onApprovalRequired) {
          await this.config.onApprovalRequired(decision, toolName);
        }

        // Wait for approval if configured
        if (this.config.waitForApproval) {
          return await this.waitForApproval(result.actionId, toolName, decision);
        }

        return decision;
      }

      // Denied
      const decision: GovernanceDecision = {
        allowed: false,
        actionId: result.actionId,
        reason: result.reason || 'Policy violation',
        riskScore: result.riskScore,
        riskLevel: result.riskLevel as RiskLevel,
        policyViolations: result.policyMatched ? [result.policyMatched] : [],
      };

      if (this.config.onDenied) {
        await this.config.onDenied(decision, toolName);
      }

      console.warn(`[ASCEND MCP] DENIED: ${toolName} - ${decision.reason}`);
      return decision;

    } catch (error) {
      console.error(`[ASCEND MCP] Governance error: ${error}`);

      // Fail-closed by default (banking-level security)
      if (this.config.failMode === 'open') {
        console.warn('[ASCEND MCP] fail_mode=open, allowing execution');
        return {
          allowed: true,
          actionId: `fail_open_${Date.now()}`,
          reason: 'Governance unavailable (fail_mode=open)',
        };
      }

      return {
        allowed: false,
        actionId: `error_${Date.now()}`,
        reason: `Governance service unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }

  /**
   * Wait for approval decision with polling
   */
  private async waitForApproval(
    actionId: string,
    toolName: string,
    initialDecision: GovernanceDecision
  ): Promise<GovernanceDecision> {
    const startTime = Date.now();
    const timeout = this.config.approvalTimeoutMs;
    const pollInterval = this.config.approvalPollIntervalMs;

    console.log(`[ASCEND MCP] Waiting for approval (timeout: ${timeout}ms)`);

    while (Date.now() - startTime < timeout) {
      await this.sleep(pollInterval);

      try {
        const status = await this.client.getActionStatus(actionId);

        if (status.status === 'approved') {
          console.log(`[ASCEND MCP] Approval GRANTED for ${toolName}`);
          return {
            ...initialDecision,
            allowed: true,
            reason: 'Approved by reviewer',
            pendingApproval: false,
          };
        }

        if (status.status === 'denied') {
          console.log(`[ASCEND MCP] Approval REJECTED for ${toolName}`);
          return {
            ...initialDecision,
            allowed: false,
            reason: status.reason || 'Rejected by reviewer',
            pendingApproval: false,
          };
        }

        // Still pending
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        console.debug(`[ASCEND MCP] Still pending after ${elapsed}s...`);

      } catch (error) {
        console.warn(`[ASCEND MCP] Error checking approval: ${error}`);
      }
    }

    // Timeout
    console.warn(`[ASCEND MCP] Approval timeout for ${toolName}`);

    if (this.config.onTimeout) {
      await this.config.onTimeout(initialDecision, toolName);
    }

    return {
      ...initialDecision,
      allowed: false,
      reason: `Approval timeout after ${timeout}ms`,
    };
  }

  /**
   * Wrap a tool handler function with governance
   *
   * @param handler - Original tool handler
   * @param options - Governance options
   * @returns Governed tool handler
   *
   * @example
   * ```typescript
   * const governedQuery = governance.wrapTool(
   *   async (request) => {
   *     const { sql } = request.params.arguments;
   *     return { content: [{ type: "text", text: await db.execute(sql) }] };
   *   },
   *   { actionType: "database.query", resource: "production_db" }
   * );
   * ```
   */
  wrapTool<T>(
    handler: (request: McpToolCallRequest) => Promise<T>,
    options: ToolGovernanceOptions
  ): GovernedToolHandler<T | McpToolCallResponse> {
    const toolName = options.actionType.split('.').pop() || 'unknown';
    this.governedTools.add(toolName);

    return async (request: McpToolCallRequest): Promise<T | McpToolCallResponse> => {
      const { name, arguments: args } = request.params;

      // Evaluate governance
      const decision = await this.evaluate(name, args || {}, options);

      if (!decision.allowed) {
        return {
          content: [{
            type: 'text',
            text: `[ASCEND GOVERNANCE] Tool execution denied.\n` +
              `Reason: ${decision.reason}\n` +
              `Action ID: ${decision.actionId}\n` +
              `Risk Level: ${decision.riskLevel || 'unknown'}`,
          }],
          isError: true,
        };
      }

      // Execute handler
      const startTime = Date.now();
      try {
        const result = await handler(request);
        console.debug(`[ASCEND MCP] Tool ${name} completed in ${Date.now() - startTime}ms`);
        return result;
      } catch (error) {
        console.error(`[ASCEND MCP] Tool ${name} failed: ${error}`);
        throw error;
      }
    };
  }

  /**
   * Create a governed tool handler decorator
   *
   * @param options - Governance options
   * @returns Decorator function
   *
   * @example
   * ```typescript
   * const queryHandler = governance.governTool({
   *   actionType: "database.query",
   *   resource: "production_db",
   *   riskLevel: "medium"
   * })(async (request) => {
   *   return await executeQuery(request.params.arguments.sql);
   * });
   * ```
   */
  governTool(options: ToolGovernanceOptions) {
    return <T>(handler: (request: McpToolCallRequest) => Promise<T>) => {
      return this.wrapTool(handler, options);
    };
  }

  /**
   * Infer risk level from tool name patterns
   */
  private inferRiskLevel(toolName: string): RiskLevel {
    const lowerName = toolName.toLowerCase();

    for (const [pattern, level] of Object.entries(DEFAULT_RISK_PATTERNS)) {
      if (lowerName.includes(pattern)) {
        return level;
      }
    }

    return this.config.defaultRiskLevel;
  }

  /**
   * Sanitize arguments to remove sensitive data (Banking-level security)
   */
  private sanitizeArguments(args: Record<string, unknown>): Record<string, unknown> {
    const sanitized: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(args)) {
      const lowerKey = key.toLowerCase();

      // Check if key contains sensitive patterns
      if ([...SENSITIVE_KEYS].some(s => lowerKey.includes(s))) {
        sanitized[key] = '[REDACTED]';
        continue;
      }

      // Recursively sanitize objects
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        sanitized[key] = this.sanitizeArguments(value as Record<string, unknown>);
      } else if (typeof value === 'string' && value.length > 200) {
        // Truncate long strings
        sanitized[key] = value.substring(0, 200) + '...[truncated]';
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get list of governed tool names
   */
  get tools(): string[] {
    return [...this.governedTools];
  }
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Create a governed MCP tool handler
 *
 * @example
 * ```typescript
 * import { createGovernedTool } from "ascend-mcp-server";
 *
 * const queryDatabase = createGovernedTool({
 *   agentId: "mcp-server",
 *   agentName: "Database Server",
 *   actionType: "database.query",
 *   resource: "production_db"
 * }, async (request) => {
 *   const { sql } = request.params.arguments;
 *   return await db.execute(sql);
 * });
 * ```
 */
export function createGovernedTool<T>(
  options: ToolGovernanceOptions & McpGovernanceConfig,
  handler: (request: McpToolCallRequest) => Promise<T>
): GovernedToolHandler<T | McpToolCallResponse> {
  const governance = new McpGovernance(options);
  return governance.wrapTool(handler, options);
}

/**
 * Higher-order function to add governance to a tool handler
 *
 * @example
 * ```typescript
 * import { withGovernance } from "ascend-mcp-server";
 *
 * const governedHandler = withGovernance({
 *   agentId: "mcp-server",
 *   agentName: "My MCP Server",
 *   actionType: "database.query",
 *   resource: "production_db"
 * })(originalHandler);
 * ```
 */
export function withGovernance(
  options: ToolGovernanceOptions & McpGovernanceConfig
) {
  return <T>(handler: (request: McpToolCallRequest) => Promise<T>) => {
    return createGovernedTool(options, handler);
  };
}

/**
 * Mark a tool as high-risk requiring human approval
 *
 * @example
 * ```typescript
 * import { highRiskTool } from "ascend-mcp-server";
 *
 * const deleteAllRecords = highRiskTool({
 *   agentId: "mcp-server",
 *   agentName: "Database Server",
 *   actionType: "database.delete_all",
 *   resource: "production_db"
 * })(async (request) => {
 *   return await db.deleteAll(request.params.arguments.table);
 * });
 * ```
 */
export function highRiskTool(
  options: Omit<ToolGovernanceOptions & McpGovernanceConfig, 'riskLevel' | 'requireApproval'>
) {
  return withGovernance({
    ...options,
    riskLevel: 'critical',
    requireApproval: true,
  });
}

// ============================================================================
// Default Export
// ============================================================================

export default McpGovernance;
