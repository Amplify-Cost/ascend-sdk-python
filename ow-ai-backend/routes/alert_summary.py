from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from llm_utils import generate_summary
from dependencies import verify_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class AlertText(BaseModel):
    alerts: List[str]

@router.post("/alerts/summary")
async def summarize_alerts(
    request: Request,
    user: dict = Depends(verify_token)
):
    try:
        # Get raw JSON data from request
        data = await request.json()
        logger.info(f"Received alerts data: {len(data) if isinstance(data, list) else 'not a list'}")
        
        # Handle the actual format sent by frontend (array of alert objects)
        if isinstance(data, list):
            # Convert alert objects to text strings for summarization
            alert_texts = []
            for alert in data:
                if isinstance(alert, dict):
                    # Create a readable text from the alert object
                    alert_text = f"Alert: {alert.get('alert_type', 'Unknown')} | "
                    alert_text += f"Severity: {alert.get('severity', 'Unknown')} | "
                    alert_text += f"Agent: {alert.get('agent_id', 'Unknown')} | "
                    alert_text += f"Message: {alert.get('message', 'No message')} | "
                    if alert.get('mitre_tactic'):
                        alert_text += f"MITRE Tactic: {alert.get('mitre_tactic')} | "
                    if alert.get('mitre_technique'):
                        alert_text += f"MITRE Technique: {alert.get('mitre_technique')} | "
                    if alert.get('recommendation'):
                        alert_text += f"Recommendation: {alert.get('recommendation')}"
                    
                    alert_texts.append(alert_text)
                else:
                    # If it's already a string, use it directly
                    alert_texts.append(str(alert))
            
            combined_text = "\n\n".join(alert_texts)
            
        elif isinstance(data, dict) and 'alerts' in data:
            # Handle the original expected format
            combined_text = "\n".join(data['alerts'])
            
        else:
            raise ValueError("Invalid data format. Expected array of alerts or object with 'alerts' field")
        
        logger.info(f"Combined text length: {len(combined_text)}")
        
        # Generate summary using your existing utility with correct parameters
        # Extract the primary agent_id and action_type from alerts
        primary_agent_id = "multiple_agents"
        action_types = set()
        
        for alert in data if isinstance(data, list) else []:
            if isinstance(alert, dict):
                if alert.get('agent_id') and primary_agent_id == "multiple_agents":
                    primary_agent_id = alert.get('agent_id')
                if alert.get('alert_type'):
                    action_types.add(alert.get('alert_type'))
        
        # Use the most common action_type or default
        primary_action_type = list(action_types)[0] if action_types else "security_alert"
        
        logger.info(f"Calling generate_summary with agent_id: {primary_agent_id}, action_type: {primary_action_type}")
        
        # Use the combined_text as the description parameter
        summary = generate_summary(primary_agent_id, primary_action_type, combined_text)
        
        logger.info("Summary generated successfully")
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

# Keep the original endpoint for backward compatibility
@router.post("/alerts/summary-text")
async def summarize_alert_text(
    alert_text: AlertText,
    user: dict = Depends(verify_token)
):
    """Original endpoint that expects {alerts: [string, string, ...]} format"""
    try:
        combined_text = "\n".join(alert_text.alerts)
        # Use correct parameter order: agent_id, action_type, description
        summary = generate_summary("alert_system", "security_alert", combined_text)
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error in summary-text endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))