/**
 * SEC-055: Interactive API Explorer
 *
 * Enterprise-grade API testing and documentation UI
 * Aligned with Stripe/Twilio/Postman patterns
 *
 * Features:
 * - Endpoint directory with categories
 * - Request builder (method, URL, headers, body)
 * - Response viewer with JSON syntax highlighting
 * - Code generation (Python, Node.js, cURL)
 * - API key selector for authentication
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-12-03
 * Compliance: SOC 2 CC6.1, NIST SI-4
 */

import React, { useState, useEffect, useCallback } from 'react';

// API Endpoint Categories with documentation
const API_CATEGORIES = {
  authorization: {
    name: 'Authorization',
    icon: '🔐',
    description: 'Submit and manage AI agent actions for authorization',
    endpoints: [
      {
        id: 'submit-action',
        method: 'POST',
        path: '/api/authorization/agent-action',
        name: 'Submit Agent Action',
        description: 'Submit an AI agent action for authorization review',
        requiresAuth: true,
        bodySchema: {
          agent_id: { type: 'string', required: true, example: 'agent-001' },
          agent_name: { type: 'string', required: true, example: 'Financial Advisor AI' },
          action_type: { type: 'string', required: true, example: 'data_access' },
          resource: { type: 'string', required: true, example: 'customer_data' },
          resource_id: { type: 'string', required: false, example: 'CUST-12345' },
          action_details: { type: 'object', required: false, example: { operation: 'read' } }
        }
      },
      {
        id: 'get-pending',
        method: 'GET',
        path: '/api/authorization/pending-actions',
        name: 'Get Pending Actions',
        description: 'List all actions awaiting approval',
        requiresAuth: true,
        queryParams: {
          limit: { type: 'number', required: false, example: 50 },
          offset: { type: 'number', required: false, example: 0 }
        }
      },
      {
        id: 'approve-action',
        method: 'POST',
        path: '/api/authorization/authorize/{action_id}',
        name: 'Approve/Deny Action',
        description: 'Approve or deny a pending action',
        requiresAuth: true,
        pathParams: {
          action_id: { type: 'string', required: true, example: 'act-123' }
        },
        bodySchema: {
          approved: { type: 'boolean', required: true, example: true },
          comments: { type: 'string', required: false, example: 'Approved per policy' }
        }
      },
      {
        id: 'action-status',
        method: 'GET',
        path: '/api/agent-action/status/{action_id}',
        name: 'Get Action Status',
        description: 'Check the current status of an action',
        requiresAuth: true,
        pathParams: {
          action_id: { type: 'string', required: true, example: 'act-123' }
        }
      }
    ]
  },
  apiKeys: {
    name: 'API Keys',
    icon: '🔑',
    description: 'Generate and manage API keys for SDK authentication',
    endpoints: [
      {
        id: 'generate-key',
        method: 'POST',
        path: '/api/keys/generate',
        name: 'Generate API Key',
        description: 'Create a new API key for SDK integration',
        requiresAuth: true,
        bodySchema: {
          name: { type: 'string', required: true, example: 'Production SDK Key' },
          description: { type: 'string', required: false, example: 'Key for production agents' },
          expires_in_days: { type: 'number', required: false, example: 365 }
        },
        warning: 'This will create a new API key. Store the key securely - it will only be shown once.'
      },
      {
        id: 'list-keys',
        method: 'GET',
        path: '/api/keys/list',
        name: 'List API Keys',
        description: 'Get all API keys for your organization',
        requiresAuth: true
      },
      {
        id: 'key-usage',
        method: 'GET',
        path: '/api/keys/{key_id}/usage',
        name: 'Get Key Usage',
        description: 'View usage statistics for a specific API key',
        requiresAuth: true,
        pathParams: {
          key_id: { type: 'string', required: true, example: 'key-123' }
        }
      },
      {
        id: 'revoke-key',
        method: 'DELETE',
        path: '/api/keys/{key_id}',
        name: 'Revoke API Key',
        description: 'Permanently revoke an API key',
        requiresAuth: true,
        pathParams: {
          key_id: { type: 'string', required: true, example: 'key-123' }
        },
        warning: 'This action cannot be undone. All integrations using this key will stop working.'
      }
    ]
  },
  governance: {
    name: 'Governance',
    icon: '📋',
    description: 'Manage policies and governance rules',
    endpoints: [
      {
        id: 'list-policies',
        method: 'GET',
        path: '/api/governance/policies',
        name: 'List Policies',
        description: 'Get all governance policies',
        requiresAuth: true
      },
      {
        id: 'create-policy',
        method: 'POST',
        path: '/api/governance/policies/create',
        name: 'Create Policy',
        description: 'Create a new governance policy',
        requiresAuth: true,
        bodySchema: {
          policy_name: { type: 'string', required: true, example: 'Block PII Access' },
          description: { type: 'string', required: true, example: 'Prevent unauthorized PII access' },
          effect: { type: 'string', required: true, example: 'deny' },
          actions: { type: 'array', required: false, example: ['read', 'write'] },
          resources: { type: 'array', required: false, example: ['pii:*'] }
        }
      },
      {
        id: 'evaluate-policy',
        method: 'POST',
        path: '/api/governance/policies/evaluate',
        name: 'Evaluate Policy',
        description: 'Test policy evaluation against a sample action',
        requiresAuth: true,
        bodySchema: {
          agent_id: { type: 'string', required: true, example: 'agent-001' },
          action_type: { type: 'string', required: true, example: 'data_access' },
          resource: { type: 'string', required: true, example: 'customer_pii' }
        }
      },
      {
        id: 'policy-templates',
        method: 'GET',
        path: '/api/governance/policies/templates/search',
        name: 'Search Templates',
        description: 'Search policy templates by compliance framework',
        requiresAuth: true,
        queryParams: {
          compliance: { type: 'string', required: false, example: 'SOC2' },
          severity: { type: 'string', required: false, example: 'HIGH' }
        }
      }
    ]
  },
  agents: {
    name: 'Agent Registry',
    icon: '🤖',
    description: 'Register and manage AI agents',
    endpoints: [
      {
        id: 'list-agents',
        method: 'GET',
        path: '/api/agent-activity',
        name: 'List Agent Activity',
        description: 'Get recent agent activity and actions',
        requiresAuth: true,
        queryParams: {
          limit: { type: 'number', required: false, example: 50 },
          status: { type: 'string', required: false, example: 'approved' }
        }
      },
      {
        id: 'agent-details',
        method: 'GET',
        path: '/api/agent-action/{action_id}',
        name: 'Get Action Details',
        description: 'Get detailed information about a specific action',
        requiresAuth: true,
        pathParams: {
          action_id: { type: 'string', required: true, example: 'act-123' }
        }
      }
    ]
  },
  analytics: {
    name: 'Analytics',
    icon: '📊',
    description: 'Risk metrics and analytics',
    endpoints: [
      {
        id: 'risk-metrics',
        method: 'GET',
        path: '/api/analytics/risk-metrics',
        name: 'Get Risk Metrics',
        description: 'Get risk scoring analytics and trends',
        requiresAuth: true
      },
      {
        id: 'ai-insights',
        method: 'GET',
        path: '/api/ai-insights',
        name: 'AI Insights',
        description: 'Get AI-powered security insights and recommendations',
        requiresAuth: true
      }
    ]
  },
  health: {
    name: 'Health & Status',
    icon: '💚',
    description: 'API health and deployment info',
    endpoints: [
      {
        id: 'health-check',
        method: 'GET',
        path: '/health',
        name: 'Health Check',
        description: 'Check API health status',
        requiresAuth: false
      },
      {
        id: 'deployment-info',
        method: 'GET',
        path: '/api/deployment-info',
        name: 'Deployment Info',
        description: 'Get deployment version and build info',
        requiresAuth: false
      }
    ]
  }
};

