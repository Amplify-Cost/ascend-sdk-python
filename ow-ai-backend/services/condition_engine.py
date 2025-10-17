"""
Enterprise Condition Engine - Formal DSL for Policy Conditions

Provides rich boolean logic with operators for complex policy expressions.
Designed for enterprise security teams while maintaining accessibility.
"""
from typing import Dict, Any, List, Union, Optional
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConditionOperator:
    """Supported operators for condition evaluation"""
    
    @staticmethod
    def equals(context_value: Any, expected: Any) -> bool:
        """Exact match"""
        return context_value == expected
    
    @staticmethod
    def not_equals(context_value: Any, expected: Any) -> bool:
        """Not equal"""
        return context_value != expected
    
    @staticmethod
    def in_list(context_value: Any, values: List[Any]) -> bool:
        """Value in list (OR logic)"""
        return context_value in values
    
    @staticmethod
    def not_in(context_value: Any, values: List[Any]) -> bool:
        """Value not in list"""
        return context_value not in values
    
    @staticmethod
    def contains(context_value: Any, substring: str) -> bool:
        """String contains substring"""
        return substring in str(context_value)
    
    @staticmethod
    def not_contains(context_value: Any, substring: str) -> bool:
        """String does not contain substring"""
        return substring not in str(context_value)
    
    @staticmethod
    def starts_with(context_value: Any, prefix: str) -> bool:
        """String starts with prefix"""
        return str(context_value).startswith(prefix)
    
    @staticmethod
    def ends_with(context_value: Any, suffix: str) -> bool:
        """String ends with suffix"""
        return str(context_value).endswith(suffix)
    
    @staticmethod
    def regex_match(context_value: Any, pattern: str) -> bool:
        """Regex pattern match"""
        try:
            return bool(re.match(pattern, str(context_value)))
        except re.error:
            logger.error(f"Invalid regex pattern: {pattern}")
            return False
    
    @staticmethod
    def greater_than(context_value: Any, threshold: Union[int, float]) -> bool:
        """Numeric greater than"""
        try:
            return float(context_value) > float(threshold)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def less_than(context_value: Any, threshold: Union[int, float]) -> bool:
        """Numeric less than"""
        try:
            return float(context_value) < float(threshold)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def greater_equal(context_value: Any, threshold: Union[int, float]) -> bool:
        """Numeric greater than or equal"""
        try:
            return float(context_value) >= float(threshold)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def less_equal(context_value: Any, threshold: Union[int, float]) -> bool:
        """Numeric less than or equal"""
        try:
            return float(context_value) <= float(threshold)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def between(context_value: Any, range_vals: List[Union[int, float]]) -> bool:
        """Value between two numbers (inclusive)"""
        try:
            val = float(context_value)
            return range_vals[0] <= val <= range_vals[1]
        except (ValueError, TypeError, IndexError):
            return False
    
    @staticmethod
    def exists(context_value: Any, _: Any = None) -> bool:
        """Field exists (not None)"""
        return context_value is not None
    
    @staticmethod
    def not_exists(context_value: Any, _: Any = None) -> bool:
        """Field does not exist (is None)"""
        return context_value is None

# Operator registry
OPERATORS = {
    "equals": ConditionOperator.equals,
    "not_equals": ConditionOperator.not_equals,
    "in": ConditionOperator.in_list,
    "not_in": ConditionOperator.not_in,
    "contains": ConditionOperator.contains,
    "not_contains": ConditionOperator.not_contains,
    "starts_with": ConditionOperator.starts_with,
    "ends_with": ConditionOperator.ends_with,
    "regex": ConditionOperator.regex_match,
    "greater_than": ConditionOperator.greater_than,
    "less_than": ConditionOperator.less_than,
    "greater_equal": ConditionOperator.greater_equal,
    "less_equal": ConditionOperator.less_equal,
    "between": ConditionOperator.between,
    "exists": ConditionOperator.exists,
    "not_exists": ConditionOperator.not_exists,
}

