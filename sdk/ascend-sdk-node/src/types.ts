/**
 * Ascend AI Governance Platform - TypeScript Type Definitions
 * Enterprise-grade AI agent authorization and risk management
 *
 * @module types
 */

/**
 * Action types for AI agent operations
 * Maps to backend action categorization system
 */
export type ActionType =
  | 'data_access'          // Reading sensitive data
  | 'data_modification'    // Creating, updating, deleting data
  | 'transaction'          // Financial or state-changing operations
  | 'recommendation'       // AI-generated suggestions to users
  | 'communication'        // Sending emails, messages, notifications
  | 'system_operation';    // Infrastructure or system-level operations

/**
 * Risk levels assigned by the governance engine
 * Used for policy evaluation and alerting thresholds
 */
export type RiskLevel =
  | 'minimal'   // Risk score 0-20
  | 'low'       // Risk score 21-40
  | 'medium'    // Risk score 41-60
  | 'high'      // Risk score 61-80
  | 'critical'; // Risk score 81-100

/**
 * Decision status for agent actions
 */
export type ActionStatus =
  | 'approved'           // Action authorized to proceed
  | 'pending_approval'   // Awaiting human review
  | 'denied'             // Action blocked by policy or review
  | 'timeout';           // Approval timeout exceeded

/**
 * Agent action submission payload
 * Required fields for governance evaluation
 */
export interface AgentAction {
  /** Unique identifier for the AI agent (e.g., 'openai-gpt4', 'claude-v1') */
  agent_id: string;

  /** Human-readable agent name (e.g., 'Customer Support Bot') */
  agent_name: string;

  /** Type of action being requested */
  action_type: ActionType;

  /** Resource being accessed (e.g., 'customer_database', 'email_system') */
  resource: string;

  /** Optional specific resource identifier (e.g., 'user_id:12345') */
  resource_id?: string;

  /** Detailed action information for audit trail */
  action_details?: Record<string, unknown>;

  /** Contextual information (user session, environment, etc.) */
  context?: Record<string, unknown>;

  /** Risk indicators detected by the agent (anomalies, patterns) */
  risk_indicators?: Record<string, unknown>;
}

/**
 * Result from governance engine evaluation
 * Returned by all action submission and query endpoints
 */
export interface ActionResult {
  /** Database ID of the action record */
  id: number;

  /** Current decision status */
  status: ActionStatus;

  /** Computed risk score (0-100) */
  risk_score: number;

  /** Risk level classification */
  risk_level: RiskLevel;

  /** Whether action requires human approval */
  requires_approval: boolean;

  /** Whether action triggered security alert */
  alert_triggered: boolean;

  /** Optional decision reason or policy reference */
  decision?: string;

  /** Optional explanation for denial or approval */
  reason?: string;

  /** Timestamp when action was created */
  timestamp?: string;

  /** Timestamp when decision was made */
  decided_at?: string;

  /** Organization ID (multi-tenant isolation) */
  organization_id?: number;
}

/**
 * Client configuration options
 */
export interface ClientConfig {
  /** API key for authentication (from environment or constructor) */
  apiKey?: string;

  /** Base URL for Ascend API (default: https://pilot.owkai.app) */
  baseUrl?: string;

  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;

  /** Maximum retry attempts for failed requests (default: 3) */
  maxRetries?: number;

  /** Enable debug logging (default: false) */
  debug?: boolean;
}

/**
 * Parameters for listing actions
 */
export interface ListParams {
  /** Filter by action status */
  status?: ActionStatus;

  /** Filter by risk level */
  risk_level?: RiskLevel;

  /** Filter by agent ID */
  agent_id?: string;

  /** Page number for pagination (default: 1) */
  page?: number;

  /** Results per page (default: 50, max: 100) */
  limit?: number;

  /** Start date for filtering (ISO 8601) */
  start_date?: string;

  /** End date for filtering (ISO 8601) */
  end_date?: string;
}

/**
 * Result from list actions endpoint
 */
export interface ListResult {
  /** Array of action results */
  actions: ActionResult[];

  /** Total number of actions matching filters */
  total: number;

  /** Current page number */
  page: number;

  /** Results per page */
  limit: number;

  /** Total number of pages */
  total_pages: number;
}

/**
 * Connection test result
 */
export interface ConnectionStatus {
  /** Whether connection is successful */
  connected: boolean;

  /** API response time in milliseconds */
  latency_ms: number;

  /** API version */
  version?: string;

  /** Organization ID */
  organization_id?: number;

  /** Optional error message if connection failed */
  error?: string;
}

/**
 * Authorization options for AuthorizedAgent
 */
export interface AuthorizationOptions {
  /** Type of action being requested */
  action_type: ActionType;

  /** Resource being accessed */
  resource: string;

  /** Optional specific resource identifier */
  resource_id?: string;

  /** Detailed action information */
  action_details?: Record<string, unknown>;

  /** Contextual information */
  context?: Record<string, unknown>;

  /** Risk indicators */
  risk_indicators?: Record<string, unknown>;

  /** Timeout for waiting for approval decision (milliseconds) */
  wait_timeout?: number;
}

/**
 * Execute options for AuthorizedAgent
 */
export interface ExecuteOptions<T> {
  /** Authorization options */
  authorization: AuthorizationOptions;

  /** Function to execute if authorized */
  action: () => Promise<T>;

  /** Optional fallback function if denied */
  onDenied?: (result: ActionResult) => Promise<T> | T;

  /** Optional handler for pending approval state */
  onPending?: (result: ActionResult) => void;
}

/**
 * Internal retry configuration
 */
export interface RetryConfig {
  /** Maximum number of retry attempts */
  maxRetries: number;

  /** Initial delay in milliseconds */
  initialDelay: number;

  /** Maximum delay in milliseconds */
  maxDelay: number;

  /** HTTP status codes that should trigger retry */
  retryableStatusCodes: number[];
}
