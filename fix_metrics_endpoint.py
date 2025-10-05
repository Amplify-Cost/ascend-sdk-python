with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# Find and replace the metrics function to add try-catch around DB queries
old_code = '''        # Get actual policy count
        active_policies = db.query(MCPPolicy).filter(MCPPolicy.is_active == True).count()
        total_policies = db.query(MCPPolicy).count()'''

new_code = '''        # Get actual policy count with fallback
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

content = content.replace(old_code, new_code)

with open('routes/unified_governance_routes.py', 'w') as f:
    f.write(content)

print("✅ Fixed metrics endpoint with graceful fallback")
