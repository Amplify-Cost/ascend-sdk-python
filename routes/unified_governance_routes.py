
@router.get("/dashboard/pending-approvals")
async def get_pending_approvals(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workflows pending approval for current user"""
    from datetime import datetime, timedelta
    from models import WorkflowExecution
    
    user_role = current_user.get("role", "user")
    
    # Query using correct column names
    query = db.query(WorkflowExecution).filter(
        WorkflowExecution.current_stage.in_(["pending_stage_1", "pending_stage_2", "pending_stage_3"])
    )
    
    if user_role == "security":
        query = query.filter(WorkflowExecution.current_stage == "pending_stage_1")
    elif user_role == "operations":
        query = query.filter(WorkflowExecution.current_stage.in_(["pending_stage_1", "pending_stage_2"]))
    
    workflows = query.order_by(WorkflowExecution.started_at.desc()).all()
    
    result = []
    for wf in workflows:
        sla_hours_remaining = None
        # WorkflowExecution doesn't have sla_deadline in this model
        # Calculate based on started_at + 24 hours as default
        if wf.started_at:
            deadline = wf.started_at + timedelta(hours=24)
            sla_hours_remaining = (deadline - datetime.utcnow()).total_seconds() / 3600
        
        result.append({
            "workflow_id": wf.id,
            "workflow_execution_id": wf.id,
            "action_type": wf.workflow_id or "unknown_action",  # workflow_id is the template
            "risk_score": 75,  # Default since not in WorkflowExecution model
            "current_stage": wf.current_stage,
            "required_role": "security" if wf.current_stage == "pending_stage_1" else "operations" if wf.current_stage == "pending_stage_2" else "executive",
            "sla_hours_remaining": sla_hours_remaining,
            "sla_status": "critical" if sla_hours_remaining and sla_hours_remaining < 1 else "warning" if sla_hours_remaining and sla_hours_remaining < 4 else "normal",
            "can_approve": user_role in ["admin", "operations", "executive"] if wf.current_stage == "pending_stage_2" else user_role in ["admin", "security"] if wf.current_stage == "pending_stage_1" else user_role == "admin",
            "created_at": wf.started_at.isoformat() if wf.started_at else datetime.utcnow().isoformat(),
            "agent_id": wf.executed_by or "system"
        })
    
    return {
        "my_queue": result,
        "total_pending": len(result),
        "role": user_role
    }
