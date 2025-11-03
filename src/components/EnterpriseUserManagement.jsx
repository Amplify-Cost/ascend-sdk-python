import React, { useState, useEffect } from "react";

const EnterpriseUserManagement = ({ getAuthHeaders, user }) => {
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Modal states
  const [showUserModal, setShowUserModal] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingRole, setEditingRole] = useState(null);
  const [newUser, setNewUser] = useState({
    email: "",
    first_name: "",
    last_name: "",
    department: "",
    role: "user",
    access_level: "Level 1 - Basic User",
    mfa_enabled: false
  });
  const [newRole, setNewRole] = useState({
    name: "",
    description: "",
    level: 1,
    risk_level: "Medium",
    permissions: {
      dashboard: false,
      analytics: false,
      alerts: false,
      rules: false,
      authorization: false,
      users: false,
      audit: false
    }
  });

  // Filter states
  const [userFilter, setUserFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [auditFilter, setAuditFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");

  const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // ============================================================================
  // DATA FETCHING
  // ============================================================================

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadUsers(),
        loadRoles(),
        loadAuditLogs(),
        loadAnalytics()
      ]);
    } catch (error) {
      console.error("❌ Error loading data:", error);
      setError("Failed to load enterprise data");
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      console.log("🔄 Loading users...");
      const response = await fetch(`${BASE_URL}/api/enterprise-users/users`, {
        credentials: "include",
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ Users loaded:", data);
        setUsers(data.users || []);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error loading users:", error);
      // Fallback to demo data on error
      setUsers([]);
    }
  };

  const loadRoles = async () => {
    try {
      console.log("🔄 Loading roles...");
      const response = await fetch(`${BASE_URL}/api/enterprise-users/roles`, {
        credentials: "include",
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ Roles loaded:", data);
        setRoles(data.roles || []);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error loading roles:", error);
      setRoles([]);
    }
  };

  const loadAuditLogs = async () => {
    try {
      console.log("🔄 Loading audit logs...");
      const response = await fetch(`${BASE_URL}/api/enterprise-users/audit-logs?limit=50`, {
        credentials: "include",
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ Audit logs loaded:", data);
        setAuditLogs(data.logs || []);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error loading audit logs:", error);
      setAuditLogs([]);
    }
  };

  const loadAnalytics = async () => {
    try {
      console.log("🔄 Loading analytics...");
      const response = await fetch(`${BASE_URL}/api/enterprise-users/analytics`, {
        credentials: "include",
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ Analytics loaded:", data);
        setAnalytics(data);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error loading analytics:", error);
      setAnalytics(null);
    }
  };

  // ============================================================================
  // USER MANAGEMENT ACTIONS
  // ============================================================================

  const handleCreateUser = async () => {
    try {
      console.log("🔄 Creating user:", newUser);
      const response = await fetch(`${BASE_URL}/api/enterprise-users/users`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": "exempt"
        },
        credentials: "include",
  body: JSON.stringify(newUser)
      });

      if (response.ok) {
        const result = await response.json();
        console.log("✅ User created:", result);
        alert(`✅ User created successfully!\nTemporary Password: ${result.temporary_password}\n\nPlease share this password securely with the new user.`);
        setShowUserModal(false);
        setNewUser({
          email: "",
          first_name: "",
          last_name: "",
          department: "",
          role: "user",
          access_level: "Level 1 - Basic User",
          mfa_enabled: false
        });
        await loadUsers(); // Reload users
        await loadAnalytics(); // Reload analytics
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error creating user:", error);
      alert(`❌ Failed to create user: ${error.message}`);
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;

    try {
      console.log("🔄 Updating user:", editingUser);
      const response = await fetch(`${BASE_URL}/api/enterprise-users/users/${editingUser.id}`, {
        credentials: "include",
        method: "PUT",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          first_name: editingUser.first_name,
          last_name: editingUser.last_name,
          department: editingUser.department,
          role: editingUser.role,
          access_level: editingUser.access_level,
          status: editingUser.status,
          mfa_enabled: editingUser.mfa_enabled
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log("✅ User updated:", result);
        alert("✅ User updated successfully!");
        setEditingUser(null);
        await loadUsers(); // Reload users
        await loadAnalytics(); // Reload analytics
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error updating user:", error);
      alert(`❌ Failed to update user: ${error.message}`);
    }
  };

  const handleDeactivateUser = async (userId, userEmail) => {
    if (!confirm(`Are you sure you want to deactivate ${userEmail}?\n\nThis will immediately revoke all access.`)) {
      return;
    }

    try {
      console.log("🔄 Deactivating user:", userId);
      const response = await fetch(`${BASE_URL}/api/enterprise-users/users/${userId}`, {
        credentials: "include",
        method: "DELETE",
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const result = await response.json();
        console.log("✅ User deactivated:", result);
        alert("✅ User deactivated successfully!");
        await loadUsers(); // Reload users
        await loadAnalytics(); // Reload analytics
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error deactivating user:", error);
      alert(`❌ Failed to deactivate user: ${error.message}`);
    }
  };

  const handleCreateRole = async () => {
    try {
      console.log("🔄 Creating role:", newRole);
      const response = await fetch(`${BASE_URL}/api/enterprise-users/roles`, {
        credentials: "include",
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": "exempt"
        },
        body: JSON.stringify(newRole)
      });

      if (response.ok) {
        const result = await response.json();
        console.log("✅ Role created:", result);
        alert("✅ Role created successfully!");
        setShowRoleModal(false);
        setNewRole({
          name: "",
          description: "",
          level: 1,
          risk_level: "Medium",
          permissions: {
            dashboard: false,
            analytics: false,
            alerts: false,
            rules: false,
            authorization: false,
            users: false,
            audit: false
          }
        });
        await loadRoles(); // Reload roles
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error creating role:", error);
      alert(`❌ Failed to create role: ${error.message}`);
    }
  };

  const handleUpdateRole = async () => {
    if (!editingRole) return;

    try {
      console.log("🔄 Updating role:", editingRole);
      const response = await fetch(`${BASE_URL}/api/enterprise-users/roles/${editingRole.id}`, {
        credentials: "include",
        method: "PUT",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: editingRole.name,
          description: editingRole.description,
          permissions: editingRole.permissions,
          level: editingRole.level,
          risk_level: editingRole.risk_level
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log("✅ Role updated:", result);
        alert("✅ Role updated successfully!");
        setEditingRole(null);
        await loadRoles(); // Reload roles
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("❌ Error updating role:", error);
      alert(`❌ Failed to update role: ${error.message}`);
    }
  };

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================

  const getRiskBadgeColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case "critical": return "bg-red-100 text-red-800 border-red-200";
      case "high": return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low": return "bg-green-100 text-green-800 border-green-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusBadgeColor = (status) => {
    switch (status?.toLowerCase()) {
      case "active": return "bg-green-100 text-green-800 border-green-200";
      case "inactive": return "bg-red-100 text-red-800 border-red-200";
      case "pending": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesFilter = user.email?.toLowerCase().includes(userFilter.toLowerCase()) ||
                         `${user.first_name} ${user.last_name}`.toLowerCase().includes(userFilter.toLowerCase());
    const matchesStatus = statusFilter === "all" || user.status?.toLowerCase() === statusFilter.toLowerCase();
    return matchesFilter && matchesStatus;
  });

  const filteredAuditLogs = auditLogs.filter(log => {
    const matchesFilter = log.user_email?.toLowerCase().includes(auditFilter.toLowerCase()) ||
                         log.action?.toLowerCase().includes(auditFilter.toLowerCase());
    const matchesRisk = riskFilter === "all" || log.risk_level?.toLowerCase() === riskFilter.toLowerCase();
    return matchesFilter && matchesRisk;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Enterprise User Management...</p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER COMPONENTS
  // ============================================================================

  const renderUsersTab = () => (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <span className="text-2xl">👥</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">{analytics?.user_statistics?.total_users || users.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <span className="text-2xl">✅</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Users</p>
              <p className="text-2xl font-bold text-green-600">{analytics?.user_statistics?.active_users || users.filter(u => u.status === "Active").length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <span className="text-2xl">🔐</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">MFA Enabled</p>
              <p className="text-2xl font-bold text-purple-600">{analytics?.user_statistics?.mfa_enabled || users.filter(u => u.mfa_enabled).length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <span className="text-2xl">⚠️</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Risk</p>
              <p className="text-2xl font-bold text-red-600">{analytics?.user_statistics?.high_risk_users || users.filter(u => u.risk_score > 50).length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
            <input
              type="text"
              placeholder="Search users..."
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <button
            onClick={() => setShowUserModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            + Add User
          </button>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Enterprise Users ({filteredUsers.length})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role & Access</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MFA</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-gray-500">
                    <div className="space-y-2">
                      <span className="text-4xl">👥</span>
                      <p className="text-lg font-medium">No users found</p>
                      <p className="text-sm">Create your first enterprise user to get started.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                          {user.first_name?.[0]}{user.last_name?.[0]}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.first_name} {user.last_name}
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{user.department || "Unassigned"}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{user.role}</div>
                      <div className="text-sm text-gray-500">{user.access_level}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full border ${getStatusBadgeColor(user.status)}`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className={`px-2 py-1 text-xs font-medium rounded border ${getRiskBadgeColor(user.risk_score > 50 ? "High" : user.risk_score > 25 ? "Medium" : "Low")}`}>
                          {user.risk_score || 0}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.mfa_enabled ? (
                        <span className="text-green-600 font-medium">✅ Enabled</span>
                      ) : (
                        <span className="text-red-600 font-medium">❌ Disabled</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : "Never"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setEditingUser(user)}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeactivateUser(user.id, user.email)}
                          className="text-red-600 hover:text-red-900 font-medium"
                          disabled={user.status === "Inactive"}
                        >
                          Deactivate
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderRolesTab = () => (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Role & Permission Matrix</h3>
            <p className="text-sm text-gray-600 mt-1">Manage enterprise roles and granular permissions</p>
          </div>
          <button
            onClick={() => setShowRoleModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
          >
            + Create Role
          </button>
        </div>
      </div>

      {/* Roles Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {roles.length === 0 ? (
          <div className="col-span-2 bg-white rounded-lg border border-gray-200 p-12 text-center">
            <span className="text-4xl mb-4 block">🔐</span>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No roles configured</h3>
            <p className="text-gray-600 mb-4">Create enterprise roles to manage user permissions.</p>
            <button
              onClick={() => setShowRoleModal(true)}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
            >
              Create First Role
            </button>
          </div>
        ) : (
          roles.map((role) => (
            <div key={role.id} className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">{role.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{role.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs font-medium rounded border ${getRiskBadgeColor(role.risk_level)}`}>
                    {role.risk_level}
                  </span>
                  <span className="px-2 py-1 text-xs font-medium rounded border bg-blue-100 text-blue-800 border-blue-200">
                    Level {role.level}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <h5 className="text-sm font-medium text-gray-900">Permissions:</h5>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(role.permissions || {}).map(([key, value]) => (
                    <div key={key} className="flex items-center space-x-2">
                      <span className={`w-4 h-4 rounded border-2 flex items-center justify-center ${value ? 'bg-green-500 border-green-500' : 'bg-gray-200 border-gray-300'}`}>
                        {value && <span className="text-white text-xs">✓</span>}
                      </span>
                      <span className="text-sm text-gray-700 capitalize">{key.replace('_', ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">
                    Created: {role.created_at ? new Date(role.created_at).toLocaleDateString() : "Unknown"}
                  </span>
                  <button
                    onClick={() => setEditingRole(role)}
                    className="text-blue-600 hover:text-blue-900 font-medium text-sm"
                  >
                    Edit Role
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderAuditTab = () => (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Audit Trail</h3>
            <p className="text-sm text-gray-600 mt-1">Complete activity logs for compliance</p>
          </div>
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
            <input
              type="text"
              placeholder="Search audit logs..."
              value={auditFilter}
              onChange={(e) => setAuditFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Risk Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Audit Logs */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Security Audit Log ({filteredAuditLogs.length})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Level</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAuditLogs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                    <div className="space-y-2">
                      <span className="text-4xl">📋</span>
                      <p className="text-lg font-medium">No audit logs found</p>
                      <p className="text-sm">User activity will appear here once actions are performed.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredAuditLogs.map((log, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : "Unknown"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{log.user_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.target}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                      {log.details}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full border ${getRiskBadgeColor(log.risk_level)}`}>
                        {log.risk_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderProvisioningTab = () => (
    <div className="space-y-6">
      {/* Provisioning Overview */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Enterprise Provisioning</h3>
            <p className="text-sm text-gray-600 mt-1">Automated user lifecycle management</p>
          </div>
          <div className="text-sm text-gray-500">
            Last sync: {new Date().toLocaleString()}
          </div>
        </div>

        {/* Integration Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100">Active Directory</p>
                <p className="text-2xl font-bold">Connected</p>
              </div>
              <span className="text-3xl">🔗</span>
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100">LDAP</p>
                <p className="text-2xl font-bold">Synced</p>
              </div>
              <span className="text-3xl">📁</span>
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100">SSO</p>
                <p className="text-2xl font-bold">Active</p>
              </div>
              <span className="text-3xl">🔐</span>
            </div>
          </div>

          <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100">HRIS</p>
                <p className="text-2xl font-bold">Pending</p>
              </div>
              <span className="text-3xl">👥</span>
            </div>
          </div>
        </div>

        {/* Workflow Status */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">Automated Workflows</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium text-gray-900">User Onboarding</p>
                  <p className="text-sm text-gray-600">Automatic role assignment and access provisioning</p>
                </div>
              </div>
              <span className="text-sm font-medium text-green-600">Active</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium text-gray-900">Role Change Management</p>
                  <p className="text-sm text-gray-600">Automatic permission updates on role changes</p>
                </div>
              </div>
              <span className="text-sm font-medium text-green-600">Active</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium text-gray-900">User Offboarding</p>
                  <p className="text-sm text-gray-600">Immediate access revocation and data archival</p>
                </div>
              </div>
              <span className="text-sm font-medium text-green-600">Active</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <div>
                  <p className="font-medium text-gray-900">MFA Enforcement</p>
                  <p className="text-sm text-gray-600">Automatic MFA setup for privileged accounts</p>
                </div>
              </div>
              <span className="text-sm font-medium text-yellow-600">Configuring</span>
            </div>
          </div>
        </div>

        {/* Analytics Overview */}
        {analytics && (
          <div className="mt-8">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Compliance Dashboard</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">SOX Compliance</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics.compliance_metrics?.sox_compliance || 0}%</p>
                  </div>
                  <div className="text-2xl">📊</div>
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">HIPAA Compliance</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics.compliance_metrics?.hipaa_compliance || 0}%</p>
                  </div>
                  <div className="text-2xl">🏥</div>
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">PCI Compliance</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics.compliance_metrics?.pci_compliance || 0}%</p>
                  </div>
                  <div className="text-2xl">💳</div>
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Security Score</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics.security_score || 0}</p>
                  </div>
                  <div className="text-2xl">🛡️</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // ============================================================================
  // MODALS
  // ============================================================================

  const renderUserModal = () => (
    showUserModal && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Create New User</h3>
            <button
              onClick={() => setShowUserModal(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="user@company.com"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <input
                  type="text"
                  value={newUser.first_name}
                  onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <input
                  type="text"
                  value={newUser.last_name}
                  onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
              <select
                value={newUser.department}
                onChange={(e) => setNewUser({ ...newUser, department: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select Department</option>
                <option value="IT">IT</option>
                <option value="Finance">Finance</option>
                <option value="HR">HR</option>
                <option value="Operations">Operations</option>
                <option value="Security">Security</option>
                <option value="Management">Management</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                value={newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="user">User</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Access Level</label>
              <select
                value={newUser.access_level}
                onChange={(e) => setNewUser({ ...newUser, access_level: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="Level 1 - Basic User">Level 1 - Basic User</option>
                <option value="Level 2 - Power User">Level 2 - Power User</option>
                <option value="Level 3 - Manager">Level 3 - Manager</option>
                <option value="Level 4 - Administrator">Level 4 - Administrator</option>
                <option value="Level 5 - Executive">Level 5 - Executive</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="mfa_enabled"
                checked={newUser.mfa_enabled}
                onChange={(e) => setNewUser({ ...newUser, mfa_enabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="mfa_enabled" className="ml-2 block text-sm text-gray-900">
                Enable Multi-Factor Authentication
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => setShowUserModal(false)}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateUser}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              disabled={!newUser.email || !newUser.first_name || !newUser.last_name}
            >
              Create User
            </button>
          </div>
        </div>
      </div>
    )
  );

  const renderEditUserModal = () => (
    editingUser && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Edit User</h3>
            <button
              onClick={() => setEditingUser(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <input
                  type="text"
                  value={editingUser.first_name}
                  onChange={(e) => setEditingUser({ ...editingUser, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <input
                  type="text"
                  value={editingUser.last_name}
                  onChange={(e) => setEditingUser({ ...editingUser, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
              <select
                value={editingUser.department}
                onChange={(e) => setEditingUser({ ...editingUser, department: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select Department</option>
                <option value="IT">IT</option>
                <option value="Finance">Finance</option>
                <option value="HR">HR</option>
                <option value="Operations">Operations</option>
                <option value="Security">Security</option>
                <option value="Management">Management</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                value={editingUser.role}
                onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="user">User</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Access Level</label>
              <select
                value={editingUser.access_level}
                onChange={(e) => setEditingUser({ ...editingUser, access_level: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="Level 1 - Basic User">Level 1 - Basic User</option>
                <option value="Level 2 - Power User">Level 2 - Power User</option>
                <option value="Level 3 - Manager">Level 3 - Manager</option>
                <option value="Level 4 - Administrator">Level 4 - Administrator</option>
                <option value="Level 5 - Executive">Level 5 - Executive</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={editingUser.status}
                onChange={(e) => setEditingUser({ ...editingUser, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
                <option value="Pending">Pending</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="edit_mfa_enabled"
                checked={editingUser.mfa_enabled}
                onChange={(e) => setEditingUser({ ...editingUser, mfa_enabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="edit_mfa_enabled" className="ml-2 block text-sm text-gray-900">
                Enable Multi-Factor Authentication
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => setEditingUser(null)}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdateUser}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Update User
            </button>
          </div>
        </div>
      </div>
    )
  );

  const renderRoleModal = () => (
    showRoleModal && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Create New Role</h3>
            <button
              onClick={() => setShowRoleModal(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role Name</label>
              <input
                type="text"
                value={newRole.name}
                onChange={(e) => setNewRole({ ...newRole, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Senior Manager"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={newRole.description}
                onChange={(e) => setNewRole({ ...newRole, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="3"
                placeholder="Describe the role and its responsibilities..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Access Level</label>
                <select
                  value={newRole.level}
                  onChange={(e) => setNewRole({ ...newRole, level: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={1}>Level 1</option>
                  <option value={2}>Level 2</option>
                  <option value={3}>Level 3</option>
                  <option value={4}>Level 4</option>
                  <option value={5}>Level 5</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
                <select
                  value={newRole.risk_level}
                  onChange={(e) => setNewRole({ ...newRole, risk_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Permissions</label>
              <div className="space-y-2">
                {Object.entries(newRole.permissions).map(([key, value]) => (
                  <div key={key} className="flex items-center">
                    <input
                      type="checkbox"
                      id={`perm_${key}`}
                      checked={value}
                      onChange={(e) => setNewRole({
                        ...newRole,
                        permissions: {
                          ...newRole.permissions,
                          [key]: e.target.checked
                        }
                      })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor={`perm_${key}`} className="ml-2 block text-sm text-gray-900 capitalize">
                      {key.replace('_', ' ')}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => setShowRoleModal(false)}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateRole}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              disabled={!newRole.name || !newRole.description}
            >
              Create Role
            </button>
          </div>
        </div>
      </div>
    )
  );

  const renderEditRoleModal = () => (
    editingRole && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Edit Role</h3>
            <button
              onClick={() => setEditingRole(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role Name</label>
              <input
                type="text"
                value={editingRole.name}
                onChange={(e) => setEditingRole({ ...editingRole, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="e.g., Senior Manager"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={editingRole.description}
                onChange={(e) => setEditingRole({ ...editingRole, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                rows="3"
                placeholder="Describe the role and its responsibilities..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Access Level</label>
                <select
                  value={editingRole.level}
                  onChange={(e) => setEditingRole({ ...editingRole, level: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value={1}>Level 1</option>
                  <option value={2}>Level 2</option>
                  <option value={3}>Level 3</option>
                  <option value={4}>Level 4</option>
                  <option value={5}>Level 5</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
                <select
                  value={editingRole.risk_level}
                  onChange={(e) => setEditingRole({ ...editingRole, risk_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Permissions</label>
              <div className="space-y-2">
                {Object.entries(editingRole.permissions || {}).map(([key, value]) => (
                  <div key={key} className="flex items-center">
                    <input
                      type="checkbox"
                      id={`edit_perm_${key}`}
                      checked={value}
                      onChange={(e) => setEditingRole({
                        ...editingRole,
                        permissions: {
                          ...editingRole.permissions,
                          [key]: e.target.checked
                        }
                      })}
                      className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                    />
                    <label htmlFor={`edit_perm_${key}`} className="ml-2 block text-sm text-gray-900 capitalize">
                      {key.replace('_', ' ')}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => setEditingRole(null)}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdateRole}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              disabled={!editingRole.name || !editingRole.description}
            >
              Update Role
            </button>
          </div>
        </div>
      </div>
    )
  );

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">👥 Enterprise User Management</h1>
              <p className="text-gray-600 mt-2">Role-Based Access Control with granular permissions</p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                🔐 RBAC Enabled
              </span>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                ✅ Enterprise Ready
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: "users", label: "👥 Users", count: users.length },
                { id: "roles", label: "🔐 Roles & Permissions", count: roles.length },
                { id: "audit", label: "📋 Audit Trail", count: auditLogs.length },
                { id: "provisioning", label: "⚙️ Provisioning" }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  {tab.label}
                  {tab.count !== undefined && (
                    <span className="ml-2 py-0.5 px-2 rounded-full text-xs bg-gray-100 text-gray-900">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === "users" && renderUsersTab()}
          {activeTab === "roles" && renderRolesTab()}
          {activeTab === "audit" && renderAuditTab()}
          {activeTab === "provisioning" && renderProvisioningTab()}
        </div>

        {/* Modals */}
        {renderUserModal()}
        {renderEditUserModal()}
        {renderRoleModal()}
        {renderEditRoleModal()}

        {/* Error Display */}
        {error && (
          <div className="fixed bottom-4 right-4 bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded-lg shadow-lg">
            <div className="flex">
              <span className="mr-2">❌</span>
              <span>{error}</span>
              <button 
                onClick={() => setError(null)} 
                className="ml-3 text-red-500 hover:text-red-700"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnterpriseUserManagement;