import React from "react";

/**
 * WeightSlider Component
 * Enterprise-grade reusable slider for risk weight configuration
 *
 * Supports:
 * - Range: 0-100 (integers)
 * - Real-time validation
 * - Visual feedback
 * - Keyboard navigation (WCAG 2.1 AA)
 */
const WeightSlider = ({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  icon = "",
  tooltip = "",
  disabled = false,
  warning = null
}) => {
  const percentage = ((value - min) / (max - min)) * 100;

  const handleSliderChange = (e) => {
    const newValue = parseInt(e.target.value);
    onChange(newValue);
  };

  const handleInputChange = (e) => {
    const newValue = parseInt(e.target.value) || min;
    const clampedValue = Math.max(min, Math.min(max, newValue));
    onChange(clampedValue);
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
            min={min}
            max={max}
            step={step}
            disabled={disabled}
            className="w-16 px-2 py-1 text-sm border border-gray-300 rounded text-right focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label={`${label} numeric input`}
          />
        </div>
      </div>

      {/* Slider Track with Visual Fill */}
      <div className="relative">
        {/* Background Track */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          {/* Active Fill */}
          <div
            className={`h-full transition-all duration-200 ${
              disabled ? 'bg-gray-400' : 'bg-blue-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Range Input (Overlay) */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={handleSliderChange}
          disabled={disabled}
          className="absolute top-0 left-0 w-full h-2 opacity-0 cursor-pointer"
          aria-label={label}
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={value}
        />
      </div>

      {/* Warning Message */}
      {warning && (
        <div className="flex items-start space-x-1 text-xs text-yellow-600">
          <span>⚠️</span>
          <span>{warning}</span>
        </div>
      )}
    </div>
  );
};

export default WeightSlider;
