#!/usr/bin/env node
/**
 * OW-AI Enterprise SDK Integration Example (Node.js)
 * ===================================================
 *
 * This example demonstrates how to integrate OW-AI Authorization Center
 * into your AI agent infrastructure for enterprise-grade governance.
 *
 * Prerequisites:
 * - Node.js 16+
 * - npm install axios dotenv
 *
 * Environment Variables:
 * - OWKAI_API_URL: API endpoint (default: https://pilot.owkai.app)
 * - OWKAI_API_KEY: Your organization's API key
 * - OWKAI_ORG_SLUG: Your organization slug
 *
 * Usage:
 *   node nodejs_sdk_example.js
 *
 * Security Standards:
 * - SOC 2 Type II Compliant
 * - PCI-DSS 8.3 (MFA)
 * - HIPAA 164.312 (Audit)
 * - NIST 800-63B (Authentication)
 *
 * Author: OW-AI Enterprise
 * Date: 2025-11-30
 */

require('dotenv').config();
const axios = require('axios');

// Configuration
const CONFIG = {
  apiUrl: process.env.OWKAI_API_URL || 'https://pilot.owkai.app',
  apiKey: process.env.OWKAI_API_KEY,
  orgSlug: process.env.OWKAI_ORG_SLUG,
  timeout: 30000,
  debug: process.env.DEBUG === 'true'
};

/**
 * Logger utility
 */
const logger = {
  info: (msg, ...args) => console.log(`[INFO] ${new Date().toISOString()} - ${msg}`, ...args),
  debug: (msg, ...args) => CONFIG.debug && console.log(`[DEBUG] ${new Date().toISOString()} - ${msg}`, ...args),
  error: (msg, ...args) => console.error(`[ERROR] ${new Date().toISOString()} - ${msg}`, ...args),
  warn: (msg, ...args) => console.warn(`[WARN] ${new Date().toISOString()} - ${msg}`, ...args)
};

/**
 * Action types supported by OW-AI
 */
const ActionType = {
  DATA_ACCESS: 'data_access',
  DATA_MODIFICATION: 'data_modification',
  TRANSACTION: 'transaction',
  RECOMMENDATION: 'recommendation',
  COMMUNICATION: 'communication',
  SYSTEM_OPERATION: 'system_operation'
};

/**
 * Decision statuses
 */
const DecisionStatus = {
  PENDING: 'pending',
  APPROVED: 'approved',
  DENIED: 'denied',
  REQUIRES_MODIFICATION: 'requires_modification',
  TIMEOUT: 'timeout'
};

/**
 * OW-AI Authorization Center SDK Client
 *
 * Enterprise-grade client for submitting agent actions
 * for authorization and policy enforcement.
 */
class OWKAIClient {
  /**
   * Initialize the OW-AI client
   * @param {Object} options - Client options
   * @param {string} options.apiUrl - API endpoint URL
   * @param {string} options.apiKey - Organization API key
   * @param {string} options.orgSlug - Organization identifier
   * @param {number} options.timeout - Request timeout in ms
   * @param {boolean} options.debug - Enable debug logging
   */
  constructor(options = {}) {
    this.apiUrl = options.apiUrl || CONFIG.apiUrl;
    this.apiKey = options.apiKey || CONFIG.apiKey;
    this.orgSlug = options.orgSlug || CONFIG.orgSlug;
    this.timeout = options.timeout || CONFIG.timeout;

    if (!this.apiKey) {
      throw new Error('API key is required. Set OWKAI_API_KEY environment variable.');
    }

    // SEC-033: Support both X-API-Key header and Authorization Bearer
    this.headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      'Authorization': `Bearer ${this.apiKey}`,
      'User-Agent': 'OWKAIClient/2.0 NodeJS'
    };

    this.client = axios.create({
      baseURL: this.apiUrl,
      headers: this.headers,
      timeout: this.timeout
    });

