/**
 * ASCEND SDK Client Tests
 * =======================
 *
 * Comprehensive test suite for AscendClient v2.0.
 *
 * Run with: npm test
 */

import {
  AscendClient,
  FailMode,
  Decision,
  CircuitBreaker,
  CircuitState,
  AscendLogger,
  AuthenticationError,
  AuthorizationError,
  CircuitBreakerOpenError,
  ConnectionError,
  TimeoutError,
  RateLimitError,
} from '../src';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    request: jest.fn(),
  })),
}));

describe('FailMode', () => {
  describe('configuration', () => {
    it('should default to CLOSED', () => {
      const client = new AscendClient({
        apiKey: 'test_key',
        agentId: 'test-agent',
        agentName: 'Test Agent',
      });

      expect((client as any).failMode).toBe(FailMode.CLOSED);
    });

    it('should accept OPEN mode', () => {
      const client = new AscendClient({
        apiKey: 'test_key',
        agentId: 'test-agent',
        agentName: 'Test Agent',
        failMode: FailMode.OPEN,
      });

      expect((client as any).failMode).toBe(FailMode.OPEN);
    });
  });
});

describe('CircuitBreaker', () => {
  describe('initial state', () => {
    it('should start in CLOSED state', () => {
      const cb = new CircuitBreaker();
      expect(cb.getState()).toBe(CircuitState.CLOSED);
      expect(cb.getFailures()).toBe(0);
    });
  });

  describe('failure handling', () => {
    it('should open after threshold failures', () => {
      const cb = new CircuitBreaker({ failureThreshold: 3 });

      cb.recordFailure();
      expect(cb.getState()).toBe(CircuitState.CLOSED);

      cb.recordFailure();
      expect(cb.getState()).toBe(CircuitState.CLOSED);

      cb.recordFailure();
      expect(cb.getState()).toBe(CircuitState.OPEN);
    });

    it('should deny requests when open', () => {
      const cb = new CircuitBreaker({ failureThreshold: 1 });
      cb.recordFailure();

      expect(cb.getState()).toBe(CircuitState.OPEN);
      expect(cb.allowRequest()).toBe(false);
    });
  });

  describe('recovery', () => {
    it('should transition to half-open after recovery timeout', () => {
      const cb = new CircuitBreaker({
        failureThreshold: 1,
        recoveryTimeout: 0, // Immediate recovery for test
      });
      cb.recordFailure();

      // With 0 recovery timeout, should allow test request
      expect(cb.allowRequest()).toBe(true);
      expect(cb.getState()).toBe(CircuitState.HALF_OPEN);
    });

    it('should close on success in half-open state', () => {
      const cb = new CircuitBreaker({
        failureThreshold: 1,
        recoveryTimeout: 0,
      });
      cb.recordFailure();
      cb.allowRequest(); // Transitions to half-open

      cb.recordSuccess();
      expect(cb.getState()).toBe(CircuitState.CLOSED);
      expect(cb.getFailures()).toBe(0);
    });

    it('should reopen on failure in half-open state', () => {
      const cb = new CircuitBreaker({
        failureThreshold: 1,
        recoveryTimeout: 0,
      });
      cb.recordFailure();
      cb.allowRequest(); // Transitions to half-open

      cb.recordFailure();
      expect(cb.getState()).toBe(CircuitState.OPEN);
    });
  });

  describe('reset', () => {
    it('should return to initial state', () => {
      const cb = new CircuitBreaker({ failureThreshold: 1 });
      cb.recordFailure();
      expect(cb.getState()).toBe(CircuitState.OPEN);

      cb.reset();
      expect(cb.getState()).toBe(CircuitState.CLOSED);
      expect(cb.getFailures()).toBe(0);
    });
  });
});

describe('AscendLogger', () => {
  let consoleSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleSpy = jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  describe('API key masking', () => {
    it('should mask API keys in log output', () => {
      const logger = new AscendLogger({ level: 'INFO', jsonFormat: false });
      logger.info('Testing with owkai_secret_key_12345');

      const output = consoleSpy.mock.calls[0][0];
      expect(output).not.toContain('owkai_secret_key_12345');
      expect(output).toContain('owkai_****');
    });
  });

  describe('JSON format', () => {
    it('should output valid JSON when configured', () => {
      const logger = new AscendLogger({ level: 'INFO', jsonFormat: true });
      logger.info('Test message', { extraField: 'test' });

      const output = consoleSpy.mock.calls[0][0];
      const logEntry = JSON.parse(output);

      expect(logEntry.message).toBe('Test message');
      expect(logEntry.level).toBe('INFO');
    });
  });

  describe('log levels', () => {
    it('should respect configured log level', () => {
      const logger = new AscendLogger({ level: 'WARNING' });

      logger.debug('Debug message');
      logger.info('Info message');

      // Debug and Info should not be logged at WARNING level
      expect(consoleSpy).not.toHaveBeenCalled();

      logger.warning('Warning message');
      expect(consoleSpy).toHaveBeenCalled();
    });
  });
});

