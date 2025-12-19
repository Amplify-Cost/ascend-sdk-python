"""
Ascend Documentation Routes
===========================

SEC-081: Enterprise Documentation System
Provides API endpoints to serve integration documentation to customers.
This allows customers to access documentation directly within the application.

Document Categories:
- Getting Started (4 docs)
- Core Concepts (5 docs)
- API Reference (1 doc)
- Enterprise Integrations (12 docs)
- Agent Integrations (6 docs)
- Python SDK (6 docs)
- Node.js SDK (4 docs)
- REST API (3 docs)
- Security & Compliance (4 docs)
- Governance (2 docs)

Total: 56 documents
Version: 3.0.0
Publisher: OW-kai Technologies Inc.
Updated: 2025-12-04
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


# ============================================================================
# DOCUMENT REGISTRY - All available documentation organized by category
# ============================================================================

DOCUMENT_CATEGORIES = {
    "getting-started": {
        "title": "Getting Started",
        "description": "Quick start guides for new users",
        "icon": "rocket",
        "documents": [
            {
                "id": "quick-start",
                "title": "Quick Start Guide",
                "description": "Get started with Ascend in 5 minutes",
                "path": "/api/docs/category/getting-started/quick-start",
                "filename": "getting-started/quick-start.md"
            },
            {
                "id": "installation",
                "title": "Installation",
                "description": "Setup and configuration guide",
                "path": "/api/docs/category/getting-started/installation",
                "filename": "getting-started/installation.md"
            },
            {
                "id": "authentication",
                "title": "Authentication",
                "description": "API key management and authentication",
                "path": "/api/docs/category/getting-started/authentication",
                "filename": "getting-started/authentication.md"
            },
            {
                "id": "first-agent-action",
                "title": "First Agent Action",
                "description": "Submit your first AI agent action",
                "path": "/api/docs/category/getting-started/first-agent-action",
                "filename": "getting-started/first-agent-action.md"
            }
        ]
    },
    "core-concepts": {
        "title": "Core Concepts",
        "description": "Understanding Ascend's architecture",
        "icon": "book",
        "documents": [
            {
                "id": "how-ascend-works",
                "title": "How Ascend Works",
                "description": "Platform overview and 7-step governance pipeline",
                "path": "/api/docs/category/core-concepts/how-ascend-works",
                "filename": "core-concepts/how-ascend-works.md"
            },
            {
                "id": "risk-scoring",
                "title": "Risk Scoring",
                "description": "Multi-layer risk assessment with CVSS v3.1",
                "path": "/api/docs/category/core-concepts/risk-scoring",
                "filename": "core-concepts/risk-scoring.md"
            },
            {
                "id": "approval-workflows",
                "title": "Approval Workflows",
                "description": "Human-in-the-loop authorization flows",
                "path": "/api/docs/category/core-concepts/approval-workflows",
                "filename": "core-concepts/approval-workflows.md"
            },
            {
                "id": "multi-tenancy",
                "title": "Multi-Tenancy",
                "description": "Organization isolation and data security",
                "path": "/api/docs/category/core-concepts/multi-tenancy",
                "filename": "core-concepts/multi-tenancy.md"
            },
            {
                "id": "audit-logging",
                "title": "Audit Logging",
                "description": "Immutable audit trails and compliance",
                "path": "/api/docs/category/core-concepts/audit-logging",
                "filename": "core-concepts/audit-logging.md"
            }
        ]
    },
    "enterprise": {
        "title": "Enterprise Integrations",
        "description": "Enterprise system integrations",
        "icon": "building",
        "documents": [
            {
                "id": "enterprise-overview",
                "title": "Enterprise Overview",
                "description": "All enterprise integrations at a glance",
                "path": "/api/docs/category/enterprise/overview",
                "filename": "enterprise/overview.md"
            },
            {
                "id": "sso",
                "title": "Single Sign-On (SSO)",
                "description": "OIDC and SAML authentication",
                "path": "/api/docs/category/enterprise/sso",
                "filename": "enterprise/sso.md"
            },
            {
                "id": "oidc",
                "title": "OIDC Configuration",
                "description": "OpenID Connect setup guide",
                "path": "/api/docs/category/enterprise/oidc",
                "filename": "enterprise/oidc.md"
            },
            {
                "id": "saml",
                "title": "SAML Configuration",
                "description": "SAML 2.0 integration guide",
                "path": "/api/docs/category/enterprise/saml",
                "filename": "enterprise/saml.md"
            },
            {
                "id": "servicenow",
                "title": "ServiceNow Integration",
                "description": "Incident management integration",
                "path": "/api/docs/category/enterprise/servicenow",
                "filename": "enterprise/servicenow.md"
            },
            {
                "id": "splunk",
                "title": "Splunk Integration",
                "description": "SIEM integration with Splunk HEC",
                "path": "/api/docs/category/enterprise/splunk",
                "filename": "enterprise/splunk.md"
            },
            {
                "id": "siem",
                "title": "SIEM Integration",
                "description": "Generic SIEM configuration",
                "path": "/api/docs/category/enterprise/siem",
                "filename": "enterprise/siem.md"
            },
            {
                "id": "slack-teams",
                "title": "Slack & Teams",
                "description": "Notification channel setup",
                "path": "/api/docs/category/enterprise/slack-teams",
                "filename": "enterprise/slack-teams.md"
            },
            {
                "id": "pagerduty",
                "title": "PagerDuty Integration",
                "description": "Alert escalation configuration",
                "path": "/api/docs/category/enterprise/pagerduty",
                "filename": "enterprise/pagerduty.md"
            },
            {
                "id": "compliance",
                "title": "Compliance Exports",
                "description": "SOX, PCI-DSS, HIPAA, GDPR reports",
                "path": "/api/docs/category/enterprise/compliance",
                "filename": "enterprise/compliance.md"
            },
            {
                "id": "analytics",
                "title": "Analytics & Reporting",
                "description": "Real-time analytics and dashboards",
                "path": "/api/docs/category/enterprise/analytics",
                "filename": "enterprise/analytics.md"
            },
            {
                "id": "system-diagnostics",
                "title": "System Diagnostics",
                "description": "Health monitoring and diagnostics",
                "path": "/api/docs/category/enterprise/system-diagnostics",
                "filename": "enterprise/system-diagnostics.md"
            }
        ]
    },
    "integrations": {
        "title": "Agent Integrations",
        "description": "Connect AI agents to Ascend",
        "icon": "robot",
        "documents": [
            {
                "id": "integrations-overview",
                "title": "Integrations Overview",
                "description": "Supported agent frameworks",
                "path": "/api/docs/category/integrations/overview",
                "filename": "integrations/overview.md"
            },
            {
                "id": "langchain",
                "title": "LangChain Integration",
                "description": "Integrate with LangChain agents",
                "path": "/api/docs/category/integrations/langchain",
                "filename": "integrations/langchain.md"
            },
            {
                "id": "autogpt",
                "title": "AutoGPT Integration",
                "description": "Govern AutoGPT autonomous agents",
                "path": "/api/docs/category/integrations/autogpt",
                "filename": "integrations/autogpt.md"
            },
            {
                "id": "claude-code",
                "title": "Claude Code Integration",
                "description": "Integrate Claude Code with governance",
                "path": "/api/docs/category/integrations/claude-code",
                "filename": "integrations/claude-code.md"
            },
            {
                "id": "mcp-server",
                "title": "MCP Server",
                "description": "Model Context Protocol server setup",
                "path": "/api/docs/category/integrations/mcp-server",
                "filename": "integrations/mcp-server.md"
            },
            {
                "id": "custom-agents",
                "title": "Custom Agents",
                "description": "Build custom agent integrations",
                "path": "/api/docs/category/integrations/custom-agents",
                "filename": "integrations/custom-agents.md"
            }
        ]
    },
    "sdk-python": {
        "title": "Python SDK",
        "description": "Python integration reference",
        "icon": "python",
        "documents": [
            {
                "id": "installation",  # SEC-096: Removed prefix to match path
                "title": "Installation",
                "description": "Python SDK setup",
                "path": "/api/docs/category/sdk-python/installation",
                "filename": "sdk-python/installation.md"
            },
            {
                "id": "client-configuration",  # SEC-096: Removed prefix to match path
                "title": "Client Configuration",
                "description": "Configure the Python client",
                "path": "/api/docs/category/sdk-python/client-configuration",
                "filename": "sdk-python/client-configuration.md"
            },
            {
                "id": "agent-actions",  # SEC-096: Removed prefix to match path
                "title": "Agent Actions",
                "description": "Submit and manage agent actions",
                "path": "/api/docs/category/sdk-python/agent-actions",
                "filename": "sdk-python/agent-actions.md"
            },
            {
                "id": "policies",  # SEC-096: Removed prefix to match path
                "title": "Policies",
                "description": "Policy management with Python",
                "path": "/api/docs/category/sdk-python/policies",
                "filename": "sdk-python/policies.md"
            },
            {
                "id": "error-handling",  # SEC-096: Removed prefix to match path
                "title": "Error Handling",
                "description": "Handle errors gracefully",
                "path": "/api/docs/category/sdk-python/error-handling",
                "filename": "sdk-python/error-handling.md"
            },
            {
                "id": "api-reference",  # SEC-096: Removed prefix to match path
                "title": "API Reference",
                "description": "Complete Python API reference",
                "path": "/api/docs/category/sdk-python/api-reference",
                "filename": "sdk-python/api-reference.md"
            }
        ]
    },
    "sdk-nodejs": {
        "title": "Node.js SDK",
        "description": "Node.js integration reference",
        "icon": "nodejs",
        "documents": [
            {
                "id": "installation",  # SEC-096: Removed prefix to match path
                "title": "Installation",
                "description": "Node.js SDK setup",
                "path": "/api/docs/category/sdk-nodejs/installation",
                "filename": "sdk-nodejs/installation.md"
            },
            {
                "id": "client-configuration",  # SEC-096: Removed prefix to match path
                "title": "Client Configuration",
                "description": "Configure the Node.js client",
                "path": "/api/docs/category/sdk-nodejs/client-configuration",
                "filename": "sdk-nodejs/client-configuration.md"
            },
            {
                "id": "agent-actions",  # SEC-096: Removed prefix to match path
                "title": "Agent Actions",
                "description": "Submit and manage agent actions",
                "path": "/api/docs/category/sdk-nodejs/agent-actions",
                "filename": "sdk-nodejs/agent-actions.md"
            },
            {
                "id": "error-handling",  # SEC-096: Removed prefix to match path
                "title": "Error Handling",
                "description": "Handle errors in Node.js",
                "path": "/api/docs/category/sdk-nodejs/error-handling",
                "filename": "sdk-nodejs/error-handling.md"
            }
        ]
    },
    "sdk-rest": {
        "title": "REST API",
        "description": "Direct REST API integration",
        "icon": "api",
        "documents": [
            {
                "id": "authentication",  # SEC-096: Removed prefix to match path
                "title": "Authentication",
                "description": "API authentication methods",
                "path": "/api/docs/category/sdk-rest/authentication",
                "filename": "sdk-rest/authentication.md"
            },
            {
                "id": "endpoints",  # SEC-096: Removed prefix to match path
                "title": "Endpoints",
                "description": "Complete endpoint reference",
                "path": "/api/docs/category/sdk-rest/endpoints",
                "filename": "sdk-rest/endpoints.md"
            },
            {
                "id": "webhooks",  # SEC-096: Removed prefix to match path
                "title": "Webhooks",
                "description": "Webhook configuration and events",
                "path": "/api/docs/category/sdk-rest/webhooks",
                "filename": "sdk-rest/webhooks.md"
            }
        ]
    },
    "security": {
        "title": "Security & Compliance",
        "description": "Security documentation",
        "icon": "shield",
        "documents": [
            {
                "id": "security-overview",
                "title": "Security Overview",
                "description": "Platform security architecture",
                "path": "/api/docs/category/security/overview",
                "filename": "security/overview.md"
            },
            {
                "id": "prompt-injection",
                "title": "Prompt Injection Detection",
                "description": "Real-time prompt injection detection with 21 patterns",
                "path": "/api/docs/category/security/prompt-injection",
                "filename": "security/prompt-injection.md"
            },
            {
                "id": "llm-governance",
                "title": "LLM-to-LLM Governance",
                "description": "Govern AI agent-to-agent communication chains",
                "path": "/api/docs/category/security/llm-governance",
                "filename": "security/llm-governance.md"
            },
            {
                "id": "code-analysis",
                "title": "Code Analysis",
                "description": "Dangerous code pattern detection with 20 patterns",
                "path": "/api/docs/category/security/code-analysis",
                "filename": "security/code-analysis.md"
            },
            {
                "id": "data-encryption",
                "title": "Data Encryption",
                "description": "Encryption at rest and in transit",
                "path": "/api/docs/category/security/data-encryption",
                "filename": "security/data-encryption.md"
            },
            {
                "id": "compliance",
                "title": "Compliance",
                "description": "SOC 2, HIPAA, PCI-DSS, GDPR",
                "path": "/api/docs/category/security/compliance",
                "filename": "security/compliance.md"
            },
            {
                "id": "responsible-disclosure",
                "title": "Responsible Disclosure",
                "description": "Security vulnerability reporting",
                "path": "/api/docs/category/security/responsible-disclosure",
                "filename": "security/responsible-disclosure.md"
            }
        ]
    },
    "sdk-wrappers": {
        "title": "SDK Wrappers",
        "description": "Governed Python wrappers for dangerous operations",
        "icon": "code",
        "documents": [
            {
                "id": "subprocess-wrapper",
                "title": "subprocess Wrapper",
                "description": "Governed subprocess execution for AI agents",
                "path": "/api/docs/category/sdk-wrappers/subprocess-wrapper",
                "filename": "sdk/subprocess-wrapper.md"
            },
            {
                "id": "eval-exec-wrapper",
                "title": "eval/exec Wrapper",
                "description": "Governed dynamic code execution with AST analysis",
                "path": "/api/docs/category/sdk-wrappers/eval-exec-wrapper",
                "filename": "sdk/eval-exec-wrapper.md"
            }
        ]
    },
    "admin": {
        "title": "Administration",
        "description": "Platform administration and configuration",
        "icon": "settings",
        "documents": [
            {
                "id": "rate-limiting",
                "title": "Rate Limiting",
                "description": "Per-agent and per-tenant rate limiting with Redis",
                "path": "/api/docs/category/admin/rate-limiting",
                "filename": "admin/rate-limiting.md"
            }
        ]
    },
    "governance": {
        "title": "Governance",
        "description": "Governance configuration guides",
        "icon": "gavel",
        "documents": [
            {
                "id": "enterprise-governance",
                "title": "Enterprise Governance",
                "description": "Complete governance framework",
                "path": "/api/docs/category/governance/enterprise-governance",
                "filename": "governance/enterprise-governance.md"
            },
            {
                "id": "governance-integration",
                "title": "Governance Integration",
                "description": "Integrate governance into workflows",
                "path": "/api/docs/category/governance/governance-integration",
                "filename": "governance/governance-integration.md"
            }
        ]
    },
    "reference": {
        "title": "Technical Reference",
        "description": "Detailed technical documentation",
        "icon": "code",
        "documents": [
            {
                "id": "readme",
                "title": "Integration Guide",
                "description": "Quick start integration guide",
                "path": "/api/docs/integration/readme",
                "filename": "README.md"
            },
            {
                "id": "agent-registry",
                "title": "Agent Registry",
                "description": "AI agent registration and management",
                "path": "/api/docs/integration/agent-registry",
                "filename": "AGENT_REGISTRY.md",
                "audience": "engineers"
            },
            {
                "id": "agent-governance",
                "title": "Agent Governance",
                "description": "Business governance guide",
                "path": "/api/docs/integration/agent-governance",
                "filename": "AGENT_GOVERNANCE.md",
                "audience": "clients"
            },
            {
                "id": "risk-scoring-deep",
                "title": "Risk Scoring Deep Dive",
                "description": "Multi-layer risk scoring architecture",
                "path": "/api/docs/integration/risk-scoring",
                "filename": "RISK_SCORING.md"
            },
            {
                "id": "api-reference",
                "title": "API Reference",
                "description": "Complete API documentation",
                "path": "/api/docs/integration/api-reference",
                "filename": "API_REFERENCE.md"
            },
            {
                "id": "sdk-guide",
                "title": "SDK Guide",
                "description": "SDK integration patterns",
                "path": "/api/docs/integration/sdk-guide",
                "filename": "SDK_GUIDE.md"
            },
            {
                "id": "architecture",
                "title": "Platform Architecture",
                "description": "System architecture overview",
                "path": "/api/docs/integration/architecture",
                "filename": "ARCHITECTURE.md"
            },
            {
                "id": "governance-controls",
                "title": "Governance Controls",
                "description": "Configure governance controls",
                "path": "/api/docs/integration/governance-controls",
                "filename": "GOVERNANCE_CONTROLS.md",
                "audience": "clients"
            }
        ]
    }
}


# ============================================================================
# MAIN DOCUMENTATION INDEX ENDPOINT
# ============================================================================

@router.get("/integration")
async def get_integration_docs_index():
    """
    Get complete documentation index organized by category.

    SEC-081: Enterprise Documentation System
    Returns all available documentation files with descriptions,
    organized by category for the in-app Documentation viewer.

    Returns:
        dict: Documentation index with categories and documents
    """
    # Build flat list for backward compatibility
    all_docs = []
    for category_id, category in DOCUMENT_CATEGORIES.items():
        for doc in category["documents"]:
            doc_entry = {
                "id": doc["id"],
                "title": doc["title"],
                "description": doc["description"],
                "path": doc["path"],
                "filename": doc["filename"],
                "category": category_id,
                "category_title": category["title"]
            }
            if "audience" in doc:
                doc_entry["audience"] = doc["audience"]
            all_docs.append(doc_entry)

    return {
        "title": "Ascend Platform Documentation",
        "description": "Enterprise AI Agent Governance Platform - Complete Documentation",
        "publisher": "OW-kai Technologies Inc.",
        "version": "3.0.0",
        "updated": "2025-12-04",
        "total_documents": len(all_docs),
        "categories": DOCUMENT_CATEGORIES,
        "documents": all_docs
    }


@router.get("/categories")
async def get_documentation_categories():
    """
    Get list of documentation categories.

    Returns category metadata without full document listings.
    """
    categories = []
    for category_id, category in DOCUMENT_CATEGORIES.items():
        categories.append({
            "id": category_id,
            "title": category["title"],
            "description": category["description"],
            "icon": category.get("icon", "document"),
            "document_count": len(category["documents"])
        })

    return {
        "categories": categories,
        "total_categories": len(categories)
    }


# ============================================================================
# CATEGORY-BASED DOCUMENT ENDPOINTS
# ============================================================================

@router.get("/category/{category_id}")
async def get_category_documents(category_id: str):
    """
    Get all documents in a category.

    Args:
        category_id: Category identifier (e.g., 'getting-started', 'enterprise')
    """
    if category_id not in DOCUMENT_CATEGORIES:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_id}' not found. Available: {list(DOCUMENT_CATEGORIES.keys())}"
        )

    category = DOCUMENT_CATEGORIES[category_id]
    return {
        "id": category_id,
        "title": category["title"],
        "description": category["description"],
        "documents": category["documents"]
    }


@router.get("/category/{category_id}/{doc_id}")
async def get_category_document(category_id: str, doc_id: str):
    """
    Get a specific document from a category.

    Args:
        category_id: Category identifier
        doc_id: Document identifier within the category
    """
    if category_id not in DOCUMENT_CATEGORIES:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_id}' not found"
        )

    category = DOCUMENT_CATEGORIES[category_id]

    # Find document in category
    doc = None
    for d in category["documents"]:
        if d["id"] == doc_id:
            doc = d
            break

    if not doc:
        available = [d["id"] for d in category["documents"]]
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' not found in category '{category_id}'. Available: {available}"
        )

    content = get_doc_content(doc["filename"])
    return PlainTextResponse(content, media_type="text/markdown")


# ============================================================================
# LEGACY ENDPOINTS (Backward Compatibility)
# ============================================================================

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


@router.get("/integration/agent-registry")
async def get_agent_registry_doc():
    """Get the Agent Registry technical documentation."""
    content = get_doc_content("AGENT_REGISTRY.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/agent-governance")
async def get_agent_governance_doc():
    """Get the AI Agent Governance guide."""
    content = get_doc_content("AGENT_GOVERNANCE.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/governance-controls")
async def get_governance_controls_doc():
    """Get the Governance Controls Configuration Guide."""
    content = get_doc_content("GOVERNANCE_CONTROLS.md")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/integration/{doc_name}")
async def get_integration_doc_by_name(doc_name: str):
    """
    Get integration documentation by name (legacy endpoint).

    Args:
        doc_name: Document name without extension
    """
    # Map friendly names to actual files
    doc_map = {
        "readme": "README.md",
        "risk-scoring": "RISK_SCORING.md",
        "api-reference": "API_REFERENCE.md",
        "sdk-guide": "SDK_GUIDE.md",
        "architecture": "ARCHITECTURE.md",
        "agent-registry": "AGENT_REGISTRY.md",
        "agent-governance": "AGENT_GOVERNANCE.md",
        "governance-controls": "GOVERNANCE_CONTROLS.md",
        "intro": "INTRO.md"
    }

    filename = doc_map.get(doc_name.lower())
    if not filename:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_name}' not found. Available: {list(doc_map.keys())}"
        )

    content = get_doc_content(filename)
    return PlainTextResponse(content, media_type="text/markdown")


# ============================================================================
# QUICK START AND ACTION TYPES ENDPOINTS
# ============================================================================

@router.get("/quick-start")
async def get_quick_start():
    """
    Get quick start information for new integrations.

    SEC-081: Updated to reference real endpoints and remove fake packages.
    Source: /ow-ai-backend/routes/actions_v1_routes.py
    """
    return {
        "title": "Ascend Quick Start",
        "version": "3.0.0",
        "steps": [
            {
                "step": 1,
                "title": "Generate API Key",
                "description": "Navigate to Settings > API Keys and generate a new key",
                "action": "Navigate to /settings/api-keys",
                "note": "API keys are shown only once - store securely"
            },
            {
                "step": 2,
                "title": "Set Environment Variables",
                "description": "Configure your environment for API access",
                "code": {
                    "bash": "export ASCEND_API_KEY='owkai_admin_xxxxxxxxxxxx'\nexport ASCEND_API_URL='https://pilot.owkai.app'"
                },
                "note": "No pip or npm package required - use REST API directly"
            },
            {
                "step": 3,
                "title": "Submit Your First Action",
                "description": "POST to /api/v1/actions/submit (Unified API Gateway)",
                "source": "/ow-ai-backend/routes/actions_v1_routes.py:199",
                "example": {
                    "method": "POST",
                    "endpoint": "/api/v1/actions/submit",
                    "headers": {
                        "Authorization": "Bearer owkai_admin_xxxxxxxxxxxx",
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "agent_id": "your-agent-001",
                        "agent_name": "Your Agent Name",
                        "action_type": "data_access",
                        "resource": "customer_database",
                        "description": "Read customer profile data",
                        "tool_name": "database_query"
                    }
                }
            },
            {
                "step": 4,
                "title": "Handle the Response",
                "description": "Process authorization decision",
                "response_fields": {
                    "id": "Integer - Action ID for tracking",
                    "status": "String - approved/pending_approval/denied",
                    "risk_score": "Float 0-100 - Computed risk score",
                    "risk_level": "String - low/medium/high/critical",
                    "requires_approval": "Boolean - if manual review needed",
                    "alert_triggered": "Boolean - if alert was generated"
                }
            }
        ],
        "endpoints": {
            "v1_unified": {
                "submit": "/api/v1/actions/submit",
                "status": "/api/v1/actions/{action_id}/status",
                "list": "/api/v1/actions",
                "approve": "/api/v1/actions/{action_id}/approve",
                "reject": "/api/v1/actions/{action_id}/reject"
            },
            "system": {
                "health": "/health",
                "deployment_info": "/api/deployment-info"
            }
        },
        "support": {
            "documentation": "https://pilot.owkai.app (Documentation tab)",
            "email": "support@ascendowkai.com"
        }
    }


@router.get("/action-types")
async def get_action_types():
    """
    Get all supported action types with risk levels.

    Source: /ow-ai-backend/sdk/ascend-sdk-python/ascend/constants.py
    Source: /ow-ai-backend/enrichment.py (lines 43-65)
    """
    return {
        "title": "Supported Action Types",
        "source": "/ow-ai-backend/enrichment.py",
        "categories": {
            "database": {
                "description": "Database operations",
                "actions": [
                    {"type": "database_read", "risk": "low", "description": "Read/query operations"},
                    {"type": "database_write", "risk": "critical", "description": "Insert/Update operations (CVSS 9.0+)"},
                    {"type": "database_delete", "risk": "high", "description": "Delete operations"},
                    {"type": "schema_change", "risk": "critical", "description": "DDL operations"},
                    {"type": "data_export", "risk": "high", "description": "Data export/exfiltration risk"},
                    {"type": "data_exfiltration", "risk": "critical", "description": "Explicit exfiltration attempts"}
                ]
            },
            "user_management": {
                "description": "User and permission operations",
                "actions": [
                    {"type": "user_create", "risk": "high", "description": "User provisioning"},
                    {"type": "user_provision", "risk": "high", "description": "User provisioning (alternate)"},
                    {"type": "permission_grant", "risk": "high", "description": "Permission escalation"},
                    {"type": "access_grant", "risk": "high", "description": "Access control modifications"},
                    {"type": "secret_access", "risk": "high", "description": "Secrets/credentials access"},
                    {"type": "credential_access", "risk": "high", "description": "Credential operations"}
                ]
            },
            "system": {
                "description": "System operations",
                "actions": [
                    {"type": "system_modification", "risk": "medium", "description": "System configuration changes"},
                    {"type": "config_change", "risk": "medium", "description": "Configuration modifications"},
                    {"type": "service_restart", "risk": "medium", "description": "Service control operations"},
                    {"type": "file_write", "risk": "medium", "description": "File system modifications"},
                    {"type": "network_access", "risk": "medium", "description": "Network operations"}
                ]
            },
            "financial": {
                "description": "Financial operations (CVSS enhanced)",
                "source": "/ow-ai-backend/services/cvss_auto_mapper.py:79-88",
                "actions": [
                    {"type": "financial_transaction", "risk": "critical", "description": "Payment processing, billing"},
                    {"type": "transaction", "risk": "high", "description": "State-changing financial operations"}
                ]
            },
            "standard": {
                "description": "Standard SDK action types",
                "source": "/ow-ai-backend/sdk/ascend-sdk-python/ascend/constants.py:11-27",
                "actions": [
                    {"type": "data_access", "risk": "low-medium", "description": "Reading sensitive data"},
                    {"type": "data_modification", "risk": "medium-high", "description": "Creating, updating, deleting data"},
                    {"type": "recommendation", "risk": "low", "description": "AI-generated suggestions"},
                    {"type": "communication", "risk": "medium", "description": "Sending emails, messages"},
                    {"type": "system_operation", "risk": "medium-high", "description": "Infrastructure operations"},
                    {"type": "query", "risk": "low", "description": "Read-only queries"},
                    {"type": "file_access", "risk": "low-medium", "description": "File system access"},
                    {"type": "api_call", "risk": "medium", "description": "External API calls"}
                ]
            }
        }
    }