    logger.info(`OW-AI Client initialized for ${this.apiUrl}`);
  }

  /**
   * Make authenticated request to API
   * @private
   */
  async _request(method, endpoint, data = null, params = null) {
    logger.debug(`${method.toUpperCase()} ${endpoint}`);

    try {
      const response = await this.client.request({
        method,
        url: endpoint,
        data,
        params
      });

      return response.data;

    } catch (error) {
      if (error.response) {
        const detail = error.response.data?.detail || error.message;
        logger.error(`API Error: ${detail}`);
        throw new Error(`API Error: ${detail}`);
      } else if (error.code === 'ECONNABORTED') {
        logger.error('Request timeout');
        throw new Error('API request timed out');
      } else {
        logger.error(`Connection error: ${error.message}`);
        throw new Error('Failed to connect to OW-AI API');
      }
    }
  }

  /**
   * Test API connectivity and authentication
   * @returns {Promise<Object>} Connection status
   */
  async testConnection() {
    try {
      const health = await this._request('get', '/health');
      const deployment = await this._request('get', '/api/deployment-info');

      return {
        status: 'connected',
        apiVersion: deployment.version || 'unknown',
        serverTime: new Date().toISOString()
      };
    } catch (error) {
      return {
        status: 'error',
        error: error.message
      };
    }
  }

  /**
   * Submit an agent action for authorization
   * @param {Object} action - Action details
   * @returns {Promise<Object>} Authorization response
   */
  async submitAction(action) {
    logger.info(`Submitting action: ${action.actionType} on ${action.resource}`);

    const payload = {
      agent_id: action.agentId,
      agent_name: action.agentName,
      action_type: action.actionType,
      resource: action.resource,
      resource_id: action.resourceId,
      action_details: action.details,
      context: action.context,
      risk_indicators: action.riskIndicators
    };

    const response = await this._request('post', '/api/authorization/agent-action', payload);

    logger.info(`Action submitted: ${response.action_id} - Status: ${response.status}`);
    return response;
  }

  /**
   * Get the current status of an action
   * @param {string} actionId - The action ID
   * @returns {Promise<Object>} Current status
   */
  async getActionStatus(actionId) {
    return this._request('get', `/api/agent-action/status/${actionId}`);
  }

  /**
   * Wait for an authorization decision
   * @param {string} actionId - The action ID
   * @param {number} timeout - Max wait time in ms
   * @param {number} pollInterval - Polling interval in ms
   * @returns {Promise<Object>} Final decision
   */
  async waitForDecision(actionId, timeout = 60000, pollInterval = 2000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const status = await this.getActionStatus(actionId);

      if (status.decision !== 'pending') {
        return status;
      }

      logger.debug(`Action ${actionId} still pending...`);
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    return {
      action_id: actionId,
      decision: 'timeout',
      error: `Decision not received within ${timeout}ms`
    };
  }

  /**
   * List recent agent actions
   * @param {Object} options - Query options
   * @returns {Promise<Object>} List of actions
   */
  async listActions(options = {}) {
    const params = {
      limit: options.limit || 50,
      offset: options.offset || 0
    };

    if (options.status) {
      params.status = options.status;
    }

    return this._request('get', '/api/agent-activity', null, params);
  }

  /**
   * Get detailed information about an action
   * @param {string} actionId - The action ID
   * @returns {Promise<Object>} Full action details
   */
  async getActionDetails(actionId) {
    return this._request('get', `/api/agent-action/${actionId}`);
  }
}

/**
 * Wrapper for AI agents that require OW-AI authorization
 */
class AuthorizedAgent {
  /**
   * Initialize an authorized agent
   * @param {string} agentId - Unique agent identifier
   * @param {string} agentName - Human-readable agent name
   * @param {OWKAIClient} client - OWKAIClient instance
   */
  constructor(agentId, agentName, client = null) {
    this.agentId = agentId;
    this.agentName = agentName;
    this.client = client || new OWKAIClient();
  }

  /**
   * Request authorization for an action
   * @param {Object} options - Action options
   * @returns {Promise<Object>} Authorization decision
   */
  async requestAuthorization(options) {
    const {
      actionType,
      resource,
      resourceId,
      details,
      context,
      riskIndicators,
      waitForDecision = true,
      timeout = 60000
    } = options;

    const action = {
      agentId: this.agentId,
      agentName: this.agentName,
      actionType,
      resource,
      resourceId,
      details,
      context,
      riskIndicators
    };

    const response = await this.client.submitAction(action);

    if (waitForDecision && response.decision === 'pending') {
      return this.client.waitForDecision(response.action_id, timeout);
    }

    return response;
  }

