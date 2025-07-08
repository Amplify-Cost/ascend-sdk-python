from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from llm_utils import generate_summary  # Assumes you already have this utility

router = APIRouter()

class AlertText(BaseModel):
    alerts: List[str]

@router.post("/alerts/summary")
async def summarize_alerts(alert_text: AlertText):
    try:
        combined_text = "\n".join(alert_text.alerts)
        summary = generate_summary(combined_text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
