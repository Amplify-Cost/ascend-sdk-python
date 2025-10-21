import React, { useState } from 'react';
import { 
import logger from '../utils/logger.js';
  Shield, Plus, Code, Sparkles, TestTube, BarChart3, 
  FileText, Check, X, AlertTriangle, ChevronDown, Edit2, Trash2
} from 'lucide-react';

/**
 * Enhanced Enterprise Policy Tab
 * Visual builder + templates + testing
 */
export const EnhancedPolicyTab = ({ 
  policies, 
  onCreatePolicy, 
  onDeletePolicy,
  API_BASE_URL,
  getAuthHeaders 
}) => {
  const [view, setView] = useState('list');
  const [policyForm, setPolicyForm] = useState({
    policy_name: '',
    description: ''
  });
  const [templates, setTemplates] = useState([]);

  React.useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/templates`,
        { headers: getAuthHeaders() }
      );
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      logger.error('Failed to load templates:', error);
    }
  };

  const createPolicy = async () => {
    if (!policyForm.policy_name || !policyForm.description) {
      alert('Please fill in both fields');
      return;
    }
    await onCreatePolicy();
    setPolicyForm({ policy_name: '', description: '' });
    setView('list');
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
        setView('list');
        window.location.reload();
      }
    } catch (error) {
      alert('Failed to create from template');
    }
  };

  if (view === 'templates') {
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
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-bold text-lg mb-1">{template.name}</h4>
                      <p className="text-sm text-gray-600">{template.description}</p>
                    </div>
                  </div>
                  
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
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
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
  }

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => setView('list')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            view === 'list' 
              ? 'bg-blue-600 text-white' 
              : 'bg-white border border-gray-300 hover:bg-gray-50'
          }`}
        >
          <Shield className="h-4 w-4" />
          Policies
        </button>
        <button
          onClick={() => setView('templates')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            view === 'templates' 
              ? 'bg-purple-600 text-white' 
              : 'bg-white border border-gray-300 hover:bg-gray-50'
          }`}
        >
          <FileText className="h-4 w-4" />
          Templates ({templates.length})
        </button>
      </div>

      {/* Create Policy Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Plus className="h-5 w-5 text-blue-600" />
          Create New Policy
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Policy Name
            </label>
            <input
              type="text"
              value={policyForm.policy_name}
              onChange={e => setPolicyForm({...policyForm, policy_name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Block Production Database Deletes"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Natural Language Description
            </label>
            <textarea
              rows={4}
              value={policyForm.description}
              onChange={e => setPolicyForm({...policyForm, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe the policy in natural language, e.g., 'Deny all delete operations on production databases during business hours'"
            />
          </div>
          
          <button
            onClick={createPolicy}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Create Policy
          </button>
        </div>
      </div>

      {/* Active Policies */}
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
            <p className="text-gray-500">Create your first policy above or use a template</p>
          </div>
        ) : (
          <div className="divide-y">
            {policies.map((policy) => (
              <div key={policy.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-xl font-bold text-gray-900">{policy.policy_name}</h4>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        policy.risk_level === 'high' ? 'bg-red-500 text-white' :
                        policy.risk_level === 'medium' ? 'bg-yellow-500 text-white' :
                        'bg-green-500 text-white'
                      }`}>
                        {(policy.risk_level || 'medium').toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-700">{policy.description}</p>
                    
                    <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
                      <div>
                        <span className="text-gray-500">Created By:</span>
                        <p className="font-semibold">{policy.created_by}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Created:</span>
                        <p className="font-semibold">
                          {new Date(policy.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">Status:</span>
                        <p className="font-semibold text-green-600">Active</p>
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => onDeletePolicy(policy.id)}
                    className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete Policy"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedPolicyTab;
