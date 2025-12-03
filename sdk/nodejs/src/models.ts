/**
 * OW-AI SDK Data Models
 * =====================
 *
 * Type-safe data models for API interactions.
 */

/**
 * Supported action types for agent authorization
 */
export enum ActionType {
  DATA_ACCESS = 'data_access',
  DATA_MODIFICATION = 'data_modification',
  TRANSACTION = 'transaction',
  RECOMMENDATION = 'recommendation',
  COMMUNICATION = 'communication',
  SYSTEM_OPERATION = 'system_operation',
  QUERY = 'query',
  ANALYSIS = 'analysis',
  REPORT_GENERATION = 'report_generation',
  API_CALL = 'api_call',
}

/**
 * Authorization decision statuses (legacy v1.0)
 */
export enum DecisionStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  DENIED = 'denied',
  REQUIRES_MODIFICATION = 'requires_modification',
  TIMEOUT = 'timeout',
  AUTO_APPROVED = 'auto_approved',
  ESCALATED = 'escalated',
}

/**
 * Authorization decision values (v2.0)
 *
 * Used by AscendClient.evaluateAction() response.
 */
export enum Decision {
  /** Action is allowed to proceed */
  ALLOWED = 'allowed',
  /** Action is denied */
  DENIED = 'denied',
  /** Action is pending human approval */
  PENDING = 'pending',
}

/**
 * Risk assessment levels
 */
export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

/**
 * Risk assessment indicators for an action
 */
export interface RiskIndicators {
  /** Whether PII data is involved */
  piiInvolved?: boolean;
  /** Whether financial data is involved */
  financialData?: boolean;
  /** Whether this is an external transfer */
  externalTransfer?: boolean;
  /** Data sensitivity level */
  dataSensitivity?: 'low' | 'medium' | 'high' | 'critical';
  /** Amount threshold status */
  amountThreshold?: 'normal' | 'exceeded';
  /** Compliance flags */
  complianceFlags?: string[];
}

/**
 * Contextual information for an action
 */
export interface ActionContext {
  /** Original user request */
  userRequest?: string;
  /** Session identifier */
  sessionId?: string;
  /** Client IP address */
  ipAddress?: string;
  /** Client user agent */
  userAgent?: string;
  /** Timestamp */
  timestamp?: string;
  /** Custom context fields */
  [key: string]: unknown;
}

/**
 * Represents an agent action requiring authorization
 */
export interface AgentAction {
  /** Unique agent identifier */
  agentId: string;
  /** Human-readable agent name */
  agentName: string;
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
}

/**
 * Authorization decision response from OW-AI
 */
export interface AuthorizationDecision {
  /** Action ID */
  actionId: string;
  /** Decision status */
  decision: DecisionStatus;
  /** Calculated risk score (0-100) */
  riskScore?: number;
  /** Risk level */
  riskLevel?: RiskLevel;
  /** List of policy violations */
  policyViolations?: string[];
  /** Who approved the action */
  approvedBy?: string;
  /** When the action was approved */
  approvedAt?: string;
  /** Approval/denial comments */
  comments?: string;
  /** Whether execution is allowed */
  executionAllowed: boolean;
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Detailed information about an action
 */
export interface ActionDetails {
  /** Action ID */
  actionId: string;
  /** Agent ID */
  agentId: string;
  /** Agent name */
  agentName: string;
  /** Action type */
  actionType: string;
  /** Resource */
  resource: string;
  /** Resource ID */
  resourceId?: string;
  /** Current status */
  status: DecisionStatus;
  /** Risk score */
  riskScore?: number;
  /** When created */
  createdAt?: string;
  /** Last updated */
  updatedAt?: string;
  /** Audit trail */
  auditTrail?: Array<{
    timestamp: string;
    action: string;
    actor?: string;
    details?: string;
  }>;
}

/**
 * API response for action listing
 */
export interface ActionListResponse {
  /** List of actions */
  actions: ActionDetails[];
  /** Total count */
  total: number;
  /** Current offset */
  offset: number;
  /** Page limit */
  limit: number;
}

/**
 * SEC-054: Batch action submission options
 */
export interface BatchOptions {
  /** Process actions in parallel (default: true) */
  parallel?: boolean;
  /** Timeout for entire batch in milliseconds */
  timeout?: number;
  /** Continue processing if some actions fail */
  continueOnError?: boolean;
  /** Wait for all decisions before returning */
  waitForDecisions?: boolean;
}

/**
 * SEC-054: Individual batch action result
 */
export interface BatchActionResult {
  /** Original action index in batch */
  index: number;
  /** Action ID if submitted successfully */
  actionId?: string;
  /** Authorization decision */
  decision?: AuthorizationDecision;
  /** Error if submission failed */
  error?: {
    code: string;
    message: string;
  };
  /** Whether this action succeeded */
  success: boolean;
}

/**
 * SEC-054: Batch submission response
 */
export interface BatchResponse {
  /** Results for each action */
  results: BatchActionResult[];
  /** Total actions submitted */
  totalSubmitted: number;
  /** Successfully submitted */
  successCount: number;
  /** Failed submissions */
  errorCount: number;
  /** Total batch duration in ms */
  duration: number;
  /** Whether all actions succeeded */
  allSucceeded: boolean;
}

/**
 * Convert AgentAction to API payload format
 */
export function toApiPayload(action: AgentAction): Record<string, unknown> {
  return {
    agent_id: action.agentId,
    agent_name: action.agentName,
    action_type: action.actionType,
    resource: action.resource,
    resource_id: action.resourceId,
    action_details: action.details,
    context: action.context,
    risk_indicators: action.riskIndicators
      ? {
          pii_involved: action.riskIndicators.piiInvolved,
          financial_data: action.riskIndicators.financialData,
          external_transfer: action.riskIndicators.externalTransfer,
          data_sensitivity: action.riskIndicators.dataSensitivity,
          amount_threshold: action.riskIndicators.amountThreshold,
          compliance_flags: action.riskIndicators.complianceFlags,
        }
      : undefined,
  };
}

/**
 * Parse API response to AuthorizationDecision
 */
export function parseDecision(data: Record<string, unknown>): AuthorizationDecision {
  return {
    actionId: String(data.action_id || data.id || ''),
    decision: (data.decision || data.status || 'pending') as DecisionStatus,
    riskScore: data.risk_score as number | undefined,
    riskLevel: data.risk_level as RiskLevel | undefined,
    policyViolations: data.policy_violations as string[] | undefined,
    approvedBy: (data.approved_by || data.reviewed_by) as string | undefined,
    approvedAt: (data.approved_at || data.reviewed_at) as string | undefined,
    comments: data.comments as string | undefined,
    executionAllowed: data.execution_allowed === true || data.decision === 'approved',
    metadata: data.metadata as Record<string, unknown> | undefined,
  };
}
