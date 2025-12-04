/**
 * Ascend AI Governance Platform - Node.js SDK
 * Enterprise-grade AI agent authorization and risk management
 *
 * @packageDocumentation
 */

// Main client
export { AscendClient } from './client';

// Agent wrapper
export { AuthorizedAgent } from './agents';

// Type definitions
export type {
  AgentAction,
  ActionResult,
  ActionType,
  ActionStatus,
  RiskLevel,
  ClientConfig,
  ListParams,
  ListResult,
  ConnectionStatus,
  AuthorizationOptions,
  ExecuteOptions,
} from './types';

// Error classes
export {
  AscendError,
  AuthenticationError,
  AuthorizationDeniedError,
  RateLimitError,
  TimeoutError,
  ValidationError,
  NetworkError,
} from './errors';

// Constants (for advanced usage)
export {
  ACTION_TYPES,
  RISK_LEVELS,
  ACTION_STATUS,
  DEFAULT_API_URL,
  SDK_VERSION,
} from './constants';

// Utilities (for advanced usage)
export {
  generateCorrelationId,
  maskString,
} from './utils';

/**
 * Quick start example:
 *
 * @example
 * ```typescript
 * import { AscendClient, AuthorizedAgent } from '@ascend-ai/sdk';
 *
 * // Option 1: Direct client usage
 * const client = new AscendClient({ apiKey: 'owkai_...' });
 * const result = await client.submitAction({
 *   agent_id: 'gpt-4',
 *   agent_name: 'Customer Support Bot',
 *   action_type: 'data_access',
 *   resource: 'customer_database'
 * });
 *
 * // Option 2: Authorized agent wrapper
 * const agent = new AuthorizedAgent('gpt-4', 'Customer Support Bot');
 * const data = await agent.executeIfAuthorized({
 *   authorization: {
 *     action_type: 'data_access',
 *     resource: 'customer_database'
 *   },
 *   action: async () => {
 *     return await database.getCustomers();
 *   }
 * });
 * ```
 */
