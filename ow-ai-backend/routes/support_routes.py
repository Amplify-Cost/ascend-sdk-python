from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from models import SupportTicket
from database import get_db
from sqlalchemy.orm import Session
import datetime

router = APIRouter()

class SupportIssue(BaseModel):
    message: str

@router.post("/support/issue")
async def submit_issue(issue: SupportIssue, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    ticket = SupportTicket(
        user_id=user["id"],
        message=issue.message,
        timestamp=int(datetime.datetime.utcnow().timestamp())
    )
    db.add(ticket)
    db.commit()
    return {"status": "success"}