  /**
   * Execute a function only if authorized
   * @param {Object} options - Action and execution options
   * @param {Function} executeFn - Function to execute if authorized
   * @returns {Promise<any>} Result of executeFn
   * @throws {Error} If action is denied or times out
   */
  async executeIfAuthorized(options, executeFn) {
    const decision = await this.requestAuthorization({
      ...options,
      waitForDecision: true
    });

    const status = decision.decision || decision.status;

    if (status === 'approved') {
      logger.info('Action authorized, executing...');
      return executeFn();
    } else if (status === 'denied') {
      const reason = decision.reason || 'No reason provided';
      throw new Error(`Permission denied: ${reason}`);
    } else if (status === 'timeout') {
      throw new Error('Authorization decision timed out');
    } else {
      throw new Error(`Unexpected authorization status: ${status}`);
    }
  }
}

// =============================================================================
// Example Usage
// =============================================================================

async function exampleFinancialAdvisorAgent() {
  console.log('\n' + '='.repeat(60));
  console.log('OW-AI SDK Example: Financial Advisor Agent (Node.js)');
  console.log('='.repeat(60) + '\n');

  // Initialize client
  let client;
  try {
    client = new OWKAIClient();

    // Test connection
    console.log('Testing connection...');
    const connStatus = await client.testConnection();
    console.log(`Connection: ${connStatus.status}`);

    if (connStatus.status !== 'connected') {
      console.log(`Error: ${connStatus.error}`);
      return;
    }

  } catch (error) {
    console.log(`Failed to initialize client: ${error.message}`);
    console.log('\nMake sure OWKAI_API_KEY is set in your environment.');
    return;
  }

  // Create authorized agent
  const agent = new AuthorizedAgent(
    'financial-advisor-001',
    'Financial Advisor AI',
    client
  );

  // Example 1: Low-risk action (should auto-approve)
  console.log('\n--- Example 1: Low-Risk Query ---');
  try {
    const decision = await agent.requestAuthorization({
      actionType: ActionType.DATA_ACCESS,
      resource: 'market_data',
      details: {
        operation: 'read',
        dataType: 'public_prices'
      },
      riskIndicators: {
        pii_involved: false,
        financial_data: false
      }
    });
    console.log(`Decision: ${decision.decision || decision.status}`);

  } catch (error) {
    console.log(`Error: ${error.message}`);
  }

  // Example 2: Medium-risk action (may require review)
  console.log('\n--- Example 2: Customer Data Access ---');
  try {
    const decision = await agent.requestAuthorization({
      actionType: ActionType.DATA_ACCESS,
      resource: 'customer_portfolio',
      resourceId: 'CUST-12345',
      details: {
        operation: 'read',
        fields: ['balance', 'holdings']
      },
      context: {
        user_request: 'Show my portfolio',
        session_id: 'sess_abc123'
      },
      riskIndicators: {
        pii_involved: true,
        financial_data: true,
        data_sensitivity: 'medium'
      }
    });
    console.log(`Decision: ${decision.decision || decision.status}`);
    console.log(`Risk Score: ${decision.risk_score || 'N/A'}`);

  } catch (error) {
    console.log(`Error: ${error.message}`);
  }

  // Example 3: High-risk action (likely requires approval)
  console.log('\n--- Example 3: High-Value Transaction ---');
  try {
    const decision = await agent.requestAuthorization({
      actionType: ActionType.TRANSACTION,
      resource: 'customer_account',
      resourceId: 'ACC-98765',
      details: {
        operation: 'transfer',
        amount: 50000,
        currency: 'USD',
        destination: 'external_account'
      },
      context: {
        user_request: 'Transfer $50,000 to my savings',
        ip_address: '192.168.1.100'
      },
      riskIndicators: {
        amount_threshold: 'exceeded',
        external_transfer: true,
        data_sensitivity: 'critical'
      },
      timeout: 30000  // Shorter timeout for demo
    });
    console.log(`Decision: ${decision.decision || decision.status}`);

    if (decision.decision === 'pending') {
      console.log('Action requires manual review by compliance officer');
    }

  } catch (error) {
    if (error.message.includes('Permission denied')) {
      console.log(`Action denied: ${error.message}`);
    } else if (error.message.includes('timeout')) {
      console.log('Decision pending - requires manual approval');
    } else {
      console.log(`Error: ${error.message}`);
    }
  }

  // Example 4: Execute with authorization
  console.log('\n--- Example 4: Conditional Execution ---');

  const getPortfolioData = () => ({
    balance: 125000.00,
    holdings: ['AAPL', 'GOOGL', 'MSFT'],
    lastUpdated: new Date().toISOString()
  });

  try {
    const result = await agent.executeIfAuthorized(
      {
        actionType: ActionType.DATA_ACCESS,
        resource: 'portfolio_summary',
        details: { operation: 'read' },
        riskIndicators: { pii_involved: false }
      },
      getPortfolioData
    );
    console.log('Authorized result:', result);

  } catch (error) {
    if (error.message.includes('Permission denied')) {
      console.log(`Not authorized: ${error.message}`);
    } else {
      console.log(`Error: ${error.message}`);
    }
  }

  // List recent actions
  console.log('\n--- Recent Actions ---');
  try {
    const actions = await client.listActions({ limit: 5 });
    (actions.actions || []).forEach(action => {
      console.log(`  - ${action.action_id}: ${action.action_type} -> ${action.status}`);
    });
  } catch (error) {
    console.log(`Error listing actions: ${error.message}`);
  }

  // ==========================================================================
  // SEC-054: New Features - Batch Submission, Metrics, Interceptors
  // ==========================================================================

  // Example 5: Batch Action Submission
  console.log('\n--- Example 5: Batch Action Submission (SEC-054) ---');
  try {
    const batchActions = [
      {
        agentId: 'batch-agent-001',
        agentName: 'Batch Processor',
        actionType: ActionType.DATA_ACCESS,
        resource: 'inventory_db',
        details: { operation: 'read', table: 'products' }
      },
      {
        agentId: 'batch-agent-001',
        agentName: 'Batch Processor',
        actionType: ActionType.DATA_ACCESS,
        resource: 'customer_db',
        details: { operation: 'read', table: 'orders' }
      },
      {
        agentId: 'batch-agent-001',
        agentName: 'Batch Processor',
        actionType: ActionType.DATA_MODIFICATION,
        resource: 'reports_db',
        details: { operation: 'write', table: 'daily_summary' }
      }
    ];

    // Note: submitActionBatch is available in the TypeScript SDK
    // For JavaScript, we can simulate batch processing:
    console.log(`Submitting ${batchActions.length} actions in batch...`);
    const startTime = Date.now();
    const results = await Promise.all(
      batchActions.map(async (action, index) => {
        try {
          const decision = await client.submitAction(action);
          return { index, success: true, actionId: decision.action_id, decision: decision.decision };
        } catch (error) {
          return { index, success: false, error: error.message };
        }
      })
    );
    const duration = Date.now() - startTime;

    const successCount = results.filter(r => r.success).length;
    console.log(`Batch complete: ${successCount}/${batchActions.length} succeeded in ${duration}ms`);
    results.forEach(r => {
      if (r.success) {
        console.log(`  - Action ${r.index}: ${r.decision} (ID: ${r.actionId})`);
      } else {
        console.log(`  - Action ${r.index}: FAILED - ${r.error}`);
      }
    });

  } catch (error) {
    console.log(`Batch error: ${error.message}`);
  }

  // Example 6: SDK Metrics (SEC-054)
  console.log('\n--- Example 6: SDK Metrics (SEC-054) ---');
  // Note: Full metrics API available in TypeScript SDK
  // Here's how to track your own metrics:
  const metricsTracker = {
    requests: 0,
    errors: 0,
    totalLatency: 0,
    getSnapshot: function() {
      return {
        totalRequests: this.requests,
        errorCount: this.errors,
        avgLatency: this.requests > 0 ? Math.round(this.totalLatency / this.requests) : 0,
        successRate: this.requests > 0 ? (this.requests - this.errors) / this.requests : 0
      };
    }
  };

  // Track a few requests
  for (let i = 0; i < 3; i++) {
    const start = Date.now();
    try {
      await client.testConnection();
      metricsTracker.requests++;
      metricsTracker.totalLatency += Date.now() - start;
    } catch (e) {
      metricsTracker.requests++;
      metricsTracker.errors++;
      metricsTracker.totalLatency += Date.now() - start;
    }
  }

  const metrics = metricsTracker.getSnapshot();
  console.log(`Metrics Snapshot:`);
  console.log(`  - Total Requests: ${metrics.totalRequests}`);
  console.log(`  - Success Rate: ${(metrics.successRate * 100).toFixed(1)}%`);
  console.log(`  - Avg Latency: ${metrics.avgLatency}ms`);

  console.log('\n' + '='.repeat(60));
  console.log('Example Complete');
  console.log('='.repeat(60) + '\n');
}

// Export for module usage
module.exports = {
  OWKAIClient,
  AuthorizedAgent,
  ActionType,
  DecisionStatus
};

// Run if executed directly
if (require.main === module) {
  exampleFinancialAdvisorAgent().catch(console.error);
}
