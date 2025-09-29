"""
Enterprise Policy Enforcement using Cedar-like structured rules
Since py-cedar doesn't exist, we'll implement Cedar-style evaluation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

class CedarStylePolicy:
    """Cedar-style policy structure"""
    def __init__(self, policy_data: Dict[str, Any]):
        self.id = policy_data.get("id")
        self.effect = policy_data.get("effect", "deny")  # permit or deny
        self.principal = policy_data.get("principal", "ai_agent:*")
        self.actions = policy_data.get("actions", [])
        self.resources = policy_data.get("resources", [])
        self.conditions = policy_data.get("conditions", {})
        self.natural_language = policy_data.get("description", "")
        
class PolicyCompiler:
    """Compile natural language policies to Cedar-style structured rules"""
    
    @staticmethod
    def compile(natural_language: str, risk_level: str = "medium") -> Dict[str, Any]:
        """Convert natural language policy to structured Cedar-style policy"""
        
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
            "export": ["export", "download", "extract"]
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
        Evaluate action against all policies
        Returns: {decision: "ALLOW|DENY|REQUIRE_APPROVAL", policies_triggered: [...]}
        """
        self.stats["total_evaluations"] += 1
        
        # Check cache
        cache_key = f"{principal}:{action}:{resource}"
        if cache_key in self.evaluation_cache:
            self.stats["cache_hits"] += 1
            return self.evaluation_cache[cache_key]
            
        context = context or {}
        triggered_policies = []
        final_decision = "ALLOW"
        
        for policy in self.policies:
            if self._matches_policy(policy, principal, action, resource, context):
                triggered_policies.append({
                    "policy_id": policy.id,
                    "policy_name": policy.natural_language,
                    "effect": policy.effect
                })
                
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
            "evaluation_time_ms": 0,  # Will be calculated by caller
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache result
        self.evaluation_cache[cache_key] = result
        return result
        
    def _matches_policy(self, 
                       policy: CedarStylePolicy,
                       principal: str,
                       action: str,
                       resource: str,
                       context: Dict) -> bool:
        """Check if action matches policy conditions"""
        
        # Match principal (simplified - in production use proper pattern matching)
        if policy.principal != "ai_agent:*" and policy.principal != principal:
            return False
            
        # Match action
        action_matches = False
        for policy_action in policy.actions:
            if policy_action == "*" or policy_action in action.lower():
                action_matches = True
                break
        if not action_matches:
            return False
            
        # Match resource
        resource_matches = False
        for policy_resource in policy.resources:
            if policy_resource == "*":
                resource_matches = True
                break
            # Pattern matching: "database:production:*" matches "database:production:users"
            pattern = policy_resource.replace("*", ".*")
            if re.match(pattern, resource.lower()):
                resource_matches = True
                break
        if not resource_matches:
            return False
            
        # Match conditions
        for condition_key, condition_value in policy.conditions.items():
            if context.get(condition_key) != condition_value:
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