class ConditionEngine:
    """
    Enterprise condition evaluation engine
    
    Supports:
    - Rich operators (equals, in, contains, regex, numeric comparisons)
    - Boolean logic (all_of, any_of, none_of)
    - Required vs optional fields
    - Nested conditions
    """
    
    def __init__(self):
        self.operators = OPERATORS
    
    def evaluate(self, condition: Union[Dict, List], context: Dict[str, Any]) -> bool:
        """
        Evaluate condition against context
        
        Args:
            condition: Condition definition (simple, complex, or legacy format)
            context: Action context to evaluate against
            
        Returns:
            True if condition matches, False otherwise
        """
        # Handle legacy simple format (backwards compatibility)
        if not isinstance(condition, dict):
            return True  # No conditions = always match
        
        # Check for boolean logic groups
        if "all_of" in condition:
            return self._evaluate_all_of(condition["all_of"], context)
        
        if "any_of" in condition:
            return self._evaluate_any_of(condition["any_of"], context)
        
        if "none_of" in condition:
            return not self._evaluate_any_of(condition["none_of"], context)
        
        # Single condition evaluation
        return self._evaluate_single_condition(condition, context)
    
    def _evaluate_all_of(self, conditions: List[Dict], context: Dict[str, Any]) -> bool:
        """All conditions must be true (AND logic)"""
        if not conditions:
            return True
        
        for condition in conditions:
            if not self.evaluate(condition, context):
                return False
        return True
    
    def _evaluate_any_of(self, conditions: List[Dict], context: Dict[str, Any]) -> bool:
        """At least one condition must be true (OR logic)"""
        if not conditions:
            return False
        
        for condition in conditions:
            if self.evaluate(condition, context):
                return True
        return False
    
    def _evaluate_single_condition(self, condition: Dict, context: Dict[str, Any]) -> bool:
        """
        Evaluate single condition
        
        Format:
        {
            "field": "environment",
            "operator": "in",
            "value": ["production", "staging"],
            "required": true
        }
        """
        field = condition.get("field")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("value")
        required = condition.get("required", False)
        
        # Get actual value from context
        context_value = context.get(field)
        
        # Handle required fields
        if required and context_value is None:
            logger.debug(f"Required field '{field}' not present in context")
            return False
        
        # If field not required and not present, condition passes
        if not required and context_value is None:
            return True
        
        # Get operator function
        operator_func = self.operators.get(operator)
        if not operator_func:
            logger.error(f"Unknown operator: {operator}")
            return False
        
        # Evaluate
        try:
            result = operator_func(context_value, expected_value)
            logger.debug(f"Condition evaluation: {field} {operator} {expected_value} = {result}")
            return result
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def validate_condition(self, condition: Union[Dict, List]) -> tuple[bool, Optional[str]]:
        """
        Validate condition syntax
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(condition, dict):
            return True, None
        
        # Check boolean groups
        if "all_of" in condition:
            if not isinstance(condition["all_of"], list):
                return False, "'all_of' must be a list"
            for sub_condition in condition["all_of"]:
                valid, error = self.validate_condition(sub_condition)
                if not valid:
                    return False, f"Invalid condition in 'all_of': {error}"
            return True, None
        
        if "any_of" in condition:
            if not isinstance(condition["any_of"], list):
                return False, "'any_of' must be a list"
            for sub_condition in condition["any_of"]:
                valid, error = self.validate_condition(sub_condition)
                if not valid:
                    return False, f"Invalid condition in 'any_of': {error}"
            return True, None
        
        if "none_of" in condition:
            if not isinstance(condition["none_of"], list):
                return False, "'none_of' must be a list"
            for sub_condition in condition["none_of"]:
                valid, error = self.validate_condition(sub_condition)
                if not valid:
                    return False, f"Invalid condition in 'none_of': {error}"
            return True, None
        
        # Validate single condition
        if "field" not in condition:
            return False, "Condition must have 'field'"
        
        operator = condition.get("operator", "equals")
        if operator not in self.operators:
            return False, f"Unknown operator '{operator}'. Valid operators: {list(self.operators.keys())}"
        
        if "value" not in condition and operator not in ["exists", "not_exists"]:
            return False, f"Condition with operator '{operator}' must have 'value'"
        
        return True, None

# Global engine instance
condition_engine = ConditionEngine()
