"""
Input validation utilities.

Banking-level validation for API inputs.
"""

import re
from typing import Dict, Any

from ..exceptions import ValidationError
from ..models import AgentAction


def validate_api_key(api_key: str) -> None:
    """
    Validate API key format.

    Ascend API keys follow the format: ascend_<env>_<random>
    - Production: ascend_prod_...
    - Staging: ascend_stag_...
    - Development: ascend_dev_...

    Legacy format (OW-kai): owkai_<env>_... (also supported)

    Args:
        api_key: API key to validate

    Raises:
        ValidationError: If API key format is invalid
    """
    if not api_key:
        raise ValidationError("API key is required")

    if not isinstance(api_key, str):
        raise ValidationError("API key must be a string")

    # Check length (minimum security requirement)
    if len(api_key) < 20:
        raise ValidationError("API key is too short (minimum 20 characters)")

    # Check format (ascend_ or owkai_ prefix)
    if not (api_key.startswith("ascend_") or api_key.startswith("owkai_")):
        raise ValidationError(
            "Invalid API key format. Expected format: ascend_<env>_<key> "
            "or owkai_<env>_<key> (legacy)"
        )

    # Validate characters (alphanumeric and underscore only)
    if not re.match(r'^[a-zA-Z0-9_]+$', api_key):
        raise ValidationError("API key contains invalid characters")


def validate_action(action: AgentAction) -> None:
    """
    Validate AgentAction before submission.

    Checks required fields and value constraints.

    Args:
        action: AgentAction to validate

    Raises:
        ValidationError: If validation fails
    """
    # Required fields
    if not action.agent_id:
        raise ValidationError("agent_id is required")

    if not action.agent_name:
        raise ValidationError("agent_name is required")

    if not action.action_type:
        raise ValidationError("action_type is required")

    if not action.resource:
        raise ValidationError("resource is required")

    # Type checks
    if not isinstance(action.agent_id, str):
        raise ValidationError("agent_id must be a string")

    if not isinstance(action.agent_name, str):
        raise ValidationError("agent_name must be a string")

    if not isinstance(action.action_type, str):
        raise ValidationError("action_type must be a string")

    if not isinstance(action.resource, str):
        raise ValidationError("resource must be a string")

    # Length constraints
    if len(action.agent_id) > 255:
        raise ValidationError("agent_id too long (max 255 characters)")

    if len(action.agent_name) > 255:
        raise ValidationError("agent_name too long (max 255 characters)")

    if len(action.action_type) > 100:
        raise ValidationError("action_type too long (max 100 characters)")

    if len(action.resource) > 500:
        raise ValidationError("resource too long (max 500 characters)")

    # Optional field validation
    if action.resource_id and not isinstance(action.resource_id, str):
        raise ValidationError("resource_id must be a string")

    if action.action_details and not isinstance(action.action_details, dict):
        raise ValidationError("action_details must be a dictionary")

    if action.context and not isinstance(action.context, dict):
        raise ValidationError("context must be a dictionary")

    if action.risk_indicators and not isinstance(action.risk_indicators, dict):
        raise ValidationError("risk_indicators must be a dictionary")


def validate_action_id(action_id: str) -> None:
    """
    Validate action_id format.

    Args:
        action_id: Action ID to validate

    Raises:
        ValidationError: If action_id format is invalid
    """
    if not action_id:
        raise ValidationError("action_id is required")

    if not isinstance(action_id, str):
        raise ValidationError("action_id must be a string")

    # Action IDs should be numeric (integer primary keys)
    if not action_id.isdigit():
        raise ValidationError("action_id must be numeric")
