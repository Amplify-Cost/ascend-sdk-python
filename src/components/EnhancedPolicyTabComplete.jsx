import React, { useState, useEffect } from 'react';
import {
  Shield, Plus, FileText, TestTube, BarChart3, History,
  Activity, Award, Zap, AlertTriangle, Download
} from 'lucide-react';
import { PolicyAnalytics } from './PolicyAnalytics';
import { PolicyTester } from './PolicyTester';
import { VisualPolicyBuilderAdvanced } from './VisualPolicyBuilderAdvanced';
import { ComplianceMapping } from './ComplianceMapping';
import { PolicyVersionControl } from './PolicyVersionControl';
import { PolicyImpactAnalysis } from './PolicyImpactAnalysis';
import { PolicyConflictDetector } from './PolicyConflictDetector';
import { PolicyImportExport } from './PolicyImportExport';
import { PolicyBulkActions } from './PolicyBulkActions';

export const EnhancedPolicyTabComplete = ({
  policies,
  onCreatePolicy,
  onDeletePolicy,
  onRefreshPolicies,
  API_BASE_URL,
  getAuthHeaders
}) => {
  const [view, setView] = useState('list');
  const [templates, setTemplates] = useState([]);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [selectedPolicies, setSelectedPolicies] = useState([]);
  const [policyForm, setPolicyForm] = useState({
    policy_name: '',
    description: ''
  });

  useEffect(() => {
    loadTemplates();
  }, []); // Only load once on mount

  const loadTemplates = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/templates`,
        { credentials: "include", headers: getAuthHeaders() }
      );
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const createFromTemplate = async (templateId) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/from-template`,
        {
          method: 'POST',
          headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ template_id: templateId })
        }
      );
      if (response.ok) {
        alert('Policy created from template!');
        // Refresh the policy list immediately using parent's fetch function
        if (onRefreshPolicies) {
          await onRefreshPolicies();
        }
        setView('list');
        // Also trigger parent callback if provided
        if (onCreatePolicy) onCreatePolicy();
      } else {
        const errorData = await response.json();
        alert(`Failed to create from template: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Template creation error:', error);
      alert('Failed to create from template');
    }
  };

  // Navigation tabs
  const tabs = [
    { id: 'list', label: 'Policies', icon: Shield },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'test', label: 'Testing', icon: TestTube },
    { id: 'compliance', label: 'Compliance', icon: Award },
    { id: 'conflicts', label: 'Conflicts', icon: AlertTriangle },
    { id: 'import-export', label: 'Import/Export', icon: Download },
    { id: 'create', label: 'Create', icon: Plus }
  ];

  // Render based on view
  const renderView = () => {
    switch (view) {
      case 'analytics':
        return <PolicyAnalytics API_BASE_URL={API_BASE_URL} getAuthHeaders={getAuthHeaders} />;

      case 'test':
        return <PolicyTester API_BASE_URL={API_BASE_URL} getAuthHeaders={getAuthHeaders} />;

      case 'compliance':
        return <ComplianceMapping policies={policies} />;

      case 'conflicts':
        return <PolicyConflictDetector API_BASE_URL={API_BASE_URL} getAuthHeaders={getAuthHeaders} />;

      case 'import-export':
        return (
          <PolicyImportExport
            API_BASE_URL={API_BASE_URL}
            getAuthHeaders={getAuthHeaders}
            onImportComplete={async () => {
              await onRefreshPolicies();
              setView('list');
            }}
          />
        );

      case 'create':
        return (
          <VisualPolicyBuilderAdvanced
            onSave={async (policy) => {
              await onCreatePolicy(policy);
              setView('list');
            }}
            onCancel={() => setView('list')}
            API_BASE_URL={API_BASE_URL}
            getAuthHeaders={getAuthHeaders}
          />
        );
      
      case 'templates':
        return (
          <div className="space-y-4">
            <button 
              onClick={() => setView('list')}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              ← Back to Policies
            </button>
            
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-xl font-bold mb-6">Policy Template Gallery</h3>
              
              {templates.length === 0 ? (
                <p className="text-gray-500">Loading templates...</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {templates.map((template, idx) => (
                    <div key={idx} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <h4 className="font-bold text-lg mb-1">{template.name}</h4>
                      <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                      
                      <div className="flex gap-2 mb-3">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {template.severity}
                        </span>
                        {template.compliance_frameworks?.map((fw, i) => (
                          <span key={i} className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                            {fw}
                          </span>
                        ))}
                      </div>
                      
                      <button
                        onClick={() => createFromTemplate(template.id)}
                        className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                      >
                        Use Template
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      
      case 'version-history':
        return (
          <div>
            <button onClick={() => setView('list')} className="text-blue-600 mb-4">
              ← Back to Policies
            </button>
            <PolicyVersionControl 
              policyId={selectedPolicy?.id}
              API_BASE_URL={API_BASE_URL}
              getAuthHeaders={getAuthHeaders}
            />
          </div>
        );
      
      case 'impact':
        return (
          <div>
            <button onClick={() => setView('list')} className="text-blue-600 mb-4">
              ← Back to Policies
            </button>
            <PolicyImpactAnalysis 
              policy={selectedPolicy}
              API_BASE_URL={API_BASE_URL}
              getAuthHeaders={getAuthHeaders}
            />
          </div>
        );
      
      default: // list view
        return (
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={() => setView('templates')}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <FileText className="h-4 w-4" />
                Templates ({templates.length})
              </button>
            </div>

            {/* Policy List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Shield className="h-5 w-5 text-blue-600" />
                  Active Policies ({policies.length})
                </h3>
              </div>
              
              {policies.length === 0 ? (
                <div className="p-12 text-center">
                  <Shield className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No Active Policies</h4>
                  <p className="text-gray-500 mb-4">Create your first policy to start</p>
                  <button
                    onClick={() => setView('create')}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Create Policy
                  </button>
                </div>
              ) : (
                <div className="divide-y">
                  {policies.map((policy) => {
                    const isSelected = selectedPolicies.some(p => p.id === policy.id);
                    return (
                      <div key={policy.id} className={`p-6 transition-colors ${
                        isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                      }`}>
                        <div className="flex items-start gap-4">
                          {/* Selection Checkbox */}
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedPolicies([...selectedPolicies, policy]);
                              } else {
                                setSelectedPolicies(selectedPolicies.filter(p => p.id !== policy.id));
                              }
                            }}
                            className="mt-1 h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            aria-label={`Select ${policy.policy_name}`}
                          />

                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h4 className="text-xl font-bold">{policy.policy_name}</h4>
                              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                                policy.risk_level === 'high' ? 'bg-red-500 text-white' :
                                policy.risk_level === 'medium' ? 'bg-yellow-500 text-white' :
                                'bg-green-500 text-white'
                              }`}>
                                {(policy.risk_level || 'medium').toUpperCase()}
                              </span>
                            </div>
                            <p className="text-gray-700 mb-3">{policy.description}</p>

                            <div className="flex gap-2">
                              <button
                                onClick={() => {
                                  setSelectedPolicy(policy);
                                  setView('version-history');
                                }}
                                className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                              >
                                <History className="h-4 w-4 inline mr-1" />
                                History
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedPolicy(policy);
                                  setView('impact');
                                }}
                                className="text-sm px-3 py-1 bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
                              >
                                <Activity className="h-4 w-4 inline mr-1" />
                                Impact
                              </button>
                            </div>
                          </div>

                          <button
                            onClick={() => onDeletePolicy(policy.id)}
                            className="ml-4 px-4 py-2 text-red-600 hover:bg-red-50 rounded"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Bulk Actions Floating Toolbar */}
            <PolicyBulkActions
              selectedPolicies={selectedPolicies}
              onBulkComplete={async () => {
                setSelectedPolicies([]);
                await onRefreshPolicies();
              }}
              onClearSelection={() => setSelectedPolicies([])}
              API_BASE_URL={API_BASE_URL}
              getAuthHeaders={getAuthHeaders}
            />
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-2">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setView(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                  view === tab.id
                    ? 'border-blue-600 text-blue-600 font-semibold'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      {renderView()}
    </div>
  );
};

export default EnhancedPolicyTabComplete;
