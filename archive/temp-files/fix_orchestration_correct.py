# Read the file
with open('main.py', 'r') as f:
    lines = f.readlines()

# Find the line BEFORE the assessment except block (around line 1399)
# We want to insert BEFORE "except Exception as assessment_error:"
insert_position = None
for i, line in enumerate(lines):
    if 'except Exception as assessment_error:' in line:
        # Insert 2 lines before (after logger.info, before blank line, before except)
        insert_position = i - 2
        break

if not insert_position:
    print("❌ Could not find insertion point")
    exit(1)

# Orchestration code (16 spaces indentation to match inside try block)
orchestration_code = '''                
                # === ENTERPRISE ORCHESTRATION: Auto-trigger workflows and alerts ===
                # 1. HIGH-RISK ACTIONS → Auto-create Alert
                if data.get("risk_level", "medium") == "high":
                    try:
                        db.execute(text("""
                            INSERT INTO alerts (
                                alert_type, severity, message, agent_action_id, 
                                agent_id, status, timestamp
                            ) VALUES (
                                :alert_type, :severity, :message, :action_id,
                                :agent_id, :status, NOW()
                            )
                        """), {
                            'alert_type': 'High Risk Agent Action',
                            'severity': 'high',
                            'message': f'High-risk action detected: {data["action_type"]} (ID: {action_id})',
                            'action_id': action_id,
                            'agent_id': data["agent_id"],
                            'status': 'new'
                        })
                        db.commit()
                        logger.info(f"✅ Auto-created alert for high-risk action {action_id}")
                    except Exception as alert_error:
                        logger.warning(f"⚠️ Alert creation failed: {alert_error}")
                
                # 2. PENDING ACTIONS → Check for active workflows to trigger
                try:
                    from models import WorkflowConfig, WorkflowExecution
                    active_workflows = db.query(WorkflowConfig).filter(
                        WorkflowConfig.is_active == True
                    ).all()
                    
                    for workflow in active_workflows:
                        trigger_conditions = workflow.trigger_conditions or {}
                        if isinstance(trigger_conditions, str):
                            import json
                            trigger_conditions = json.loads(trigger_conditions)
                        
                        should_trigger = (
                            not trigger_conditions or 
                            data["action_type"] in str(trigger_conditions)
                        )
                        
                        if should_trigger:
                            db.execute(text("""
                                INSERT INTO workflow_executions (
                                    workflow_id, action_id, executed_by, execution_status,
                                    current_stage, started_at, input_data
                                ) VALUES (
                                    :workflow_id, :action_id, :executed_by, :execution_status,
                                    :current_stage, NOW(), :input_data
                                )
                            """), {
                                'workflow_id': workflow.id,
                                'action_id': action_id,
                                'executed_by': current_user.get('email', 'system'),
                                'execution_status': 'in_progress',
                                'current_stage': '0',
                                'input_data': '{}'
                            })
                            db.commit()
                            logger.info(f"✅ Auto-triggered workflow {workflow.id} for action {action_id}")
                except Exception as workflow_error:
                    logger.warning(f"⚠️ Workflow trigger failed: {workflow_error}")
                # === END ORCHESTRATION ===
'''

# Insert the code
lines.insert(insert_position, orchestration_code)

# Write back
with open('main.py', 'w') as f:
    f.writelines(lines)

print(f"✅ Orchestration added at line {insert_position + 1}")
print("📍 Location: INSIDE assessment try block, BEFORE except")
