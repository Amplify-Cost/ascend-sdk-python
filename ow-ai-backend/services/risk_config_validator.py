"""
Enterprise Risk Scoring Configuration Validator
Validates weight ranges, component sums, and business rules

Engineer: Donald King (OW-kai Enterprise)
Created: 2025-11-14
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def validate_risk_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate risk scoring configuration

    Args:
        config: Dictionary with weight configurations

    Returns:
        {
            "valid": bool,
            "errors": List[str],       # Blocking errors
            "warnings": List[str]      # Non-blocking warnings
        }
    """
    errors = []
    warnings = []

    # ==================================================================
    # VALIDATION 1: Component Percentages Must Sum to 100
    # ==================================================================
    comp_pct = config.get('component_percentages', {})
    total_pct = (
        comp_pct.get('environment', 0) +
        comp_pct.get('data_sensitivity', 0) +
        comp_pct.get('action_type', 0) +
        comp_pct.get('operational_context', 0)
    )

    if total_pct != 100:
        errors.append(
            f"Component percentages must sum to 100% (got {total_pct}%)\n"
            f"   Environment: {comp_pct.get('environment')}%, "
            f"Data: {comp_pct.get('data_sensitivity')}%, "
            f"Action: {comp_pct.get('action_type')}%, "
            f"Context: {comp_pct.get('operational_context')}%"
        )

    # ==================================================================
    # VALIDATION 2: Environment Weights (0-35 range)
    # ==================================================================
    env_weights = config.get('environment_weights', {})
    for env, weight in env_weights.items():
        if not isinstance(weight, (int, float)):
            errors.append(f"Environment weight '{env}' must be numeric, got {type(weight)}")
        elif not (0 <= weight <= 35):
            errors.append(f"Environment weight '{env}' must be 0-35, got {weight}")

    # ==================================================================
    # VALIDATION 3: Action Weights (0-25 range)
    # ==================================================================
    action_weights = config.get('action_weights', {})
    for action, weight in action_weights.items():
        if not isinstance(weight, (int, float)):
            errors.append(f"Action weight '{action}' must be numeric, got {type(weight)}")
        elif not (0 <= weight <= 25):
            errors.append(f"Action weight '{action}' must be 0-25, got {weight}")

    # ==================================================================
    # VALIDATION 4: Resource Multipliers (0.5-2.0 range)
    # ==================================================================
    resource_mult = config.get('resource_multipliers', {})
    for resource, mult in resource_mult.items():
        if not isinstance(mult, (int, float)):
            errors.append(f"Resource multiplier '{resource}' must be numeric, got {type(mult)}")
        elif not (0.5 <= mult <= 2.0):
            errors.append(f"Resource multiplier '{resource}' must be 0.5-2.0, got {mult}")

    # ==================================================================
    # VALIDATION 5: PII Weights (0-30 range)
    # ==================================================================
    pii_weights = config.get('pii_weights', {})
    for category, weight in pii_weights.items():
        if not isinstance(weight, (int, float)):
            errors.append(f"PII weight '{category}' must be numeric, got {type(weight)}")
        elif not (0 <= weight <= 30):
            errors.append(f"PII weight '{category}' must be 0-30, got {weight}")

    # ==================================================================
    # WARNINGS: Business Logic Checks (Non-Blocking)
    # ==================================================================

    # Warning 1: Production environment should be high risk
    if env_weights.get('production', 0) < 30:
        warnings.append(
            "Production environment weight < 30 may be too permissive "
            "(recommended: 35 for maximum protection)"
        )

    # Warning 2: Destructive actions should be high risk
    if action_weights.get('delete', 0) < 20:
        warnings.append(
            "Delete action weight < 20 may underestimate risk "
            "(recommended: 25 for dangerous operations)"
        )

    # Warning 3: Development environment should be low risk
    if env_weights.get('development', 0) > 10:
        warnings.append(
            "Development environment weight > 10 may be too restrictive "
            "(recommended: 5 for developer productivity)"
        )

    # Warning 4: Critical resources should have high multipliers
    critical_resources = ['rds', 'dynamodb', 'iam', 'secretsmanager', 'kms']
    for resource in critical_resources:
        if resource_mult.get(resource, 1.0) < 1.1:
            warnings.append(
                f"Critical resource '{resource}' multiplier < 1.1 may underestimate risk "
                f"(recommended: 1.2 for databases, IAM, and secrets management)"
            )

    # ==================================================================
    # RETURN VALIDATION RESULT
    # ==================================================================

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

    if not result['valid']:
        logger.error(f"Risk config validation failed: {len(errors)} errors, {len(warnings)} warnings")
    elif warnings:
        logger.warning(f"Risk config validation passed with {len(warnings)} warnings")
    else:
        logger.info("Risk config validation passed (no errors or warnings)")

    return result
