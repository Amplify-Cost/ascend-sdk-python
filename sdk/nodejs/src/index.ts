/**
 * OW-AI Enterprise SDK for Node.js/TypeScript
 * ============================================
 *
 * Enterprise-grade authorization SDK for AI agent governance.
 *
 * @example
 * ```typescript
 * import { OWKAIClient, AuthorizedAgent } from '@owkai/sdk';
 *
 * // Initialize client
 * const client = new OWKAIClient({ apiKey: 'your-api-key' });
 *
 * // Create authorized agent
 * const agent = new AuthorizedAgent('agent-001', 'My AI Agent', client);
 *
 * // Request authorization
 * const decision = await agent.requestAuthorization({
 *   actionType: ActionType.DATA_ACCESS,
 *   resource: 'customer_data'
 * });
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
  AgentAction,
  AuthorizationDecision,
  ActionType,
  DecisionStatus,
  RiskLevel,
  RiskIndicators,
  ActionContext,
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

/**
 * SDK Version
 */
export const VERSION = '1.0.0';
