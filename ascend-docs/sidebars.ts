import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/**
 * Ascend Documentation Sidebars
 * Enterprise AI Governance Platform
 *
 * Updated: 2025-12-16
 * Added: Gateway Integrations, BYOK/CMK Encryption
 */
const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'getting-started/quick-start',
        'getting-started/installation',
        'getting-started/authentication',
        'getting-started/first-agent-action',
      ],
    },
    {
      type: 'category',
      label: 'User Guide',
      collapsed: false,
      items: [
        'user-guide/dashboard',
        'user-guide/agent-registry',
        'user-guide/action-approval',
        'user-guide/smart-rules',
        'user-guide/alerts',
        'user-guide/activity-feed',
        'user-guide/reports',
      ],
    },
    {
      type: 'category',
      label: 'Admin Guide',
      collapsed: false,
      items: [
        'admin-guide/organization-setup',
        'admin-guide/user-management',
        'admin-guide/api-keys',
        'admin-guide/policy-configuration',
        'admin-guide/threshold-tuning',
        'admin-guide/mfa-setup',
        'admin-guide/audit-logs',
      ],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      collapsed: false,
      items: [
        'core-concepts/how-ascend-works',
        'core-concepts/risk-scoring',
        'core-concepts/approval-workflows',
        'core-concepts/multi-tenancy',
        'core-concepts/audit-logging',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      collapsed: false,
      items: [
        'api-reference/overview',
        'api-reference/authentication',
        'api-reference/actions',
        'api-reference/agents',
        'api-reference/smart-rules',
        'api-reference/analytics',
        'api-reference/mcp-governance',
        'api-reference/error-codes',
      ],
    },
    {
      type: 'category',
      label: 'Python SDK',
      collapsed: true,
      items: [
        'sdk/python/installation',
        'sdk/python/client-configuration',
        'sdk/python/agent-actions',
        'sdk/python/policies',
        'sdk/python/error-handling',
        'sdk/python/api-reference',
      ],
    },
    {
      type: 'category',
      label: 'Node.js SDK',
      collapsed: true,
      items: [
        'sdk/nodejs/installation',
        'sdk/nodejs/client-configuration',
        'sdk/nodejs/agent-actions',
        'sdk/nodejs/error-handling',
      ],
    },
    {
      type: 'category',
      label: 'REST API',
      collapsed: true,
      items: [
        'api/overview',
        'sdk/rest/authentication',
        'sdk/rest/endpoints',
        'sdk/rest/webhooks',
      ],
    },
    {
      type: 'category',
      label: 'Integrations',
      collapsed: false,  // EXPANDED - high traffic section
      items: [
        'integrations/overview',
        {
          type: 'category',
          label: 'Gateway Integrations',
          collapsed: false,  // EXPANDED - customers need to see options
          link: {
            type: 'doc',
            id: 'integrations/gateway/index',
          },
          items: [
            {
              type: 'doc',
              id: 'integrations/gateway/aws-lambda-authorizer',
              label: 'AWS API Gateway',
            },
            {
              type: 'doc',
              id: 'integrations/gateway/kong-plugin',
              label: 'Kong Gateway',
            },
            {
              type: 'doc',
              id: 'integrations/gateway/envoy-istio',
              label: 'Envoy / Istio',
            },
          ],
        },
        'integrations/mcp-server',
        'integrations/langchain',
        'integrations/claude-code',
        'integrations/autogpt',
        'integrations/custom-agents',
      ],
    },
    {
      type: 'category',
      label: 'Enterprise',
      collapsed: true,
      items: [
        'enterprise/overview',
        'enterprise/sso',
        'enterprise/oidc',
        'enterprise/saml',
        'enterprise/siem',
        'enterprise/splunk',
        'enterprise/servicenow',
        'enterprise/pagerduty',
        'enterprise/slack-teams',
        'enterprise/compliance',
        'enterprise/analytics',
        'enterprise/system-diagnostics',
      ],
    },
    {
      type: 'category',
      label: 'Governance',
      collapsed: true,
      items: [
        'governance/enterprise-governance',
        'sdk/governance-integration',
      ],
    },
    {
      type: 'category',
      label: 'Security',
      collapsed: false,  // EXPANDED - enterprise customers check this first
      items: [
        'security/overview',
        {
          type: 'category',
          label: 'BYOK/CMK Encryption',
          collapsed: false,  // EXPANDED - key enterprise feature
          link: {
            type: 'doc',
            id: 'security/byok/index',
          },
          items: [
            {
              type: 'doc',
              id: 'security/byok/setup-guide',
              label: 'Setup Guide',
            },
            {
              type: 'doc',
              id: 'security/byok/api-reference',
              label: 'API Reference',
            },
            {
              type: 'doc',
              id: 'security/byok/troubleshooting',
              label: 'Troubleshooting',
            },
          ],
        },
        'security/data-encryption',
        'security/compliance',
        'security/responsible-disclosure',
      ],
    },
    {
      type: 'category',
      label: 'Compliance',
      collapsed: true,
      items: [
        'compliance/overview',
        'compliance/soc2',
        'compliance/hipaa',
        'compliance/nist-800-53',
        'compliance/mitre-attack',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      collapsed: true,
      items: [
        'reference/action-types',
        'reference/risk-levels',
        'reference/glossary',
        'reference/faq',
      ],
    },
  ],
};

export default sidebars;
