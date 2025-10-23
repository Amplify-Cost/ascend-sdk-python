from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel
import json

import sys
sys.path.append('..')
from database import get_db
from models import Alert
from dependencies import get_current_user

router = APIRouter()

class AlertCreate(BaseModel):
    alert_type: str
    message: str
    severity: str = "medium"
    agent_id: str = "manual"
    action_type: str = "manual_entry"
    tool_name: Optional[str] = "admin_console"
    risk_level: Optional[str] = "medium"

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    message: str
    severity: str
    status: str
    timestamp: datetime
    agent_id: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all alerts"""
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(100).all()
    return alerts

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new alert"""
    alert = Alert(
        alert_type=alert_data.alert_type,
        message=alert_data.message,
        severity=alert_data.severity,
        agent_id=alert_data.agent_id,
        timestamp=datetime.now(UTC),
        status="new"
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.get("email")
    alert.acknowledged_at = datetime.now(UTC)
    db.commit()
    
    return {"message": "Alert acknowledged", "id": alert_id}
