"""
Enterprise Policy Enforcement using Cedar-like structured rules
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
from services.action_taxonomy import actions_match, resource_matches

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
            "evaluation_time_ms": 0,
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
        """Check if action matches policy conditions - ENTERPRISE VERSION"""
        
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 Checking policy {policy.id}: effect={policy.effect}")
        logger.info(f"   Policy actions: {policy.actions}")
        logger.info(f"   Policy resources: {policy.resources}")
        logger.info(f"   Actual action: {action}")
        logger.info(f"   Actual resource: {resource}")
        
        # Match principal
        if policy.principal != "ai_agent:*" and policy.principal != principal:
            logger.info(f"   ❌ Principal mismatch")
            return False
            
        # Match action using semantic taxonomy
        action_matches_found = False
        for policy_action in policy.actions:
            if actions_match(policy_action, action):
                action_matches_found = True
                logger.info(f"   ✅ Action matched: {policy_action}")
                break
        if not action_matches_found:
            logger.info(f"   ❌ No action match")
            return False
            
        # Match resource using hierarchy
        resource_matches_found = False
        for policy_resource in policy.resources:
            if resource_matches(policy_resource, resource):
                resource_matches_found = True
                logger.info(f"   ✅ Resource matched: {policy_resource}")
                break
        if not resource_matches_found:
            logger.info(f"   ❌ No resource match")
            return False
            
        # Match conditions
        for condition_key, condition_value in policy.conditions.items():
            context_val = context.get(condition_key)
            # Handle list conditions
            if isinstance(condition_value, list):
                if context_val not in condition_value:
                    logger.info(f"   ❌ Condition mismatch: {condition_key}")
                    return False
            else:
                if context_val != condition_value:
                    logger.info(f"   ❌ Condition mismatch: {condition_key}")
                    return False
        
        logger.info(f"   ✅✅✅ POLICY MATCHED - Effect: {policy.effect}")
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
