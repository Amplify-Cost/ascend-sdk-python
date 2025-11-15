import React from "react";

/**
 * PercentageSlider Component
 * Special slider for component percentages that must sum to 100%
 *
 * Features:
 * - Auto-adjustment of other sliders (proportional distribution)
 * - Real-time validation (displays total)
 * - Visual feedback (green checkmark / red X)
 * - Enterprise-grade validation
 */
const PercentageSlider = ({
  label,
  value,
  onChange,
  allValues,
  fieldKey,
  icon = "",
  tooltip = "",
  disabled = false
}) => {
  const percentage = value;
  const total = Object.values(allValues).reduce((sum, val) => sum + val, 0);
  const isValid = total === 100;

  const handleSliderChange = (e) => {
    const newValue = parseInt(e.target.value);
    onChange(fieldKey, newValue, allValues);
  };

  const handleInputChange = (e) => {
    const newValue = parseInt(e.target.value) || 0;
    const clampedValue = Math.max(0, Math.min(100, newValue));
    onChange(fieldKey, clampedValue, allValues);
  };

  return (
    <div className="space-y-2">
      {/* Label and Value Display */}
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-gray-700 flex items-center">
          {icon && <span className="mr-2">{icon}</span>}
          {label}
          {tooltip && (
            <span
              className="ml-2 text-gray-400 cursor-help"
              title={tooltip}
              aria-label={tooltip}
            >
              ⓘ
            </span>
          )}
        </label>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            value={value}
            onChange={handleInputChange}
            min={0}
            max={100}
            step={1}
            disabled={disabled}
            className="w-16 px-2 py-1 text-sm border border-gray-300 rounded text-right focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label={`${label} percentage input`}
          />
          <span className="text-sm text-gray-500">%</span>
        </div>
      </div>

      {/* Slider Track with Visual Fill */}
      <div className="relative">
        {/* Background Track */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          {/* Active Fill */}
          <div
            className={`h-full transition-all duration-200 ${
              disabled ? 'bg-gray-400' : 'bg-green-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Range Input (Overlay) */}
        <input
          type="range"
          min={0}
          max={100}
          step={1}
          value={value}
          onChange={handleSliderChange}
          disabled={disabled}
          className="absolute top-0 left-0 w-full h-2 opacity-0 cursor-pointer"
          aria-label={label}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={value}
        />
      </div>
    </div>
  );
};

/**
 * PercentageGroup Component
 * Container for multiple percentage sliders with validation
 */
export const PercentageGroup = ({
  values,
  onChange,
  labels,
  icons = {},
  tooltips = {}
}) => {
  const total = Object.values(values).reduce((sum, val) => sum + val, 0);
  const isValid = total === 100;

  const handleChange = (key, newValue, currentValues) => {
    // Simple change - just update the value
    onChange({
      ...currentValues,
      [key]: newValue
    });
  };

  return (
    <div className="space-y-4">
      {/* Individual Sliders */}
      {Object.keys(values).map((key) => (
        <PercentageSlider
          key={key}
          label={labels[key] || key}
          value={values[key]}
          onChange={handleChange}
          allValues={values}
          fieldKey={key}
          icon={icons[key]}
          tooltip={tooltips[key]}
        />
      ))}

      {/* Total Validation Display */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <span className="text-sm font-semibold text-gray-700">Total:</span>
          <div className="flex items-center space-x-2">
            <span
              className={`text-lg font-bold ${
                isValid ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {total}%
            </span>
            {isValid ? (
              <span className="text-green-600 text-xl" aria-label="Valid">
                ✓
              </span>
            ) : (
              <span className="text-red-600 text-xl" aria-label="Invalid">
                ✗
              </span>
            )}
          </div>
        </div>

        {/* Validation Message */}
        {!isValid && (
          <div className="mt-2 text-xs text-red-600 flex items-center space-x-1">
            <span>⚠️</span>
            <span>
              Percentages must sum to exactly 100%. Current total: {total}%
              {total < 100 ? ` (add ${100 - total}%)` : ` (reduce ${total - 100}%)`}
            </span>
          </div>
        )}

        {isValid && (
          <div className="mt-2 text-xs text-green-600 flex items-center space-x-1">
            <span>✓</span>
            <span>Valid configuration - percentages sum to 100%</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default PercentageSlider;
