with open('services/cedar_enforcement_service.py', 'r') as f:
    content = f.read()

# Add error handling to evaluate method
old_evaluate = '''    def evaluate(self, 
                 principal: str,
                 action: str,
                 resource: str,
                 context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Evaluate action against all policies
        Returns: {decision: "ALLOW|DENY|REQUIRE_APPROVAL", policies_triggered: [...]}
        """
        self.stats["total_evaluations"] += 1
        
        # Check cache'''

new_evaluate = '''    def evaluate(self, 
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
        
        # Check cache'''

content = content.replace(old_evaluate, new_evaluate)

# Wrap policy matching in try-except
old_loop = '''        for policy in self.policies:
            if self._matches_policy(policy, principal, action, resource, context):
                triggered_policies.append({
                    "policy_id": policy.id,
                    "policy_name": policy.natural_language,
                    "effect": policy.effect
                })'''

new_loop = '''        for policy in self.policies:
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
                continue'''

content = content.replace(old_loop, new_loop)

with open('services/cedar_enforcement_service.py', 'w') as f:
    f.write(content)

print("✅ Added error handling to evaluate()")
