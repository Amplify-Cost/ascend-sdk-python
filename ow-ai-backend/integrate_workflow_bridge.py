with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# 1. Add import at the top (after other service imports)
import_line = "from services.workflow_bridge import WorkflowBridge"
if import_line not in content:
    # Find the line with cedar_enforcement_service import
    content = content.replace(
        "from services.cedar_enforcement_service import enforcement_engine, policy_compiler",
        "from services.cedar_enforcement_service import enforcement_engine, policy_compiler\n" + import_line
    )
    print("✅ Added WorkflowBridge import")

# 2. Add workflow creation after policy evaluation
old_return = '''        logger.info(f"Policy enforcement: {result['decision']} for {action_data.get('action_type')} on {action_data.get('target')}")
        
        return {
            "success": True,
            **result
        }'''

new_return = '''        logger.info(f"Policy enforcement: {result['decision']} for {action_data.get('action_type')} on {action_data.get('target')}")
        
        # Create workflow if approval required
        if result.get("decision") == "REQUIRE_APPROVAL":
            try:
                bridge = WorkflowBridge(db)
                workflow_execution = bridge.create_workflow_execution(
                    action_data=action_data,
                    risk_score=action_data.get("risk_score", 50),
                    policies_triggered=result.get("policies_triggered", [])
                )
                result["workflow_execution_id"] = workflow_execution.id
                result["workflow_id"] = workflow_execution.workflow_id
                logger.info(f"✅ Created workflow execution {workflow_execution.id}")
            except Exception as e:
                logger.error(f"❌ Workflow creation failed: {e}")
                # Don't fail the whole request if workflow creation fails
        
        return {
            "success": True,
            **result
        }'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print("✅ Added workflow creation logic")
else:
    print("❌ Return statement not found")
    exit(1)

with open('routes/unified_governance_routes.py', 'w') as f:
    f.write(content)

print("✅ Integration complete")
