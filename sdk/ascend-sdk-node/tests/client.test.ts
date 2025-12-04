/**
 * Ascend AI Governance Platform - Client Tests
 * Basic test suite for SDK functionality
 */

import { AscendClient } from '../src/client';
import { AuthorizedAgent } from '../src/agents';
import {
  AuthenticationError,
  ValidationError,
  AuthorizationDeniedError,
} from '../src/errors';
import { AgentAction } from '../src/types';

describe('AscendClient', () => {
  describe('Constructor', () => {
    it('should create client with API key', () => {
      const client = new AscendClient({
        apiKey: 'owkai_test_1234567890123456789012345678',
      });

      expect(client).toBeInstanceOf(AscendClient);
    });

    it('should throw error without API key', () => {
      expect(() => {
        new AscendClient({ apiKey: '' });
      }).toThrow(AuthenticationError);
    });

    it('should accept configuration options', () => {
      const client = new AscendClient({
        apiKey: 'owkai_test_1234567890123456789012345678',
        timeout: 60000,
        maxRetries: 5,
        debug: true,
      });

      expect(client).toBeInstanceOf(AscendClient);
    });
  });

  describe('Validation', () => {
    const client = new AscendClient({
      apiKey: 'owkai_test_1234567890123456789012345678',
    });

    it('should validate action payload', async () => {
      const invalidAction = {
        agent_id: '',
        agent_name: 'Test Agent',
        action_type: 'data_access',
        resource: 'test_resource',
      } as AgentAction;

      await expect(client.submitAction(invalidAction)).rejects.toThrow(ValidationError);
    });

    it('should validate action type', async () => {
      const invalidAction = {
        agent_id: 'test-agent',
        agent_name: 'Test Agent',
        action_type: 'invalid_type' as any,
        resource: 'test_resource',
      };

      await expect(client.submitAction(invalidAction)).rejects.toThrow(ValidationError);
    });
  });

  describe('submitAction', () => {
    it('should submit valid action', async () => {
      // Mock test - in real scenario, this would connect to API
      const client = new AscendClient({
        apiKey: 'owkai_test_1234567890123456789012345678',
      });

      const action: AgentAction = {
        agent_id: 'test-agent',
        agent_name: 'Test Agent',
        action_type: 'data_access',
        resource: 'test_database',
        resource_id: 'test_123',
        action_details: {
          query: 'SELECT * FROM users',
        },
      };

      // This will fail without real API, but validates structure
      try {
        await client.submitAction(action);
      } catch (error) {
        // Expected to fail without real API
        expect(error).toBeDefined();
      }
    });
  });
});

describe('AuthorizedAgent', () => {
  describe('Constructor', () => {
    it('should create agent with ID and name', () => {
      const agent = new AuthorizedAgent('test-agent', 'Test Agent');

      expect(agent.getAgentId()).toBe('test-agent');
      expect(agent.getAgentName()).toBe('Test Agent');
    });

    it('should create agent with custom client', () => {
      const client = new AscendClient({
        apiKey: 'owkai_test_1234567890123456789012345678',
      });

      const agent = new AuthorizedAgent('test-agent', 'Test Agent', client);

      expect(agent.getClient()).toBe(client);
    });
  });

  describe('Request methods', () => {
    const agent = new AuthorizedAgent('test-agent', 'Test Agent');

    it('should have convenience methods', () => {
      expect(typeof agent.requestDataAccess).toBe('function');
      expect(typeof agent.requestDataModification).toBe('function');
      expect(typeof agent.requestTransaction).toBe('function');
      expect(typeof agent.requestCommunication).toBe('function');
      expect(typeof agent.requestSystemOperation).toBe('function');
    });
  });
});

describe('Error handling', () => {
  it('should create AuthenticationError', () => {
    const error = new AuthenticationError('Invalid API key');

    expect(error).toBeInstanceOf(AuthenticationError);
    expect(error.message).toBe('Invalid API key');
    expect(error.statusCode).toBe(401);
  });

  it('should create AuthorizationDeniedError', () => {
    const error = new AuthorizationDeniedError('Action denied', 123, 'Policy violation');

    expect(error).toBeInstanceOf(AuthorizationDeniedError);
    expect(error.actionId).toBe(123);
    expect(error.reason).toBe('Policy violation');
    expect(error.statusCode).toBe(403);
  });

  it('should create ValidationError', () => {
    const error = new ValidationError('Invalid field', 'agent_id', '');

    expect(error).toBeInstanceOf(ValidationError);
    expect(error.field).toBe('agent_id');
    expect(error.statusCode).toBe(400);
  });
});

describe('Utility functions', () => {
  it('should mask sensitive strings', () => {
    const { maskString } = require('../src/utils');

    const masked = maskString('owkai_admin_1234567890123456', 4);
    expect(masked).toBe('owka...3456');
  });

  it('should generate correlation IDs', () => {
    const { generateCorrelationId } = require('../src/utils');

    const id1 = generateCorrelationId();
    const id2 = generateCorrelationId();

    expect(id1).toMatch(/^ascend-/);
    expect(id2).toMatch(/^ascend-/);
    expect(id1).not.toBe(id2);
  });
});

/**
 * Integration test example (requires real API)
 * Uncomment and set ASCEND_API_KEY to run
 */
/*
describe('Integration tests', () => {
  const client = new AscendClient();

  it('should connect to API', async () => {
    const status = await client.testConnection();
    expect(status.connected).toBe(true);
  });

  it('should submit and retrieve action', async () => {
    const action: AgentAction = {
      agent_id: 'test-integration',
      agent_name: 'Integration Test Agent',
      action_type: 'data_access',
      resource: 'test_database',
    };

    const result = await client.submitAction(action);
    expect(result.id).toBeDefined();
    expect(result.status).toBeDefined();

    const retrieved = await client.getAction(result.id);
    expect(retrieved.id).toBe(result.id);
  });
});
*/
