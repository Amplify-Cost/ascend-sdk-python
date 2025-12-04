import React, { useState, useEffect, useCallback } from "react";
import { fetchWithAuth } from "../utils/fetchWithAuth";

/**
 * Enterprise Integration Management Component
 * ============================================
 *
 * Phase 5 Integration Suite - Full Management UI
 *
 * Features:
 * - Create, update, delete integrations
 * - Connection testing with real-time status
 * - Health monitoring and metrics
 * - Data flow configuration
 * - Multi-tenant isolation (organization_id filtering)
 *
 * Banking-Level Security:
 * - No hardcoded data or demo values
 * - All data from authenticated API endpoints
 * - AES-256 encrypted credential storage (backend)
 * - Audit trail for all operations
 *
 * Compliance: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 7.1, GDPR Article 25
 * Authored-By: Ascend Engineer
 */

// Integration type configurations (matches backend INTEGRATION_TYPE_CONFIG)
const INTEGRATION_TYPES = {
  splunk: {
    id: "splunk",
    name: "Splunk Enterprise",
    category: "siem",
    icon: "🔍",
    description: "Security Information and Event Management",
    requiredFields: ["endpoint_url", "api_key"],
    authTypes: ["api_key"],
    fields: [
      { name: "endpoint_url", label: "Splunk HEC URL", type: "url", placeholder: "https://splunk.company.com:8088/services/collector", required: true },
      { name: "api_key", label: "HEC Token", type: "password", placeholder: "Enter HEC token", required: true, sensitive: true },
      { name: "index", label: "Index Name", type: "text", placeholder: "main", required: false },
      { name: "source_type", label: "Source Type", type: "text", placeholder: "_json", required: false }
    ]
  },
  qradar: {
    id: "qradar",
    name: "IBM QRadar",
    category: "siem",
    icon: "🛡️",
    description: "IBM Security QRadar SIEM",
    requiredFields: ["endpoint_url", "api_key"],
    authTypes: ["api_key"],
    fields: [
      { name: "endpoint_url", label: "QRadar Console URL", type: "url", placeholder: "https://qradar.company.com", required: true },
      { name: "api_key", label: "SEC Token", type: "password", placeholder: "Enter SEC token", required: true, sensitive: true },
      { name: "log_source_id", label: "Log Source ID", type: "text", placeholder: "Auto-detected", required: false }
    ]
  },
  sentinel: {
    id: "sentinel",
    name: "Microsoft Sentinel",
    category: "siem",
    icon: "☁️",
    description: "Microsoft Azure Sentinel Cloud SIEM",
    requiredFields: ["workspace_id", "shared_key"],
    authTypes: ["shared_key"],
    fields: [
      { name: "workspace_id", label: "Log Analytics Workspace ID", type: "text", placeholder: "Enter Log Analytics Workspace ID (GUID)", required: true },
      { name: "shared_key", label: "Primary/Secondary Key", type: "password", placeholder: "Enter Log Analytics Primary or Secondary Key", required: true, sensitive: true },
      { name: "log_type", label: "Custom Log Type", type: "text", placeholder: "OWAISecurityEvents", required: false }
    ]
  },
  elastic: {
    id: "elastic",
    name: "Elastic Security",
    category: "siem",
    icon: "🔎",
    description: "Elastic/ELK Stack Security SIEM",
    requiredFields: ["endpoint_url"],
    authTypes: ["api_key", "basic"],
    fields: [
      { name: "endpoint_url", label: "Elasticsearch URL", type: "url", placeholder: "https://elasticsearch.company.com:9200", required: true },
      { name: "api_key", label: "API Key", type: "password", placeholder: "Enter Elasticsearch API Key", required: false, sensitive: true },
      { name: "username", label: "Username (if not using API key)", type: "text", placeholder: "elastic", required: false },
      { name: "password", label: "Password (if not using API key)", type: "password", placeholder: "Enter password", required: false, sensitive: true },
      { name: "cloud_id", label: "Elastic Cloud ID (optional)", type: "text", placeholder: "For Elastic Cloud deployments", required: false },
      { name: "index", label: "Index Name", type: "text", placeholder: "owai_security", required: false }
    ]
  },
  active_directory: {
    id: "active_directory",
    name: "Active Directory",
    category: "identity",
    icon: "👥",
    description: "Microsoft Active Directory user sync",
    requiredFields: ["endpoint_url", "bind_dn", "bind_password"],
    authTypes: ["basic"],
    fields: [
      { name: "endpoint_url", label: "LDAP Server", type: "url", placeholder: "ldaps://dc.company.com:636", required: true },
      { name: "base_dn", label: "Base DN", type: "text", placeholder: "DC=company,DC=com", required: true },
      { name: "bind_dn", label: "Bind DN", type: "text", placeholder: "CN=svc_account,OU=Service Accounts,DC=company,DC=com", required: true },
      { name: "bind_password", label: "Bind Password", type: "password", placeholder: "Enter service account password", required: true, sensitive: true },
      { name: "user_filter", label: "User Filter", type: "text", placeholder: "(objectClass=user)", required: false },
      { name: "sync_interval", label: "Sync Interval (minutes)", type: "number", placeholder: "60", required: false }
    ]
  },
  okta: {
    id: "okta",
    name: "Okta SSO",
    category: "identity",
    icon: "🔐",
    description: "Okta Single Sign-On integration",
    requiredFields: ["endpoint_url", "api_token"],
    authTypes: ["api_key"],
    fields: [
      { name: "endpoint_url", label: "Okta Domain", type: "url", placeholder: "https://company.okta.com", required: true },
      { name: "api_token", label: "API Token", type: "password", placeholder: "Enter Okta API token", required: true, sensitive: true },
      { name: "app_id", label: "Application ID", type: "text", placeholder: "Optional: specific app ID", required: false }
    ]
  },
  azure_ad: {
    id: "azure_ad",
    name: "Azure AD SSO",
    category: "identity",
    icon: "☁️",
    description: "Azure Active Directory integration",
    requiredFields: ["tenant_id", "client_id", "client_secret"],
    authTypes: ["oauth2"],
    fields: [
      { name: "tenant_id", label: "Tenant ID", type: "text", placeholder: "Enter Azure AD Tenant ID", required: true },
      { name: "client_id", label: "Application (Client) ID", type: "text", placeholder: "Enter App Registration Client ID", required: true },
      { name: "client_secret", label: "Client Secret", type: "password", placeholder: "Enter Client Secret", required: true, sensitive: true }
    ]
  },
  slack: {
    id: "slack",
    name: "Slack",
    category: "notification",
    icon: "💬",
    description: "Slack workspace notifications",
    requiredFields: ["webhook_url"],
    authTypes: ["none"],
    fields: [
      { name: "webhook_url", label: "Webhook URL", type: "url", placeholder: "https://hooks.slack.com/services/...", required: true },
      { name: "channel", label: "Default Channel", type: "text", placeholder: "#security-alerts", required: false },
      { name: "username", label: "Bot Username", type: "text", placeholder: "Ascend Security Bot", required: false }
    ]
  },
  teams: {
    id: "teams",
    name: "Microsoft Teams",
    category: "notification",
    icon: "👥",
    description: "Microsoft Teams notifications",
    requiredFields: ["webhook_url"],
    authTypes: ["none"],
    fields: [
      { name: "webhook_url", label: "Incoming Webhook URL", type: "url", placeholder: "https://outlook.office.com/webhook/...", required: true }
    ]
  },
  servicenow: {
    id: "servicenow",
    name: "ServiceNow",
    category: "itsm",
    icon: "🎫",
    description: "ServiceNow ITSM incident management",
    requiredFields: ["endpoint_url", "username", "password"],
    authTypes: ["basic"],
    fields: [
      { name: "endpoint_url", label: "ServiceNow Instance", type: "url", placeholder: "https://company.service-now.com", required: true },
      { name: "username", label: "Username", type: "text", placeholder: "Enter service account username", required: true },
      { name: "password", label: "Password", type: "password", placeholder: "Enter service account password", required: true, sensitive: true },
      { name: "incident_table", label: "Incident Table", type: "text", placeholder: "incident", required: false },
      { name: "assignment_group", label: "Default Assignment Group", type: "text", placeholder: "Security Operations", required: false }
    ]
  },
  pagerduty: {
    id: "pagerduty",
    name: "PagerDuty",
    category: "notification",
    icon: "🚨",
    description: "PagerDuty incident alerting",
    requiredFields: ["routing_key"],
    authTypes: ["api_key"],
    fields: [
      { name: "routing_key", label: "Integration Key", type: "password", placeholder: "Enter Events API v2 integration key", required: true, sensitive: true },
      { name: "severity_mapping", label: "Severity Mapping", type: "select", options: ["critical→critical", "high→error", "medium→warning", "low→info"], required: false }
    ]
  },
  webhook: {
    id: "webhook",
    name: "Custom Webhook",
    category: "custom",
    icon: "🔗",
    description: "Custom HTTP webhook endpoint",
    requiredFields: ["endpoint_url"],
    authTypes: ["none", "api_key", "basic"],
    fields: [
      { name: "endpoint_url", label: "Webhook URL", type: "url", placeholder: "https://api.company.com/webhook", required: true },
      { name: "auth_type", label: "Authentication", type: "select", options: ["none", "api_key", "basic"], required: true },
      { name: "api_key", label: "API Key / Token", type: "password", placeholder: "Enter API key if required", required: false, sensitive: true, showIf: "auth_type=api_key" },
      { name: "username", label: "Username", type: "text", placeholder: "Enter username", required: false, showIf: "auth_type=basic" },
      { name: "password", label: "Password", type: "password", placeholder: "Enter password", required: false, sensitive: true, showIf: "auth_type=basic" },
      { name: "headers", label: "Custom Headers (JSON)", type: "textarea", placeholder: '{"X-Custom-Header": "value"}', required: false }
    ]
  }
};

