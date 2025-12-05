"""
MCP Governance Adapter - Provides exact endpoints frontend expects
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging
from datetime import datetime, UTC

from dependencies import get_current_user

router = APIRouter(prefix="/api/mcp-governance", tags=["mcp-governance"])
logger = logging.getLogger(__name__)

def get_mcp_governance_data():
    return [
        {
            "id": "mcp-001",
            "agent_id": "security-scanner-01",
            "action_type": "file_read",
            "resource": "/logs/security.log",
            "risk_score": 25,
            "status": "approved",
            "timestamp": datetime.now(UTC).isoformat()
        },
        {
            "id": "mcp-002", 
            "agent_id": "vulnerability-scanner",
            "action_type": "network_scan",
            "resource": "192.168.1.0/24",
            "risk_score": 45,
            "status": "pending",
            "timestamp": datetime.now(UTC).isoformat()
        }
    ]

@router.post("/evaluate-action")
async def evaluate_mcp_action(action_data: dict, current_user = Depends(get_current_user)):
    mcp_data = get_mcp_governance_data()
    return {
        "success": True,
        "actions": mcp_data,
        "total_count": len(mcp_data)
    }

@router.get("/actions")
async def get_mcp_governance_actions(current_user = Depends(get_current_user)):
    mcp_data = get_mcp_governance_data()
    return {
        "success": True,
        "actions": mcp_data,
        "total_count": len(mcp_data)
    }
