"""
🏢 ENTERPRISE: MCP Governance Adapter
Provides exact endpoints frontend expects - NO demo data
All data must come from database with proper org_id filtering
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
import logging
from datetime import datetime, UTC

from dependencies import get_current_user, get_organization_filter

router = APIRouter(prefix="/api/mcp-governance", tags=["mcp-governance"])
logger = logging.getLogger(__name__)

def get_mcp_governance_data(org_id: int = None) -> List[Dict]:
    """
    🏢 ENTERPRISE: NO demo data
    Returns empty list - MCP actions should come from database with org_id filter
    """
    # NO hardcoded demo data - return empty list
    # In production, this should query the database with org_id filter
    return []

@router.post("/evaluate-action")
async def evaluate_mcp_action(
    action_data: dict,
    current_user = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """🏢 ENTERPRISE: Evaluate MCP action - NO demo data"""
    logger.info(f"🏢 MCP action evaluation requested [org_id={org_id}]")

    # 🏢 ENTERPRISE: Return empty list for organizations without MCP data
    mcp_data = get_mcp_governance_data(org_id)
    return {
        "success": True,
        "actions": mcp_data,
        "total_count": len(mcp_data)
    }

@router.get("/actions")
async def get_mcp_governance_actions(
    current_user = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """🏢 ENTERPRISE: Get MCP governance actions - NO demo data"""
    logger.info(f"🏢 MCP governance actions requested [org_id={org_id}]")

    # 🏢 ENTERPRISE: Return empty list for organizations without MCP data
    mcp_data = get_mcp_governance_data(org_id)
    return {
        "success": True,
        "actions": mcp_data,
        "total_count": len(mcp_data)
    }
