/**
 * ASCEND SDK for Node.js/TypeScript
 * ==================================
 *
 * Enterprise-grade authorization SDK for AI agent governance.
 *
 * v2.0 Features:
 * - Fail mode configuration (closed/open)
 * - Circuit breaker pattern for resilience
 * - HMAC-SHA256 request signing
 * - Agent registration and lifecycle
 * - Action completion/failure logging
 * - Approval workflow support
 * - Webhook configuration
 * - Structured JSON logging
 *
 * @example
 * ```typescript
 * import { AscendClient, FailMode, Decision } from '@ascend/sdk';
 *
 * // Initialize client with fail mode
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
 * Security Standards:
 * - SOC 2 Type II Compliant (CC6.1)
 * - PCI-DSS 8.2 (API Key Management), 8.3 (MFA)
 * - HIPAA 164.312(e) (Transmission Security)
 * - NIST AI RMF (Govern, Map, Measure, Manage)
 * - NIST 800-63B (Authentication)
 *
 * @packageDocumentation
 */

// v2.0 Client and configuration
export {
  AscendClient,
  FailMode,
  CircuitBreaker,
  CircuitState,
  AscendLogger,
  type AscendClientOptions,
  type CircuitBreakerOptions,
  type AscendLoggerOptions,
  type LogLevel,
  type EvaluateActionResult,
  type RegisterResponse,
  type ActionLogResponse,
  type ApprovalStatusResponse,
  type WebhookConfigResponse,
} from './client';

// Legacy v1.0 client (deprecated)
export { OWKAIClient, type OWKAIClientOptions } from './client';
export { AuthorizedAgent, type AuthorizationOptions } from './agent';

// Models
export {
  ActionType,
  DecisionStatus,
  Decision,
  RiskLevel,
  toApiPayload,
  parseDecision,
} from './models';
export type {
  AgentAction,
  AuthorizationDecision,
  RiskIndicators,
  ActionContext,
  ActionDetails,
  ActionListResponse,
  BatchOptions,
  BatchResponse,
  BatchActionResult,
} from './models';

// Errors
export {
  OWKAIError,
  AuthenticationError,
  AuthorizationError,
  TimeoutError,
  RateLimitError,
  ValidationError,
  ConnectionError,
  CircuitBreakerOpenError,
} from './errors';

// Metrics
export {
  MetricsCollector,
  type MetricEvent,
  type MetricsSnapshot,
  type MetricsCallback,
  type EndpointMetrics,
} from './metrics';

// Interceptors
export {
  InterceptorManager,
  InterceptorChain,
  type RequestConfig,
  type ResponseData,
  type InterceptorError,
  type RequestInterceptor,
  type ResponseInterceptor,
  type ErrorInterceptor,
  generateRequestId,
  requestIdInterceptor,
  timestampInterceptor,
  debugLogInterceptor,
  responseTimingInterceptor,
} from './interceptors';

// MCP Governance
export {
  mcpGovernance,
  requireGovernance,
  highRiskAction,
  MCPGovernanceMiddleware,
  type GovernanceOptions,
  type MCPGovernanceConfig,
} from './mcp';

/**
 * SDK Version
 */
export const VERSION = '2.0.0';
