"""
SEC-066: Enterprise Metric Registry
Central catalog with metadata, versioning, and validation

Aligned with:
- Datadog Metrics Summary / Metric Metadata
- Splunk CIM Add-on

Compliance:
- SOC 2 PI-1: Processing Integrity
- SOC 2 CC7.2: System monitoring
- PCI-DSS 10.6: Review logs and security events

All metric access MUST go through this registry.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass

from services.metric_definitions import (
    MetricCIM,
    MetricDefinition,
    MetricCategory,
    MetricUnit,
    MetricValueType,
    METRIC_DEFINITIONS,
    OrgMetricConfig
)

logger = logging.getLogger(__name__)


# =============================================================================
# METRIC VALIDATION ERROR
# =============================================================================

class MetricValidationError(Exception):
    """Raised when a metric value violates its definition constraints"""

    def __init__(self, metric_id: str, value: Any, message: str):
        self.metric_id = metric_id
        self.value = value
        self.message = message
        super().__init__(f"SEC-066 Validation Error [{metric_id}]: {message} (value={value})")


# =============================================================================
# METRIC REGISTRY
# =============================================================================

class MetricRegistry:
    """
    Enterprise Metric Registry

    Central catalog providing:
    - Metric definition lookup
    - Validation against constraints
    - Versioning support
    - Audit trail integration

    Usage:
        registry = MetricRegistry()

        # Get definition
        definition = registry.get(MetricCIM.COST_SAVINGS)

        # Validate value
        registry.validate(MetricCIM.COST_SAVINGS, 150000)

        # Get all metrics in category
        financial_metrics = registry.get_by_category(MetricCategory.FINANCIAL)
    """

    VERSION = "1.0.0"

    def __init__(self):
        """Initialize registry with standard definitions"""
        self._definitions: Dict[str, MetricDefinition] = METRIC_DEFINITIONS.copy()
        self._custom_definitions: Dict[str, MetricDefinition] = {}
        self._deprecated: Set[str] = set()

        logger.info(f"SEC-066: MetricRegistry initialized v{self.VERSION} with {len(self._definitions)} definitions")

    # =========================================================================
    # DEFINITION ACCESS
    # =========================================================================

    def get(self, metric_id: str) -> Optional[MetricDefinition]:
        """
        Get metric definition by ID.

        Args:
            metric_id: The CIM metric identifier

        Returns:
            MetricDefinition or None if not found
        """
        # Check custom definitions first (organization overrides)
        if metric_id in self._custom_definitions:
            return self._custom_definitions[metric_id]

        # Fall back to standard definitions
        return self._definitions.get(metric_id)

    def get_all(self) -> Dict[str, MetricDefinition]:
        """Get all registered metric definitions"""
        all_defs = self._definitions.copy()
        all_defs.update(self._custom_definitions)
        return all_defs

    def get_by_category(self, category: MetricCategory) -> List[MetricDefinition]:
        """Get all metrics in a specific category"""
        return [
            defn for defn in self.get_all().values()
            if defn.category == category
        ]

    def get_by_unit(self, unit: MetricUnit) -> List[MetricDefinition]:
        """Get all metrics with a specific unit"""
        return [
            defn for defn in self.get_all().values()
            if defn.unit == unit
        ]

    def exists(self, metric_id: str) -> bool:
        """Check if a metric is registered"""
        return metric_id in self._definitions or metric_id in self._custom_definitions

    def is_deprecated(self, metric_id: str) -> bool:
        """Check if a metric is deprecated"""
        defn = self.get(metric_id)
        return defn is not None and defn.deprecated

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate(self, metric_id: str, value: Any, raise_on_error: bool = True) -> bool:
        """
        Validate a metric value against its definition constraints.

        Args:
            metric_id: The CIM metric identifier
            value: The value to validate
            raise_on_error: If True, raise MetricValidationError on failure

        Returns:
            True if valid, False if invalid (when raise_on_error=False)

        Raises:
            MetricValidationError: If validation fails and raise_on_error=True
        """
        definition = self.get(metric_id)

        if definition is None:
            if raise_on_error:
                raise MetricValidationError(
                    metric_id, value,
                    f"Unknown metric: {metric_id}"
                )
            return False

        # Check minimum value
        if definition.min_value is not None and value < definition.min_value:
            if raise_on_error:
                raise MetricValidationError(
                    metric_id, value,
                    f"Value {value} below minimum {definition.min_value}"
                )
            logger.warning(f"SEC-066: {metric_id} value {value} below min {definition.min_value}")
            return False

        # Check maximum value
        if definition.max_value is not None and value > definition.max_value:
            if raise_on_error:
                raise MetricValidationError(
                    metric_id, value,
                    f"Value {value} above maximum {definition.max_value}"
                )
            logger.warning(f"SEC-066: {metric_id} value {value} above max {definition.max_value}")
            return False

        # Type validation
        if definition.value_type == MetricValueType.INTEGER:
            if not isinstance(value, (int, float)) or (isinstance(value, float) and not value.is_integer()):
                if raise_on_error:
                    raise MetricValidationError(
                        metric_id, value,
                        f"Expected integer, got {type(value).__name__}"
                    )
                return False

        return True

    def validate_all(self, metrics: Dict[str, Any], raise_on_error: bool = True) -> Dict[str, bool]:
        """
        Validate multiple metrics at once.

        Args:
            metrics: Dictionary of metric_id -> value
            raise_on_error: If True, raise on first error

        Returns:
            Dictionary of metric_id -> validation result
        """
        results = {}
        for metric_id, value in metrics.items():
            try:
                results[metric_id] = self.validate(metric_id, value, raise_on_error)
            except MetricValidationError:
                if raise_on_error:
                    raise
                results[metric_id] = False
        return results

    def clamp(self, metric_id: str, value: float) -> float:
        """
        Clamp a value to the valid range for a metric.

        This is used to enforce constraints without raising errors.
        CRITICAL: Used to prevent negative cost_savings.

        Args:
            metric_id: The CIM metric identifier
            value: The value to clamp

        Returns:
            Clamped value within valid range
        """
        definition = self.get(metric_id)

        if definition is None:
            logger.warning(f"SEC-066: Unknown metric {metric_id}, returning original value")
            return value

        original = value

        if definition.min_value is not None:
            value = max(definition.min_value, value)

        if definition.max_value is not None:
            value = min(definition.max_value, value)

        if value != original:
            logger.info(f"SEC-066: Clamped {metric_id} from {original} to {value}")

        return value

    # =========================================================================
    # CUSTOM DEFINITIONS (Organization Overrides)
    # =========================================================================

    def register_custom(self, definition: MetricDefinition) -> None:
        """
        Register a custom metric definition (organization-specific).

        Args:
            definition: The custom metric definition
        """
        self._custom_definitions[definition.metric_id] = definition
        logger.info(f"SEC-066: Registered custom metric {definition.metric_id}")

    def unregister_custom(self, metric_id: str) -> bool:
        """
        Unregister a custom metric definition.

        Args:
            metric_id: The metric to unregister

        Returns:
            True if removed, False if not found
        """
        if metric_id in self._custom_definitions:
            del self._custom_definitions[metric_id]
            logger.info(f"SEC-066: Unregistered custom metric {metric_id}")
            return True
        return False

    # =========================================================================
    # DOCUMENTATION
    # =========================================================================

    def get_documentation(self) -> List[Dict[str, Any]]:
        """
        Get documentation for all registered metrics.

        Returns:
            List of metric documentation entries for API/UI display
        """
        docs = []
        for metric_id, definition in sorted(self.get_all().items()):
            docs.append({
                "metric_id": metric_id,
                "display_name": definition.display_name,
                "description": definition.description,
                "category": definition.category.value,
                "unit": definition.unit.value,
                "value_type": definition.value_type.value,
                "calculation": definition.calculation,
                "min_value": definition.min_value,
                "max_value": definition.max_value,
                "version": definition.version,
                "deprecated": definition.deprecated
            })
        return docs

    def get_schema(self) -> Dict[str, Any]:
        """
        Get JSON Schema for metric validation.

        Returns:
            JSON Schema compatible dictionary
        """
        properties = {}
        for metric_id, definition in self.get_all().items():
            prop = {
                "description": definition.description,
                "type": "number" if definition.value_type != MetricValueType.STRING else "string"
            }
            if definition.min_value is not None:
                prop["minimum"] = definition.min_value
            if definition.max_value is not None:
                prop["maximum"] = definition.max_value
            properties[metric_id] = prop

        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "OW-kai Metric Schema",
            "description": "SEC-066 Common Information Model metrics",
            "type": "object",
            "properties": properties
        }


# =============================================================================
# GLOBAL REGISTRY INSTANCE
# =============================================================================

# Singleton instance for application-wide access
_registry_instance: Optional[MetricRegistry] = None


def get_metric_registry() -> MetricRegistry:
    """
    Get the global MetricRegistry instance.

    Usage:
        from services.metric_registry import get_metric_registry

        registry = get_metric_registry()
        registry.validate(MetricCIM.COST_SAVINGS, 150000)
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = MetricRegistry()
    return _registry_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_metric(metric_id: str, value: Any) -> bool:
    """Convenience function to validate a single metric"""
    return get_metric_registry().validate(metric_id, value, raise_on_error=False)


def clamp_metric(metric_id: str, value: float) -> float:
    """Convenience function to clamp a metric value"""
    return get_metric_registry().clamp(metric_id, value)


def get_metric_definition(metric_id: str) -> Optional[MetricDefinition]:
    """Convenience function to get a metric definition"""
    return get_metric_registry().get(metric_id)
