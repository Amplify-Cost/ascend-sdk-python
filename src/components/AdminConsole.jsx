/**
 * SEC-046: Admin Console - Banking-Level Enterprise Management
 *
 * ASCEND AI Governance Platform
 * Organization administration with enterprise security controls
 *
 * Features:
 * - Organization settings management
 * - User management (invite, remove, role changes)
 * - Billing & subscription management
 * - Usage analytics dashboard
 * - Audit log with compliance reporting
 *
 * SEC-041: API key management consolidated to Settings tab (EnterpriseSettings.jsx)
 * SEC-046: Added toast notifications, loading states, fixed field name alignment
 *
 * Security: Requires org_admin role
 * Compliance: SOC 2, HIPAA, PCI-DSS, GDPR
 */

import React, { useState, useEffect, useCallback } from 'react';

// Tab configuration
// SEC-041: API Keys tab REMOVED - consolidated to Settings tab (single source of truth)
// Settings API Keys has more features: expiration, usage stats, descriptions
const ADMIN_TABS = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'organization', label: 'Organization', icon: '🏢' },
  { id: 'users', label: 'Users', icon: '👥' },
  { id: 'billing', label: 'Billing', icon: '💳' },
  { id: 'analytics', label: 'Analytics', icon: '📈' },
  { id: 'audit', label: 'Audit Log', icon: '📋' },
];

// Role definitions
const USER_ROLES = [
  { value: 'viewer', label: 'Viewer', description: 'Read-only access to dashboards' },
  { value: 'analyst', label: 'Analyst', description: 'Can create rules and view alerts' },
  { value: 'admin', label: 'Admin', description: 'Full access except billing' },
  { value: 'org_admin', label: 'Organization Admin', description: 'Full administrative access' },
];

// SEC-046: Toast notification component
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const colors = {
    success: { bg: 'rgba(76, 175, 80, 0.15)', border: 'rgba(76, 175, 80, 0.5)', text: '#4caf50' },
    error: { bg: 'rgba(244, 67, 54, 0.15)', border: 'rgba(244, 67, 54, 0.5)', text: '#f44336' },
    warning: { bg: 'rgba(255, 152, 0, 0.15)', border: 'rgba(255, 152, 0, 0.5)', text: '#ff9800' },
    info: { bg: 'rgba(33, 150, 243, 0.15)', border: 'rgba(33, 150, 243, 0.5)', text: '#2196f3' }
  };

  const color = colors[type] || colors.info;

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '16px 24px',
      background: color.bg,
      border: `1px solid ${color.border}`,
      borderRadius: '8px',
      color: color.text,
      fontWeight: '500',
      zIndex: 10000,
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      animation: 'slideIn 0.3s ease'
    }}>
      <span>{type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠' : 'ℹ'}</span>
      <span>{message}</span>
      <button
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: color.text,
          cursor: 'pointer',
          fontSize: '18px',
          marginLeft: '8px'
        }}
      >×</button>
    </div>
  );
};

