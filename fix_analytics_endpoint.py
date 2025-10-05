with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# Find the engine-metrics endpoint and add fallback
old_metrics = '''async def get_policy_engine_metrics('''

# Check if we need to add error handling
if 'try:' not in content[content.find(old_metrics):content.find(old_metrics)+500]:
    print("Endpoint needs error handling - will add graceful fallback")
else:
    print("Endpoint already has error handling")

# Add fallback for missing mcp_policies table
replacement = '''async def get_policy_engine_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get policy engine performance metrics with graceful fallback"""
    try:
        # Try to get real metrics from policy engine
        from services.cedar_enforcement_service import enforcement_engine
        stats = enforcement_engine.get_stats()
        
        # Try to count active policies
        try:
            active_count = db.query(MCPPolicy).filter(MCPPolicy.is_active == True).count()
        except Exception:
            # Fallback if mcp_policies table doesn't exist
            active_count = len(enforcement_engine.policies)
        
        return {
            "loaded_policies": stats.get("loaded_policies", active_count),
            "total_evaluations": stats.get("total_evaluations", 0),
            "cache_hits": stats.get("cache_hits", 0),
            "denials": stats.get("denials", 0),
            "approvals_required": stats.get("approvals_required", 0),
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.warning(f"Policy metrics unavailable, using fallback: {e}")
        # Return sensible defaults
        return {
            "loaded_policies": 0,
            "total_evaluations": 0,
            "cache_hits": 0,
            "denials": 0,
            "approvals_required": 0,
            "timestamp": datetime.now(UTC).isoformat()
        }'''

