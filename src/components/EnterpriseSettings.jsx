import React, { useState, useEffect, useCallback } from "react";
import AgentActionSubmitPanel from "./AgentActionSubmitPanel";
import RiskConfigurationTab from "./risk-config/RiskConfigurationTab";
import ApiKeyManagement from "./ApiKeyManagement";
import fetchWithAuth from "../utils/fetchWithAuth";

/**
 * 🏢 SEC-013: Enterprise Settings with API Key Management
 * 🏢 SEC-028: Enterprise Integration Status (No Hardcoded Data)
 * Banking-Level Security: PCI-DSS 8.3.1, HIPAA 164.312(d), SOC 2 CC6.1
 * Authored-By: OW-KAI Engineer
 */
const EnterpriseSettings = ({ getAuthHeaders, user, API_BASE_URL }) => {
  const [activeSettingsTab, setActiveSettingsTab] = useState("general");
  const [acknowledgment, setAcknowledgment] = useState(false);

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

  // SEC-028: Helper to render integration status badge
  const renderIntegrationStatus = (integration, name, colorScheme) => {
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
          <button className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">
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
        <span className={`px-2 py-1 ${colors.badge} text-xs rounded`}>
          {integration.status?.toUpperCase() || 'UNKNOWN'}
        </span>
      </div>
    );
  };

  const settingsTabs = [
    { id: "general", label: "General Settings" },
    { id: "security", label: "Security Settings" },
    { id: "api-keys", label: "🔑 API Keys" }, // SEC-013: Enterprise API Key Management
    { id: "integrations", label: "Integrations" },
    { id: "risk-config", label: "🎯 Risk Configuration" }, // Enterprise Risk Scoring
    { id: "admin-tools", label: "🔧 Admin Tools" } // Admin-only tab
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

  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">🔐 Authentication Settings</h4>
        <div className="space-y-4">
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" defaultChecked />
            <span className="text-sm">Require MFA for admin actions</span>
          </label>
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" defaultChecked />
            <span className="text-sm">Auto-logout after 8 hours</span>
          </label>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password Policy</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option>Enterprise (12+ chars, complex)</option>
              <option>Standard (8+ chars)</option>
              <option>High Security (16+ chars, MFA required)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">🛡️ Risk Management</h4>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Default Risk Threshold</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option>Conservative (60+ requires approval)</option>
              <option>Balanced (70+ requires approval)</option>
              <option>Aggressive (80+ requires approval)</option>
            </select>
          </div>
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" defaultChecked />
            <span className="text-sm">Auto-escalate critical threats</span>
          </label>
        </div>
      </div>
    </div>
  );

  // SEC-028: Enterprise Integrations (Dynamic from API - Multi-Tenant)
  const renderIntegrations = () => (
    <div className="space-y-6">
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
          {/* SEC-028: Dynamic Splunk Status */}
          {renderIntegrationStatus(integrationStatus.splunk, 'Splunk Enterprise', 'green')}

          {/* SEC-028: Dynamic QRadar Status */}
          {renderIntegrationStatus(integrationStatus.qradar, 'IBM QRadar', 'blue')}

          {/* SEC-028: Dynamic Sentinel Status */}
          {renderIntegrationStatus(integrationStatus.sentinel, 'Microsoft Sentinel', 'purple')}
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">🏢 Enterprise Systems</h4>
        <div className="space-y-4">
          {/* SEC-028: Dynamic Active Directory Status (with user count) */}
          {renderIntegrationStatus(integrationStatus.activeDirectory, 'Active Directory', 'yellow')}

          {/* SEC-028: Dynamic SSO Status */}
          {renderIntegrationStatus(integrationStatus.sso, 'SSO Integration', 'gray')}
        </div>
      </div>

      {/* SEC-028: Multi-Tenant Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-700">
          <strong>🏢 Multi-Tenant Note:</strong> Integration status shown is specific to your organization.
          Contact your administrator to configure additional integrations.
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
      
      {/* Audit Tools */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4">📋 Audit & Compliance Tools</h4>
        <p className="text-gray-600 text-sm mb-4">
          Generate compliance reports and audit trails for regulatory review.
        </p>
        
        <div className="space-y-3">
          <button className="w-full p-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <div className="flex justify-between items-center">
              <div>
                <h5 className="font-medium text-gray-900">📊 SOX Compliance Report</h5>
                <p className="text-sm text-gray-600">Generate Sarbanes-Oxley audit trail</p>
              </div>
              <span className="text-blue-600">Generate →</span>
            </div>
          </button>
          
          <button className="w-full p-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <div className="flex justify-between items-center">
              <div>
                <h5 className="font-medium text-gray-900">🏥 HIPAA Security Report</h5>
                <p className="text-sm text-gray-600">Healthcare data protection audit</p>
              </div>
              <span className="text-blue-600">Generate →</span>
            </div>
          </button>
          
          <button className="w-full p-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <div className="flex justify-between items-center">
              <div>
                <h5 className="font-medium text-gray-900">💳 PCI-DSS Assessment</h5>
                <p className="text-sm text-gray-600">Payment card security compliance</p>
              </div>
              <span className="text-blue-600">Generate →</span>
            </div>
          </button>
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
      <div className="min-h-[400px]">
        {activeSettingsTab === "general" && renderGeneralSettings()}
        {activeSettingsTab === "security" && renderSecuritySettings()}
        {/* 🏢 SEC-013: Enterprise API Key Management Tab */}
        {activeSettingsTab === "api-keys" && (
          <ApiKeyManagement
            API_BASE_URL={API_BASE_URL || ""}
            getAuthHeaders={getAuthHeaders}
          />
        )}
        {activeSettingsTab === "integrations" && renderIntegrations()}
        {activeSettingsTab === "risk-config" && <RiskConfigurationTab getAuthHeaders={getAuthHeaders} />}
        {activeSettingsTab === "admin-tools" && renderAdminTools()}
      </div>
    </div>
  );
};

export default EnterpriseSettings;