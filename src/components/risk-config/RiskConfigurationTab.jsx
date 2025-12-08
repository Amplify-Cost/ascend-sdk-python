import React, { useState, useEffect } from "react";
import ActiveConfigCard from "./ActiveConfigCard";
import WeightSlider from "./WeightSlider";
import { PercentageGroup } from "./PercentageSlider";
import ValidationResultCard from "./ValidationResultCard";
import ConfigHistoryTable from "./ConfigHistoryTable";

/**
 * RiskConfigurationTab Component
 * Main tab for Risk Scoring Weight Configuration
 *
 * Engineer: Donald King (OW-kai Enterprise)
 * Date: 2025-11-15
 *
 * Features:
 * - Enterprise-grade risk weight configuration
 * - Real-time validation
 * - Configuration versioning
 * - Audit trail
 * - Emergency rollback
 *
 * Aligned with: Splunk Enterprise Security, Palo Alto quality standards
 */
const RiskConfigurationTab = ({ getAuthHeaders }) => {
  // State Management
  const [activeConfig, setActiveConfig] = useState(null);
  const [configDraft, setConfigDraft] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [configHistory, setConfigHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  // ONBOARD-026: Track "no config exists" state for 404 handling
  const [noConfigExists, setNoConfigExists] = useState(false);

  // API Integration
  useEffect(() => {
    fetchActiveConfig();
    fetchConfigHistory();
  }, []);

  const fetchActiveConfig = async () => {
    try {
      const response = await fetch("/api/risk-scoring/config", {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setActiveConfig(data);
        setConfigDraft(data); // Initialize draft with active config
        setNoConfigExists(false);
      } else if (response.status === 404) {
        // ONBOARD-026: 404 means no config exists yet - show create option
        console.log("No risk config exists for this organization - showing create option");
        setNoConfigExists(true);
        setActiveConfig(null);
        setConfigDraft(null);
      } else {
        console.error("Failed to fetch active config:", response.statusText);
      }
    } catch (error) {
      console.error("Error fetching active config:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConfigHistory = async () => {
    try {
      const response = await fetch("/api/risk-scoring/config/history?limit=10", {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setConfigHistory(data);
      }
    } catch (error) {
      console.error("Error fetching config history:", error);
    }
  };

  const validateConfig = async () => {
    if (!configDraft) return;

    try {
      const response = await fetch("/api/risk-scoring/config/validate", {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          config_version: configDraft.config_version,
          algorithm_version: configDraft.algorithm_version,
          environment_weights: configDraft.environment_weights,
          action_weights: configDraft.action_weights,
          resource_multipliers: configDraft.resource_multipliers,
          pii_weights: configDraft.pii_weights,
          component_percentages: configDraft.component_percentages,
          description: configDraft.description
        })
      });

      if (response.ok) {
        const result = await response.json();
        setValidationResult(result);
        return result;
      }
    } catch (error) {
      console.error("Error validating config:", error);
    }
  };

  const saveAndActivateConfig = async () => {
    // Validate first
    const validation = await validateConfig();
    if (!validation || !validation.valid) {
      alert("❌ Configuration has errors. Please fix before saving.");
      return;
    }

    if (!confirm("Are you sure you want to save and activate this configuration? This will affect all risk score calculations.")) {
      return;
    }

    setSaving(true);

    try {
      // Step 1: Create config
      const createResponse = await fetch("/api/risk-scoring/config", {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          config_version: configDraft.config_version,
          algorithm_version: configDraft.algorithm_version,
          environment_weights: configDraft.environment_weights,
          action_weights: configDraft.action_weights,
          resource_multipliers: configDraft.resource_multipliers,
          pii_weights: configDraft.pii_weights,
          component_percentages: configDraft.component_percentages,
          description: configDraft.description
        })
      });

      if (!createResponse.ok) {
        throw new Error("Failed to create configuration");
      }

      const newConfig = await createResponse.json();

      // Step 2: Activate config
      const activateResponse = await fetch(
        `/api/risk-scoring/config/${newConfig.id}/activate`,
        {
          method: "PUT",
          headers: getAuthHeaders()
        }
      );

      if (!activateResponse.ok) {
        throw new Error("Failed to activate configuration");
      }

      alert("✅ Configuration saved and activated successfully!");

      // Refresh data
      await fetchActiveConfig();
      await fetchConfigHistory();
    } catch (error) {
      console.error("Error saving config:", error);
      alert(`❌ Failed to save configuration: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleRollback = async () => {
    if (!confirm("⚠️ Are you sure you want to rollback to factory default? This cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch("/api/risk-scoring/config/rollback-to-default", {
        method: "POST",
        headers: getAuthHeaders()
      });

      if (response.ok) {
        alert("✅ Rolled back to factory default successfully!");
        await fetchActiveConfig();
        await fetchConfigHistory();
      } else {
        throw new Error("Rollback failed");
      }
    } catch (error) {
      console.error("Error during rollback:", error);
      alert(`❌ Rollback failed: ${error.message}`);
    }
  };

  const handleActivateHistory = async (configId) => {
    if (!confirm("Are you sure you want to activate this configuration?")) {
      return;
    }

    try {
      const response = await fetch(
        `/api/risk-scoring/config/${configId}/activate`,
        {
          method: "PUT",
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        alert("✅ Configuration activated successfully!");
        await fetchActiveConfig();
        await fetchConfigHistory();
      }
    } catch (error) {
      console.error("Error activating config:", error);
      alert(`❌ Failed to activate configuration: ${error.message}`);
    }
  };

  // Update Handlers
  const updateEnvironmentWeight = (key, value) => {
    setConfigDraft({
      ...configDraft,
      environment_weights: {
        ...configDraft.environment_weights,
        [key]: value
      }
    });
  };

  const updateActionWeight = (key, value) => {
    setConfigDraft({
      ...configDraft,
      action_weights: {
        ...configDraft.action_weights,
        [key]: value
      }
    });
  };

  const updateResourceMultiplier = (key, value) => {
    setConfigDraft({
      ...configDraft,
      resource_multipliers: {
        ...configDraft.resource_multipliers,
        [key]: value
      }
    });
  };

  const updatePIIWeight = (key, value) => {
    setConfigDraft({
      ...configDraft,
      pii_weights: {
        ...configDraft.pii_weights,
        [key]: value
      }
    });
  };

  const updateComponentPercentages = (newPercentages) => {
    setConfigDraft({
      ...configDraft,
      component_percentages: newPercentages
    });
  };

  // Debounced validation
  useEffect(() => {
    if (configDraft) {
      const timer = setTimeout(() => {
        validateConfig();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [configDraft]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Loading risk configuration...</p>
        </div>
      </div>
    );
  }

  // ONBOARD-026: Show empty state with Create Configuration option for new organizations
  if (noConfigExists) {
    const defaultConfig = {
      config_version: "1.0.0",
      algorithm_version: "1.0.0",
      environment_weights: { production: 100, staging: 60, development: 20 },
      action_weights: { delete: 100, write: 60, read: 20 },
      resource_multipliers: { rds: 1.5, s3: 1.2, lambda: 1.0 },
      pii_weights: { high_sensitivity: 100, medium_sensitivity: 60, low_sensitivity: 20 },
      component_percentages: { environment: 30, data_sensitivity: 30, action_type: 25, operational_context: 15 },
      description: "Initial enterprise risk scoring configuration"
    };

    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-8">
        <div className="text-center max-w-2xl mx-auto">
          <div className="text-6xl mb-4">⚙️</div>
          <h3 className="text-2xl font-semibold text-gray-900 mb-4">No Risk Configuration Found</h3>
          <p className="text-gray-600 mb-6">
            Your organization doesn't have a risk scoring configuration yet.
            Create one to customize how risk scores are calculated for agent actions.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 text-left">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="font-medium text-gray-900 mb-2">🌍 Environment Weights</div>
              <p className="text-sm text-gray-600">
                Configure how production, staging, and development environments affect risk scores.
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="font-medium text-gray-900 mb-2">⚡ Action Weights</div>
              <p className="text-sm text-gray-600">
                Set risk levels for delete, write, and read operations.
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="font-medium text-gray-900 mb-2">☁️ Resource Multipliers</div>
              <p className="text-sm text-gray-600">
                Adjust risk based on resource types like RDS, S3, and Lambda.
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="font-medium text-gray-900 mb-2">🔒 Data Sensitivity</div>
              <p className="text-sm text-gray-600">
                Configure how PII and sensitive data affect risk calculations.
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setConfigDraft(defaultConfig);
              setNoConfigExists(false);
            }}
            className="mt-8 px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-sm"
          >
            ✨ Create Default Configuration
          </button>

          <p className="text-sm text-gray-500 mt-4">
            You can customize all settings after creation.
          </p>
        </div>
      </div>
    );
  }

  if (!configDraft) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-700">❌ Failed to load risk configuration. Please refresh the page.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Section 1: Active Config Overview */}
      <ActiveConfigCard
        config={activeConfig}
        onViewHistory={() => setShowHistory(!showHistory)}
        onRollback={handleRollback}
      />

      {/* Section 2: Weight Configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
        <h3 className="text-lg font-semibold text-gray-800">⚙️ Risk Scoring Weights</h3>

        {/* A. Environment Weights */}
        <div>
          <h4 className="text-md font-semibold text-gray-700 mb-4 flex items-center">
            <span className="mr-2">🌍</span>
            Environment Impact Weights
          </h4>
          <div className="space-y-4">
            <WeightSlider
              label="Production"
              value={configDraft.environment_weights?.production || 0}
              onChange={(val) => updateEnvironmentWeight("production", val)}
              tooltip="Weight for production environment actions (higher = more risky)"
            />
            <WeightSlider
              label="Staging"
              value={configDraft.environment_weights?.staging || 0}
              onChange={(val) => updateEnvironmentWeight("staging", val)}
              tooltip="Weight for staging environment actions"
            />
            <WeightSlider
              label="Development"
              value={configDraft.environment_weights?.development || 0}
              onChange={(val) => updateEnvironmentWeight("development", val)}
              tooltip="Weight for development environment actions (lower = less risky)"
            />
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* B. Action Weights */}
        <div>
          <h4 className="text-md font-semibold text-gray-700 mb-4 flex items-center">
            <span className="mr-2">⚡</span>
            Action Type Weights
          </h4>
          <div className="space-y-4">
            <WeightSlider
              label="Delete"
              value={configDraft.action_weights?.delete || 0}
              onChange={(val) => updateActionWeight("delete", val)}
              tooltip="Weight for delete operations (highest risk)"
            />
            <WeightSlider
              label="Write"
              value={configDraft.action_weights?.write || 0}
              onChange={(val) => updateActionWeight("write", val)}
              tooltip="Weight for write/modify operations"
            />
            <WeightSlider
              label="Read"
              value={configDraft.action_weights?.read || 0}
              onChange={(val) => updateActionWeight("read", val)}
              tooltip="Weight for read operations (lowest risk)"
            />
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* C. Resource Multipliers */}
        <div>
          <h4 className="text-md font-semibold text-gray-700 mb-4 flex items-center">
            <span className="mr-2">☁️</span>
            Resource Type Multipliers
          </h4>
          <div className="space-y-4">
            <WeightSlider
              label="RDS (Database)"
              value={configDraft.resource_multipliers?.rds || 1.0}
              onChange={(val) => updateResourceMultiplier("rds", val)}
              min={0}
              max={3}
              step={0.1}
              tooltip="Multiplier for RDS/database operations"
            />
            <WeightSlider
              label="S3 (Storage)"
              value={configDraft.resource_multipliers?.s3 || 1.0}
              onChange={(val) => updateResourceMultiplier("s3", val)}
              min={0}
              max={3}
              step={0.1}
              tooltip="Multiplier for S3/storage operations"
            />
            <WeightSlider
              label="Lambda (Functions)"
              value={configDraft.resource_multipliers?.lambda || 1.0}
              onChange={(val) => updateResourceMultiplier("lambda", val)}
              min={0}
              max={3}
              step={0.1}
              tooltip="Multiplier for Lambda/serverless operations"
            />
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* D. PII Weights */}
        <div>
          <h4 className="text-md font-semibold text-gray-700 mb-4 flex items-center">
            <span className="mr-2">🔒</span>
            Data Sensitivity Weights
          </h4>
          <div className="space-y-4">
            <WeightSlider
              label="High Sensitivity PII"
              value={configDraft.pii_weights?.high_sensitivity || 0}
              onChange={(val) => updatePIIWeight("high_sensitivity", val)}
              tooltip="Weight for high-sensitivity PII (SSN, financial data)"
            />
            <WeightSlider
              label="Medium Sensitivity PII"
              value={configDraft.pii_weights?.medium_sensitivity || 0}
              onChange={(val) => updatePIIWeight("medium_sensitivity", val)}
              tooltip="Weight for medium-sensitivity PII (email, phone)"
            />
            <WeightSlider
              label="Low Sensitivity PII"
              value={configDraft.pii_weights?.low_sensitivity || 0}
              onChange={(val) => updatePIIWeight("low_sensitivity", val)}
              tooltip="Weight for low-sensitivity PII (name, public data)"
            />
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* E. Component Percentages */}
        <div>
          <h4 className="text-md font-semibold text-gray-700 mb-4 flex items-center">
            <span className="mr-2">📊</span>
            Risk Score Component Distribution
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Adjust how each category contributes to the final risk score. Total must equal 100%.
          </p>
          <PercentageGroup
            values={configDraft.component_percentages || {}}
            onChange={updateComponentPercentages}
            labels={{
              environment: "Environment",
              data_sensitivity: "Data Sensitivity",
              action_type: "Action Type",
              operational_context: "Operational Context"
            }}
            tooltips={{
              environment: "Impact of production/staging/dev environment",
              data_sensitivity: "Impact of PII and sensitive data",
              action_type: "Impact of delete/write/read actions",
              operational_context: "Impact of time, user role, and other factors"
            }}
          />
        </div>
      </div>

      {/* Section 3: Validation */}
      <ValidationResultCard result={validationResult} />

      {/* Section 4: Configuration Details & Actions */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <h4 className="text-lg font-semibold text-gray-800">Configuration Details</h4>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Version
            </label>
            <input
              type="text"
              value={configDraft.config_version || ""}
              onChange={(e) =>
                setConfigDraft({ ...configDraft, config_version: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g., 2.1.0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Algorithm Version
            </label>
            <input
              type="text"
              value={configDraft.algorithm_version || ""}
              onChange={(e) =>
                setConfigDraft({ ...configDraft, algorithm_version: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g., 2.0.0"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description (Optional)
          </label>
          <textarea
            value={configDraft.description || ""}
            onChange={(e) =>
              setConfigDraft({ ...configDraft, description: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            rows={3}
            placeholder="Describe the purpose of this configuration..."
          />
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={() => setConfigDraft(activeConfig)}
            className="px-6 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={validateConfig}
            className="px-6 py-2 text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-300 rounded-md transition-colors"
          >
            🧪 Validate
          </button>
          <button
            onClick={saveAndActivateConfig}
            disabled={!validationResult?.valid || saving}
            className={`px-6 py-2 rounded-md transition-colors ${
              validationResult?.valid && !saving
                ? "bg-green-600 hover:bg-green-700 text-white"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }`}
          >
            {saving ? "Saving..." : "✅ Save & Activate"}
          </button>
        </div>
      </div>

      {/* Section 5: Configuration History */}
      {showHistory && (
        <ConfigHistoryTable
          history={configHistory}
          onActivate={handleActivateHistory}
          loading={false}
        />
      )}
    </div>
  );
};

export default RiskConfigurationTab;
