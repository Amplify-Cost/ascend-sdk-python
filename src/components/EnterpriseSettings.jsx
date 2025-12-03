import React, { useState, useEffect, useCallback } from "react";
import AgentActionSubmitPanel from "./AgentActionSubmitPanel";
import RiskConfigurationTab from "./risk-config/RiskConfigurationTab";
import ApiKeyManagement from "./ApiKeyManagement";
import IntegrationManagement from "./IntegrationManagement";
import IntegrationHealthDashboard from "./IntegrationHealthDashboard";
import IntegrationWizard from "./IntegrationWizard";
import InteractiveApiExplorer from "./InteractiveApiExplorer";
import fetchWithAuth from "../utils/fetchWithAuth";

/**
 * Enterprise Settings with Full Integration Management
 * =====================================================
 *
 * SEC-013: API Key Management
 * SEC-028: Enterprise Integration Status (No Hardcoded Data)
 * Phase 5: Full Integration Suite Management
 *
 * Banking-Level Security: PCI-DSS 8.3.1, HIPAA 164.312(d), SOC 2 CC6.1
 * Authored-By: Ascend Engineer
 */
const EnterpriseSettings = ({ getAuthHeaders, user, API_BASE_URL }) => {
  const [activeSettingsTab, setActiveSettingsTab] = useState("general");
  const [acknowledgment, setAcknowledgment] = useState(false);

  // Phase 5: Integration Management Modal State
  const [showIntegrationModal, setShowIntegrationModal] = useState(false);
  const [selectedIntegrationType, setSelectedIntegrationType] = useState(null);

  // SEC-047: Integration Wizard State (Datadog-style quick setup)
  const [showIntegrationWizard, setShowIntegrationWizard] = useState(false);

  // SEC-051: Integration Health Dashboard State
  const [showHealthDashboard, setShowHealthDashboard] = useState(false);

  // SEC-028: Dynamic integration status state (no hardcoded defaults)
  const [integrationStatus, setIntegrationStatus] = useState({
    loading: true,
    error: null,
    splunk: null,
    qradar: null,
    sentinel: null,
    activeDirectory: null,
    sso: null
  });

  // SEC-028: Organization settings from API (no hardcoded defaults)
  const [orgSettings, setOrgSettings] = useState({
    loading: true,
    name: null,
    timezone: null
  });

  // SEC-028: Fetch integration status from backend (multi-tenant)
  const fetchIntegrationStatus = useCallback(async () => {
    try {
      setIntegrationStatus(prev => ({ ...prev, loading: true, error: null }));

      const response = await fetchWithAuth('/api/integrations/status');

      setIntegrationStatus({
        loading: false,
        error: null,
        splunk: response.splunk || null,
        qradar: response.qradar || null,
        sentinel: response.sentinel || null,
        activeDirectory: response.active_directory || null,
        sso: response.sso || null
      });
    } catch (error) {
      console.error('SEC-028: Failed to fetch integration status:', error);
      setIntegrationStatus(prev => ({
        ...prev,
        loading: false,
        error: 'Unable to load integration status'
      }));
    }
  }, []);

  // SEC-028: Fetch organization settings from API
  const fetchOrgSettings = useCallback(async () => {
    try {
      const response = await fetchWithAuth('/api/organizations/settings');
      setOrgSettings({
        loading: false,
        name: response.name || null,
        timezone: response.timezone || null
      });
    } catch (error) {
      console.error('SEC-028: Failed to fetch org settings:', error);
      // On error, try to get name from user prop
      setOrgSettings(prev => ({ ...prev, loading: false }));
    }
  }, []);

  // SEC-028: Load data when integrations tab is active
  useEffect(() => {
    if (activeSettingsTab === 'integrations') {
      fetchIntegrationStatus();
    }
    if (activeSettingsTab === 'general') {
      fetchOrgSettings();
    }
  }, [activeSettingsTab, fetchIntegrationStatus, fetchOrgSettings]);

  // Phase 5: Open integration configuration modal
  const handleConfigureIntegration = (integrationType) => {
    setSelectedIntegrationType(integrationType);
    setShowIntegrationModal(true);
  };

  // Phase 5: Handle integration saved - refresh status
  const handleIntegrationSaved = () => {
    fetchIntegrationStatus();
  };

  // SEC-028: Helper to render integration status badge
  // Phase 5: Updated to support CONFIGURE button with modal
  const renderIntegrationStatus = (integration, name, colorScheme, integrationType) => {
    if (integrationStatus.loading) {
      return (
        <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded animate-pulse">
          <div>
            <h5 className="font-medium text-gray-800">{name}</h5>
            <p className="text-sm text-gray-500">Loading status...</p>
          </div>
          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">LOADING</span>
        </div>
      );
    }

    if (!integration) {
      return (
        <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded">
          <div>
            <h5 className="font-medium text-gray-800">{name}</h5>
            <p className="text-sm text-gray-600">Not configured for this organization</p>
          </div>
          <button
            onClick={() => handleConfigureIntegration(integrationType)}
            className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
          >
            CONFIGURE
          </button>
        </div>
      );
    }

    const statusColors = {
      active: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-600', badge: 'bg-green-100 text-green-800' },
      syncing: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-600', badge: 'bg-yellow-100 text-yellow-800' },
      error: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-600', badge: 'bg-red-100 text-red-800' },
      inactive: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-600', badge: 'bg-gray-100 text-gray-800' }
    };

    const colors = statusColors[integration.status] || statusColors.inactive;
    const lastSync = integration.last_sync
      ? new Date(integration.last_sync).toLocaleString()
      : 'Never';

    return (
      <div className={`flex items-center justify-between p-3 ${colors.bg} ${colors.border} border rounded`}>
        <div>
          <h5 className={`font-medium ${colors.text.replace('600', '800')}`}>{name}</h5>
          <p className={`text-sm ${colors.text}`}>
            {integration.status === 'active' ? 'Connected' : integration.status === 'syncing' ? 'Syncing' : integration.status === 'error' ? 'Connection Error' : 'Inactive'}
            {integration.status === 'active' && ` • Last sync: ${lastSync}`}
            {integration.user_count !== undefined && ` • ${integration.user_count.toLocaleString()} users`}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 ${colors.badge} text-xs rounded`}>
            {integration.status?.toUpperCase() || 'UNKNOWN'}
          </span>
          <button
            onClick={() => handleConfigureIntegration(integrationType)}
            className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded hover:bg-gray-300 transition-colors"
          >
            MANAGE
          </button>
        </div>
      </div>
    );
  };

  // SEC-041: Enterprise Clean Separation - Settings = Platform Configuration
  // Security Settings REMOVED - was non-functional (local state only, not persisted)
  // Security settings are properly managed in Admin Console → Organization tab
  const settingsTabs = [
    { id: "general", label: "General Settings" },
    { id: "api-keys", label: "🔑 API Keys" }, // SEC-013: Enterprise API Key Management (consolidated here)
    { id: "api-explorer", label: "🔍 API Explorer" }, // SEC-055: Interactive API Explorer
    { id: "integrations", label: "Integrations" },
    { id: "risk-config", label: "🎯 Risk Configuration" }, // Enterprise Risk Scoring
    { id: "admin-tools", label: "🔧 Admin Tools" } // Admin-only tab (compliance reports removed - use Admin Console)
  ];

  // SEC-028: Enterprise General Settings (Dynamic from API)
  const renderGeneralSettings = () => (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">🏢 Organization Settings</h4>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Organization Name</label>
            {orgSettings.loading ? (
              <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 animate-pulse">
                <span className="text-gray-400">Loading...</span>
              </div>
            ) : (
              <input
                type="text"
                defaultValue={orgSettings.name || user?.organization_name || ''}
                placeholder="Organization name not configured"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Time Zone</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              defaultValue={orgSettings.timezone || 'UTC'}
            >
              <option value="America/New_York">UTC-5 (Eastern Time)</option>
              <option value="America/Chicago">UTC-6 (Central Time)</option>
              <option value="America/Denver">UTC-7 (Mountain Time)</option>
              <option value="America/Los_Angeles">UTC-8 (Pacific Time)</option>
              <option value="UTC">UTC+0 (GMT)</option>
              <option value="Europe/London">Europe/London</option>
              <option value="Europe/Paris">Europe/Paris (CET)</option>
              <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
              <option value="Australia/Sydney">Australia/Sydney (AEST)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">📊 Dashboard Preferences</h4>
        <div className="space-y-4">
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" defaultChecked />
            <span className="text-sm">Show real-time metrics</span>
          </label>
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" defaultChecked />
            <span className="text-sm">Enable executive briefings</span>
          </label>
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" />
            <span className="text-sm">Dark mode interface</span>
          </label>
        </div>
      </div>
    </div>
  );

  // SEC-041: renderSecuritySettings REMOVED - was non-functional (local state only, not persisted)
  // Security settings are now managed in Admin Console → Organization tab
  // This deletion reduces code bloat and eliminates dead code per OWASP guidelines

  // SEC-028: Enterprise Integrations (Dynamic from API - Multi-Tenant)
  const renderIntegrations = () => (
    <div className="space-y-6">
      {/* SEC-047: Quick Setup Banner - Prominent CTA */}
      <div
        onClick={() => setShowIntegrationWizard(true)}
        className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-6 cursor-pointer hover:from-blue-700 hover:to-indigo-800 transition-all shadow-lg hover:shadow-xl group"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
              <span className="text-3xl">🚀</span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-xl font-bold text-white">Quick Setup</h3>
                <span className="px-2 py-0.5 bg-white/20 text-white text-xs rounded-full">Recommended</span>
              </div>
              <p className="text-blue-100 mt-1">
                Connect your first AI agent or integration in under 5 minutes
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="text-right hidden md:block">
              <p className="text-blue-100 text-sm">Guided setup wizard</p>
              <p className="text-white text-sm font-medium">3 simple steps</p>
            </div>
            <svg className="w-8 h-8 text-white group-hover:translate-x-2 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>

      {/* SEC-028: Error State */}
      {integrationStatus.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h5 className="font-medium text-red-800">Unable to Load Integration Status</h5>
              <p className="text-sm text-red-600">{integrationStatus.error}</p>
            </div>
            <button
              onClick={fetchIntegrationStatus}
              className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
            >
              RETRY
            </button>
          </div>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold">🔗 SIEM Integrations</h4>
          {!integrationStatus.loading && (
            <button
              onClick={fetchIntegrationStatus}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              ↻ Refresh
            </button>
          )}
        </div>
        <div className="space-y-4">
          {/* Phase 5: Dynamic Splunk Status with CONFIGURE button */}
          {renderIntegrationStatus(integrationStatus.splunk, 'Splunk Enterprise', 'green', 'splunk')}

          {/* Phase 5: Dynamic QRadar Status with CONFIGURE button */}
          {renderIntegrationStatus(integrationStatus.qradar, 'IBM QRadar', 'blue', 'qradar')}

          {/* Phase 5: Dynamic Sentinel Status with CONFIGURE button */}
          {renderIntegrationStatus(integrationStatus.sentinel, 'Microsoft Sentinel', 'purple', 'sentinel')}
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">🏢 Enterprise Systems</h4>
        <div className="space-y-4">
          {/* Phase 5: Dynamic Active Directory Status with CONFIGURE button */}
          {renderIntegrationStatus(integrationStatus.activeDirectory, 'Active Directory', 'yellow', 'active_directory')}

          {/* Phase 5: Dynamic SSO Status with CONFIGURE button */}
          {renderIntegrationStatus(integrationStatus.sso, 'SSO Integration', 'gray', 'okta')}
        </div>
      </div>

      {/* Phase 5: Notification Integrations */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">🔔 Notification Channels</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => handleConfigureIntegration('slack')}
            className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded hover:border-blue-400 hover:bg-blue-50 transition-all"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">💬</span>
              <div className="text-left">
                <h5 className="font-medium text-gray-800">Slack</h5>
                <p className="text-sm text-gray-600">Send alerts to Slack channels</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">ADD</span>
          </button>

          <button
            onClick={() => handleConfigureIntegration('teams')}
            className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded hover:border-blue-400 hover:bg-blue-50 transition-all"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">👥</span>
              <div className="text-left">
                <h5 className="font-medium text-gray-800">Microsoft Teams</h5>
                <p className="text-sm text-gray-600">Send alerts to Teams channels</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">ADD</span>
          </button>

          <button
            onClick={() => handleConfigureIntegration('pagerduty')}
            className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded hover:border-blue-400 hover:bg-blue-50 transition-all"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🚨</span>
              <div className="text-left">
                <h5 className="font-medium text-gray-800">PagerDuty</h5>
                <p className="text-sm text-gray-600">Incident alerting</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">ADD</span>
          </button>

          <button
            onClick={() => handleConfigureIntegration('servicenow')}
            className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded hover:border-blue-400 hover:bg-blue-50 transition-all"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🎫</span>
              <div className="text-left">
                <h5 className="font-medium text-gray-800">ServiceNow</h5>
                <p className="text-sm text-gray-600">ITSM incident creation</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">ADD</span>
          </button>
        </div>
      </div>

      {/* Phase 5: Custom Webhooks */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold">🔗 Custom Webhooks</h4>
          <button
            onClick={() => handleConfigureIntegration('webhook')}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            + Add Webhook
          </button>
        </div>
        <p className="text-sm text-gray-600">
          Configure custom HTTP endpoints to receive security events and alerts from the platform.
        </p>
      </div>

      {/* Phase 5: Manage All Integrations Button */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-semibold text-blue-900">Manage All Integrations</h4>
            <p className="text-sm text-blue-700">
              View, edit, delete, and test all configured integrations
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowHealthDashboard(true)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center"
            >
              📊 Health Dashboard
            </button>
            <button
              onClick={() => {
                setSelectedIntegrationType(null);
                setShowIntegrationModal(true);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
            >
              🔌 Open Integration Manager
            </button>
          </div>
        </div>
      </div>

      {/* Multi-Tenant Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-700">
          <strong>🏢 Multi-Tenant Note:</strong> Integration status shown is specific to your organization.
          All credentials are encrypted with AES-256 and stored securely.
        </p>
      </div>
    </div>
  );

  const renderAdminTools = () => (
    <div className="space-y-6">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-red-800 mb-2">⚠️ Administrator Tools</h3>
        <p className="text-red-700 text-sm">
          These tools are for system testing, troubleshooting, and emergency operations. 
          All actions are logged, audited, and require proper authorization.
        </p>
      </div>
      
      {/* Enterprise Agent Submission Tool */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold">🤖 Manual Agent Action Submission</h4>
          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded font-medium">
            ADMIN ONLY
          </span>
        </div>
        
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
          <h5 className="font-medium text-amber-800 mb-2">📋 Enterprise Guidelines</h5>
          <ul className="text-amber-700 text-sm space-y-1">
            <li>• Use only for testing workflow functionality and system validation</li>
            <li>• All submissions are logged with full audit trail including user identity</li>
            <li>• Include comprehensive business justification in description field</li>
            <li>• Coordinate with security team lead before production environment testing</li>
            <li>• Follow change management procedures for any production testing</li>
          </ul>
          
          <div className="mt-4 p-3 bg-amber-100 rounded">
            <p className="text-amber-800 text-sm font-medium">
              🏢 Compliance Note: This tool is provided for authorized administrative testing only. 
              Unauthorized use may violate company security policies and regulatory requirements.
            </p>
          </div>
          
          <label className="flex items-center mt-4">
            <input
              type="checkbox"
              checked={acknowledgment}
              onChange={(e) => setAcknowledgment(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-amber-800 font-medium">
              I acknowledge this is for authorized testing purposes only and understand all actions are audited
            </span>
          </label>
        </div>
        
        {acknowledgment ? (
          <div className="border-t border-gray-200 pt-4">
            <AgentActionSubmitPanel getAuthHeaders={getAuthHeaders} />
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>Please acknowledge the enterprise guidelines above to access the submission tool.</p>
          </div>
        )}
      </div>
      
      {/* System Diagnostics */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">📊 System Diagnostics</h4>
        <p className="text-gray-600 text-sm mb-4">
          Run system health checks, performance diagnostics, and connectivity tests.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <h5 className="font-medium text-gray-900">🔍 API Health Check</h5>
            <p className="text-sm text-gray-600">Test all endpoint connectivity</p>
          </button>
          
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <h5 className="font-medium text-gray-900">🗄️ Database Status</h5>
            <p className="text-sm text-gray-600">Check database performance</p>
          </button>
          
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <h5 className="font-medium text-gray-900">🔗 Integration Tests</h5>
            <p className="text-sm text-gray-600">Validate SIEM connections</p>
          </button>
        </div>
      </div>

      {/* SEC-048: Developer Resources */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">👨‍💻 Developer Resources</h4>
        <p className="text-gray-600 text-sm mb-4">
          API documentation, SDK references, and integration guides for developers.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 border border-blue-200 bg-blue-50 rounded-lg hover:bg-blue-100 hover:border-blue-300 transition-colors group"
          >
            <div className="flex items-center justify-between">
              <div>
                <h5 className="font-medium text-blue-900">📚 API Documentation</h5>
                <p className="text-sm text-blue-700">Interactive Swagger UI</p>
              </div>
              <svg className="w-5 h-5 text-blue-600 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </div>
          </a>

          <a
            href="/redoc"
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors group"
          >
            <div className="flex items-center justify-between">
              <div>
                <h5 className="font-medium text-gray-900">📖 ReDoc Reference</h5>
                <p className="text-sm text-gray-600">Clean API reference docs</p>
              </div>
              <svg className="w-5 h-5 text-gray-600 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </div>
          </a>

          <a
            href="/openapi.json"
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors group"
          >
            <div className="flex items-center justify-between">
              <div>
                <h5 className="font-medium text-gray-900">📋 OpenAPI Schema</h5>
                <p className="text-sm text-gray-600">Download JSON schema</p>
              </div>
              <svg className="w-5 h-5 text-gray-600 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </div>
          </a>
        </div>

        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h5 className="font-medium text-gray-900 mb-2">🚀 Quick Links</h5>
          <div className="flex flex-wrap gap-3">
            <a href="/docs#/Authorization" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
              Submit Agent Action →
            </a>
            <a href="/docs#/API%20Key%20Management" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
              API Key Endpoints →
            </a>
            <a href="/docs#/Integration%20Wizard" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
              Integration Wizard →
            </a>
            <a href="/docs#/Enterprise%20Webhooks" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
              Webhooks →
            </a>
          </div>
        </div>
      </div>

      {/* SEC-041: Compliance Tools - CONSOLIDATED to Admin Console */}
      {/* Duplicate compliance reports removed - use Admin Console → Compliance Metrics */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-lg font-semibold text-blue-900 mb-2">📋 Audit & Compliance Reports</h4>
            <p className="text-blue-700 text-sm">
              Compliance reports (SOX, HIPAA, PCI-DSS) have been consolidated to the Admin Console
              for centralized compliance management and audit trail visibility.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium">
              SEC-041: Enterprise Consolidation
            </span>
            <p className="text-xs text-blue-600">
              Navigate to: Admin Console → Compliance Metrics
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">⚙️ Enterprise Settings</h2>
        <p className="text-gray-600">Configure system settings, integrations, and administrative tools</p>
      </div>
      
      {/* Settings Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {settingsTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSettingsTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeSettingsTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {/* SEC-041: Security Settings REMOVED - was non-functional, use Admin Console instead */}
      <div className="min-h-[400px]">
        {activeSettingsTab === "general" && renderGeneralSettings()}
        {/* SEC-013: Enterprise API Key Management Tab - CONSOLIDATED HERE (single source of truth) */}
        {activeSettingsTab === "api-keys" && (
          <ApiKeyManagement
            API_BASE_URL={API_BASE_URL || ""}
            getAuthHeaders={getAuthHeaders}
          />
        )}
        {/* SEC-055: Interactive API Explorer - Stripe/Postman style */}
        {activeSettingsTab === "api-explorer" && (
          <InteractiveApiExplorer
            getAuthHeaders={getAuthHeaders}
            API_BASE_URL={API_BASE_URL || ""}
          />
        )}
        {activeSettingsTab === "integrations" && renderIntegrations()}
        {activeSettingsTab === "risk-config" && <RiskConfigurationTab getAuthHeaders={getAuthHeaders} />}
        {activeSettingsTab === "admin-tools" && renderAdminTools()}
      </div>

      {/* Phase 5: Integration Management Modal */}
      <IntegrationManagement
        isOpen={showIntegrationModal}
        onClose={() => {
          setShowIntegrationModal(false);
          setSelectedIntegrationType(null);
        }}
        initialType={selectedIntegrationType}
        onIntegrationSaved={handleIntegrationSaved}
      />

      {/* SEC-047: Integration Setup Wizard (Datadog-style) */}
      <IntegrationWizard
        isOpen={showIntegrationWizard}
        onClose={() => setShowIntegrationWizard(false)}
        onComplete={() => {
          setShowIntegrationWizard(false);
          fetchIntegrationStatus();
        }}
      />

      {/* SEC-051: Integration Health Dashboard Modal */}
      {showHealthDashboard && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Integration Health Dashboard</h2>
              <button
                onClick={() => setShowHealthDashboard(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-light"
              >
                &times;
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <IntegrationHealthDashboard />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnterpriseSettings;