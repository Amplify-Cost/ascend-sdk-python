/**
 * OW-AI Enterprise SDK for Node.js/TypeScript
 * ============================================
 *
 * Enterprise-grade authorization SDK for AI agent governance.
 *
 * SEC-054 Enhancements:
 * - Batch action submission for high-throughput scenarios
 * - Metrics collection and telemetry for monitoring
 * - Request/response interceptors for middleware patterns
 *
 * @example
 * ```typescript
 * import { OWKAIClient, AuthorizedAgent } from '@owkai/sdk';
 *
 * // Initialize client with metrics
 * const client = new OWKAIClient({
 *   apiKey: 'your-api-key',
 *   enableMetrics: true
 * });
 *
 * // Add request interceptor for tracing
 * client.interceptors.request.use((config) => {
 *   config.headers['X-Trace-ID'] = generateTraceId();
 *   return config;
 * });
 *
 * // Create authorized agent
 * const agent = new AuthorizedAgent('agent-001', 'My AI Agent', client);
 *
 * // Request authorization
 * const decision = await agent.requestAuthorization({
 *   actionType: ActionType.DATA_ACCESS,
 *   resource: 'customer_data'
 * });
 *
 * // Batch submit multiple actions
 * const batch = await client.submitActionBatch([action1, action2, action3]);
 *
 * // Get metrics
 * const metrics = client.getMetrics();
 * console.log(`Success rate: ${metrics.successRate * 100}%`);
 * ```
 *
 * Security Standards:
 * - SOC 2 Type II Compliant
 * - PCI-DSS 8.3 (MFA)
 * - HIPAA 164.312 (Audit)
 * - NIST 800-63B (Authentication)
 *
 * @packageDocumentation
 */

export { OWKAIClient, type OWKAIClientOptions } from './client';
export { AuthorizedAgent, type AuthorizationOptions } from './agent';
export {
  ActionType,
  DecisionStatus,
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
  // SEC-054: Batch types
  BatchOptions,
  BatchResponse,
  BatchActionResult,
} from './models';
export {
  OWKAIError,
  AuthenticationError,
  AuthorizationError,
  TimeoutError,
  RateLimitError,
  ValidationError,
  ConnectionError,
} from './errors';

// SEC-054: Metrics exports
export {
  MetricsCollector,
  type MetricEvent,
  type MetricsSnapshot,
  type MetricsCallback,
  type EndpointMetrics,
} from './metrics';

// SEC-054: Interceptor exports
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

/**
 * SDK Version
 */
export const VERSION = '1.1.0';
