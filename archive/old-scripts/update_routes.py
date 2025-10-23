"""Update automation_orchestration_routes.py to use database"""
import re

# Read the file
with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# 1. Update imports
old_import = "from models import AgentAction, LogAuditTrail, Alert, User"
new_import = "from models import AgentAction, LogAuditTrail, Alert, User, AutomationPlaybook, PlaybookExecution"
content = content.replace(old_import, new_import)

# 2. Find and replace the GET playbooks endpoint
old_endpoint = '''@router.get("/automation/playbooks")
async def get_automation_playbooks(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all automation playbooks with filtering capabilities."""
    try:
        # Log access attempt
        logger.info(f"Automation playbooks accessed by user {current_user.get("email", "unknown")}")
        
        # Filter playbooks based on query parameters
        filtered_playbooks = ENTERPRISE_PLAYBOOKS.copy()
        
        if status:
            filtered_playbooks = [pb for pb in filtered_playbooks if pb.status.value == status]
            
        if risk_level:
            filtered_playbooks = [pb for pb in filtered_playbooks if pb.risk_level == risk_level.upper()]
        
        # Convert to dict format for JSON response
        playbooks_data = []
        for pb in filtered_playbooks:
            pb_dict = asdict(pb)
            pb_dict['created_at'] = pb.created_at.isoformat()
            if pb.last_executed:
                pb_dict['last_executed'] = pb.last_executed.isoformat()
            playbooks_data.append(pb_dict)
        
        return {
            "status": "success",
            "data": playbooks_data,
            "total": len(playbooks_data)
        }
        
    except Exception as e:
        logger.error(f"Error fetching automation playbooks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch automation playbooks")'''

new_endpoint = '''@router.get("/automation/playbooks")
async def get_automation_playbooks(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Get automation playbooks from database
    Supports filtering by status and risk_level
    Returns real data with creator information
    """
    try:
        logger.info(f"📋 Automation playbooks accessed by user {current_user.get('email', 'unknown')}")
        
        # Build database query
        query = db.query(AutomationPlaybook)
        
        # Apply filters if provided
        if status:
            query = query.filter(AutomationPlaybook.status == status)
        
        if risk_level:
            query = query.filter(AutomationPlaybook.risk_level == risk_level.lower())
        
        # Execute query
        playbooks = query.all()
        
        # Convert to response format
        playbooks_data = []
        for pb in playbooks:
            playbook_dict = {
                'id': pb.id,
                'name': pb.name,
                'description': pb.description,
                'status': pb.status,
                'risk_level': pb.risk_level,
                'approval_required': pb.approval_required,
                'trigger_conditions': pb.trigger_conditions,
                'actions': pb.actions,
                'last_executed': pb.last_executed.isoformat() if pb.last_executed else None,
                'execution_count': pb.execution_count,
                'success_rate': pb.success_rate,
                'created_by': pb.created_by,
                'created_at': pb.created_at.isoformat(),
                'updated_at': pb.updated_at.isoformat() if pb.updated_at else None
            }
            playbooks_data.append(playbook_dict)
        
        logger.info(f"✅ Retrieved {len(playbooks_data)} playbooks from database")
        
        return {
            "status": "success",
            "data": playbooks_data,
            "total": len(playbooks_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching automation playbooks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch automation playbooks")'''

content = content.replace(old_endpoint, new_endpoint)

# Write back
with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)

print("✅ Routes file updated successfully")
print("  • Imports: Added AutomationPlaybook, PlaybookExecution")
print("  • GET /automation/playbooks: Now queries database")
