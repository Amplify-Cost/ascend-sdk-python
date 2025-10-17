"""
Enterprise Policy Enforcement using Cedar-like structured rules
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from services.condition_engine import condition_engine
import json
import re
from services.action_taxonomy import actions_match, resource_matches

class PolicyValidationError(Exception):
    """Raised when policy validation fails"""
    pass

class PolicyValidator:
    """Validate policy inputs and structure"""
    
    @staticmethod
    def validate_natural_language(text: str) -> tuple:
        """Validate natural language policy input"""
        errors = []
        
        if not text or not text.strip():
            errors.append("Policy text cannot be empty")
        elif len(text.strip()) < 10:
            errors.append("Policy too short - provide more details (min 10 characters)")
        elif len(text) > 5000:
            errors.append("Policy too long - maximum 5000 characters")
        
        # Check for at least one action indicator
        action_keywords = ["block", "deny", "allow", "permit", "require", "approval", 
                          "read", "write", "delete", "modify", "create", "execute", "prevent"]
        if not any(kw in text.lower() for kw in action_keywords):
            errors.append("Policy must specify an action (e.g., block, allow, require approval)")
        
        return (len(errors) == 0, errors)

class CedarStylePolicy:
    """Cedar-style policy structure"""
    def __init__(self, policy_data: Dict[str, Any]):
        self.id = policy_data.get("id")
        self.effect = policy_data.get("effect", "deny")
        self.principal = policy_data.get("principal", "ai_agent:*")
        self.actions = policy_data.get("actions", [])
        self.resources = policy_data.get("resources", [])
        self.conditions = policy_data.get("conditions", {})
        self.natural_language = policy_data.get("natural_language", "")

class PolicyCompiler:
    """Compile natural language policies to Cedar-style structured rules"""
    
    @staticmethod
    def compile(natural_language: str, risk_level: str = "medium") -> Dict[str, Any]:
        """
        Convert natural language policy to structured Cedar-style policy
        
        Args:
            natural_language: Policy description in plain English
            risk_level: "low", "medium", or "high"
            
        Raises:
            PolicyValidationError: If input is invalid
        """
        # Validate input
        is_valid, errors = PolicyValidator.validate_natural_language(natural_language)
        if not is_valid:
            raise PolicyValidationError(f"Invalid policy: {'; '.join(errors)}")
        
        text_lower = natural_language.lower()
        
        # Determine effect
        if any(word in text_lower for word in ["block", "deny", "prevent", "prohibit"]):
            effect = "deny"
        elif any(word in text_lower for word in ["require approval", "manager approval", "human review"]):
            effect = "require_approval"
        else:
            effect = "permit"
            
        # Extract actions
        actions = []
        action_map = {
            "delete": ["delete", "remove", "drop"],
            "modify": ["modify", "update", "change", "edit", "alter"],
            "read": ["read", "access", "view", "query"],
            "create": ["create", "add", "insert"],
            "execute": ["execute", "run", "trigger"],
            "export": ["export", "download", "extract"],
            "write": ["write", "put"]
        }
        
        for action_type, keywords in action_map.items():
            if any(keyword in text_lower for keyword in keywords):
                actions.append(action_type)
                
        # Extract resources
        resources = []
        resource_map = {
            "database:production:*": ["production database", "prod db", "production data"],
            "s3://*": ["s3", "s3 bucket", "storage bucket"],
            "database:*": ["database", "db"],
            "financial:*": ["financial", "payment", "transaction", "money"],
            "pii:*": ["pii", "personal data", "user data", "customer data"]
        }
        
        for resource_pattern, keywords in resource_map.items():
            if any(keyword in text_lower for keyword in keywords):
                resources.append(resource_pattern)
                
        # Build conditions
        conditions = {}
        if "production" in text_lower or "prod" in text_lower:
            conditions["environment"] = "production"
        if risk_level == "high":
            conditions["min_approvers"] = 2
        elif risk_level == "medium":
            conditions["min_approvers"] = 1
            
        return {
            "effect": effect,
            "principal": "ai_agent:*",
            "actions": actions or ["*"],
            "resources": resources or ["*"],
            "conditions": conditions,
            "natural_language": natural_language,
            "risk_level": risk_level
        }

class EnforcementEngine:
    """High-performance policy evaluation engine"""
    
    def __init__(self):
        self.policies: List[CedarStylePolicy] = []
        self.evaluation_cache = {}
        self.stats = {
            "total_evaluations": 0,
            "cache_hits": 0,
            "denials": 0,
            "approvals_required": 0
        }
        
    def load_policies(self, policies: List[Dict[str, Any]]):
        """Load compiled policies into engine"""
        self.policies = [CedarStylePolicy(p) for p in policies]
        self.evaluation_cache.clear()
        
    def evaluate(self, 
                 principal: str,
                 action: str,
                 resource: str,
                 context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Evaluate action against all policies with error handling
        
        Returns: {decision: "ALLOW|DENY|REQUIRE_APPROVAL", policies_triggered: [...]}
        """
        self.stats["total_evaluations"] += 1
        
        # Validate inputs - fail closed if invalid
        if not principal or not action or not resource:
            import logging
            logging.getLogger(__name__).warning(
                f"Invalid inputs to evaluate: principal={principal}, action={action}, resource={resource}"
            )
            return {
                "decision": "DENY",
                "allowed": False,
                "policies_triggered": [],
                "error": "Invalid input parameters",
                "timestamp": datetime.now(UTC).isoformat()
            }
        
        # Check cache
        cache_key = f"{principal}:{action}:{resource}"
        if cache_key in self.evaluation_cache:
            self.stats["cache_hits"] += 1
            return self.evaluation_cache[cache_key]
            
        context = context or {}
        triggered_policies = []
        final_decision = "ALLOW"
        
        for policy in self.policies:
            try:
                if self._matches_policy(policy, principal, action, resource, context):
                    triggered_policies.append({
                        "policy_id": policy.id,
                        "policy_name": policy.natural_language,
                        "effect": policy.effect
                    })
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(
                    f"Error evaluating policy {policy.id}: {str(e)}"
                )
                # Skip failed policy, continue with others
                continue
                
                # Deny takes precedence
                if policy.effect == "deny":
                    final_decision = "DENY"
                    self.stats["denials"] += 1
                    break
                elif policy.effect == "require_approval" and final_decision == "ALLOW":
                    final_decision = "REQUIRE_APPROVAL"
                    self.stats["approvals_required"] += 1
                    
        result = {
            "decision": final_decision,
            "allowed": final_decision == "ALLOW",
            "policies_triggered": triggered_policies,
            "evaluation_time_ms": 0,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Cache result
        self.evaluation_cache[cache_key] = result
        return result
        
# Add import at the top (after existing imports)

    def _matches_policy(self, 
                       policy: CedarStylePolicy,
                       principal: str,
                       action: str,
                       resource: str,
                       context: Dict) -> bool:
        """
        Check if action matches policy conditions - ENTERPRISE VERSION with DSL
        
        Now supports:
        - Rich operators (in, contains, regex, numeric comparisons)
        - Boolean logic (all_of, any_of, none_of)
        - Required vs optional fields
        - Backwards compatibility with simple conditions
        """
        
        # Match principal
        if policy.principal != "ai_agent:*" and policy.principal != principal:
            return False
            
        # Match action using semantic taxonomy
        action_matches_found = False
        for policy_action in policy.actions:
            if actions_match(policy_action, action):
                action_matches_found = True
                break
        if not action_matches_found:
            return False
            
        # Match resource using hierarchy
        resource_matches_found = False
        for policy_resource in policy.resources:
            if resource_matches(policy_resource, resource):
                resource_matches_found = True
                break
        if not resource_matches_found:
            return False
            
        # Match conditions using enterprise condition engine
        if not policy.conditions:
            return True  # No conditions = always match
        
        # Check if conditions use new DSL format or legacy format
        if self._is_legacy_conditions(policy.conditions):
            # Legacy format: simple key-value matching
            return self._match_legacy_conditions(policy.conditions, context)
        else:
            # New DSL format: use condition engine
            return condition_engine.evaluate(policy.conditions, context)
    
    def _is_legacy_conditions(self, conditions: Dict) -> bool:
        """Check if conditions use legacy simple format"""
        if not isinstance(conditions, dict):
            return True
        
        # If has DSL keywords, it's not legacy
        if any(key in conditions for key in ["all_of", "any_of", "none_of", "field", "operator"]):
            return False
        
        return True
    
    def _match_legacy_conditions(self, conditions: Dict, context: Dict) -> bool:
        """
        Match legacy simple conditions (backwards compatibility)
        
        Format: {"environment": "production", "acl_contains": "public-read"}
        All conditions must match (AND logic)
        """
        for condition_key, condition_value in conditions.items():
            context_val = context.get(condition_key)
            
            # Handle list conditions (OR logic for legacy compatibility)
            if isinstance(condition_value, list):
                # Special handling for "*_contains" keys - do substring matching
                if condition_key.endswith("_contains") and isinstance(context_val, str):
                    # Check if any policy value is contained in the context value
                    if not any(policy_val in context_val for policy_val in condition_value):
                        return False
                else:
                    # Exact match for non-contains keys
                    if context_val not in condition_value:
                        return False
            else:
                if context_val != condition_value:
                    return False
                    
        return True
    def get_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics"""
        cache_hit_rate = (self.stats["cache_hits"] / max(self.stats["total_evaluations"], 1)) * 100
        return {
            **self.stats,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "loaded_policies": len(self.policies)
        }

# Global engine instance
enforcement_engine = EnforcementEngine()
policy_compiler = PolicyCompiler()