// Method color mapping
const METHOD_COLORS = {
  GET: 'bg-green-100 text-green-800 border-green-200',
  POST: 'bg-blue-100 text-blue-800 border-blue-200',
  PUT: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  DELETE: 'bg-red-100 text-red-800 border-red-200',
  PATCH: 'bg-purple-100 text-purple-800 border-purple-200'
};

const InteractiveApiExplorer = ({ getAuthHeaders, API_BASE_URL }) => {
  // State
  const [selectedCategory, setSelectedCategory] = useState('authorization');
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [requestBody, setRequestBody] = useState('{}');
  const [pathParams, setPathParams] = useState({});
  const [queryParams, setQueryParams] = useState({});
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [responseTime, setResponseTime] = useState(null);
  const [codeLanguage, setCodeLanguage] = useState('curl');
  const [searchQuery, setSearchQuery] = useState('');

  // Handle endpoint selection
  const handleSelectEndpoint = useCallback((endpoint) => {
    setSelectedEndpoint(endpoint);
    setResponse(null);
    setError(null);
    setResponseTime(null);

    // Initialize path params
    if (endpoint.pathParams) {
      const params = {};
      Object.entries(endpoint.pathParams).forEach(([key, paramConfig]) => {
        params[key] = paramConfig.example || '';
      });
      setPathParams(params);
    } else {
      setPathParams({});
    }

    // Initialize query params
    if (endpoint.queryParams) {
      const params = {};
      Object.entries(endpoint.queryParams).forEach(([key]) => {
        params[key] = '';
      });
      setQueryParams(params);
    } else {
      setQueryParams({});
    }

    // Initialize request body from bodySchema examples
    if (endpoint.bodySchema) {
      const exampleBody = {};
      Object.entries(endpoint.bodySchema).forEach(([key, config]) => {
        exampleBody[key] = config.example;
      });
      setRequestBody(JSON.stringify(exampleBody, null, 2));
    } else {
      setRequestBody('{}');
    }
  }, []);

  // Select first endpoint when category changes
  useEffect(() => {
    const category = API_CATEGORIES[selectedCategory];
    if (category && category.endpoints.length > 0) {
      handleSelectEndpoint(category.endpoints[0]);
    }
  }, [selectedCategory, handleSelectEndpoint]);

  // Build final URL with path and query params
  const buildUrl = useCallback(() => {
    if (!selectedEndpoint) return '';

    let url = selectedEndpoint.path;

    // Replace path params
    Object.entries(pathParams).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, encodeURIComponent(value));
    });

    // Add query params
    const queryString = Object.entries(queryParams)
      .filter(([, value]) => value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');

    if (queryString) {
      url += `?${queryString}`;
    }

    return url;
  }, [selectedEndpoint, pathParams, queryParams]);

  // Execute API request
  const executeRequest = async () => {
    if (!selectedEndpoint) return;

    // SEC-055: Input validation before request (HIGH-001)
    // Validate required path parameters
    if (selectedEndpoint.pathParams) {
      const missingParams = Object.entries(selectedEndpoint.pathParams)
        .filter(([key, config]) => config.required && !pathParams[key])
        .map(([key]) => key);

      if (missingParams.length > 0) {
        setError(`Missing required path parameters: ${missingParams.join(', ')}`);
        return;
      }
    }

    // Validate JSON body syntax
    if (['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method) && requestBody) {
      try {
        JSON.parse(requestBody);
      } catch (e) {
        setError(`Invalid JSON in request body: ${e.message}`);
        return;
      }
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    const startTime = Date.now();

    try {
      const url = `${API_BASE_URL}${buildUrl()}`;
      const options = {
        method: selectedEndpoint.method,
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      };

      if (['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method)) {
        options.body = requestBody;
      }

      const res = await fetch(url, options);
      const endTime = Date.now();
      setResponseTime(endTime - startTime);

      let data;
      const contentType = res.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await res.json();
      } else {
        data = await res.text();
      }

      setResponse({
        status: res.status,
        statusText: res.statusText,
        headers: Object.fromEntries(res.headers.entries()),
        data
      });
    } catch (err) {
      setError(err.message);
      setResponseTime(Date.now() - startTime);
    } finally {
      setLoading(false);
    }
  };

  // Generate code snippets
  const generateCode = useCallback(() => {
    if (!selectedEndpoint) return '';

    const url = `${API_BASE_URL}${buildUrl()}`;
    const headers = getAuthHeaders();
    // SEC-055: Mask actual API keys in generated code (PCI-DSS 8.3.1 compliance)
    const rawAuthHeader = headers.Authorization || 'Bearer YOUR_API_KEY';
    const authHeader = rawAuthHeader.replace(/owkai_[a-zA-Z0-9_]+/g, 'owkai_YOUR_API_KEY_HERE');

    switch (codeLanguage) {
      case 'curl': {
        let curlCmd = `curl -X ${selectedEndpoint.method} "${url}"`;
        curlCmd += ` \\\n  -H "Authorization: ${authHeader}"`;
        curlCmd += ` \\\n  -H "Content-Type: application/json"`;
        if (['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method) && requestBody !== '{}') {
          curlCmd += ` \\\n  -d '${requestBody}'`;
        }
        return curlCmd;
      }

      case 'python': {
        let pythonCode = `import requests\n\n`;
        pythonCode += `url = "${url}"\n`;
        pythonCode += `headers = {\n`;
        pythonCode += `    "Authorization": "${authHeader}",\n`;
        pythonCode += `    "Content-Type": "application/json"\n`;
        pythonCode += `}\n\n`;
        if (['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method)) {
          pythonCode += `data = ${requestBody}\n\n`;
          pythonCode += `response = requests.${selectedEndpoint.method.toLowerCase()}(url, headers=headers, json=data)\n`;
        } else {
          pythonCode += `response = requests.${selectedEndpoint.method.toLowerCase()}(url, headers=headers)\n`;
        }
        pythonCode += `print(response.json())`;
        return pythonCode;
      }

      case 'javascript': {
        let jsCode = `const response = await fetch("${url}", {\n`;
        jsCode += `  method: "${selectedEndpoint.method}",\n`;
        jsCode += `  headers: {\n`;
        jsCode += `    "Authorization": "${authHeader}",\n`;
        jsCode += `    "Content-Type": "application/json"\n`;
        jsCode += `  }`;
        if (['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method) && requestBody !== '{}') {
          jsCode += `,\n  body: JSON.stringify(${requestBody})`;
        }
        jsCode += `\n});\n\n`;
        jsCode += `const data = await response.json();\nconsole.log(data);`;
        return jsCode;
      }

      default:
        return '';
    }
  }, [selectedEndpoint, buildUrl, requestBody, codeLanguage, API_BASE_URL, getAuthHeaders]);

  // Filter endpoints by search
  const filteredCategories = Object.entries(API_CATEGORIES).map(([key, category]) => ({
    key,
    ...category,
    endpoints: category.endpoints.filter(endpoint =>
      searchQuery === '' ||
      endpoint.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(cat => cat.endpoints.length > 0);

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{ height: 'calc(100vh - 200px)', minHeight: '600px' }}>
      <div className="flex h-full">
        {/* Left Sidebar - Endpoint Directory */}
        <div className="w-72 border-r border-gray-200 flex flex-col bg-gray-50">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">API Explorer</h3>
            <input
              type="text"
              placeholder="Search endpoints..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex-1 overflow-y-auto">
            {filteredCategories.map((category) => (
              <div key={category.key} className="border-b border-gray-200">
                <button
                  onClick={() => setSelectedCategory(category.key)}
                  className={`w-full px-4 py-3 text-left flex items-center gap-2 hover:bg-gray-100 transition-colors ${
                    selectedCategory === category.key ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                  }`}
                >
                  <span className="text-lg">{category.icon}</span>
                  <span className="font-medium text-gray-900">{category.name}</span>
                  <span className="ml-auto text-xs text-gray-500">{category.endpoints.length}</span>
                </button>

                {selectedCategory === category.key && (
                  <div className="bg-white">
                    {category.endpoints.map((endpoint) => (
                      <button
                        key={endpoint.id}
                        onClick={() => handleSelectEndpoint(endpoint)}
                        className={`w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
                          selectedEndpoint?.id === endpoint.id ? 'bg-blue-50' : ''
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 text-xs font-mono rounded border ${METHOD_COLORS[endpoint.method]}`}>
                            {endpoint.method}
                          </span>
                          <span className="text-sm text-gray-700 truncate">{endpoint.name}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selectedEndpoint ? (
            <>
              {/* Endpoint Header */}
              <div className="p-4 border-b border-gray-200 bg-white">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-3 py-1 text-sm font-mono rounded border ${METHOD_COLORS[selectedEndpoint.method]}`}>
                    {selectedEndpoint.method}
                  </span>
                  <code className="text-sm text-gray-700 font-mono">{selectedEndpoint.path}</code>
                  {selectedEndpoint.requiresAuth && (
                    <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">Auth Required</span>
                  )}
                </div>
                <h2 className="text-xl font-semibold text-gray-900">{selectedEndpoint.name}</h2>
                <p className="text-sm text-gray-600 mt-1">{selectedEndpoint.description}</p>
                {selectedEndpoint.warning && (
                  <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
                    ⚠️ {selectedEndpoint.warning}
                  </div>
                )}
              </div>

              {/* Request Builder & Response */}
              <div className="flex-1 flex overflow-hidden">
                {/* Request Builder */}
                <div className="w-1/2 border-r border-gray-200 flex flex-col overflow-hidden">
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-900">Request</h3>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {/* Path Parameters */}
                    {selectedEndpoint.pathParams && Object.keys(selectedEndpoint.pathParams).length > 0 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Path Parameters</label>
                        {Object.entries(selectedEndpoint.pathParams).map(([key, config]) => (
                          <div key={key} className="mb-2">
                            <label className="block text-xs text-gray-500 mb-1">
                              {key} {config.required && <span className="text-red-500">*</span>}
                            </label>
                            <input
                              type="text"
                              value={pathParams[key] || ''}
                              onChange={(e) => setPathParams({ ...pathParams, [key]: e.target.value })}
                              placeholder={config.example}
                              className="w-full px-3 py-2 border border-gray-300 rounded text-sm font-mono"
                            />
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Query Parameters */}
                    {selectedEndpoint.queryParams && Object.keys(selectedEndpoint.queryParams).length > 0 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Query Parameters</label>
                        {Object.entries(selectedEndpoint.queryParams).map(([key, config]) => (
                          <div key={key} className="mb-2">
                            <label className="block text-xs text-gray-500 mb-1">{key}</label>
                            <input
                              type="text"
                              value={queryParams[key] || ''}
                              onChange={(e) => setQueryParams({ ...queryParams, [key]: e.target.value })}
                              placeholder={config.example?.toString()}
                              className="w-full px-3 py-2 border border-gray-300 rounded text-sm font-mono"
                            />
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Request Body */}
                    {['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method) && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Request Body (JSON)</label>
                        <textarea
                          value={requestBody}
                          onChange={(e) => setRequestBody(e.target.value)}
                          rows={10}
                          className="w-full px-3 py-2 border border-gray-300 rounded text-sm font-mono bg-gray-900 text-green-400"
                          spellCheck={false}
                        />
                      </div>
                    )}

                    {/* Send Button */}
                    <button
                      onClick={executeRequest}
                      disabled={loading}
                      className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 font-medium transition-colors"
                    >
                      {loading ? 'Sending...' : 'Send Request'}
                    </button>

                    {/* Code Generator */}
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <label className="block text-sm font-medium text-gray-700">Code Snippet</label>
                        <div className="flex gap-1">
                          {['curl', 'python', 'javascript'].map((lang) => (
                            <button
                              key={lang}
                              onClick={() => setCodeLanguage(lang)}
                              className={`px-2 py-1 text-xs rounded ${
                                codeLanguage === lang
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                              }`}
                            >
                              {lang === 'javascript' ? 'Node.js' : lang.charAt(0).toUpperCase() + lang.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                      <pre className="p-3 bg-gray-900 text-green-400 rounded text-xs overflow-x-auto font-mono">
                        {generateCode()}
                      </pre>
                      <button
                        onClick={() => navigator.clipboard.writeText(generateCode())}
                        className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                      >
                        Copy to clipboard
                      </button>
                    </div>
                  </div>
                </div>

                {/* Response Viewer */}
                <div className="w-1/2 flex flex-col overflow-hidden">
                  <div className="p-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">Response</h3>
                    {responseTime !== null && (
                      <span className="text-xs text-gray-500">{responseTime}ms</span>
                    )}
                  </div>
                  <div className="flex-1 overflow-y-auto p-4">
                    {loading && (
                      <div className="flex items-center justify-center h-32">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      </div>
                    )}

                    {error && (
                      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-800 font-medium">Request Failed</p>
                        <p className="text-red-600 text-sm mt-1">{error}</p>
                      </div>
                    )}

                    {response && (
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <span className={`px-2 py-1 rounded text-sm font-mono ${
                            response.status >= 200 && response.status < 300
                              ? 'bg-green-100 text-green-800'
                              : response.status >= 400
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {response.status} {response.statusText}
                          </span>
                        </div>
                        <pre className="p-4 bg-gray-900 text-green-400 rounded-lg text-sm overflow-auto font-mono" style={{ maxHeight: '400px' }}>
                          {typeof response.data === 'object'
                            ? JSON.stringify(response.data, null, 2)
                            : response.data}
                        </pre>
                        <button
                          onClick={() => navigator.clipboard.writeText(
                            typeof response.data === 'object'
                              ? JSON.stringify(response.data, null, 2)
                              : response.data
                          )}
                          className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                        >
                          Copy response
                        </button>
                      </div>
                    )}

                    {!loading && !error && !response && (
                      <div className="text-center text-gray-500 py-12">
                        <p className="text-lg mb-2">No response yet</p>
                        <p className="text-sm">Click "Send Request" to execute the API call</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <p className="text-xl mb-2">Select an endpoint to begin</p>
                <p className="text-sm">Choose from the sidebar to view details and test the API</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InteractiveApiExplorer;
