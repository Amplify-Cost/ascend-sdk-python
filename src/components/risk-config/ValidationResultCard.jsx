import React from "react";

/**
 * ValidationResultCard Component
 * Displays real-time validation results for risk configuration
 *
 * Shows:
 * - Validation status (Valid/Invalid)
 * - Blocking errors (prevent save)
 * - Non-blocking warnings (allow save with caution)
 */
const ValidationResultCard = ({ result }) => {
  if (!result) {
    return null;
  }

  const { valid, errors = [], warnings = [] } = result;

  return (
    <div
      className={`border rounded-lg p-6 ${
        valid
          ? "bg-green-50 border-green-200"
          : "bg-red-50 border-red-200"
      }`}
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          {valid ? (
            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white text-2xl">✓</span>
            </div>
          ) : (
            <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-white text-2xl">✗</span>
            </div>
          )}
        </div>

        <div className="flex-1">
          <h4 className="text-lg font-semibold mb-2">
            {valid ? (
              <span className="text-green-800">✅ Configuration Valid</span>
            ) : (
              <span className="text-red-800">❌ Configuration Invalid</span>
            )}
          </h4>

          {/* Blocking Errors */}
          {errors.length > 0 && (
            <div className="mb-4">
              <h5 className="text-sm font-semibold text-red-700 mb-2">
                Errors (Must Fix):
              </h5>
              <ul className="space-y-1">
                {errors.map((error, index) => (
                  <li
                    key={index}
                    className="text-sm text-red-700 flex items-start"
                  >
                    <span className="mr-2">🔴</span>
                    <span>{error}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Non-Blocking Warnings */}
          {warnings.length > 0 && (
            <div>
              <h5 className="text-sm font-semibold text-yellow-700 mb-2">
                Warnings (Review Recommended):
              </h5>
              <ul className="space-y-1">
                {warnings.map((warning, index) => (
                  <li
                    key={index}
                    className="text-sm text-yellow-700 flex items-start"
                  >
                    <span className="mr-2">⚠️</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Success Message */}
          {valid && errors.length === 0 && warnings.length === 0 && (
            <p className="text-sm text-green-700">
              All validation checks passed. Configuration is ready to be saved.
            </p>
          )}

          {/* Valid with Warnings */}
          {valid && warnings.length > 0 && (
            <p className="text-sm text-green-700 mt-2">
              Configuration is valid but has {warnings.length} warning(s).
              You may save, but please review warnings above.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ValidationResultCard;
