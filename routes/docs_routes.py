"""
Ascend Documentation Routes

Provides API endpoints to serve integration documentation to customers.
This allows customers to access documentation directly within the application.

Document ID: ASCEND-DOCS-001
Publisher: OW-kai Corporation
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from dependencies import get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/docs", tags=["documentation"])

# Path to integration documentation
DOCS_BASE_PATH = Path(__file__).parent.parent / "docs" / "integration-guide"


def get_doc_content(filename: str) -> str:
    """Read documentation file content."""
    filepath = DOCS_BASE_PATH / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")

    # Security: Ensure we're not accessing files outside the docs directory
    try:
        filepath.resolve().relative_to(DOCS_BASE_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return filepath.read_text(encoding='utf-8')


@router.get("/integration")
async def get_integration_docs_index():
    """
    Get integration documentation index.

    Returns a list of available documentation files with descriptions.
    """
    docs = [
        {
            "id": "readme",
            "title": "Ascend Enterprise Integration Guide",
            "description": "Quick start guide for integrating with Ascend",
            "path": "/api/docs/integration/readme",
            "filename": "README.md"
        },
        {
            "id": "risk_scoring",
            "title": "Risk Scoring System",
            "description": "Deep dive into Ascend's multi-layer risk scoring architecture",
            "path": "/api/docs/integration/risk-scoring",
            "filename": "RISK_SCORING.md"
        },
        {
            "id": "api_reference",
            "title": "API Reference",
            "description": "Complete API endpoint documentation",
            "path": "/api/docs/integration/api-reference",
            "filename": "API_REFERENCE.md"
        },
        {
            "id": "sdk_guide",
            "title": "SDK Integration Guide",
            "description": "How to use the Ascend SDK in your applications",
            "path": "/api/docs/integration/sdk-guide",
            "filename": "SDK_GUIDE.md"
        },
        {
            "id": "architecture",
            "title": "Platform Architecture",
            "description": "Technical architecture and component overview",
            "path": "/api/docs/integration/architecture",
            "filename": "ARCHITECTURE.md"
        }
    ]

    return {
        "title": "Ascend Integration Documentation",
        "description": "Enterprise AI Agent Governance Platform Documentation",
        "publisher": "OW-kai Corporation",
        "version": "2.0.0",
        "documents": docs
    }


@router.get("/integration/readme")
async def get_readme():
    """Get the main integration README."""
    content = get_doc_content("README.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/risk-scoring")
async def get_risk_scoring_doc():
    """Get the risk scoring documentation."""
    content = get_doc_content("RISK_SCORING.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/api-reference")
async def get_api_reference_doc():
    """Get the API reference documentation."""
    content = get_doc_content("API_REFERENCE.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/sdk-guide")
async def get_sdk_guide_doc():
    """Get the SDK guide documentation."""
    content = get_doc_content("SDK_GUIDE.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/architecture")
async def get_architecture_doc():
    """Get the architecture documentation."""
    content = get_doc_content("ARCHITECTURE.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/{doc_name}")
async def get_integration_doc_by_name(doc_name: str):
    """
    Get integration documentation by name.

    Args:
        doc_name: Document name without extension (e.g., 'readme', 'risk-scoring')
    """
    # Map friendly names to actual files
    doc_map = {
        "readme": "README.md",
        "risk-scoring": "RISK_SCORING.md",
        "api-reference": "API_REFERENCE.md",
        "sdk-guide": "SDK_GUIDE.md",
        "architecture": "ARCHITECTURE.md"
    }

    filename = doc_map.get(doc_name.lower())
    if not filename:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_name}' not found. Available: {list(doc_map.keys())}"
        )

    content = get_doc_content(filename)
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/quick-start")
async def get_quick_start():
    """
    Get quick start information for new integrations.

    Returns essential information for getting started quickly.
    """
    return {
        "title": "Ascend Quick Start",
        "steps": [
            {
                "step": 1,
                "title": "Generate API Key",
                "description": "Navigate to Settings > API Keys and generate a new key",
                "action": "Navigate to /settings/api-keys"
            },
            {
                "step": 2,
                "title": "Install SDK (Optional)",
                "description": "Install the Ascend SDK for your language",
                "code": {
                    "python": "pip install ascend-sdk",
                    "javascript": "npm install @ascend/sdk",
                    "go": "go get github.com/ascendowkai/sdk-go"
                }
            },
            {
                "step": 3,
                "title": "Submit Your First Action",
                "description": "Make a POST request to /api/authorization/agent-action",
                "example": {
                    "method": "POST",
                    "endpoint": "/api/authorization/agent-action",
                    "headers": {
                        "Authorization": "Bearer ascend_your_api_key",
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "agent_id": "your-agent-001",
                        "action_type": "database.read",
                        "tool_name": "postgres_query",
                        "description": "Querying user analytics data"
                    }
                }
            },
            {
                "step": 4,
                "title": "Check Response",
                "description": "Handle the response based on approval status",
                "response_fields": {
                    "approved": "Boolean - whether action is approved",
                    "risk_score": "Integer 0-100 - final risk score",
                    "risk_level": "String - low/medium/high/critical",
                    "requires_approval": "Boolean - if manual approval needed"
                }
            }
        ],
        "endpoints": {
            "primary": "/api/authorization/agent-action",
            "sdk_optimized": "/api/sdk/agent-action",
            "status_polling": "/api/agent-action/status/{action_id}"
        },
        "support": {
            "documentation": "https://docs.ascendowkai.com",
            "email": "support@ascendowkai.com",
            "status": "https://status.ascendowkai.com"
        }
    }


@router.get("/action-types")
async def get_action_types():
    """
    Get all supported action types with risk levels.

    Returns a categorized list of action types for integration reference.
    """
    return {
        "title": "Supported Action Types",
        "categories": {
            "database": {
                "description": "Database operations",
                "actions": [
                    {"type": "database.read", "risk": "low", "description": "Read/query operations"},
                    {"type": "database.write", "risk": "medium", "description": "Insert/Update operations"},
                    {"type": "database.delete", "risk": "high", "description": "Delete operations"},
                    {"type": "database.schema_change", "risk": "critical", "description": "DDL operations"},
                    {"type": "database.bulk_update", "risk": "high", "description": "Bulk modifications"},
                    {"type": "database.export", "risk": "high", "description": "Data export"}
                ]
            },
            "file": {
                "description": "File system operations",
                "actions": [
                    {"type": "file.read", "risk": "low", "description": "File read access"},
                    {"type": "file.write", "risk": "medium", "description": "File write operations"},
                    {"type": "file.delete", "risk": "high", "description": "File deletion"},
                    {"type": "file.permission_change", "risk": "high", "description": "Permission modifications"},
                    {"type": "file.bulk_delete", "risk": "critical", "description": "Bulk file deletion"}
                ]
            },
            "financial": {
                "description": "Financial operations",
                "actions": [
                    {"type": "financial.read", "risk": "medium", "description": "Account queries"},
                    {"type": "financial.transfer", "risk": "high", "description": "Money transfers"},
                    {"type": "financial.bulk_transfer", "risk": "critical", "description": "Bulk operations"},
                    {"type": "financial.modify_limits", "risk": "high", "description": "Limit changes"}
                ]
            },
            "security": {
                "description": "Security operations",
                "actions": [
                    {"type": "security.authentication", "risk": "medium", "description": "Auth events"},
                    {"type": "security.access_control", "risk": "high", "description": "Permission changes"},
                    {"type": "security.encryption_change", "risk": "critical", "description": "Encryption modifications"},
                    {"type": "security.key_rotation", "risk": "high", "description": "Key management"}
                ]
            },
            "communication": {
                "description": "Communication operations",
                "actions": [
                    {"type": "email.send", "risk": "medium", "description": "Email dispatch"},
                    {"type": "email.bulk_send", "risk": "high", "description": "Bulk email"},
                    {"type": "sms.send", "risk": "medium", "description": "SMS dispatch"},
                    {"type": "notification.push", "risk": "low", "description": "Push notifications"}
                ]
            },
            "api": {
                "description": "API operations",
                "actions": [
                    {"type": "api.external_call", "risk": "medium", "description": "External API calls"},
                    {"type": "api.data_sync", "risk": "medium", "description": "Data synchronization"},
                    {"type": "api.webhook", "risk": "low", "description": "Webhook dispatch"}
                ]
            }
        }
    }