const AdminConsole = () => {
  // State management
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // SEC-046: Toast notification state
  const [toast, setToast] = useState(null);

  // SEC-046: Operation loading states
  const [operationLoading, setOperationLoading] = useState({
    invite: false,
    delete: false,
    roleChange: false,
    save: false,
    // Phase 2: User action operations
    suspend: false,
    editProfile: false,
    resetPassword: false,
    forceLogout: false
  });

  // Data states
  const [organization, setOrganization] = useState(null);
  const [users, setUsers] = useState([]);
  const [billing, setBilling] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  // SEC-041: apiKeys state REMOVED - consolidated to Settings tab
  const [auditLog, setAuditLog] = useState([]);

  // Modal states
  const [showInviteModal, setShowInviteModal] = useState(false);
  // SEC-041: showApiKeyModal, newApiKey REMOVED - consolidated to Settings tab
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  // SEC-046 Phase 2: User action modal states
  const [showUserActionsMenu, setShowUserActionsMenu] = useState(null); // user id or null
  const [showSuspendModal, setShowSuspendModal] = useState(null); // user object or null
  const [showEditProfileModal, setShowEditProfileModal] = useState(null); // user object or null
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(null); // user object or null
  const [showForceLogoutModal, setShowForceLogoutModal] = useState(null); // user object or null
  const [showActivityModal, setShowActivityModal] = useState(null); // user object or null
  const [userActivityData, setUserActivityData] = useState([]);
  const [activityLoading, setActivityLoading] = useState(false);

  // Form states
  // SEC-043: Fixed field names to match backend (snake_case: first_name, last_name)
  const [inviteForm, setInviteForm] = useState({ email: '', first_name: '', last_name: '', role: 'analyst' });
  // SEC-041: apiKeyForm REMOVED - consolidated to Settings tab

  // SEC-046 Phase 2: Edit profile form state
  const [editProfileForm, setEditProfileForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    job_title: ''
  });
  const [suspendReason, setSuspendReason] = useState('');
  const [forceLogoutReason, setForceLogoutReason] = useState('');

  // ===========================================
  // SEC-046 Phase 3: Enterprise Features State
  // ===========================================

  // Bulk operations
  const [selectedUsers, setSelectedUsers] = useState(new Set());
  const [bulkOperationLoading, setBulkOperationLoading] = useState(false);
  const [showBulkActionModal, setShowBulkActionModal] = useState(null); // 'suspend' | 'reactivate' | 'delete' | 'role_change'
  const [bulkRoleChange, setBulkRoleChange] = useState('analyst');
  const [bulkReason, setBulkReason] = useState('');

  // Usage alerts
  const [usageAlerts, setUsageAlerts] = useState({ warnings: [], critical: [] });

  // Analytics charts
  const [chartData, setChartData] = useState(null);
  const [chartPeriod, setChartPeriod] = useState(30);

  // Audit log export
  const [exportLoading, setExportLoading] = useState(false);

  // Real-time status
  const [realtimeStatus, setRealtimeStatus] = useState(null);
  const [lastStatusUpdate, setLastStatusUpdate] = useState(null);

  // SEC-046: Show toast notification
  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type });
  }, []);

  // SEC-046: Get CSRF token from cookie (for double-submit protection)
  const getCsrfToken = useCallback(() => {
    const cookies = document.cookie.split('; ');
    const csrfCookie = cookies.find(row => row.startsWith('owai_csrf='));
    return csrfCookie ? csrfCookie.split('=')[1] : null;
  }, []);

  // API helper
  // SEC-042: Fixed route prefix to match backend (/api/admin, not /api/admin-console)
  // SEC-046: Added CSRF token for POST/PATCH/DELETE (double-submit pattern)
  const apiCall = useCallback(async (endpoint, options = {}) => {
    const token = localStorage.getItem('token');
    const method = (options.method || 'GET').toUpperCase();

    // SEC-046: Include CSRF token for mutating requests
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add CSRF token for POST/PATCH/DELETE/PUT requests
    if (['POST', 'PATCH', 'DELETE', 'PUT'].includes(method)) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }
    }

    const response = await fetch(`/api/admin${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      // SEC-058: Handle non-JSON error responses (e.g., "Internal Server Error")
      let errorMessage = 'API request failed';
      try {
        const error = await response.json();
        errorMessage = error.detail || errorMessage;
      } catch {
        errorMessage = `Server error (${response.status})`;
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }, [getCsrfToken]);

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // SEC-041: API keys fetch REMOVED - consolidated to Settings tab
      // SEC-043: Fixed analytics path to match backend (/analytics/overview)
      const [orgData, usersData, billingData, analyticsData] = await Promise.all([
        apiCall('/organization'),
        apiCall('/users'),
        apiCall('/billing'),
        apiCall('/analytics/overview'),
      ]);

      setOrganization(orgData);
      setUsers(usersData.users || []);
      setBilling(billingData);
      setAnalytics(analyticsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // User management functions
  // SEC-046: Added loading states and toast notifications for enterprise UX
  const inviteUser = async () => {
    setOperationLoading(prev => ({ ...prev, invite: true }));
    try {
      await apiCall('/users/invite', {
        method: 'POST',
        body: JSON.stringify(inviteForm),
      });
      setShowInviteModal(false);
      setInviteForm({ email: '', first_name: '', last_name: '', role: 'analyst' });
      showToast(`Invitation sent to ${inviteForm.email}`, 'success');
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
      setError(err.message);
    } finally {
      setOperationLoading(prev => ({ ...prev, invite: false }));
    }
  };

  const updateUserRole = async (userId, newRole) => {
    setOperationLoading(prev => ({ ...prev, roleChange: true }));
    try {
      // SEC-043: Fixed HTTP method to PATCH (backend uses @router.patch)
      await apiCall(`/users/${userId}/role`, {
        method: 'PATCH',
        body: JSON.stringify({ role: newRole }),
      });
      showToast('User role updated successfully', 'success');
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
      setError(err.message);
    } finally {
      setOperationLoading(prev => ({ ...prev, roleChange: false }));
    }
  };

  const removeUser = async (userId) => {
    setOperationLoading(prev => ({ ...prev, delete: true }));
    try {
      const userEmail = showDeleteConfirm?.email || 'User';
      await apiCall(`/users/${userId}`, { method: 'DELETE' });
      setShowDeleteConfirm(null);
      showToast(`${userEmail} has been removed from the organization`, 'success');
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
      setError(err.message);
    } finally {
      setOperationLoading(prev => ({ ...prev, delete: false }));
    }
  };

  // ===========================================
  // SEC-046 Phase 2: User Action Functions
  // Enterprise user management with audit trail
  // ===========================================

  // Suspend or reactivate a user
  const suspendUser = async (userId, suspend) => {
    setOperationLoading(prev => ({ ...prev, suspend: true }));
    try {
      await apiCall(`/users/${userId}/suspend`, {
        method: 'PATCH',
        body: JSON.stringify({
          suspended: suspend,
          reason: suspendReason || undefined
        }),
      });
      setShowSuspendModal(null);
      setSuspendReason('');
      showToast(
        suspend ? 'User has been suspended' : 'User has been reactivated',
        'success'
      );
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setOperationLoading(prev => ({ ...prev, suspend: false }));
    }
  };

  // Edit user profile
  const editUserProfile = async (userId) => {
    setOperationLoading(prev => ({ ...prev, editProfile: true }));
    try {
      // Only send non-empty fields
      const updates = {};
      Object.entries(editProfileForm).forEach(([key, value]) => {
        if (value && value.trim()) {
          updates[key] = value.trim();
        }
      });

      await apiCall(`/users/${userId}/profile`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
      setShowEditProfileModal(null);
      setEditProfileForm({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        department: '',
        job_title: ''
      });
      showToast('User profile updated successfully', 'success');
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setOperationLoading(prev => ({ ...prev, editProfile: false }));
    }
  };

  // Reset user password (triggers Cognito password reset)
  const resetUserPassword = async (userId) => {
    setOperationLoading(prev => ({ ...prev, resetPassword: true }));
    try {
      const response = await apiCall(`/users/${userId}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ send_email: true }),
      });
      setShowResetPasswordModal(null);
      showToast(
        response.email_sent
          ? 'Password reset email sent to user'
          : 'Password reset initiated (email not sent)',
        'success'
      );
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setOperationLoading(prev => ({ ...prev, resetPassword: false }));
    }
  };

  // Force logout user from all sessions
  const forceLogoutUser = async (userId) => {
    setOperationLoading(prev => ({ ...prev, forceLogout: true }));
    try {
      await apiCall(`/users/${userId}/force-logout`, {
        method: 'POST',
        body: JSON.stringify({
          revoke_all_tokens: true,
          reason: forceLogoutReason || undefined
        }),
      });
      setShowForceLogoutModal(null);
      setForceLogoutReason('');
      showToast('User has been logged out from all sessions', 'success');
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setOperationLoading(prev => ({ ...prev, forceLogout: false }));
    }
  };

  // Load user activity log
  const loadUserActivity = async (userId) => {
    setActivityLoading(true);
    try {
      const data = await apiCall(`/users/${userId}/activity?limit=50`);
      setUserActivityData(data.activities || []);
    } catch (err) {
      showToast('Failed to load user activity', 'error');
      setUserActivityData([]);
    } finally {
      setActivityLoading(false);
    }
  };

  // Open edit profile modal with user data
  const openEditProfileModal = (user) => {
    setEditProfileForm({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email || '',
      phone: user.phone || '',
      department: user.department || '',
      job_title: user.job_title || ''
    });
    setShowEditProfileModal(user);
  };

  // Open activity modal and load data
  const openActivityModal = (user) => {
    setShowActivityModal(user);
    loadUserActivity(user.id);
  };

  // ===========================================
  // SEC-046 Phase 3: Enterprise Feature Functions
  // ===========================================

  // Bulk user selection
  const toggleUserSelection = (userId) => {
    setSelectedUsers(prev => {
      const next = new Set(prev);
      if (next.has(userId)) {
        next.delete(userId);
      } else {
        next.add(userId);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    const selectableUsers = users.filter(u => !u.is_owner);
    if (selectedUsers.size === selectableUsers.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(selectableUsers.map(u => u.id)));
    }
  };

  // Execute bulk operation
  const executeBulkOperation = async () => {
    if (selectedUsers.size === 0) return;

    setBulkOperationLoading(true);
    try {
      const payload = {
        user_ids: Array.from(selectedUsers),
        operation: showBulkActionModal,
        reason: bulkReason || undefined
      };

      if (showBulkActionModal === 'role_change') {
        payload.role = bulkRoleChange;
      }

      const result = await apiCall('/users/bulk-operation', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setShowBulkActionModal(null);
      setSelectedUsers(new Set());
      setBulkReason('');

      const successCount = result.results?.filter(r => r.success).length || 0;
      const failCount = result.results?.filter(r => !r.success).length || 0;

      if (failCount > 0) {
        showToast(`${successCount} succeeded, ${failCount} failed`, 'warning');
      } else {
        showToast(`Bulk ${showBulkActionModal} completed for ${successCount} users`, 'success');
      }

      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setBulkOperationLoading(false);
    }
  };

  // Load usage alerts
  const loadUsageAlerts = async () => {
    try {
      const data = await apiCall('/alerts/usage-status');
      setUsageAlerts({
        warnings: data.warnings || [],
        critical: data.critical || []
      });
    } catch (err) {
      console.error('Failed to load usage alerts:', err);
    }
  };

  // Load chart data
  const loadChartData = async (days = chartPeriod) => {
    try {
      const data = await apiCall(`/analytics/charts?days=${days}`);
      setChartData(data);
    } catch (err) {
      console.error('Failed to load chart data:', err);
    }
  };

  // Export audit log
  const exportAuditLog = async (format) => {
    setExportLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/audit-log/export?format=${format}&days=30`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Get filename from header or generate one
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `audit_log_${new Date().toISOString().split('T')[0]}.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) filename = match[1];
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast(`Audit log exported as ${format.toUpperCase()}`, 'success');
    } catch (err) {
      showToast(`Export failed: ${err.message}`, 'error');
    } finally {
      setExportLoading(false);
    }
  };

  // Load real-time status
  const loadRealtimeStatus = async () => {
    try {
      const data = await apiCall('/status/realtime');
      setRealtimeStatus(data);
      setLastStatusUpdate(new Date());
    } catch (err) {
      console.error('Failed to load realtime status:', err);
    }
  };

  // Real-time status polling (every 30 seconds)
  useEffect(() => {
    loadUsageAlerts();
    loadRealtimeStatus();

    const statusInterval = setInterval(() => {
      loadRealtimeStatus();
    }, 30000);

    return () => clearInterval(statusInterval);
  }, []);

  // Load chart data when analytics tab is active
  useEffect(() => {
    if (activeTab === 'analytics') {
      loadChartData(chartPeriod);
    }
  }, [activeTab, chartPeriod]);

  // SEC-046: Save organization settings with toast feedback
  const saveOrganizationSettings = async () => {
    setOperationLoading(prev => ({ ...prev, save: true }));
    try {
      await apiCall('/organization', {
        method: 'PATCH',
        body: JSON.stringify(organization),
      });
      showToast('Organization settings saved successfully', 'success');
    } catch (err) {
      showToast(err.message, 'error');
      setError(err.message);
    } finally {
      setOperationLoading(prev => ({ ...prev, save: false }));
    }
  };

  // SEC-041: generateApiKey(), revokeApiKey() REMOVED - consolidated to Settings tab

  // Load audit log
  // SEC-046: Fixed to use `entries` field from backend response
  const loadAuditLog = async () => {
    try {
      const data = await apiCall('/audit-log?limit=100');
      // SEC-046: Backend returns both `entries` and `logs` for compatibility
      setAuditLog(data.entries || data.logs || []);
    } catch (err) {
      showToast('Failed to load audit log', 'error');
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

      {/* SEC-046 Phase 3: Usage Alerts Banner */}
      {(usageAlerts.critical.length > 0 || usageAlerts.warnings.length > 0) && (
        <div className="usage-alerts-section">
          {usageAlerts.critical.map((alert, i) => (
            <div key={`critical-${i}`} className="usage-alert critical">
              <span className="alert-icon">🚨</span>
              <div className="alert-content">
                <strong>Critical: {alert.resource}</strong>
                <span>{alert.current} / {alert.limit} ({alert.percentage}%)</span>
              </div>
              <span className="alert-message">{alert.message}</span>
            </div>
          ))}
          {usageAlerts.warnings.map((alert, i) => (
            <div key={`warning-${i}`} className="usage-alert warning">
              <span className="alert-icon">⚠️</span>
              <div className="alert-content">
                <strong>Warning: {alert.resource}</strong>
                <span>{alert.current} / {alert.limit} ({alert.percentage}%)</span>
              </div>
              <span className="alert-message">{alert.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* SEC-046 Phase 3: Real-time Status Indicator */}
      {realtimeStatus && (
        <div className="realtime-status-bar">
          <div className="status-indicator">
            <span className={`status-dot ${realtimeStatus.system_status}`} />
            <span>System: {realtimeStatus.system_status}</span>
          </div>
          <div className="status-metrics">
            <span>Active Users: {realtimeStatus.active_users || 0}</span>
            <span>|</span>
            <span>Pending Actions: {realtimeStatus.pending_actions || 0}</span>
            <span>|</span>
            <span>API Latency: {realtimeStatus.api_latency_ms || 0}ms</span>
          </div>
          {lastStatusUpdate && (
            <span className="last-update">
              Updated: {lastStatusUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <div className="stat-value">{users.length}</div>
            <div className="stat-label">Total Users</div>
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
          onClick={saveOrganizationSettings}
          disabled={operationLoading.save}
        >
          {operationLoading.save ? 'Saving...' : 'Save Changes'}
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

      {/* SEC-046 Phase 3: Bulk Actions Bar */}
      {selectedUsers.size > 0 && (
        <div className="bulk-actions-bar">
          <span className="bulk-count">{selectedUsers.size} user{selectedUsers.size > 1 ? 's' : ''} selected</span>
          <div className="bulk-buttons">
            <button className="btn-bulk" onClick={() => setShowBulkActionModal('suspend')}>
              ⏸️ Suspend
            </button>
            <button className="btn-bulk" onClick={() => setShowBulkActionModal('reactivate')}>
              ✅ Reactivate
            </button>
            <button className="btn-bulk" onClick={() => setShowBulkActionModal('role_change')}>
              👤 Change Role
            </button>
            <button className="btn-bulk danger" onClick={() => setShowBulkActionModal('delete')}>
              🗑️ Delete
            </button>
            <button className="btn-bulk-clear" onClick={() => setSelectedUsers(new Set())}>
              Clear Selection
            </button>
          </div>
        </div>
      )}

      <div className="users-table">
        <table>
          <thead>
            <tr>
              {/* SEC-046 Phase 3: Select All Checkbox */}
              <th className="checkbox-column">
                <input
                  type="checkbox"
                  checked={selectedUsers.size > 0 && selectedUsers.size === users.filter(u => !u.is_owner).length}
                  onChange={toggleSelectAll}
                  title="Select all"
                />
              </th>
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
              <tr key={user.id} className={selectedUsers.has(user.id) ? 'selected' : ''}>
                {/* SEC-046 Phase 3: Row Checkbox */}
                <td className="checkbox-column">
                  {!user.is_owner && (
                    <input
                      type="checkbox"
                      checked={selectedUsers.has(user.id)}
                      onChange={() => toggleUserSelection(user.id)}
                    />
                  )}
                </td>
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
                    <div className="user-actions-cell">
                      <button
                        className="btn-actions"
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowUserActionsMenu(showUserActionsMenu === user.id ? null : user.id);
                        }}
                      >
                        ⋮
                      </button>
                      {showUserActionsMenu === user.id && (
                        <div className="actions-dropdown">
                          <button onClick={() => { openEditProfileModal(user); setShowUserActionsMenu(null); }}>
                            ✏️ Edit Profile
                          </button>
                          <button onClick={() => { openActivityModal(user); setShowUserActionsMenu(null); }}>
                            📋 View Activity
                          </button>
                          <button onClick={() => { setShowSuspendModal(user); setShowUserActionsMenu(null); }}>
                            {user.status === 'suspended' ? '✅ Reactivate' : '⏸️ Suspend'}
                          </button>
                          <button onClick={() => { setShowResetPasswordModal(user); setShowUserActionsMenu(null); }}>
                            🔑 Reset Password
                          </button>
                          <button onClick={() => { setShowForceLogoutModal(user); setShowUserActionsMenu(null); }}>
                            🚪 Force Logout
                          </button>
                          <div className="dropdown-divider" />
                          <button className="danger" onClick={() => { setShowDeleteConfirm(user); setShowUserActionsMenu(null); }}>
                            🗑️ Remove User
                          </button>
                        </div>
                      )}
                    </div>
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
                  value={inviteForm.first_name}
                  onChange={(e) => setInviteForm({ ...inviteForm, first_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input
                  type="text"
                  value={inviteForm.last_name}
                  onChange={(e) => setInviteForm({ ...inviteForm, last_name: e.target.value })}
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
              <button className="btn-secondary" onClick={() => setShowInviteModal(false)} disabled={operationLoading.invite}>Cancel</button>
              <button className="btn-primary" onClick={inviteUser} disabled={operationLoading.invite}>
                {operationLoading.invite ? 'Sending...' : 'Send Invitation'}
              </button>
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
              <button className="btn-secondary" onClick={() => setShowDeleteConfirm(null)} disabled={operationLoading.delete}>Cancel</button>
              <button className="btn-danger" onClick={() => removeUser(showDeleteConfirm.id)} disabled={operationLoading.delete}>
                {operationLoading.delete ? 'Removing...' : 'Remove User'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SEC-046 Phase 2: Suspend/Reactivate Modal */}
      {showSuspendModal && (
        <div className="modal-overlay" onClick={() => setShowSuspendModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{showSuspendModal.status === 'suspended' ? 'Reactivate User' : 'Suspend User'}</h3>
            <p>
              {showSuspendModal.status === 'suspended'
                ? <>Are you sure you want to reactivate <strong>{showSuspendModal.email}</strong>? They will regain access to the platform.</>
                : <>Are you sure you want to suspend <strong>{showSuspendModal.email}</strong>? They will be unable to access the platform.</>
              }
            </p>
            <div className="form-group">
              <label>Reason (optional)</label>
              <textarea
                value={suspendReason}
                onChange={(e) => setSuspendReason(e.target.value)}
                placeholder={showSuspendModal.status === 'suspended' ? 'Reason for reactivation...' : 'Reason for suspension...'}
                rows={3}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => { setShowSuspendModal(null); setSuspendReason(''); }} disabled={operationLoading.suspend}>Cancel</button>
              <button
                className={showSuspendModal.status === 'suspended' ? 'btn-primary' : 'btn-warning'}
                onClick={() => suspendUser(showSuspendModal.id, showSuspendModal.status !== 'suspended')}
                disabled={operationLoading.suspend}
              >
                {operationLoading.suspend ? 'Processing...' : (showSuspendModal.status === 'suspended' ? 'Reactivate' : 'Suspend')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SEC-046 Phase 2: Edit Profile Modal */}
      {showEditProfileModal && (
        <div className="modal-overlay" onClick={() => setShowEditProfileModal(null)}>
          <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
            <h3>Edit User Profile</h3>
            <p className="modal-subtitle">Editing: {showEditProfileModal.email}</p>
            <div className="form-row">
              <div className="form-group">
                <label>First Name</label>
                <input
                  type="text"
                  value={editProfileForm.first_name}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, first_name: e.target.value })}
                  placeholder="First name"
                />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input
                  type="text"
                  value={editProfileForm.last_name}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, last_name: e.target.value })}
                  placeholder="Last name"
                />
              </div>
            </div>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                value={editProfileForm.email}
                onChange={(e) => setEditProfileForm({ ...editProfileForm, email: e.target.value })}
                placeholder="email@company.com"
              />
              <span className="help-text">Changing email will require re-verification</span>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={editProfileForm.phone}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, phone: e.target.value })}
                  placeholder="+1 (555) 123-4567"
                />
              </div>
              <div className="form-group">
                <label>Department</label>
                <input
                  type="text"
                  value={editProfileForm.department}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, department: e.target.value })}
                  placeholder="Engineering, Sales, etc."
                />
              </div>
            </div>
            <div className="form-group">
              <label>Job Title</label>
              <input
                type="text"
                value={editProfileForm.job_title}
                onChange={(e) => setEditProfileForm({ ...editProfileForm, job_title: e.target.value })}
                placeholder="Software Engineer, Manager, etc."
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowEditProfileModal(null)} disabled={operationLoading.editProfile}>Cancel</button>
              <button className="btn-primary" onClick={() => editUserProfile(showEditProfileModal.id)} disabled={operationLoading.editProfile}>
                {operationLoading.editProfile ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SEC-046 Phase 2: Reset Password Modal */}
      {showResetPasswordModal && (
        <div className="modal-overlay" onClick={() => setShowResetPasswordModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Reset User Password</h3>
            <p>
              Send a password reset email to <strong>{showResetPasswordModal.email}</strong>?
            </p>
            <div className="info-box">
              <span className="info-icon">ℹ️</span>
              <div>
                <strong>What happens:</strong>
                <ul>
                  <li>User will receive a password reset email</li>
                  <li>Current password will remain valid until reset</li>
                  <li>Reset link expires in 24 hours</li>
                </ul>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowResetPasswordModal(null)} disabled={operationLoading.resetPassword}>Cancel</button>
              <button className="btn-primary" onClick={() => resetUserPassword(showResetPasswordModal.id)} disabled={operationLoading.resetPassword}>
                {operationLoading.resetPassword ? 'Sending...' : 'Send Reset Email'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SEC-046 Phase 2: Force Logout Modal */}
      {showForceLogoutModal && (
        <div className="modal-overlay" onClick={() => setShowForceLogoutModal(null)}>
          <div className="modal modal-warning" onClick={(e) => e.stopPropagation()}>
            <h3>Force Logout User</h3>
            <p>
              This will immediately log out <strong>{showForceLogoutModal.email}</strong> from all devices and sessions.
            </p>
            <div className="warning-box">
              <span className="warning-icon">⚠️</span>
              <div>
                <strong>This action will:</strong>
                <ul>
                  <li>Terminate all active sessions</li>
                  <li>Revoke all access tokens</li>
                  <li>Require user to log in again</li>
                </ul>
              </div>
            </div>
            <div className="form-group">
              <label>Reason (optional)</label>
              <textarea
                value={forceLogoutReason}
                onChange={(e) => setForceLogoutReason(e.target.value)}
                placeholder="Security concern, policy violation, etc."
                rows={2}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => { setShowForceLogoutModal(null); setForceLogoutReason(''); }} disabled={operationLoading.forceLogout}>Cancel</button>
              <button className="btn-warning" onClick={() => forceLogoutUser(showForceLogoutModal.id)} disabled={operationLoading.forceLogout}>
                {operationLoading.forceLogout ? 'Logging out...' : 'Force Logout'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SEC-046 Phase 2: User Activity Modal */}
      {showActivityModal && (
        <div className="modal-overlay" onClick={() => setShowActivityModal(null)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>User Activity Log</h3>
              <button className="btn-close" onClick={() => setShowActivityModal(null)}>×</button>
            </div>
            <p className="modal-subtitle">
              Activity for: <strong>{showActivityModal.first_name} {showActivityModal.last_name}</strong> ({showActivityModal.email})
            </p>
            {activityLoading ? (
              <div className="activity-loading">
                <div className="loading-spinner small" />
                <span>Loading activity...</span>
              </div>
            ) : userActivityData.length === 0 ? (
              <div className="no-activity">
                <span>📭</span>
                <p>No activity recorded for this user</p>
              </div>
            ) : (
              <div className="activity-list">
                <table className="activity-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Action</th>
                      <th>Details</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userActivityData.map((activity, i) => (
                      <tr key={i}>
                        <td className="timestamp">{new Date(activity.timestamp).toLocaleString()}</td>
                        <td>
                          <span className={`action-badge action-${activity.action_type?.split('.')[0] || 'default'}`}>
                            {activity.action_display || activity.action_type}
                          </span>
                        </td>
                        <td className="details">{activity.details || '-'}</td>
                        <td><code>{activity.ip_address || '-'}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="modal-footer">
              <span className="activity-count">{userActivityData.length} activities shown</span>
              <button className="btn-secondary" onClick={() => loadUserActivity(showActivityModal.id)}>
                Refresh
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SEC-046 Phase 3: Bulk Action Modal */}
      {showBulkActionModal && (
        <div className="modal-overlay" onClick={() => setShowBulkActionModal(null)}>
          <div className={`modal ${showBulkActionModal === 'delete' ? 'modal-danger' : ''}`} onClick={(e) => e.stopPropagation()}>
            <h3>
              {showBulkActionModal === 'suspend' && 'Suspend Users'}
              {showBulkActionModal === 'reactivate' && 'Reactivate Users'}
              {showBulkActionModal === 'delete' && 'Delete Users'}
              {showBulkActionModal === 'role_change' && 'Change User Roles'}
            </h3>
            <p>
              This action will affect <strong>{selectedUsers.size} user{selectedUsers.size > 1 ? 's' : ''}</strong>.
            </p>

            {showBulkActionModal === 'delete' && (
              <div className="warning-box">
                <span className="warning-icon">⚠️</span>
                <div>
                  <strong>Warning: This action cannot be undone!</strong>
                  <p>All selected users will be permanently removed from the organization.</p>
                </div>
              </div>
            )}

            {showBulkActionModal === 'role_change' && (
              <div className="form-group">
                <label>New Role</label>
                <select value={bulkRoleChange} onChange={(e) => setBulkRoleChange(e.target.value)}>
                  {USER_ROLES.map(role => (
                    <option key={role.value} value={role.value}>{role.label}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-group">
              <label>Reason (for audit log)</label>
              <textarea
                value={bulkReason}
                onChange={(e) => setBulkReason(e.target.value)}
                placeholder="Enter reason for this bulk action..."
                rows={2}
              />
            </div>

            <div className="affected-users">
              <strong>Affected Users:</strong>
              <div className="user-chips">
                {users.filter(u => selectedUsers.has(u.id)).slice(0, 5).map(u => (
                  <span key={u.id} className="user-chip">{u.email}</span>
                ))}
                {selectedUsers.size > 5 && (
                  <span className="user-chip more">+{selectedUsers.size - 5} more</span>
                )}
              </div>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => { setShowBulkActionModal(null); setBulkReason(''); }} disabled={bulkOperationLoading}>
                Cancel
              </button>
              <button
                className={showBulkActionModal === 'delete' ? 'btn-danger' : 'btn-primary'}
                onClick={executeBulkOperation}
                disabled={bulkOperationLoading}
              >
                {bulkOperationLoading ? 'Processing...' : `Confirm ${showBulkActionModal === 'role_change' ? 'Role Change' : showBulkActionModal}`}
              </button>
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
        <select value={chartPeriod} onChange={(e) => setChartPeriod(parseInt(e.target.value))}>
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

      {/* SEC-046 Phase 3: Time Series Charts */}
      {chartData && (
        <div className="charts-section">
          <h3>Trends Over Time</h3>
          <div className="charts-grid">
            {/* API Calls Chart */}
            <div className="chart-card">
              <h4>API Calls</h4>
              <div className="simple-chart">
                {chartData.api_calls?.time_series?.slice(-14).map((point, i, arr) => {
                  const max = Math.max(...arr.map(p => p.value), 1);
                  const height = (point.value / max) * 100;
                  return (
                    <div key={i} className="chart-bar-container" title={`${point.date}: ${point.value.toLocaleString()}`}>
                      <div className="chart-bar" style={{ height: `${height}%` }} />
                      <span className="chart-label">{point.date?.slice(-5)}</span>
                    </div>
                  );
                })}
              </div>
              <div className="chart-summary">
                <span>Total: {chartData.api_calls?.total?.toLocaleString() || 0}</span>
                <span className={`trend ${chartData.api_calls?.trend >= 0 ? 'positive' : 'negative'}`}>
                  {chartData.api_calls?.trend >= 0 ? '+' : ''}{chartData.api_calls?.trend || 0}%
                </span>
              </div>
            </div>

            {/* User Activity Chart */}
            <div className="chart-card">
              <h4>Active Users</h4>
              <div className="simple-chart">
                {chartData.user_activity?.time_series?.slice(-14).map((point, i, arr) => {
                  const max = Math.max(...arr.map(p => p.value), 1);
                  const height = (point.value / max) * 100;
                  return (
                    <div key={i} className="chart-bar-container" title={`${point.date}: ${point.value}`}>
                      <div className="chart-bar user" style={{ height: `${height}%` }} />
                      <span className="chart-label">{point.date?.slice(-5)}</span>
                    </div>
                  );
                })}
              </div>
              <div className="chart-summary">
                <span>Avg: {chartData.user_activity?.average || 0}</span>
                <span className={`trend ${chartData.user_activity?.trend >= 0 ? 'positive' : 'negative'}`}>
                  {chartData.user_activity?.trend >= 0 ? '+' : ''}{chartData.user_activity?.trend || 0}%
                </span>
              </div>
            </div>

            {/* Alerts Chart */}
            <div className="chart-card">
              <h4>Alerts Processed</h4>
              <div className="simple-chart">
                {chartData.alerts?.time_series?.slice(-14).map((point, i, arr) => {
                  const max = Math.max(...arr.map(p => p.value), 1);
                  const height = (point.value / max) * 100;
                  return (
                    <div key={i} className="chart-bar-container" title={`${point.date}: ${point.value}`}>
                      <div className="chart-bar alerts" style={{ height: `${height}%` }} />
                      <span className="chart-label">{point.date?.slice(-5)}</span>
                    </div>
                  );
                })}
              </div>
              <div className="chart-summary">
                <span>Total: {chartData.alerts?.total?.toLocaleString() || 0}</span>
                <span className={`trend ${chartData.alerts?.trend >= 0 ? 'positive' : 'negative'}`}>
                  {chartData.alerts?.trend >= 0 ? '+' : ''}{chartData.alerts?.trend || 0}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

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

  // SEC-041: renderApiKeys() REMOVED (146 lines) - consolidated to Settings tab
  // API Key management now lives in EnterpriseSettings.jsx → ApiKeyManagement.jsx
  // Features: expiration options, usage stats, descriptions, SHA-256 hashing

  const renderAuditLog = () => (
    <div className="admin-audit">
      <div className="section-header">
        <h2>Audit Log</h2>
        <div className="section-header-actions">
          {/* SEC-046 Phase 3: Export Buttons */}
          <div className="export-buttons">
            <button
              className="btn-export"
              onClick={() => exportAuditLog('csv')}
              disabled={exportLoading}
              title="Export as CSV"
            >
              📊 CSV
            </button>
            <button
              className="btn-export"
              onClick={() => exportAuditLog('json')}
              disabled={exportLoading}
              title="Export as JSON"
            >
              📄 JSON
            </button>
          </div>
          <button className="btn-secondary" onClick={loadAuditLog}>Refresh</button>
        </div>
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
      // SEC-041: API Keys consolidated to Settings tab
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
      {/* SEC-046: Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

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

        /* SEC-046 Phase 2: User Actions Dropdown */
        .user-actions-cell {
          position: relative;
        }

        .btn-actions {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          padding: 6px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 18px;
          color: #888;
          transition: all 0.2s;
        }

        .btn-actions:hover {
          background: rgba(255, 255, 255, 0.2);
          color: #e0e0e0;
        }

        .actions-dropdown {
          position: absolute;
          top: 100%;
          right: 0;
          background: #1a1a2e;
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 8px;
          padding: 8px 0;
          min-width: 180px;
          z-index: 100;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }

        .actions-dropdown button {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 10px 16px;
          background: none;
          border: none;
          color: #e0e0e0;
          font-size: 14px;
          cursor: pointer;
          text-align: left;
          transition: background 0.2s;
        }

        .actions-dropdown button:hover {
          background: rgba(0, 212, 255, 0.1);
        }

        .actions-dropdown button.danger {
          color: #ff5252;
        }

        .actions-dropdown button.danger:hover {
          background: rgba(255, 82, 82, 0.1);
        }

        .dropdown-divider {
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
          margin: 8px 0;
        }

        /* SEC-046 Phase 2: Modal Variants */
        .modal-wide {
          max-width: 560px;
        }

        .modal-large {
          max-width: 720px;
          max-height: 80vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .modal-warning {
          border-color: rgba(255, 193, 7, 0.3);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .modal-header h3 {
          margin: 0;
        }

        .btn-close {
          background: none;
          border: none;
          color: #888;
          font-size: 24px;
          cursor: pointer;
          padding: 4px 8px;
        }

        .btn-close:hover {
          color: #e0e0e0;
        }

        .modal-subtitle {
          color: #888;
          font-size: 14px;
          margin-bottom: 20px;
        }

        .modal-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 20px;
          padding-top: 16px;
          border-top: 1px solid #1a1a2e;
        }

        .activity-count {
          color: #666;
          font-size: 13px;
        }

        /* SEC-046 Phase 2: Warning Button */
        .btn-warning {
          background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
          color: #000;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-warning:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
        }

        .btn-warning:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        /* SEC-046 Phase 2: Info/Warning Boxes */
        .info-box, .warning-box {
          display: flex;
          gap: 12px;
          padding: 16px;
          border-radius: 8px;
          margin: 16px 0;
        }

        .info-box {
          background: rgba(33, 150, 243, 0.1);
          border: 1px solid rgba(33, 150, 243, 0.2);
        }

        .warning-box {
          background: rgba(255, 152, 0, 0.1);
          border: 1px solid rgba(255, 152, 0, 0.2);
        }

        .info-icon, .warning-icon {
          font-size: 20px;
        }

        .info-box ul, .warning-box ul {
          margin: 8px 0 0 0;
          padding-left: 20px;
        }

        .info-box li, .warning-box li {
          font-size: 13px;
          color: #888;
          margin: 4px 0;
        }

        /* SEC-046 Phase 2: Textarea */
        .form-group textarea {
          width: 100%;
          padding: 12px 16px;
          background: #0f0f1a;
          border: 1px solid #2a2a3e;
          border-radius: 8px;
          color: #e0e0e0;
          font-size: 14px;
          font-family: inherit;
          resize: vertical;
        }

        .form-group textarea:focus {
          outline: none;
          border-color: #00d4ff;
        }

        /* SEC-046 Phase 2: Activity Modal */
        .activity-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          padding: 40px 0;
          color: #888;
        }

        .loading-spinner.small {
          width: 32px;
          height: 32px;
        }

        .no-activity {
          text-align: center;
          padding: 40px 0;
          color: #666;
        }

        .no-activity span {
          font-size: 48px;
        }

        .no-activity p {
          margin-top: 12px;
        }

        .activity-list {
          max-height: 400px;
          overflow-y: auto;
        }

        .activity-table {
          width: 100%;
        }

        .activity-table td.timestamp {
          white-space: nowrap;
          font-size: 12px;
          color: #888;
        }

        .activity-table td.details {
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-size: 13px;
          color: #666;
        }

        .action-badge {
          display: inline-block;
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .action-login, .action-auth {
          background: rgba(76, 175, 80, 0.1);
          color: #4caf50;
        }

        .action-logout {
          background: rgba(255, 152, 0, 0.1);
          color: #ff9800;
        }

        .action-update, .action-edit {
          background: rgba(33, 150, 243, 0.1);
          color: #2196f3;
        }

        .action-delete, .action-remove {
          background: rgba(244, 67, 54, 0.1);
          color: #f44336;
        }

        .action-create, .action-add {
          background: rgba(0, 212, 255, 0.1);
          color: #00d4ff;
        }

        .action-default {
          background: rgba(255, 255, 255, 0.1);
          color: #888;
        }

        /* Status badge for suspended */
        .status-suspended {
          background: rgba(255, 152, 0, 0.1);
          color: #ff9800;
        }

        /* ===========================================
           SEC-046 Phase 3: Enterprise Features Styles
           =========================================== */

        /* Usage Alerts Section */
        .usage-alerts-section {
          margin-bottom: 24px;
        }

        .usage-alert {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px 20px;
          border-radius: 8px;
          margin-bottom: 12px;
        }

        .usage-alert.critical {
          background: rgba(244, 67, 54, 0.1);
          border: 1px solid rgba(244, 67, 54, 0.3);
        }

        .usage-alert.warning {
          background: rgba(255, 152, 0, 0.1);
          border: 1px solid rgba(255, 152, 0, 0.3);
        }

        .usage-alert .alert-icon {
          font-size: 24px;
        }

        .usage-alert .alert-content {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .usage-alert .alert-content strong {
          color: #fff;
        }

        .usage-alert .alert-content span {
          font-size: 13px;
          color: #888;
        }

        .usage-alert .alert-message {
          flex: 1;
          text-align: right;
          font-size: 14px;
          color: #e0e0e0;
        }

        /* Real-time Status Bar */
        .realtime-status-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: rgba(0, 212, 255, 0.05);
          border: 1px solid rgba(0, 212, 255, 0.1);
          border-radius: 8px;
          padding: 12px 20px;
          margin-bottom: 24px;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          animation: pulse 2s ease-in-out infinite;
        }

        .status-dot.healthy {
          background: #4caf50;
        }

        .status-dot.degraded {
          background: #ff9800;
        }

        .status-dot.down {
          background: #f44336;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .status-metrics {
          display: flex;
          gap: 16px;
          font-size: 13px;
          color: #888;
        }

        .last-update {
          font-size: 12px;
          color: #666;
        }

        /* Bulk Actions Bar */
        .bulk-actions-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 204, 0.1) 100%);
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 8px;
          padding: 12px 20px;
          margin-bottom: 16px;
        }

        .bulk-count {
          font-weight: 600;
          color: #00d4ff;
        }

        .bulk-buttons {
          display: flex;
          gap: 8px;
        }

        .btn-bulk {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: #e0e0e0;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-bulk:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .btn-bulk.danger {
          color: #ff5252;
          border-color: rgba(255, 82, 82, 0.3);
        }

        .btn-bulk.danger:hover {
          background: rgba(255, 82, 82, 0.1);
        }

        .btn-bulk-clear {
          background: none;
          border: none;
          color: #888;
          padding: 6px 12px;
          cursor: pointer;
          font-size: 13px;
        }

        .btn-bulk-clear:hover {
          color: #e0e0e0;
        }

        /* Checkbox Column */
        .checkbox-column {
          width: 40px;
          text-align: center;
        }

        .checkbox-column input[type="checkbox"] {
          width: 18px;
          height: 18px;
          accent-color: #00d4ff;
          cursor: pointer;
        }

        tr.selected {
          background: rgba(0, 212, 255, 0.05);
        }

        /* Affected Users in Modal */
        .affected-users {
          margin-top: 16px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
        }

        .user-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 8px;
        }

        .user-chip {
          background: rgba(0, 212, 255, 0.1);
          border: 1px solid rgba(0, 212, 255, 0.2);
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          color: #00d4ff;
        }

        .user-chip.more {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.2);
          color: #888;
        }

        /* Charts Section */
        .charts-section {
          margin-bottom: 32px;
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
        }

        .chart-card {
          background: #0f0f1a;
          border: 1px solid #1a1a2e;
          border-radius: 12px;
          padding: 20px;
        }

        .chart-card h4 {
          margin-bottom: 16px;
        }

        .simple-chart {
          display: flex;
          align-items: flex-end;
          gap: 4px;
          height: 120px;
          padding: 0 8px;
        }

        .chart-bar-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          height: 100%;
          justify-content: flex-end;
        }

        .chart-bar {
          width: 100%;
          max-width: 24px;
          background: linear-gradient(180deg, #00d4ff 0%, #0099cc 100%);
          border-radius: 4px 4px 0 0;
          transition: height 0.3s ease;
          min-height: 4px;
        }

        .chart-bar.user {
          background: linear-gradient(180deg, #9c27b0 0%, #7b1fa2 100%);
        }

        .chart-bar.alerts {
          background: linear-gradient(180deg, #ff9800 0%, #f57c00 100%);
        }

        .chart-label {
          font-size: 9px;
          color: #666;
          margin-top: 4px;
          transform: rotate(-45deg);
          white-space: nowrap;
        }

        .chart-summary {
          display: flex;
          justify-content: space-between;
          margin-top: 16px;
          padding-top: 12px;
          border-top: 1px solid #1a1a2e;
          font-size: 13px;
        }

        .chart-summary .trend {
          font-weight: 600;
        }

        .chart-summary .trend.positive {
          color: #4caf50;
        }

        .chart-summary .trend.negative {
          color: #f44336;
        }

        /* Export Buttons */
        .section-header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .export-buttons {
          display: flex;
          gap: 8px;
        }

        .btn-export {
          background: rgba(76, 175, 80, 0.1);
          border: 1px solid rgba(76, 175, 80, 0.3);
          color: #4caf50;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-export:hover {
          background: rgba(76, 175, 80, 0.2);
        }

        .btn-export:disabled {
          opacity: 0.5;
          cursor: not-allowed;
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

          .modal-large {
            max-width: 95%;
            max-height: 90vh;
          }

          .actions-dropdown {
            position: fixed;
            top: 50%;
            left: 50%;
            right: auto;
            transform: translate(-50%, -50%);
            min-width: 280px;
          }

          /* SEC-046 Phase 3: Responsive */
          .bulk-actions-bar {
            flex-direction: column;
            gap: 12px;
          }

          .bulk-buttons {
            flex-wrap: wrap;
            justify-content: center;
          }

          .realtime-status-bar {
            flex-direction: column;
            gap: 12px;
            text-align: center;
          }

          .status-metrics {
            flex-wrap: wrap;
            justify-content: center;
          }

          .usage-alert {
            flex-wrap: wrap;
          }

          .charts-grid {
            grid-template-columns: 1fr;
          }

          .section-header-actions {
            flex-direction: column;
            gap: 8px;
          }

          .export-buttons {
            width: 100%;
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
};

export default AdminConsole;
