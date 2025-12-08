import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/**
 * Ascend Documentation Sidebars
 * Enterprise AI Governance Platform
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
      collapsed: true,
      items: [
        'integrations/overview',
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
      collapsed: true,
      items: [
        'security/overview',
        'security/data-encryption',
        'security/compliance',
        'security/responsible-disclosure',
      ],
    },
  ],
};

export default sidebars;
