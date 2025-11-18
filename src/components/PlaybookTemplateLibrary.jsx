/**
 * 🏢 ENTERPRISE PLAYBOOK TEMPLATE LIBRARY
 *
 * Phase 2 Frontend Component
 * Pre-built playbook templates for quick deployment
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-11-18
 */

import React, { useState, useEffect } from 'react';

const PlaybookTemplateLibrary = ({ onSelectTemplate, onClose, getAuthHeaders, API_BASE_URL }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [error, setError] = useState(null);

  const CATEGORIES = [
    { value: 'all', label: '📚 All Templates', color: 'gray' },
    { value: 'productivity', label: '⚡ Productivity', color: 'green' },
    { value: 'security', label: '🔒 Security', color: 'red' },
    { value: 'compliance', label: '📋 Compliance', color: 'blue' },
    { value: 'cost_optimization', label: '💰 Cost Optimization', color: 'yellow' }
  ];

  useEffect(() => {
    fetchTemplates();
  }, [selectedCategory]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);

      const categoryParam = selectedCategory !== 'all' ? `?category=${selectedCategory}` : '';
      const response = await fetch(
        `${API_BASE_URL}/api/authorization/automation/playbook-templates${categoryParam}`,
        {
          credentials: 'include',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.data || []);
      } else {
        setError('Failed to load templates');
      }
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category) => {
    const cat = CATEGORIES.find(c => c.value === category);
    return cat?.color || 'gray';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      productivity: '⚡',
      security: '🔒',
      compliance: '📋',
      cost_optimization: '💰'
    };
    return icons[category] || '📚';
  };

  const getComplexityBadge = (complexity) => {
    const badges = {
      low: { label: 'Low', color: 'bg-green-100 text-green-800' },
      medium: { label: 'Medium', color: 'bg-yellow-100 text-yellow-800' },
      high: { label: 'High', color: 'bg-red-100 text-red-800' }
    };
    return badges[complexity] || badges.medium;
  };

  const handleUseTemplate = (template) => {
    // Convert template to playbook format
    const playbookData = {
      id: '', // User will need to provide unique ID
      name: template.name,
      description: template.description,
      status: 'active',
      risk_level: template.trigger_conditions.risk_score?.max > 70 ? 'high' :
                  template.trigger_conditions.risk_score?.max > 40 ? 'medium' : 'low',
      approval_required: false,
      trigger_conditions: template.trigger_conditions,
      actions: template.actions
    };

    onSelectTemplate(playbookData);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-screen overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-2xl font-semibold">📚 Playbook Template Library</h3>
              <p className="text-sm text-gray-600 mt-1">
                Choose a pre-built template to get started quickly
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl"
            >
              ×
            </button>
          </div>

          {/* Category Filter */}
          <div className="flex gap-2 overflow-x-auto">
            {CATEGORIES.map(category => (
              <button
                key={category.value}
                onClick={() => setSelectedCategory(category.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  selectedCategory === category.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Templates Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-4">Loading templates...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <p className="text-red-800">❌ {error}</p>
              <button
                onClick={fetchTemplates}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          )}

          {!loading && !error && templates.length === 0 && (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-600">No templates found in this category</p>
              <button
                onClick={() => setSelectedCategory('all')}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800 underline"
              >
                View all templates
              </button>
            </div>
          )}

          {!loading && !error && templates.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((template) => {
                const complexityBadge = getComplexityBadge(template.complexity);
                const categoryColor = getCategoryColor(template.category);

                return (
                  <div
                    key={template.id}
                    className="bg-white border border-gray-200 rounded-lg p-5 hover:border-blue-400 hover:shadow-md transition-all"
                  >
                    {/* Template Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-2xl">{getCategoryIcon(template.category)}</span>
                          <h4 className="font-semibold text-lg">{template.name}</h4>
                        </div>
                        <p className="text-sm text-gray-600">{template.description}</p>
                      </div>
                    </div>

                    {/* Badges */}
                    <div className="flex gap-2 mb-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${complexityBadge.color}`}>
                        {complexityBadge.label} Complexity
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-medium bg-${categoryColor}-100 text-${categoryColor}-800`}>
                        {template.category.replace('_', ' ')}
                      </span>
                    </div>

                    {/* Use Case */}
                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-700 mb-1">📖 Use Case:</p>
                      <p className="text-xs text-gray-600">{template.use_case}</p>
                    </div>

                    {/* Trigger Conditions Preview */}
                    <div className="mb-3 bg-gray-50 rounded p-3">
                      <p className="text-xs font-medium text-gray-700 mb-2">🎯 Triggers When:</p>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {template.trigger_conditions.risk_score && (
                          <li>
                            • Risk score: {template.trigger_conditions.risk_score.min || 0} - {template.trigger_conditions.risk_score.max || 100}
                          </li>
                        )}
                        {template.trigger_conditions.action_type && template.trigger_conditions.action_type.length > 0 && (
                          <li>
                            • Action type: {template.trigger_conditions.action_type.join(', ')}
                          </li>
                        )}
                        {template.trigger_conditions.environment && template.trigger_conditions.environment.length > 0 && (
                          <li>
                            • Environment: {template.trigger_conditions.environment.join(', ')}
                          </li>
                        )}
                        {template.trigger_conditions.business_hours && (
                          <li>• During business hours</li>
                        )}
                      </ul>
                    </div>

                    {/* Actions Preview */}
                    <div className="mb-4 bg-blue-50 rounded p-3">
                      <p className="text-xs font-medium text-gray-700 mb-2">⚡ Automated Actions:</p>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {template.actions.map((action, idx) => (
                          <li key={idx}>
                            • {action.type.replace('_', ' ')}
                            {action.parameters.recipients && ` → ${action.parameters.recipients.join(', ')}`}
                            {action.parameters.level && ` (${action.parameters.level})`}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* ROI */}
                    {template.estimated_savings_per_month && template.estimated_savings_per_month > 0 && (
                      <div className="mb-4 bg-green-50 rounded p-3">
                        <p className="text-xs font-medium text-green-800">
                          💰 Est. Savings: ${template.estimated_savings_per_month.toLocaleString()}/month
                        </p>
                      </div>
                    )}

                    {/* Use Template Button */}
                    <button
                      onClick={() => handleUseTemplate(template)}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                    >
                      Use This Template →
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-600 text-center">
            💡 <strong>Tip:</strong> Templates can be customized after selection.
            You'll need to provide a unique playbook ID.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PlaybookTemplateLibrary;