describe('AscendClient', () => {
  describe('initialization', () => {
    it('should initialize with required parameters', () => {
      const client = new AscendClient({
        apiKey: 'owkai_test_key',
        agentId: 'agent-001',
        agentName: 'Test Agent',
      });

      expect((client as any).agentId).toBe('agent-001');
      expect((client as any).agentName).toBe('Test Agent');
    });

    it('should use environment variable for API URL', () => {
      process.env.ASCEND_API_URL = 'https://custom.api.url';

      const client = new AscendClient({
        apiKey: 'test_key',
        agentId: 'test-agent',
        agentName: 'Test Agent',
      });

      expect((client as any).apiUrl).toBe('https://custom.api.url');

      delete process.env.ASCEND_API_URL;
    });
  });

  describe('circuit breaker integration', () => {
    it('should expose circuit breaker state', () => {
      const client = new AscendClient({
        apiKey: 'test_key',
        agentId: 'test-agent',
        agentName: 'Test Agent',
      });

      const state = client.getCircuitBreakerState();
      expect(state.state).toBe(CircuitState.CLOSED);
      expect(state.failures).toBe(0);
    });

    it('should allow circuit breaker reset', () => {
      const client = new AscendClient({
        apiKey: 'test_key',
        agentId: 'test-agent',
        agentName: 'Test Agent',
      });

      // Manually trigger failures through internal circuit breaker
      const cb = (client as any).circuitBreaker;
      cb.recordFailure();
      cb.recordFailure();
      cb.recordFailure();
      cb.recordFailure();
      cb.recordFailure();

      expect(cb.getState()).toBe(CircuitState.OPEN);

      client.resetCircuitBreaker();
      expect(cb.getState()).toBe(CircuitState.CLOSED);
    });
  });
});

describe('Decision enum', () => {
  it('should have correct values', () => {
    expect(Decision.ALLOWED).toBe('allowed');
    expect(Decision.DENIED).toBe('denied');
    expect(Decision.PENDING).toBe('pending');
  });
});

describe('Error classes', () => {
  describe('AuthenticationError', () => {
    it('should include correct error code', () => {
      const error = new AuthenticationError('Invalid API key');
      expect(error.code).toBe('AUTH_ERROR');
      expect(error.message).toBe('Invalid API key');
    });
  });

  describe('AuthorizationError', () => {
    it('should include policy violations', () => {
      const error = new AuthorizationError(
        'Access denied',
        ['POLICY_1', 'POLICY_2'],
        85
      );

      expect(error.code).toBe('AUTHZ_DENIED');
      expect(error.policyViolations).toEqual(['POLICY_1', 'POLICY_2']);
      expect(error.riskScore).toBe(85);
    });
  });

  describe('CircuitBreakerOpenError', () => {
    it('should include recovery time', () => {
      const error = new CircuitBreakerOpenError(
        'Service unavailable',
        30
      );

      expect(error.code).toBe('CIRCUIT_OPEN');
      expect(error.recoveryTimeSeconds).toBe(30);
    });
  });

  describe('TimeoutError', () => {
    it('should include timeout duration', () => {
      const error = new TimeoutError('Request timed out', 30000);
      expect(error.code).toBe('TIMEOUT');
      expect(error.timeoutMs).toBe(30000);
    });
  });

  describe('RateLimitError', () => {
    it('should include retry after', () => {
      const error = new RateLimitError('Rate limit exceeded', 60);
      expect(error.code).toBe('RATE_LIMIT');
      expect(error.retryAfter).toBe(60);
    });
  });

  describe('toJSON', () => {
    it('should serialize error to JSON', () => {
      const error = new AuthorizationError('Denied', ['POLICY_X'], 90);
      const json = error.toJSON();

      expect(json).toHaveProperty('name', 'AuthorizationError');
      expect(json).toHaveProperty('message', 'Denied');
      expect(json).toHaveProperty('code', 'AUTHZ_DENIED');
      expect(json.details).toHaveProperty('policyViolations', ['POLICY_X']);
    });
  });
});

describe('FailMode enum', () => {
  it('should have correct values', () => {
    expect(FailMode.CLOSED).toBe('closed');
    expect(FailMode.OPEN).toBe('open');
  });
});
