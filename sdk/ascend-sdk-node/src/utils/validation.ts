/**
 * Ascend AI Governance Platform - Input Validation
 * Enterprise-grade validation for API requests
 *
 * @module utils/validation
 */

import {
  AgentAction,
  ActionType,
  ListParams,
  ClientConfig,
} from '../types';
import { ValidationError } from '../errors';
import {
  ACTION_TYPES,
  SECURITY,
  MAX_PAGE_LIMIT,
} from '../constants';

/**
 * Validates API key format
 */
export function validateApiKey(apiKey: string): void {
  if (!apiKey || typeof apiKey !== 'string') {
    throw ValidationError.requiredField('apiKey');
  }

  if (apiKey.length < SECURITY.MIN_API_KEY_LENGTH) {
    throw new ValidationError(
      `API key must be at least ${SECURITY.MIN_API_KEY_LENGTH} characters`,
      'apiKey',
      apiKey.length
    );
  }

  if (!apiKey.startsWith(SECURITY.API_KEY_PREFIX)) {
    throw new ValidationError(
      `API key must start with '${SECURITY.API_KEY_PREFIX}'`,
      'apiKey'
    );
  }
}

/**
 * Validates action type
 */
export function validateActionType(actionType: string): ActionType {
  const validTypes = Object.values(ACTION_TYPES);

  if (!validTypes.includes(actionType as ActionType)) {
    throw ValidationError.invalidValue(
      'action_type',
      actionType,
      validTypes.join(', ')
    );
  }

  return actionType as ActionType;
}

/**
 * Validates agent action payload
 */
export function validateAgentAction(action: AgentAction): void {
  // Required fields
  if (!action.agent_id || typeof action.agent_id !== 'string') {
    throw ValidationError.requiredField('agent_id');
  }

  if (!action.agent_name || typeof action.agent_name !== 'string') {
    throw ValidationError.requiredField('agent_name');
  }

  if (!action.resource || typeof action.resource !== 'string') {
    throw ValidationError.requiredField('resource');
  }

  // Validate action type
  validateActionType(action.action_type);

  // Validate string lengths
  if (action.agent_id.length > 100) {
    throw new ValidationError(
      'agent_id must be 100 characters or less',
      'agent_id',
      action.agent_id.length
    );
  }

  if (action.agent_name.length > 200) {
    throw new ValidationError(
      'agent_name must be 200 characters or less',
      'agent_name',
      action.agent_name.length
    );
  }

  if (action.resource.length > 200) {
    throw new ValidationError(
      'resource must be 200 characters or less',
      'resource',
      action.resource.length
    );
  }

  // Validate optional fields are objects
  if (action.action_details !== undefined && typeof action.action_details !== 'object') {
    throw ValidationError.invalidValue(
      'action_details',
      typeof action.action_details,
      'object'
    );
  }

  if (action.context !== undefined && typeof action.context !== 'object') {
    throw ValidationError.invalidValue(
      'context',
      typeof action.context,
      'object'
    );
  }

  if (action.risk_indicators !== undefined && typeof action.risk_indicators !== 'object') {
    throw ValidationError.invalidValue(
      'risk_indicators',
      typeof action.risk_indicators,
      'object'
    );
  }
}

/**
 * Validates list parameters
 */
export function validateListParams(params: ListParams): void {
  if (params.page !== undefined) {
    if (!Number.isInteger(params.page) || params.page < 1) {
      throw ValidationError.invalidValue('page', params.page, 'positive integer');
    }
  }

  if (params.limit !== undefined) {
    if (!Number.isInteger(params.limit) || params.limit < 1) {
      throw ValidationError.invalidValue('limit', params.limit, 'positive integer');
    }

    if (params.limit > MAX_PAGE_LIMIT) {
      throw new ValidationError(
        `limit cannot exceed ${MAX_PAGE_LIMIT}`,
        'limit',
        params.limit
      );
    }
  }

  if (params.start_date !== undefined) {
    try {
      new Date(params.start_date);
    } catch {
      throw ValidationError.invalidValue('start_date', params.start_date, 'ISO 8601 date string');
    }
  }

  if (params.end_date !== undefined) {
    try {
      new Date(params.end_date);
    } catch {
      throw ValidationError.invalidValue('end_date', params.end_date, 'ISO 8601 date string');
    }
  }
}

/**
 * Validates client configuration
 */
export function validateClientConfig(config: ClientConfig): void {
  if (config.timeout !== undefined) {
    if (!Number.isInteger(config.timeout) || config.timeout < 1000) {
      throw ValidationError.invalidValue(
        'timeout',
        config.timeout,
        'integer >= 1000ms'
      );
    }
  }

  if (config.maxRetries !== undefined) {
    if (!Number.isInteger(config.maxRetries) || config.maxRetries < 0) {
      throw ValidationError.invalidValue(
        'maxRetries',
        config.maxRetries,
        'non-negative integer'
      );
    }
  }

  if (config.baseUrl !== undefined && typeof config.baseUrl !== 'string') {
    throw ValidationError.invalidValue(
      'baseUrl',
      typeof config.baseUrl,
      'string'
    );
  }

  if (config.debug !== undefined && typeof config.debug !== 'boolean') {
    throw ValidationError.invalidValue(
      'debug',
      typeof config.debug,
      'boolean'
    );
  }
}

/**
 * Validates action ID
 */
export function validateActionId(actionId: number): void {
  if (!Number.isInteger(actionId) || actionId < 1) {
    throw ValidationError.invalidValue('actionId', actionId, 'positive integer');
  }
}

/**
 * Sanitizes user input to prevent injection attacks
 */
export function sanitizeString(input: string, maxLength: number = 1000): string {
  if (typeof input !== 'string') {
    return String(input).substring(0, maxLength);
  }

  // Remove null bytes
  return input.replace(/\0/g, '').substring(0, maxLength);
}
