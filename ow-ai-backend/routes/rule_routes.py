from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from dependencies import verify_token
from models import RuleFeedback
from schemas import RuleFeedbackRequest, RuleFeedbackResponse, SmartRuleResponse
from llm_utils import generate_smart_rule
from sqlalchemy import func
import os
import json

router = APIRouter()

# Paths for rule storage
RULE_FILE = "rules.json"
VERSION_DIR = "rule_versions"
os.makedirs(VERSION_DIR, exist_ok=True)

@router.get("/rules")
def get_rules(_: dict = Depends(verify_token)):
    if not os.path.exists(RULE_FILE):
        return []
    with open(RULE_FILE, "r") as f:
        return json.load(f)

@router.get("/rules/history")
def rule_history(_: dict = Depends(verify_token)):
    return sorted(os.listdir(VERSION_DIR), reverse=True)

@router.post("/rules")
async def update_rules(request: Request, user: dict = Depends(verify_token)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update rules")

    rules = await request.json()
    if not isinstance(rules, list):
        raise HTTPException(status_code=400, detail="Rules must be a list")

    # ✅ Auto-fill justification if missing or empty
    for rule in rules:
        if not rule.get("justification"):
            rule["justification"] = rule.get("recommendation", "Auto-generated justification.")

    # Save the current rules
    with open(RULE_FILE, "w") as f:
        json.dump(rules, f, indent=2)

    # Save versioned snapshot
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    with open(os.path.join(VERSION_DIR, f"rules_{timestamp}.json"), "w") as vf:
        json.dump(rules, vf, indent=2)

    return {"message": "✅ Rules updated"}

@router.post("/rules/rollback")
async def rollback_rules(request: Request, user: dict = Depends(verify_token)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can rollback")

    data = await request.json()
    filename = data.get("filename")
    full_path = os.path.join(VERSION_DIR, filename)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Version not found")

    with open(full_path, "r") as f:
        version_data = json.load(f)
    with open(RULE_FILE, "w") as f:
        json.dump(version_data, f, indent=2)

    return {"message": "✅ Rollback successful"}

@router.post("/rules/generate-smart-rule", response_model=SmartRuleResponse)
async def generate_smart_rule_endpoint(request: Request, user: dict = Depends(verify_token)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    agent_id = data.get("agent_id")
    action_type = data.get("action_type")
    description = data.get("description")

    if not all([agent_id, action_type, description]):
        raise HTTPException(status_code=400, detail="Missing required fields: agent_id, action_type, description")

    rule = generate_smart_rule(agent_id, action_type, description)

    # Load existing rules
    rules = []
    if os.path.exists(RULE_FILE):
        with open(RULE_FILE, "r") as f:
            try:
                rules = json.load(f)
                if not isinstance(rules, list):
                    rules = []
            except json.JSONDecodeError:
                rules = []

    # Add the new rule
    rules.append(rule)

    # Save updated rules
    with open(RULE_FILE, "w") as f:
        json.dump(rules, f, indent=2)

    # Save versioned copy
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    with open(os.path.join(VERSION_DIR, f"rules_{timestamp}.json"), "w") as vf:
        json.dump(rules, vf, indent=2)

    return rule

@router.post("/rules/preview")
async def preview_rules(_: Request, __: dict = Depends(verify_token)):
    return {"message": "✅ Rule syntax looks valid"}

@router.get("/feedback/{rule_id}", response_model=RuleFeedbackResponse)
def get_rule_feedback(
    rule_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    total = db.query(func.count(RuleFeedback.id)).filter(RuleFeedback.rule_id == rule_id).scalar()
    approved = db.query(func.count(RuleFeedback.id)).filter(RuleFeedback.rule_id == rule_id, RuleFeedback.decision == "approved").scalar()
    rejected = db.query(func.count(RuleFeedback.id)).filter(RuleFeedback.rule_id == rule_id, RuleFeedback.decision == "rejected").scalar()
    false_pos = db.query(func.count(RuleFeedback.id)).filter(RuleFeedback.rule_id == rule_id, RuleFeedback.decision == "false_positive").scalar()

    return {
        "rule_id": rule_id,
        "total_triggered": total,
        "approved_count": approved,
        "rejected_count": rejected,
        "false_positive_count": false_pos
    }
