import re

# Fix the metrics endpoint to use governance_policies instead of MCPPolicy
with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# Replace MCPPolicy queries with governance_policies
old_metrics = '''        # Get actual policy count with fallback
        try:
            active_policies = db.query(MCPPolicy).filter(MCPPolicy.is_active == True).count()
            total_policies = db.query(MCPPolicy).count()
        except Exception as e:
            logger.warning(f"MCPPolicy table not found, using fallback: {e}")
            # Fallback to policy engine in-memory stats
            from services.cedar_enforcement_service import enforcement_engine
            stats = enforcement_engine.get_stats()
            active_policies = stats.get("loaded_policies", 0)
            total_policies = active_policies'''

new_metrics = '''        # Get actual policy count from unified governance_policies
        try:
            from models.governance_models import GovernancePolicy
            active_policies = db.query(GovernancePolicy).filter(
                GovernancePolicy.is_active == True
            ).count()
            total_policies = db.query(GovernancePolicy).count()
        except Exception as e:
            logger.warning(f"Failed to query policies, using in-memory stats: {e}")
            # Fallback to policy engine in-memory stats
            from services.cedar_enforcement_service import enforcement_engine
            stats = enforcement_engine.get_stats()
            active_policies = stats.get("loaded_policies", 0)
            total_policies = active_policies'''

content = content.replace(old_metrics, new_metrics)

# Remove MCPPolicy imports if they exist
content = re.sub(r'from models.*import.*MCPPolicy.*\n', '', content)

with open('routes/unified_governance_routes.py', 'w') as f:
    f.write(content)

print("✅ Unified metrics endpoint to use governance_policies")
