from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from models import SupportTicket
from database import get_db
from sqlalchemy.orm import Session
import datetime
from dependencies import get_current_user, require_csrf

router = APIRouter()

class SupportIssue(BaseModel):
    message: str

@router.post("/support/issue")
async def submit_issue(
    issue: SupportIssue,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(require_csrf)
):
    # Use the authenticated user from the dependency
    uid = current_user.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")

    ticket = SupportTicket(
        user_id=uid,
        message=issue.message,
        timestamp=int(datetime.datetime.utcnow().timestamp())
    )
    db.add(ticket)
    db.commit()
    return {"status": "success"}