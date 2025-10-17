import re

# Read the MCP governance routes
with open('routes/mcp_governance_routes.py', 'r') as f:
    content = f.read()

# Find the incomplete unified governance function and complete it
old_implementation = r'''# Note: In a complete implementation, you would also query agent actions.*?all_actions = mcp_actions'''

new_implementation = '''# ENTERPRISE UNIFIED GOVERNANCE: Query both MCP and agent actions
        
        # Get agent actions from the main authorization system
        agent_actions = []
        
        agent_query = db.execute(text("""
            SELECT id, agent_id, action_type, description, risk_level, risk_score, 
                   status, created_at, updated_at, approved, reviewed_by
            FROM agent_actions
            WHERE status IN ('pending', 'pending_approval', 'approved', 'submitted')
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        
        for row in agent_query:
            agent_actions.append({
                'id': str(row[0]),
                'action_type': 'agent_action',
                'created_at': row[7].isoformat() if row[7] else None,
                'updated_at': row[8].isoformat() if row[8] else None,
                'title': f"Agent {row[1]}: {row[2]}",
                'description': row[3] or "Agent security action",
                'agent_id': row[1],
                'risk_level': row[4] or 'medium',
                'risk_score': float(row[5]) if row[5] else 50.0,
                'status': row[6] or 'pending',
                'approved': bool(row[9]) if row[9] is not None else False,
                'reviewed_by': row[10],
                'enterprise_compliant': True,
                'source': 'agent_actions'
            })
        
        # Merge MCP and agent actions
        all_actions = mcp_actions + agent_actions'''

# Apply the replacement
content = re.sub(old_implementation, new_implementation, content, flags=re.DOTALL)

# Write the unified implementation
with open('routes/mcp_governance_routes.py', 'w') as f:
    f.write(content)

print("Enterprise unified governance implementation complete!")
