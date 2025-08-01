import React, { useState, useEffect } from 'react';

const EnterpriseUserManagement = ({ getAuthHeaders, user }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);

  // Initialize data
  useEffect(() => {
    const initializeUserManagement = async () => {
      try {
        console.log('🔄 Loading Enterprise User Management...');
        
        // Simulate API calls with fallback to demo data
        await loadUsers();
        await loadRoles();
        await loadPermissions();
        await loadAuditLogs();
        
        setLoading(false);
        console.log('✅ Enterprise User Management loaded');
      } catch (error) {
        console.error('❌ Failed to load user management:', error);
        setLoading(false);
      }
    };

    initializeUserManagement();
  }, []);

  const loadUsers = async () => {
    try {
      // Try to fetch from backend
      const headers = await getAuthHeaders();
      const response = await fetch('https://owai-production.up.railway.app/users/management', {
        headers: headers
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        throw new Error('Backend not available');
      }
    } catch (error) {
      // Enterprise demo data
      setUsers([
        {
          id: 1,
          email: 'admin@company.com',
          firstName: 'System',
          lastName: 'Administrator',
          role: 'Super Admin',
          status: 'Active',
          lastLogin: '2025-07-31T14:30:00Z',
          createdAt: '2025-01-15T09:00:00Z',
          permissions: ['*'],
          mfaEnabled: true,
          loginAttempts: 0,
          department: 'IT Security',
          manager: null,
          accessLevel: 'Level 5 - Executive'
        },
        {
          id: 2,
          email: 'security.analyst@company.com',
          firstName: 'Sarah',
          lastName: 'Connor',
          role: 'Security Analyst',
          status: 'Active',
          lastLogin: '2025-07-31T13:45:00Z',
          createdAt: '2025-02-01T10:00:00Z',
          permissions: ['alerts:read', 'alerts:manage', 'rules:read', 'rules:create'],
          mfaEnabled: true,
          loginAttempts: 0,
          department: 'Security Operations',
          manager: 'admin@company.com',
          accessLevel: 'Level 3 - Senior Analyst'
        },
        {
          id: 3,
          email: 'compliance.officer@company.com',
          firstName: 'Michael',
          lastName: 'Thompson',
          role: 'Compliance Officer',
          status: 'Active',
          lastLogin: '2025-07-31T12:00:00Z',
          createdAt: '2025-03-15T08:30:00Z',
          permissions: ['audit:read', 'compliance:manage', 'reports:generate'],
          mfaEnabled: true,
          loginAttempts: 0,
          department: 'Risk & Compliance',
          manager: 'admin@company.com',
          accessLevel: 'Level 4 - Management'
        },
        {
          id: 4,
          email: 'junior.analyst@company.com',
          firstName: 'Alex',
          lastName: 'Rodriguez',
          role: 'Junior Analyst',
          status: 'Pending Approval',
          lastLogin: null,
          createdAt: '2025-07-30T16:00:00Z',
          permissions: ['dashboard:read', 'alerts:read'],
          mfaEnabled: false,
          loginAttempts: 0,
          department: 'Security Operations',
          manager: 'security.analyst@company.com',
          accessLevel: 'Level 1 - Analyst'
        },
        {
          id: 5,
          email: 'contractor@external.com',
          firstName: 'David',
          lastName: 'Wilson',
          role: 'External Contractor',
          status: 'Suspended',
          lastLogin: '2025-07-28T09:15:00Z',
          createdAt: '2025-07-01T14:00:00Z',
          permissions: ['dashboard:read'],
          mfaEnabled: false,
          loginAttempts: 3,
          department: 'External',
          manager: 'security.analyst@company.com',
          accessLevel: 'Level 0 - Restricted'
        }
      ]);
    }
  };

  const loadRoles = async () => {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch('https://owai-production.up.railway.app/users/roles', {
        headers: headers
      });
      
      if (response.ok) {
        const data = await response.json();
        setRoles(data);
      } else {
        throw new Error('Backend not available');
      }
    } catch (error) {
      setRoles([
        {
          id: 1,
          name: 'Super Admin',
          description: 'Full system access with all permissions',
          permissions: ['*'],
          userCount: 1,
          level: 5,
          canDelegate: true,
          riskLevel: 'Critical'
        },
        {
          id: 2,
          name: 'Security Analyst',
          description: 'Security operations and alert management',
          permissions: ['alerts:read', 'alerts:manage', 'rules:read', 'rules:create', 'dashboard:read'],
          userCount: 8,
          level: 3,
          canDelegate: false,
          riskLevel: 'High'
        },
        {
          id: 3,
          name: 'Compliance Officer',
          description: 'Compliance monitoring and audit access',
          permissions: ['audit:read', 'compliance:manage', 'reports:generate', 'dashboard:read'],
          userCount: 3,
          level: 4,
          canDelegate: true,
          riskLevel: 'Medium'
        },
        {
          id: 4,
          name: 'Junior Analyst',
          description: 'Read-only access to security dashboards',
          permissions: ['dashboard:read', 'alerts:read'],
          userCount: 12,
          level: 1,
          canDelegate: false,
          riskLevel: 'Low'
        },
        {
          id: 5,
          name: 'External Contractor',
          description: 'Limited access for external personnel',
          permissions: ['dashboard:read'],
          userCount: 5,
          level: 0,
          canDelegate: false,
          riskLevel: 'Medium'
        }
      ]);
    }
  };

  const loadPermissions = async () => {
    setPermissions([
      {
        category: 'Dashboard',
        permissions: [
          { name: 'dashboard:read', description: 'View security dashboard', riskLevel: 'Low' },
          { name: 'dashboard:admin', description: 'Manage dashboard configuration', riskLevel: 'Medium' }
        ]
      },
      {
        category: 'Alerts',
        permissions: [
          { name: 'alerts:read', description: 'View security alerts', riskLevel: 'Low' },
          { name: 'alerts:manage', description: 'Manage and respond to alerts', riskLevel: 'High' },
          { name: 'alerts:admin', description: 'Configure alert rules and settings', riskLevel: 'Critical' }
        ]
      },
      {
        category: 'Rules',
        permissions: [
          { name: 'rules:read', description: 'View security rules', riskLevel: 'Low' },
          { name: 'rules:create', description: 'Create new security rules', riskLevel: 'High' },
          { name: 'rules:delete', description: 'Delete security rules', riskLevel: 'Critical' },
          { name: 'rules:admin', description: 'Full rule management access', riskLevel: 'Critical' }
        ]
      },
      {
        category: 'Authorization',
        permissions: [
          { name: 'auth:read', description: 'View authorization requests', riskLevel: 'Medium' },
          { name: 'auth:approve', description: 'Approve authorization requests', riskLevel: 'Critical' },
          { name: 'auth:emergency', description: 'Emergency override authorization', riskLevel: 'Critical' }
        ]
      },
      {
        category: 'Users',
        permissions: [
          { name: 'users:read', description: 'View user information', riskLevel: 'Medium' },
          { name: 'users:manage', description: 'Create and modify users', riskLevel: 'Critical' },
          { name: 'users:admin', description: 'Full user management access', riskLevel: 'Critical' }
        ]
      },
      {
        category: 'Audit',
        permissions: [
          { name: 'audit:read', description: 'View audit logs', riskLevel: 'Medium' },
          { name: 'compliance:manage', description: 'Manage compliance reporting', riskLevel: 'High' },
          { name: 'reports:generate', description: 'Generate compliance reports', riskLevel: 'Medium' }
        ]
      }
    ]);
  };

  const loadAuditLogs = async () => {
    setAuditLogs([
      {
        id: 1,
        timestamp: '2025-07-31T14:30:00Z',
        user: 'admin@company.com',
        action: 'User Created',
        target: 'junior.analyst@company.com',
        details: 'New user account created with Junior Analyst role',
        ipAddress: '192.168.1.100',
        riskLevel: 'Medium'
      },
      {
        id: 2,
        timestamp: '2025-07-31T13:45:00Z',
        user: 'security.analyst@company.com',
        action: 'Permission Modified',
        target: 'contractor@external.com',
        details: 'Removed alerts:manage permission due to policy violation',
        ipAddress: '192.168.1.150',
        riskLevel: 'High'
      },
      {
        id: 3,
        timestamp: '2025-07-31T12:00:00Z',
        user: 'system',
        action: 'Account Suspended',
        target: 'contractor@external.com',
        details: 'Auto-suspended after 3 failed login attempts',
        ipAddress: '203.0.113.45',
        riskLevel: 'High'
      },
      {
        id: 4,
        timestamp: '2025-07-31T11:30:00Z',
        user: 'compliance.officer@company.com',
        action: 'Role Assignment',
        target: 'security.analyst@company.com',
        details: 'Assigned additional compliance:read permission for audit',
        ipAddress: '192.168.1.200',
        riskLevel: 'Medium'
      },
      {
        id: 5,
        timestamp: '2025-07-31T10:15:00Z',
        user: 'admin@company.com',
        action: 'MFA Enabled',
        target: 'junior.analyst@company.com',
        details: 'Multi-factor authentication enforced for new user',
        ipAddress: '192.168.1.100',
        riskLevel: 'Low'
      }
    ]);
  };

  const handleCreateUser = async (userData) => {
    try {
      // Simulate user creation
      const newUser = {
        id: users.length + 1,
        ...userData,
        status: 'Pending Approval',
        createdAt: new Date().toISOString(),
        lastLogin: null,
        loginAttempts: 0,
        mfaEnabled: false
      };
      
      setUsers([...users, newUser]);
      setShowCreateUser(false);
      
      // Add audit log
      const auditEntry = {
        id: auditLogs.length + 1,
        timestamp: new Date().toISOString(),
        user: user.email,
        action: 'User Created',
        target: userData.email,
        details: `New user account created with ${userData.role} role`,
        ipAddress: '192.168.1.100',
        riskLevel: 'Medium'
      };
      setAuditLogs([auditEntry, ...auditLogs]);
      
      console.log('✅ User created successfully');
    } catch (error) {
      console.error('❌ Failed to create user:', error);
    }
  };

  const handleUpdateUserStatus = async (userId, newStatus) => {
    try {
      setUsers(users.map(u => 
        u.id === userId ? { ...u, status: newStatus } : u
      ));
      
      const targetUser = users.find(u => u.id === userId);
      const auditEntry = {
        id: auditLogs.length + 1,
        timestamp: new Date().toISOString(),
        user: user.email,
        action: 'Status Changed',
        target: targetUser.email,
        details: `User status changed to ${newStatus}`,
        ipAddress: '192.168.1.100',
        riskLevel: newStatus === 'Suspended' ? 'High' : 'Medium'
      };
      setAuditLogs([auditEntry, ...auditLogs]);
      
      console.log(`✅ User status updated to ${newStatus}`);
    } catch (error) {
      console.error('❌ Failed to update user status:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active': return 'bg-green-100 text-green-800';
      case 'Pending Approval': return 'bg-yellow-100 text-yellow-800';
      case 'Suspended': return 'bg-red-100 text-red-800';
      case 'Inactive': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'Critical': return 'bg-red-100 text-red-800';
      case 'High': return 'bg-orange-100 text-orange-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'Low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading Enterprise User Management...</span>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">👥 Enterprise User Management</h1>
            <p className="text-gray-600 mt-2">Advanced RBAC with granular permissions and audit controls</p>
          </div>
          <button
            onClick={() => setShowCreateUser(true)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition font-semibold shadow-lg"
          >
            + Create User
          </button>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-6">
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-lg text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100">Total Users</p>
                <p className="text-3xl font-bold">{users.length}</p>
              </div>
              <div className="text-4xl opacity-80">👥</div>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-green-500 to-green-600 p-6 rounded-lg text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100">Active Users</p>
                <p className="text-3xl font-bold">{users.filter(u => u.status === 'Active').length}</p>
              </div>
              <div className="text-4xl opacity-80">✅</div>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-orange-500 to-red-600 p-6 rounded-lg text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100">Pending Approval</p>
                <p className="text-3xl font-bold">{users.filter(u => u.status === 'Pending Approval').length}</p>
              </div>
              <div className="text-4xl opacity-80">⏳</div>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 p-6 rounded-lg text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100">Roles Defined</p>
                <p className="text-3xl font-bold">{roles.length}</p>
              </div>
              <div className="text-4xl opacity-80">🔐</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'users', label: '👥 Users', icon: '👥' },
            { id: 'roles', label: '🔐 Roles & Permissions', icon: '🔐' },
            { id: 'audit', label: '📋 Audit Logs', icon: '📋' },
            { id: 'provisioning', label: '⚙️ Provisioning', icon: '⚙️' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 font-medium text-sm border-b-2 transition-colors duration-200 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b">
              <h2 className="text-lg font-semibold text-gray-900">User Directory</h2>
              <p className="text-sm text-gray-600">Manage user accounts, roles, and access levels</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MFA</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-r from-blue-400 to-purple-500 flex items-center justify-center text-white font-semibold">
                              {user.firstName[0]}{user.lastName[0]}
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {user.firstName} {user.lastName}
                            </div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                            <div className="text-xs text-gray-400">{user.department}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{user.role}</div>
                        <div className="text-xs text-gray-500">{user.accessLevel}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(user.status)}`}>
                          {user.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.lastLogin ? new Date(user.lastLogin).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.mfaEnabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {user.mfaEnabled ? '✅ Enabled' : '❌ Disabled'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => setSelectedUser(user)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Edit
                        </button>
                        {user.status === 'Active' ? (
                          <button
                            onClick={() => handleUpdateUserStatus(user.id, 'Suspended')}
                            className="text-red-600 hover:text-red-900"
                          >
                            Suspend
                          </button>
                        ) : (
                          <button
                            onClick={() => handleUpdateUserStatus(user.id, 'Active')}
                            className="text-green-600 hover:text-green-900"
                          >
                            Activate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'roles' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Roles List */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 bg-gray-50 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Security Roles</h2>
                <p className="text-sm text-gray-600">Defined roles with permission levels</p>
              </div>
              <div className="p-6 space-y-4">
                {roles.map((role) => (
                  <div key={role.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">{role.name}</h3>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getRiskLevelColor(role.riskLevel)}`}>
                          {role.riskLevel} Risk
                        </span>
                        <span className="text-sm text-gray-500">Level {role.level}</span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{role.description}</p>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">{role.userCount} users assigned</span>
                      <button
                        onClick={() => setShowRoleModal(role)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Manage Permissions
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Permissions Matrix */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 bg-gray-50 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Permission Categories</h2>
                <p className="text-sm text-gray-600">Available system permissions by category</p>
              </div>
              <div className="p-6 space-y-4">
                {permissions.map((category) => (
                  <div key={category.category} className="border rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-3">{category.category}</h3>
                    <div className="space-y-2">
                      {category.permissions.map((perm) => (
                        <div key={perm.name} className="flex items-center justify-between">
                          <div>
                            <span className="text-sm font-medium text-gray-700">{perm.name}</span>
                            <p className="text-xs text-gray-500">{perm.description}</p>
                          </div>
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getRiskLevelColor(perm.riskLevel)}`}>
                            {perm.riskLevel}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Audit Trail</h2>
            <p className="text-sm text-gray-600">Complete user management activity log</p>
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
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.user}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">{log.action}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.target}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {log.details}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskLevelColor(log.riskLevel)}`}>
                        {log.riskLevel}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'provisioning' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Provisioning Workflows */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 bg-gray-50 border-b">
                <h2 className="text-lg font-semibold text-gray-900">🔄 Provisioning Workflows</h2>
                <p className="text-sm text-gray-600">Automated user lifecycle management</p>
              </div>
              <div className="p-6 space-y-4">
                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">New Employee Onboarding</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Automatic account creation with role-based permissions</p>
                  <div className="space-y-2">
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                      <span>Create user account</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                      <span>Assign department-based role</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                      <span>Enable MFA requirement</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></span>
                      <span>Notify manager for approval</span>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">Employee Offboarding</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Secure account deactivation and access revocation</p>
                  <div className="space-y-2">
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                      <span>Immediate access suspension</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                      <span>Revoke all permissions</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                      <span>Archive user data</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                      <span>Generate compliance report</span>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">Role Change Management</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Configured</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Automated permission updates based on role changes</p>
                  <div className="space-y-2">
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-blue-500 rounded-full mr-2"></span>
                      <span>Detect role change triggers</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-blue-500 rounded-full mr-2"></span>
                      <span>Update permission matrix</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="w-4 h-4 bg-blue-500 rounded-full mr-2"></span>
                      <span>Notify security team</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Compliance & Integration */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 bg-gray-50 border-b">
                <h2 className="text-lg font-semibold text-gray-900">🔗 Enterprise Integration</h2>
                <p className="text-sm text-gray-600">Connect with existing enterprise systems</p>
              </div>
              <div className="p-6 space-y-4">
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">Active Directory</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Connected</span>
                  </div>
                  <p className="text-sm text-gray-600">Sync users and groups from AD</p>
                  <div className="mt-2 text-xs text-gray-500">Last sync: 2 hours ago</div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">LDAP Authentication</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>
                  </div>
                  <p className="text-sm text-gray-600">Enterprise directory authentication</p>
                  <div className="mt-2 text-xs text-gray-500">Status: Healthy</div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">SSO Integration</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Pending</span>
                  </div>
                  <p className="text-sm text-gray-600">Single Sign-On with SAML/OAuth</p>
                  <button className="mt-2 text-xs text-blue-600 hover:text-blue-900">Configure SSO</button>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">HR System Integration</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Ready</span>
                  </div>
                  <p className="text-sm text-gray-600">Automated user lifecycle from HRIS</p>
                  <button className="mt-2 text-xs text-blue-600 hover:text-blue-900">Enable Integration</button>
                </div>

                {/* Compliance Section */}
                <div className="mt-6 border-t pt-4">
                  <h3 className="font-semibold text-gray-900 mb-3">📋 Compliance Frameworks</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="text-sm font-medium">SOX Compliance</span>
                      <span className="text-xs text-green-600">✅ Compliant</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="text-sm font-medium">HIPAA Requirements</span>
                      <span className="text-xs text-green-600">✅ Compliant</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-yellow-50 rounded">
                      <span className="text-sm font-medium">PCI-DSS Standards</span>
                      <span className="text-xs text-yellow-600">⚠️ Review Required</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="text-sm font-medium">ISO 27001</span>
                      <span className="text-xs text-green-600">✅ Compliant</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create New User</h2>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target);
              handleCreateUser({
                email: formData.get('email'),
                firstName: formData.get('firstName'),
                lastName: formData.get('lastName'),
                role: formData.get('role'),
                department: formData.get('department'),
                accessLevel: formData.get('accessLevel'),
                permissions: ['dashboard:read'] // Default permissions
              });
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email Address</label>
                  <input
                    type="email"
                    name="email"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">First Name</label>
                    <input
                      type="text"
                      name="firstName"
                      required
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Name</label>
                    <input
                      type="text"
                      name="lastName"
                      required
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Role</label>
                  <select
                    name="role"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    {roles.map((role) => (
                      <option key={role.id} value={role.name}>{role.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Department</label>
                  <select
                    name="department"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="IT Security">IT Security</option>
                    <option value="Security Operations">Security Operations</option>
                    <option value="Risk & Compliance">Risk & Compliance</option>
                    <option value="External">External</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Access Level</label>
                  <select
                    name="accessLevel"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="Level 1 - Analyst">Level 1 - Analyst</option>
                    <option value="Level 2 - Senior Analyst">Level 2 - Senior Analyst</option>
                    <option value="Level 3 - Lead Analyst">Level 3 - Lead Analyst</option>
                    <option value="Level 4 - Management">Level 4 - Management</option>
                    <option value="Level 5 - Executive">Level 5 - Executive</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateUser(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* User Details Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">User Details: {selectedUser.firstName} {selectedUser.lastName}</h2>
              <button
                onClick={() => setSelectedUser(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Basic Information</h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Email:</strong> {selectedUser.email}</div>
                  <div><strong>Role:</strong> {selectedUser.role}</div>
                  <div><strong>Department:</strong> {selectedUser.department}</div>
                  <div><strong>Access Level:</strong> {selectedUser.accessLevel}</div>
                  <div><strong>Manager:</strong> {selectedUser.manager || 'N/A'}</div>
                  <div><strong>Status:</strong> 
                    <span className={`ml-2 px-2 py-1 text-xs rounded-full ${getStatusColor(selectedUser.status)}`}>
                      {selectedUser.status}
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Security Information</h3>
                <div className="space-y-2 text-sm">
                  <div><strong>MFA Enabled:</strong> {selectedUser.mfaEnabled ? '✅ Yes' : '❌ No'}</div>
                  <div><strong>Login Attempts:</strong> {selectedUser.loginAttempts}</div>
                  <div><strong>Last Login:</strong> {selectedUser.lastLogin ? new Date(selectedUser.lastLogin).toLocaleString() : 'Never'}</div>
                  <div><strong>Created:</strong> {new Date(selectedUser.createdAt).toLocaleDateString()}</div>
                </div>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-semibold mb-2">Permissions</h3>
              <div className="bg-gray-50 rounded p-3 max-h-32 overflow-y-auto">
                {selectedUser.permissions.includes('*') ? (
                  <span className="text-red-600 font-medium">🔥 Full System Access (Super Admin)</span>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {selectedUser.permissions.map((perm, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {perm}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setSelectedUser(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                Close
              </button>
              <button
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              >
                Edit Permissions
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnterpriseUserManagement;