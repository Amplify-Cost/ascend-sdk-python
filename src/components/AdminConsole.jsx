/**
 * SEC-022: Admin Console - Banking-Level Enterprise Management
 *
 * ASCEND AI Governance Platform
 * Organization administration with enterprise security controls
 *
 * Features:
 * - Organization settings management
 * - User management (invite, remove, role changes)
 * - Billing & subscription management
 * - Usage analytics dashboard
 * - API key management
 *
 * Security: Requires org_admin role
 * Compliance: SOC 2, HIPAA, PCI-DSS, GDPR
 */

import React, { useState, useEffect, useCallback } from 'react';

// Tab configuration
const ADMIN_TABS = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'organization', label: 'Organization', icon: '🏢' },
  { id: 'users', label: 'Users', icon: '👥' },
  { id: 'billing', label: 'Billing', icon: '💳' },
  { id: 'analytics', label: 'Analytics', icon: '📈' },
  { id: 'api-keys', label: 'API Keys', icon: '🔑' },
  { id: 'audit', label: 'Audit Log', icon: '📋' },
];

// Role definitions
const USER_ROLES = [
  { value: 'viewer', label: 'Viewer', description: 'Read-only access to dashboards' },
  { value: 'analyst', label: 'Analyst', description: 'Can create rules and view alerts' },
  { value: 'admin', label: 'Admin', description: 'Full access except billing' },
  { value: 'org_admin', label: 'Organization Admin', description: 'Full administrative access' },
];

const AdminConsole = () => {
  // State management
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states
  const [organization, setOrganization] = useState(null);
  const [users, setUsers] = useState([]);
  const [billing, setBilling] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [apiKeys, setApiKeys] = useState([]);
  const [auditLog, setAuditLog] = useState([]);

  // Modal states
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [newApiKey, setNewApiKey] = useState(null);

  // Form states
  const [inviteForm, setInviteForm] = useState({ email: '', firstName: '', lastName: '', role: 'analyst' });
  const [apiKeyForm, setApiKeyForm] = useState({ name: '', permissions: ['read'] });

  // API helper
  const apiCall = useCallback(async (endpoint, options = {}) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/admin-console${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }, []);

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [orgData, usersData, billingData, analyticsData, keysData] = await Promise.all([
        apiCall('/organization'),
        apiCall('/users'),
        apiCall('/billing'),
        apiCall('/analytics'),
        apiCall('/api-keys'),
      ]);

      setOrganization(orgData);
      setUsers(usersData.users || []);
      setBilling(billingData);
      setAnalytics(analyticsData);
      setApiKeys(keysData.keys || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // User management functions
  const inviteUser = async () => {
    try {
      await apiCall('/users/invite', {
        method: 'POST',
        body: JSON.stringify(inviteForm),
      });
      setShowInviteModal(false);
      setInviteForm({ email: '', firstName: '', lastName: '', role: 'analyst' });
      loadDashboardData();
    } catch (err) {
      setError(err.message);
    }
  };

  const updateUserRole = async (userId, newRole) => {
    try {
      await apiCall(`/users/${userId}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole }),
      });
      loadDashboardData();
    } catch (err) {
      setError(err.message);
    }
  };

  const removeUser = async (userId) => {
    try {
      await apiCall(`/users/${userId}`, { method: 'DELETE' });
      setShowDeleteConfirm(null);
      loadDashboardData();
    } catch (err) {
      setError(err.message);
    }
  };

  // API Key functions
  const generateApiKey = async () => {
    try {
      const result = await apiCall('/api-keys/generate', {
        method: 'POST',
        body: JSON.stringify(apiKeyForm),
      });
      setNewApiKey(result.key);
      setApiKeyForm({ name: '', permissions: ['read'] });
      loadDashboardData();
    } catch (err) {
      setError(err.message);
    }
  };

  const revokeApiKey = async (keyId) => {
    try {
      await apiCall(`/api-keys/${keyId}/revoke`, { method: 'POST' });
      loadDashboardData();
    } catch (err) {
      setError(err.message);
    }
  };

  // Load audit log
  const loadAuditLog = async () => {
    try {
      const data = await apiCall('/audit-log?limit=100');
      setAuditLog(data.entries || []);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'audit') {
      loadAuditLog();
    }
  }, [activeTab]);

  // Render functions
  const renderOverview = () => (
    <div className="admin-overview">
      <h2>Organization Overview</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <div className="stat-value">{users.length}</div>
            <div className="stat-label">Total Users</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🔑</div>
          <div className="stat-content">
            <div className="stat-value">{apiKeys.filter(k => k.is_active).length}</div>
            <div className="stat-label">Active API Keys</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{analytics?.api_calls_this_month?.toLocaleString() || 0}</div>
            <div className="stat-label">API Calls (Month)</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏱️</div>
          <div className="stat-content">
            <div className="stat-value">{billing?.days_remaining || 0}</div>
            <div className="stat-label">Days Remaining</div>
          </div>
        </div>
      </div>

      <div className="overview-sections">
        <div className="overview-section">
          <h3>Subscription Status</h3>
          <div className="subscription-info">
            <div className="tier-badge">{billing?.tier?.toUpperCase() || 'PILOT'}</div>
            <p>Status: <span className={`status-${billing?.status}`}>{billing?.status || 'Active'}</span></p>
            {billing?.trial_ends_at && (
              <p>Trial ends: {new Date(billing.trial_ends_at).toLocaleDateString()}</p>
            )}
          </div>
        </div>

        <div className="overview-section">
          <h3>Recent Activity</h3>
          <div className="recent-activity">
            {analytics?.recent_activity?.slice(0, 5).map((activity, i) => (
              <div key={i} className="activity-item">
                <span className="activity-time">{new Date(activity.timestamp).toLocaleString()}</span>
                <span className="activity-text">{activity.description}</span>
              </div>
            )) || <p className="no-data">No recent activity</p>}
          </div>
        </div>
      </div>
    </div>
  );

  const renderOrganization = () => (
    <div className="admin-organization">
      <h2>Organization Settings</h2>

      <div className="settings-form">
        <div className="form-group">
          <label>Organization Name</label>
          <input
            type="text"
            value={organization?.name || ''}
            onChange={(e) => setOrganization({ ...organization, name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Organization Slug</label>
          <input
            type="text"
            value={organization?.slug || ''}
            disabled
            className="disabled"
          />
          <span className="help-text">Organization slug cannot be changed</span>
        </div>

        <div className="form-group">
          <label>Industry</label>
          <select
            value={organization?.industry || ''}
            onChange={(e) => setOrganization({ ...organization, industry: e.target.value })}
          >
            <option value="">Select Industry</option>
            <option value="finance">Financial Services</option>
            <option value="healthcare">Healthcare</option>
            <option value="technology">Technology</option>
            <option value="retail">Retail</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="government">Government</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="form-group">
          <label>Primary Contact Email</label>
          <input
            type="email"
            value={organization?.primary_email || ''}
            onChange={(e) => setOrganization({ ...organization, primary_email: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Support Email</label>
          <input
            type="email"
            value={organization?.support_email || ''}
            onChange={(e) => setOrganization({ ...organization, support_email: e.target.value })}
          />
        </div>

        <button
          className="btn-primary"
          onClick={async () => {
            try {
              await apiCall('/organization', {
                method: 'PUT',
                body: JSON.stringify(organization),
              });
              alert('Organization settings saved');
            } catch (err) {
              setError(err.message);
            }
          }}
        >
          Save Changes
        </button>
      </div>

      <div className="security-settings">
        <h3>Security Settings</h3>

        <div className="toggle-setting">
          <label>
            <input
              type="checkbox"
              checked={organization?.mfa_required || false}
              onChange={(e) => setOrganization({ ...organization, mfa_required: e.target.checked })}
            />
            Require MFA for all users
          </label>
          <span className="help-text">Enforce multi-factor authentication for enhanced security</span>
        </div>

        <div className="toggle-setting">
          <label>
            <input
              type="checkbox"
              checked={organization?.sso_enabled || false}
              onChange={(e) => setOrganization({ ...organization, sso_enabled: e.target.checked })}
            />
            Enable SSO/SAML
          </label>
          <span className="help-text">Allow single sign-on with your identity provider</span>
        </div>

        <div className="form-group">
          <label>Session Timeout (minutes)</label>
          <input
            type="number"
            min="5"
            max="1440"
            value={organization?.session_timeout_minutes || 60}
            onChange={(e) => setOrganization({ ...organization, session_timeout_minutes: parseInt(e.target.value) })}
          />
        </div>
      </div>
    </div>
  );

  const renderUsers = () => (
    <div className="admin-users">
      <div className="section-header">
        <h2>User Management</h2>
        <button className="btn-primary" onClick={() => setShowInviteModal(true)}>
          + Invite User
        </button>
      </div>

      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>
                  <div className="user-info">
                    <div className="user-avatar">{user.first_name?.[0]}{user.last_name?.[0]}</div>
                    <span>{user.first_name} {user.last_name}</span>
                  </div>
                </td>
                <td>{user.email}</td>
                <td>
                  <select
                    value={user.role}
                    onChange={(e) => updateUserRole(user.id, e.target.value)}
                    disabled={user.is_owner}
                  >
                    {USER_ROLES.map(role => (
                      <option key={role.value} value={role.value}>{role.label}</option>
                    ))}
                  </select>
                </td>
                <td>
                  <span className={`status-badge status-${user.status}`}>
                    {user.status || 'active'}
                  </span>
                </td>
                <td>{user.last_active_at ? new Date(user.last_active_at).toLocaleDateString() : 'Never'}</td>
                <td>
                  {!user.is_owner && (
                    <button
                      className="btn-danger-small"
                      onClick={() => setShowDeleteConfirm(user)}
                    >
                      Remove
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Invite User Modal */}
      {showInviteModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Invite New User</h3>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                value={inviteForm.email}
                onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                placeholder="user@company.com"
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>First Name</label>
                <input
                  type="text"
                  value={inviteForm.firstName}
                  onChange={(e) => setInviteForm({ ...inviteForm, firstName: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input
                  type="text"
                  value={inviteForm.lastName}
                  onChange={(e) => setInviteForm({ ...inviteForm, lastName: e.target.value })}
                />
              </div>
            </div>
            <div className="form-group">
              <label>Role</label>
              <select
                value={inviteForm.role}
                onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
              >
                {USER_ROLES.map(role => (
                  <option key={role.value} value={role.value}>{role.label} - {role.description}</option>
                ))}
              </select>
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowInviteModal(false)}>Cancel</button>
              <button className="btn-primary" onClick={inviteUser}>Send Invitation</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="modal-overlay">
          <div className="modal modal-danger">
            <h3>Remove User</h3>
            <p>Are you sure you want to remove <strong>{showDeleteConfirm.email}</strong> from the organization?</p>
            <p className="warning">This action cannot be undone. The user will lose access immediately.</p>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowDeleteConfirm(null)}>Cancel</button>
              <button className="btn-danger" onClick={() => removeUser(showDeleteConfirm.id)}>Remove User</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderBilling = () => (
    <div className="admin-billing">
      <h2>Billing & Subscription</h2>

      <div className="subscription-card">
        <div className="subscription-header">
          <div className="tier-info">
            <span className="tier-badge large">{billing?.tier?.toUpperCase() || 'PILOT'}</span>
            <span className={`status-badge status-${billing?.status}`}>{billing?.status || 'Active'}</span>
          </div>
          {billing?.is_trial && (
            <div className="trial-banner">
              <span>Trial Period</span>
              <span>{billing?.days_remaining} days remaining</span>
            </div>
          )}
        </div>

        <div className="subscription-details">
          <div className="detail-row">
            <span>Current Period</span>
            <span>{billing?.current_period_start ? new Date(billing.current_period_start).toLocaleDateString() : 'N/A'} - {billing?.current_period_end ? new Date(billing.current_period_end).toLocaleDateString() : 'N/A'}</span>
          </div>
          <div className="detail-row">
            <span>Monthly Price</span>
            <span>${(billing?.price_cents / 100)?.toFixed(2) || '0.00'}/month</span>
          </div>
          <div className="detail-row">
            <span>Billing Email</span>
            <span>{billing?.billing_email || organization?.primary_email || 'Not set'}</span>
          </div>
        </div>

        <div className="subscription-actions">
          <button className="btn-primary">Upgrade Plan</button>
          <button className="btn-secondary">Manage Payment Method</button>
        </div>
      </div>

      <div className="usage-section">
        <h3>Usage This Period</h3>
        <div className="usage-bars">
          <div className="usage-item">
            <div className="usage-header">
              <span>Users</span>
              <span>{users.length} / {billing?.limits?.users || 5}</span>
            </div>
            <div className="usage-bar">
              <div
                className="usage-fill"
                style={{ width: `${Math.min((users.length / (billing?.limits?.users || 5)) * 100, 100)}%` }}
              />
            </div>
          </div>

          <div className="usage-item">
            <div className="usage-header">
              <span>API Calls</span>
              <span>{analytics?.api_calls_this_month?.toLocaleString() || 0} / {(billing?.limits?.api_calls || 10000).toLocaleString()}</span>
            </div>
            <div className="usage-bar">
              <div
                className="usage-fill"
                style={{ width: `${Math.min(((analytics?.api_calls_this_month || 0) / (billing?.limits?.api_calls || 10000)) * 100, 100)}%` }}
              />
            </div>
          </div>

          <div className="usage-item">
            <div className="usage-header">
              <span>MCP Servers</span>
              <span>{analytics?.mcp_servers_count || 0} / {billing?.limits?.mcp_servers || 3}</span>
            </div>
            <div className="usage-bar">
              <div
                className="usage-fill"
                style={{ width: `${Math.min(((analytics?.mcp_servers_count || 0) / (billing?.limits?.mcp_servers || 3)) * 100, 100)}%` }}
              />
            </div>
          </div>

          <div className="usage-item">
            <div className="usage-header">
              <span>Agents</span>
              <span>{analytics?.agents_count || 0} / {billing?.limits?.agents || 10}</span>
            </div>
            <div className="usage-bar">
              <div
                className="usage-fill"
                style={{ width: `${Math.min(((analytics?.agents_count || 0) / (billing?.limits?.agents || 10)) * 100, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="invoices-section">
        <h3>Invoices</h3>
        <table className="invoices-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {billing?.invoices?.map((invoice, i) => (
              <tr key={i}>
                <td>{new Date(invoice.date).toLocaleDateString()}</td>
                <td>{invoice.description}</td>
                <td>${(invoice.amount_cents / 100).toFixed(2)}</td>
                <td>
                  <span className={`status-badge status-${invoice.status}`}>{invoice.status}</span>
                </td>
                <td>
                  <a href={invoice.pdf_url} target="_blank" rel="noopener noreferrer">Download</a>
                </td>
              </tr>
            )) || (
              <tr>
                <td colSpan="5" className="no-data">No invoices yet</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="admin-analytics">
      <h2>Usage Analytics</h2>

      <div className="analytics-period">
        <select defaultValue="30">
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>

      <div className="analytics-grid">
        <div className="analytics-card">
          <h4>API Calls</h4>
          <div className="analytics-value">{analytics?.api_calls_this_month?.toLocaleString() || 0}</div>
          <div className="analytics-trend positive">+{analytics?.api_calls_trend || 0}% from last period</div>
        </div>

        <div className="analytics-card">
          <h4>Active Users</h4>
          <div className="analytics-value">{analytics?.active_users_count || 0}</div>
          <div className="analytics-trend">{analytics?.active_users_trend || 0}% from last period</div>
        </div>

        <div className="analytics-card">
          <h4>Alerts Processed</h4>
          <div className="analytics-value">{analytics?.alerts_processed?.toLocaleString() || 0}</div>
          <div className="analytics-trend positive">+{analytics?.alerts_trend || 0}% from last period</div>
        </div>

        <div className="analytics-card">
          <h4>Rules Active</h4>
          <div className="analytics-value">{analytics?.active_rules_count || 0}</div>
          <div className="analytics-trend">{analytics?.rules_trend || 0}% from last period</div>
        </div>
      </div>

      <div className="analytics-sections">
        <div className="analytics-section">
          <h3>API Usage by Endpoint</h3>
          <table className="analytics-table">
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Calls</th>
                <th>Avg Response Time</th>
                <th>Error Rate</th>
              </tr>
            </thead>
            <tbody>
              {analytics?.endpoint_stats?.map((stat, i) => (
                <tr key={i}>
                  <td><code>{stat.endpoint}</code></td>
                  <td>{stat.calls.toLocaleString()}</td>
                  <td>{stat.avg_response_ms}ms</td>
                  <td className={stat.error_rate > 1 ? 'error' : ''}>{stat.error_rate.toFixed(2)}%</td>
                </tr>
              )) || (
                <tr>
                  <td colSpan="4" className="no-data">No endpoint data available</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="analytics-section">
          <h3>Top Users by Activity</h3>
          <table className="analytics-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Actions</th>
                <th>Last Active</th>
              </tr>
            </thead>
            <tbody>
              {analytics?.top_users?.map((user, i) => (
                <tr key={i}>
                  <td>{user.email}</td>
                  <td>{user.action_count.toLocaleString()}</td>
                  <td>{new Date(user.last_active).toLocaleString()}</td>
                </tr>
              )) || (
                <tr>
                  <td colSpan="3" className="no-data">No user activity data</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderApiKeys = () => (
    <div className="admin-api-keys">
      <div className="section-header">
        <h2>API Key Management</h2>
        <button className="btn-primary" onClick={() => setShowApiKeyModal(true)}>
          + Generate New Key
        </button>
      </div>

      <div className="security-notice">
        <span className="notice-icon">🔒</span>
        <div>
          <strong>Banking-Level Security</strong>
          <p>API keys are hashed using SHA-256. The full key is only shown once upon creation.</p>
        </div>
      </div>

      <div className="api-keys-table">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Key (Masked)</th>
              <th>Permissions</th>
              <th>Created</th>
              <th>Last Used</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {apiKeys.map(key => (
              <tr key={key.id} className={!key.is_active ? 'revoked' : ''}>
                <td>{key.name}</td>
                <td><code>{key.key_prefix}...{key.key_suffix}</code></td>
                <td>
                  {key.permissions?.map(p => (
                    <span key={p} className="permission-badge">{p}</span>
                  ))}
                </td>
                <td>{new Date(key.created_at).toLocaleDateString()}</td>
                <td>{key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : 'Never'}</td>
                <td>
                  <span className={`status-badge status-${key.is_active ? 'active' : 'revoked'}`}>
                    {key.is_active ? 'Active' : 'Revoked'}
                  </span>
                </td>
                <td>
                  {key.is_active && (
                    <button
                      className="btn-danger-small"
                      onClick={() => revokeApiKey(key.id)}
                    >
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Generate API Key Modal */}
      {showApiKeyModal && (
        <div className="modal-overlay">
          <div className="modal">
            {newApiKey ? (
              <>
                <h3>API Key Generated</h3>
                <div className="key-display">
                  <div className="key-warning">
                    <span className="warning-icon">⚠️</span>
                    <strong>Copy this key now - it won't be shown again!</strong>
                  </div>
                  <div className="key-value">
                    <code>{newApiKey}</code>
                    <button
                      className="btn-copy"
                      onClick={() => {
                        navigator.clipboard.writeText(newApiKey);
                        alert('API key copied to clipboard');
                      }}
                    >
                      Copy
                    </button>
                  </div>
                </div>
                <div className="modal-actions">
                  <button
                    className="btn-primary"
                    onClick={() => {
                      setShowApiKeyModal(false);
                      setNewApiKey(null);
                    }}
                  >
                    Done
                  </button>
                </div>
              </>
            ) : (
              <>
                <h3>Generate New API Key</h3>
                <div className="form-group">
                  <label>Key Name</label>
                  <input
                    type="text"
                    value={apiKeyForm.name}
                    onChange={(e) => setApiKeyForm({ ...apiKeyForm, name: e.target.value })}
                    placeholder="e.g., Production Server, CI/CD Pipeline"
                  />
                </div>
                <div className="form-group">
                  <label>Permissions</label>
                  <div className="checkbox-group">
                    {['read', 'write', 'admin'].map(perm => (
                      <label key={perm} className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={apiKeyForm.permissions.includes(perm)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setApiKeyForm({ ...apiKeyForm, permissions: [...apiKeyForm.permissions, perm] });
                            } else {
                              setApiKeyForm({ ...apiKeyForm, permissions: apiKeyForm.permissions.filter(p => p !== perm) });
                            }
                          }}
                        />
                        {perm.charAt(0).toUpperCase() + perm.slice(1)}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="modal-actions">
                  <button className="btn-secondary" onClick={() => setShowApiKeyModal(false)}>Cancel</button>
                  <button className="btn-primary" onClick={generateApiKey} disabled={!apiKeyForm.name}>
                    Generate Key
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderAuditLog = () => (
    <div className="admin-audit">
      <div className="section-header">
        <h2>Audit Log</h2>
        <button className="btn-secondary" onClick={loadAuditLog}>Refresh</button>
      </div>

      <div className="audit-filters">
        <input type="text" placeholder="Search events..." />
        <select defaultValue="">
          <option value="">All Event Types</option>
          <option value="user.login">User Login</option>
          <option value="user.invite">User Invite</option>
          <option value="user.remove">User Remove</option>
          <option value="api_key.generate">API Key Generate</option>
          <option value="api_key.revoke">API Key Revoke</option>
          <option value="settings.update">Settings Update</option>
        </select>
        <select defaultValue="7">
          <option value="1">Last 24 hours</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>

      <div className="audit-table">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Event Type</th>
              <th>User</th>
              <th>IP Address</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {auditLog.map((entry, i) => (
              <tr key={i}>
                <td>{new Date(entry.timestamp).toLocaleString()}</td>
                <td>
                  <span className={`event-badge event-${entry.event_type?.split('.')[0]}`}>
                    {entry.event_type}
                  </span>
                </td>
                <td>{entry.user_email}</td>
                <td><code>{entry.ip_address}</code></td>
                <td className="details-cell">{JSON.stringify(entry.details)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="compliance-info">
        <h4>Compliance Information</h4>
        <p>Audit logs are retained for {billing?.tier === 'enterprise' ? '365' : billing?.tier === 'growth' ? '90' : '30'} days per your subscription tier.</p>
        <p>All entries are immutable and include cryptographic verification for SOC 2 Type II compliance.</p>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview': return renderOverview();
      case 'organization': return renderOrganization();
      case 'users': return renderUsers();
      case 'billing': return renderBilling();
      case 'analytics': return renderAnalytics();
      case 'api-keys': return renderApiKeys();
      case 'audit': return renderAuditLog();
      default: return renderOverview();
    }
  };

  if (loading) {
    return (
      <div className="admin-console loading">
        <div className="loading-spinner" />
        <p>Loading Admin Console...</p>
      </div>
    );
  }

  return (
    <div className="admin-console">
      {/* Header */}
      <div className="admin-header">
        <div className="header-content">
          <h1>Admin Console</h1>
          <p className="org-name">{organization?.name || 'Organization'}</p>
        </div>
        <div className="header-actions">
          <button className="btn-icon" onClick={loadDashboardData} title="Refresh">
            🔄
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Navigation */}
      <nav className="admin-nav">
        {ADMIN_TABS.map(tab => (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="admin-content">
        {renderContent()}
      </main>

      <style jsx>{`
        .admin-console {
          min-height: 100vh;
          background: #0a0a0f;
          color: #e0e0e0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .admin-console.loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        .loading-spinner {
          width: 48px;
          height: 48px;
          border: 3px solid #1a1a2e;
          border-top-color: #00d4ff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        /* Header */
        .admin-header {
          background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
          padding: 24px 32px;
          border-bottom: 1px solid rgba(0, 212, 255, 0.2);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .admin-header h1 {
          font-size: 24px;
          font-weight: 600;
          color: #fff;
          margin: 0;
        }

        .org-name {
          color: #00d4ff;
          font-size: 14px;
          margin-top: 4px;
        }

        .btn-icon {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          padding: 8px 12px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 18px;
        }

        .btn-icon:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        /* Error Banner */
        .error-banner {
          background: rgba(255, 82, 82, 0.1);
          border: 1px solid rgba(255, 82, 82, 0.3);
          color: #ff5252;
          padding: 12px 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .error-banner button {
          background: none;
          border: none;
          color: #ff5252;
          font-size: 20px;
          cursor: pointer;
        }

        /* Navigation */
        .admin-nav {
          display: flex;
          background: #0f0f1a;
          border-bottom: 1px solid #1a1a2e;
          padding: 0 16px;
          overflow-x: auto;
        }

        .nav-tab {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 16px 20px;
          background: none;
          border: none;
          color: #888;
          cursor: pointer;
          border-bottom: 2px solid transparent;
          transition: all 0.2s;
          white-space: nowrap;
        }

        .nav-tab:hover {
          color: #e0e0e0;
          background: rgba(255, 255, 255, 0.05);
        }

        .nav-tab.active {
          color: #00d4ff;
          border-bottom-color: #00d4ff;
        }

        .tab-icon {
          font-size: 18px;
        }

        /* Content */
        .admin-content {
          padding: 32px;
          max-width: 1400px;
          margin: 0 auto;
        }

        h2 {
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 24px;
          color: #fff;
        }

        h3 {
          font-size: 16px;
          font-weight: 600;
          margin: 24px 0 16px;
          color: #e0e0e0;
        }

        h4 {
          font-size: 14px;
          font-weight: 500;
          color: #888;
          margin-bottom: 8px;
        }

        /* Stats Grid */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 32px;
        }

        .stat-card {
          background: linear-gradient(135deg, #1a1a2e 0%, #151525 100%);
          border: 1px solid rgba(0, 212, 255, 0.1);
          border-radius: 12px;
          padding: 20px;
          display: flex;
          gap: 16px;
          align-items: center;
        }

        .stat-icon {
          font-size: 32px;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #fff;
        }

        .stat-label {
          color: #888;
          font-size: 13px;
        }

        /* Buttons */
        .btn-primary {
          background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
          color: #000;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .btn-secondary {
          background: rgba(255, 255, 255, 0.1);
          color: #e0e0e0;
          border: 1px solid rgba(255, 255, 255, 0.2);
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
        }

        .btn-secondary:hover {
          background: rgba(255, 255, 255, 0.15);
        }

        .btn-danger {
          background: linear-gradient(135deg, #ff5252 0%, #cc0000 100%);
          color: #fff;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }

        .btn-danger-small {
          background: rgba(255, 82, 82, 0.2);
          color: #ff5252;
          border: 1px solid rgba(255, 82, 82, 0.3);
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
        }

        .btn-danger-small:hover {
          background: rgba(255, 82, 82, 0.3);
        }

        .btn-copy {
          background: rgba(0, 212, 255, 0.2);
          color: #00d4ff;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
        }

        /* Forms */
        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          color: #888;
          margin-bottom: 8px;
        }

        .form-group input,
        .form-group select {
          width: 100%;
          padding: 12px 16px;
          background: #0f0f1a;
          border: 1px solid #2a2a3e;
          border-radius: 8px;
          color: #e0e0e0;
          font-size: 14px;
        }

        .form-group input:focus,
        .form-group select:focus {
          outline: none;
          border-color: #00d4ff;
        }

        .form-group input.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .help-text {
          font-size: 12px;
          color: #666;
          margin-top: 6px;
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        /* Tables */
        table {
          width: 100%;
          border-collapse: collapse;
        }

        th, td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #1a1a2e;
        }

        th {
          font-size: 12px;
          font-weight: 600;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        td {
          font-size: 14px;
        }

        tr:hover {
          background: rgba(255, 255, 255, 0.02);
        }

        tr.revoked {
          opacity: 0.5;
        }

        .no-data {
          color: #666;
          text-align: center;
          padding: 24px;
        }

        code {
          background: rgba(0, 212, 255, 0.1);
          padding: 2px 8px;
          border-radius: 4px;
          font-family: 'Monaco', 'Consolas', monospace;
          font-size: 13px;
        }

        /* User Info */
        .user-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 600;
          color: #000;
        }

        /* Status Badges */
        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .status-active, .status-paid {
          background: rgba(0, 212, 255, 0.1);
          color: #00d4ff;
        }

        .status-pending {
          background: rgba(255, 193, 7, 0.1);
          color: #ffc107;
        }

        .status-revoked, .status-inactive {
          background: rgba(255, 82, 82, 0.1);
          color: #ff5252;
        }

        .tier-badge {
          display: inline-block;
          padding: 6px 16px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 700;
          background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
          color: #000;
        }

        .tier-badge.large {
          font-size: 16px;
          padding: 8px 24px;
        }

        .permission-badge {
          display: inline-block;
          padding: 2px 8px;
          margin-right: 4px;
          border-radius: 4px;
          font-size: 11px;
          background: rgba(255, 255, 255, 0.1);
          color: #e0e0e0;
        }

        .event-badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-family: monospace;
        }

        .event-user {
          background: rgba(0, 212, 255, 0.1);
          color: #00d4ff;
        }

        .event-api_key {
          background: rgba(255, 193, 7, 0.1);
          color: #ffc107;
        }

        .event-settings {
          background: rgba(156, 39, 176, 0.1);
          color: #9c27b0;
        }

        /* Modals */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal {
          background: #1a1a2e;
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 16px;
          padding: 32px;
          width: 100%;
          max-width: 480px;
        }

        .modal h3 {
          margin-top: 0;
          color: #fff;
        }

        .modal-danger {
          border-color: rgba(255, 82, 82, 0.3);
        }

        .modal-actions {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
          margin-top: 24px;
        }

        .warning {
          color: #ff5252;
          font-size: 13px;
        }

        /* Key Display */
        .key-display {
          background: #0f0f1a;
          border-radius: 8px;
          padding: 20px;
          margin: 20px 0;
        }

        .key-warning {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #ffc107;
          margin-bottom: 16px;
          font-size: 14px;
        }

        .key-value {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .key-value code {
          flex: 1;
          background: #0a0a0f;
          padding: 12px;
          border-radius: 6px;
          word-break: break-all;
        }

        /* Security Notice */
        .security-notice {
          display: flex;
          gap: 16px;
          background: rgba(0, 212, 255, 0.05);
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 24px;
        }

        .notice-icon {
          font-size: 24px;
        }

        .security-notice strong {
          color: #00d4ff;
        }

        .security-notice p {
          color: #888;
          font-size: 13px;
          margin-top: 4px;
        }

        /* Usage Bars */
        .usage-bars {
          display: grid;
          gap: 16px;
        }

        .usage-item {
          background: #0f0f1a;
          border-radius: 8px;
          padding: 16px;
        }

        .usage-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 14px;
        }

        .usage-bar {
          height: 8px;
          background: #1a1a2e;
          border-radius: 4px;
          overflow: hidden;
        }

        .usage-fill {
          height: 100%;
          background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        /* Subscription */
        .subscription-card {
          background: linear-gradient(135deg, #1a1a2e 0%, #151525 100%);
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 16px;
          padding: 24px;
          margin-bottom: 32px;
        }

        .subscription-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 20px;
        }

        .tier-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .trial-banner {
          background: rgba(255, 193, 7, 0.1);
          border: 1px solid rgba(255, 193, 7, 0.3);
          border-radius: 8px;
          padding: 8px 16px;
          text-align: right;
        }

        .trial-banner span:first-child {
          display: block;
          color: #ffc107;
          font-weight: 600;
          font-size: 12px;
        }

        .trial-banner span:last-child {
          font-size: 14px;
        }

        .subscription-details {
          margin-bottom: 20px;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          padding: 12px 0;
          border-bottom: 1px solid #1a1a2e;
        }

        .detail-row:last-child {
          border-bottom: none;
        }

        .subscription-actions {
          display: flex;
          gap: 12px;
        }

        /* Analytics */
        .analytics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 32px;
        }

        .analytics-card {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
        }

        .analytics-value {
          font-size: 32px;
          font-weight: 700;
          color: #fff;
          margin: 8px 0;
        }

        .analytics-trend {
          font-size: 13px;
          color: #888;
        }

        .analytics-trend.positive {
          color: #4caf50;
        }

        .analytics-period {
          margin-bottom: 24px;
        }

        .analytics-period select {
          padding: 8px 16px;
          background: #1a1a2e;
          border: 1px solid #2a2a3e;
          border-radius: 8px;
          color: #e0e0e0;
        }

        .analytics-section {
          background: #0f0f1a;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 24px;
        }

        .analytics-table td.error {
          color: #ff5252;
        }

        /* Audit */
        .audit-filters {
          display: flex;
          gap: 16px;
          margin-bottom: 24px;
        }

        .audit-filters input,
        .audit-filters select {
          padding: 10px 16px;
          background: #1a1a2e;
          border: 1px solid #2a2a3e;
          border-radius: 8px;
          color: #e0e0e0;
        }

        .audit-filters input {
          flex: 1;
        }

        .audit-table {
          background: #0f0f1a;
          border-radius: 12px;
          overflow: hidden;
        }

        .details-cell {
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-family: monospace;
          font-size: 12px;
          color: #666;
        }

        .compliance-info {
          background: rgba(0, 212, 255, 0.05);
          border: 1px solid rgba(0, 212, 255, 0.1);
          border-radius: 12px;
          padding: 20px;
          margin-top: 24px;
        }

        .compliance-info h4 {
          color: #00d4ff;
          margin-bottom: 12px;
        }

        .compliance-info p {
          font-size: 13px;
          color: #888;
          margin: 8px 0;
        }

        /* Toggle Settings */
        .toggle-setting {
          margin-bottom: 20px;
        }

        .toggle-setting label {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
        }

        .toggle-setting input[type="checkbox"] {
          width: 20px;
          height: 20px;
          accent-color: #00d4ff;
        }

        .checkbox-group {
          display: flex;
          gap: 20px;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }

        /* Section Header */
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .section-header h2 {
          margin: 0;
        }

        /* Overview Sections */
        .overview-sections {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
        }

        .overview-section {
          background: #0f0f1a;
          border-radius: 12px;
          padding: 20px;
        }

        .recent-activity {
          max-height: 200px;
          overflow-y: auto;
        }

        .activity-item {
          padding: 12px 0;
          border-bottom: 1px solid #1a1a2e;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .activity-time {
          font-size: 12px;
          color: #666;
        }

        .activity-text {
          font-size: 14px;
        }

        /* Responsive */
        @media (max-width: 768px) {
          .admin-content {
            padding: 16px;
          }

          .stats-grid,
          .analytics-grid,
          .overview-sections {
            grid-template-columns: 1fr;
          }

          .form-row {
            grid-template-columns: 1fr;
          }

          .audit-filters {
            flex-direction: column;
          }

          .subscription-header {
            flex-direction: column;
            gap: 16px;
          }
        }
      `}</style>
    </div>
  );
};

export default AdminConsole;