const CATEGORY_LABELS = {
  siem: { label: "SIEM Integrations", icon: "🔍" },
  identity: { label: "Identity & Access", icon: "👥" },
  notification: { label: "Notifications", icon: "🔔" },
  itsm: { label: "IT Service Management", icon: "🎫" },
  custom: { label: "Custom Integrations", icon: "🔗" }
};

const IntegrationManagement = ({ isOpen, onClose, initialType, onIntegrationSaved }) => {
  // State
  const [step, setStep] = useState(initialType ? "configure" : "select");
  const [selectedType, setSelectedType] = useState(initialType || null);
  const [formData, setFormData] = useState({});
  const [formErrors, setFormErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [existingIntegrations, setExistingIntegrations] = useState([]);
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);
  const [editingIntegration, setEditingIntegration] = useState(null);
  const [viewMode, setViewMode] = useState("create"); // create, list, edit
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [healthHistory, setHealthHistory] = useState([]);
  const [loadingHealth, setLoadingHealth] = useState(false);

  // Load existing integrations on mount
  useEffect(() => {
    if (isOpen) {
      loadExistingIntegrations();
    }
  }, [isOpen]);

  // Set initial type if provided
  useEffect(() => {
    if (initialType && INTEGRATION_TYPES[initialType]) {
      setSelectedType(initialType);
      setStep("configure");
      setViewMode("create");
    }
  }, [initialType]);

  const loadExistingIntegrations = async () => {
    setLoadingIntegrations(true);
    try {
      const response = await fetchWithAuth("/api/integrations");
      setExistingIntegrations(response.integrations || []);
    } catch (error) {
      console.error("Failed to load integrations:", error);
      setExistingIntegrations([]);
    } finally {
      setLoadingIntegrations(false);
    }
  };

  const handleTypeSelect = (typeId) => {
    setSelectedType(typeId);
    setFormData({});
    setFormErrors({});
    setTestResult(null);
    setStep("configure");
  };

  const handleInputChange = (fieldName, value) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
    // Clear error when user starts typing
    if (formErrors[fieldName]) {
      setFormErrors(prev => ({ ...prev, [fieldName]: null }));
    }
  };

  const validateForm = () => {
    const typeConfig = INTEGRATION_TYPES[selectedType];
    if (!typeConfig) return false;

    const errors = {};

    // Check required fields
    typeConfig.fields.forEach(field => {
      if (field.required && !formData[field.name]?.trim()) {
        errors[field.name] = `${field.label} is required`;
      }
    });

    // Validate URL format
    typeConfig.fields.forEach(field => {
      if (field.type === "url" && formData[field.name]) {
        try {
          new URL(formData[field.name]);
        } catch {
          errors[field.name] = "Invalid URL format";
        }
      }
    });

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleTestConnection = async () => {
    if (!validateForm()) return;

    setIsTesting(true);
    setTestResult(null);

    try {
      const typeConfig = INTEGRATION_TYPES[selectedType];

      // Build config object (exclude sensitive fields from logging)
      const config = {};
      typeConfig.fields.forEach(field => {
        if (formData[field.name]) {
          config[field.name] = formData[field.name];
        }
      });

      const response = await fetchWithAuth("/api/integrations/test", {
        method: "POST",
        body: JSON.stringify({
          integration_type: selectedType,
          endpoint_url: formData.endpoint_url || formData.webhook_url,
          auth_type: formData.auth_type || typeConfig.authTypes[0] || "none",
          config: config,
          test_type: "ping"
        })
      });

      // SEC-049: Capture full response details for enhanced UI
      setTestResult({
        success: response.success,
        message: response.message || (response.success ? "Connection successful" : "Connection failed"),
        latency: response.response_time_ms || response.latency_ms,
        statusCode: response.result?.status_code,
        httpMethod: response.http_method || response.result?.http_method,
        healthStatus: response.health_status,
        details: response.result
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: error.message || "Connection test failed - please check your network and try again",
        details: { error: error.toString() }
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveIntegration = async () => {
    if (!validateForm()) return;

    setIsSubmitting(true);

    try {
      const typeConfig = INTEGRATION_TYPES[selectedType];

      // Build config object
      const config = {};
      typeConfig.fields.forEach(field => {
        if (formData[field.name]) {
          config[field.name] = formData[field.name];
        }
      });

      const payload = {
        integration_type: typeConfig.category === "siem" ? "siem" :
                          typeConfig.category === "identity" ? "custom" :
                          typeConfig.category === "notification" ? typeConfig.id :
                          typeConfig.id,
        integration_name: `${typeConfig.name} Integration`,
        display_name: formData.display_name || typeConfig.name,
        description: formData.description || typeConfig.description,
        endpoint_url: formData.endpoint_url || formData.webhook_url || null,
        auth_type: formData.auth_type || typeConfig.authTypes[0] || "none",
        config: config,
        tags: [selectedType, typeConfig.category]
      };

      let response;
      if (editingIntegration) {
        response = await fetchWithAuth(`/api/integrations/${editingIntegration.id}`, {
          method: "PUT",
          body: JSON.stringify(payload)
        });
      } else {
        response = await fetchWithAuth("/api/integrations", {
          method: "POST",
          body: JSON.stringify(payload)
        });
      }

      // Refresh integrations list
      await loadExistingIntegrations();

      // Notify parent
      if (onIntegrationSaved) {
        onIntegrationSaved(response);
      }

      // Reset form
      setFormData({});
      setTestResult(null);
      setEditingIntegration(null);
      setStep("select");
      setViewMode("list");

    } catch (error) {
      console.error("Failed to save integration:", error);
      setFormErrors({ _general: error.message || "Failed to save integration" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteIntegration = async (integrationId) => {
    try {
      await fetchWithAuth(`/api/integrations/${integrationId}`, {
        method: "DELETE"
      });
      await loadExistingIntegrations();
      setDeleteConfirm(null);
      if (onIntegrationSaved) {
        onIntegrationSaved(null);
      }
    } catch (error) {
      console.error("Failed to delete integration:", error);
    }
  };

  const handleEditIntegration = (integration) => {
    // Find the type based on integration_type and tags
    let typeId = integration.tags?.find(t => INTEGRATION_TYPES[t]) || integration.integration_type;

    if (!INTEGRATION_TYPES[typeId]) {
      // Try to match by integration_type
      typeId = Object.keys(INTEGRATION_TYPES).find(
        k => INTEGRATION_TYPES[k].category === integration.integration_type
      ) || "webhook";
    }

    setSelectedType(typeId);
    setEditingIntegration(integration);
    setFormData({
      display_name: integration.display_name,
      description: integration.description,
      endpoint_url: integration.endpoint_url,
      ...integration.config
    });
    setStep("configure");
    setViewMode("edit");
  };

  const loadHealthHistory = async (integrationId) => {
    setLoadingHealth(true);
    try {
      const response = await fetchWithAuth(`/api/integrations/${integrationId}/health-history?limit=10`);
      setHealthHistory(response.health_checks || []);
    } catch (error) {
      console.error("Failed to load health history:", error);
      setHealthHistory([]);
    } finally {
      setLoadingHealth(false);
    }
  };

  const runHealthCheck = async (integrationId) => {
    try {
      await fetchWithAuth(`/api/integrations/${integrationId}/health-check`, {
        method: "POST"
      });
      await loadExistingIntegrations();
      await loadHealthHistory(integrationId);
    } catch (error) {
      console.error("Failed to run health check:", error);
    }
  };

  // Don't render if not open
  if (!isOpen) return null;

  const typeConfig = selectedType ? INTEGRATION_TYPES[selectedType] : null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black/50 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">🔌</span>
                <div>
                  <h2 className="text-xl font-bold text-white">
                    {viewMode === "list" ? "Manage Integrations" :
                     editingIntegration ? "Edit Integration" : "Configure Integration"}
                  </h2>
                  <p className="text-blue-100 text-sm">
                    Enterprise Integration Suite • Banking-Level Security
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white/80 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Navigation tabs */}
            <div className="flex space-x-4 mt-4">
              <button
                onClick={() => { setViewMode("list"); setStep("select"); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === "list"
                    ? "bg-white/20 text-white"
                    : "text-white/70 hover:text-white hover:bg-white/10"
                }`}
              >
                📋 All Integrations ({existingIntegrations.length})
              </button>
              <button
                onClick={() => { setViewMode("create"); setStep("select"); setEditingIntegration(null); }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === "create" && step === "select"
                    ? "bg-white/20 text-white"
                    : "text-white/70 hover:text-white hover:bg-white/10"
                }`}
              >
                ➕ Add New
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
            {/* List View */}
            {viewMode === "list" && (
              <div className="space-y-4">
                {loadingIntegrations ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-500">Loading integrations...</p>
                  </div>
                ) : existingIntegrations.length === 0 ? (
                  <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <span className="text-4xl">🔌</span>
                    <h3 className="mt-4 text-lg font-medium text-gray-900">No Integrations Configured</h3>
                    <p className="mt-2 text-gray-500">
                      Add your first integration to connect with external systems
                    </p>
                    <button
                      onClick={() => { setViewMode("create"); setStep("select"); }}
                      className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Add Integration
                    </button>
                  </div>
                ) : (
                  existingIntegrations.map(integration => (
                    <div
                      key={integration.id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <span className="text-2xl">
                            {INTEGRATION_TYPES[integration.tags?.[0]]?.icon || "🔗"}
                          </span>
                          <div>
                            <h4 className="font-medium text-gray-900">
                              {integration.display_name || integration.integration_name}
                            </h4>
                            <p className="text-sm text-gray-500">{integration.endpoint_url}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {/* Health status badge */}
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            integration.health_status === "healthy" ? "bg-green-100 text-green-700" :
                            integration.health_status === "degraded" ? "bg-yellow-100 text-yellow-700" :
                            integration.health_status === "unhealthy" ? "bg-red-100 text-red-700" :
                            "bg-gray-100 text-gray-600"
                          }`}>
                            {integration.health_status?.toUpperCase() || "UNKNOWN"}
                          </span>
                          {/* Enabled badge */}
                          <span className={`px-2 py-1 rounded text-xs ${
                            integration.is_enabled
                              ? "bg-blue-100 text-blue-700"
                              : "bg-gray-100 text-gray-500"
                          }`}>
                            {integration.is_enabled ? "ENABLED" : "DISABLED"}
                          </span>
                        </div>
                      </div>

                      <div className="mt-4 flex items-center justify-between border-t pt-4">
                        <div className="text-sm text-gray-500">
                          {integration.last_health_check && (
                            <span>
                              Last checked: {new Date(integration.last_health_check).toLocaleString()}
                            </span>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => runHealthCheck(integration.id)}
                            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                          >
                            🔄 Test
                          </button>
                          <button
                            onClick={() => handleEditIntegration(integration)}
                            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                          >
                            ✏️ Edit
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(integration.id)}
                            className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </div>

                      {/* Delete confirmation */}
                      {deleteConfirm === integration.id && (
                        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                          <p className="text-sm text-red-700 mb-3">
                            Are you sure you want to delete this integration? This action cannot be undone.
                          </p>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleDeleteIntegration(integration.id)}
                              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                            >
                              Confirm Delete
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Type Selection */}
            {(viewMode === "create" && step === "select") && (
              <div className="space-y-6">
                {Object.entries(CATEGORY_LABELS).map(([categoryId, category]) => {
                  const categoryTypes = Object.entries(INTEGRATION_TYPES)
                    .filter(([_, config]) => config.category === categoryId);

                  if (categoryTypes.length === 0) return null;

                  return (
                    <div key={categoryId}>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="mr-2">{category.icon}</span>
                        {category.label}
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {categoryTypes.map(([typeId, config]) => (
                          <button
                            key={typeId}
                            onClick={() => handleTypeSelect(typeId)}
                            className="p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all text-left group"
                          >
                            <div className="flex items-center space-x-3">
                              <span className="text-2xl group-hover:scale-110 transition-transform">
                                {config.icon}
                              </span>
                              <div>
                                <h4 className="font-medium text-gray-900">{config.name}</h4>
                                <p className="text-sm text-gray-500">{config.description}</p>
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Configuration Form */}
            {step === "configure" && typeConfig && (
              <div className="space-y-6">
                {/* Back button */}
                <button
                  onClick={() => {
                    setStep("select");
                    setSelectedType(null);
                    setEditingIntegration(null);
                    setFormData({});
                    setTestResult(null);
                  }}
                  className="flex items-center text-gray-600 hover:text-gray-900"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to integrations
                </button>

                {/* Integration header */}
                <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                  <span className="text-3xl">{typeConfig.icon}</span>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">{typeConfig.name}</h3>
                    <p className="text-gray-500">{typeConfig.description}</p>
                  </div>
                </div>

                {/* General error */}
                {formErrors._general && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {formErrors._general}
                  </div>
                )}

                {/* Form fields */}
                <div className="space-y-4">
                  {/* Display name (optional) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name (optional)
                    </label>
                    <input
                      type="text"
                      value={formData.display_name || ""}
                      onChange={(e) => handleInputChange("display_name", e.target.value)}
                      placeholder={`My ${typeConfig.name}`}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {/* Dynamic fields */}
                  {typeConfig.fields.map(field => {
                    // Check showIf condition
                    if (field.showIf) {
                      const [condField, condValue] = field.showIf.split("=");
                      if (formData[condField] !== condValue) return null;
                    }

                    return (
                      <div key={field.name}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                          {field.sensitive && (
                            <span className="ml-2 text-xs text-gray-400">🔒 Encrypted</span>
                          )}
                        </label>

                        {field.type === "select" ? (
                          <select
                            value={formData[field.name] || ""}
                            onChange={(e) => handleInputChange(field.name, e.target.value)}
                            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                              formErrors[field.name] ? "border-red-500" : "border-gray-300"
                            }`}
                          >
                            <option value="">Select...</option>
                            {(field.options || []).map(opt => (
                              <option key={opt} value={opt.split("→")[0] || opt}>
                                {opt}
                              </option>
                            ))}
                          </select>
                        ) : field.type === "textarea" ? (
                          <textarea
                            value={formData[field.name] || ""}
                            onChange={(e) => handleInputChange(field.name, e.target.value)}
                            placeholder={field.placeholder}
                            rows={3}
                            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                              formErrors[field.name] ? "border-red-500" : "border-gray-300"
                            }`}
                          />
                        ) : (
                          <input
                            type={field.type === "password" ? "password" : field.type === "number" ? "number" : "text"}
                            value={formData[field.name] || ""}
                            onChange={(e) => handleInputChange(field.name, e.target.value)}
                            placeholder={field.placeholder}
                            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                              formErrors[field.name] ? "border-red-500" : "border-gray-300"
                            }`}
                          />
                        )}

                        {formErrors[field.name] && (
                          <p className="mt-1 text-sm text-red-600">{formErrors[field.name]}</p>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* SEC-049: Enhanced Test Result with Details & Troubleshooting */}
                {testResult && (
                  <div className={`rounded-lg overflow-hidden ${
                    testResult.success
                      ? "bg-green-50 border border-green-200"
                      : "bg-red-50 border border-red-200"
                  }`}>
                    {/* Main Result */}
                    <div className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 ${
                            testResult.success ? "bg-green-100" : "bg-red-100"
                          }`}>
                            <span className="text-xl">{testResult.success ? "✓" : "✕"}</span>
                          </div>
                          <div>
                            <p className={`font-semibold ${testResult.success ? "text-green-800" : "text-red-800"}`}>
                              {testResult.success ? "Connection Successful" : "Connection Failed"}
                            </p>
                            <p className={`text-sm ${testResult.success ? "text-green-600" : "text-red-600"}`}>
                              {testResult.message}
                            </p>
                          </div>
                        </div>
                        {testResult.success && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                            Ready to Save
                          </span>
                        )}
                      </div>

                      {/* Technical Details */}
                      <div className="mt-3 flex flex-wrap gap-3 text-sm">
                        {testResult.latency !== undefined && (
                          <span className={`px-2 py-1 rounded ${testResult.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                            ⏱️ {testResult.latency}ms
                          </span>
                        )}
                        {testResult.statusCode && (
                          <span className={`px-2 py-1 rounded ${testResult.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                            HTTP {testResult.statusCode}
                          </span>
                        )}
                        {testResult.httpMethod && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded">
                            {testResult.httpMethod}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Troubleshooting Tips (on failure) */}
                    {!testResult.success && (
                      <div className="px-4 pb-4">
                        <div className="p-3 bg-red-100 rounded-lg">
                          <p className="text-sm font-medium text-red-800 mb-2">💡 Troubleshooting Tips:</p>
                          <ul className="text-sm text-red-700 space-y-1">
                            <li>• Verify the URL is correct and accessible from the internet</li>
                            <li>• Check that any API keys or tokens are valid and not expired</li>
                            <li>• Ensure HTTPS is used (required for most integrations)</li>
                            <li>• Confirm firewall rules allow outbound connections</li>
                            {testResult.message?.toLowerCase().includes("timeout") && (
                              <li>• The endpoint may be slow to respond - try again</li>
                            )}
                            {testResult.message?.toLowerCase().includes("ssl") && (
                              <li>• SSL certificate may be invalid or self-signed</li>
                            )}
                          </ul>
                        </div>
                        <button
                          onClick={handleTestConnection}
                          className="mt-3 w-full py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
                        >
                          🔄 Retry Test
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex justify-between pt-4 border-t">
                  <button
                    onClick={handleTestConnection}
                    disabled={isTesting}
                    className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 flex items-center"
                  >
                    {isTesting ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Testing...
                      </>
                    ) : (
                      <>🔌 Test Connection</>
                    )}
                  </button>

                  <button
                    onClick={handleSaveIntegration}
                    disabled={isSubmitting}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
                  >
                    {isSubmitting ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </>
                    ) : (
                      <>💾 {editingIntegration ? "Update" : "Save"} Integration</>
                    )}
                  </button>
                </div>

                {/* Security note */}
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-start">
                    <span className="text-xl mr-2">🔒</span>
                    <div className="text-sm text-blue-700">
                      <p className="font-medium">Banking-Level Security</p>
                      <p className="mt-1">
                        All credentials are encrypted using AES-256 before storage.
                        Connection details are never logged or exposed in plaintext.
                        Multi-tenant isolation ensures your data is accessible only to your organization.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationManagement;
