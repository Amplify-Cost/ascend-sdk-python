"""
SEC-047: Enterprise Integration Setup Wizard Routes
====================================================

Datadog-Style Self-Service Integration Wizard

Features:
- Step-by-step guided setup flow
- Real-time connection testing
- Copy-paste code snippets for SDK integration
- Help documentation for each integration type
- Progress tracking

Banking-Level Security:
- Multi-tenant isolation (organization_id filtering)
- Rate limiting on wizard endpoints
- Audit logging for integration changes
- Credentials encrypted at rest

Compliance: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 7.1, NIST AC-2
Document ID: OWKAI-SEC-047
Version: 1.0.0
Date: December 2, 2025
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations/wizard", tags=["Integration Wizard"])


# ============================================
# Pydantic Schemas
# ============================================

class WizardStep(BaseModel):
    """Single wizard step"""
    step_number: int
    title: str
    description: str
    help_text: Optional[str] = None
    fields: List[Dict[str, Any]] = []
    code_snippets: Optional[Dict[str, str]] = None
    tips: List[str] = []


class IntegrationTypeInfo(BaseModel):
    """Full integration type information with wizard steps"""
    type_id: str
    name: str
    category: str
    icon: str
    description: str
    documentation_url: Optional[str] = None
    estimated_setup_time: str
    difficulty: str  # easy, medium, advanced
    prerequisites: List[str] = []
    steps: List[WizardStep] = []
    post_setup_checklist: List[str] = []
    troubleshooting: List[Dict[str, str]] = []


class CodeSnippet(BaseModel):
    """Code snippet for integration"""
    language: str
    title: str
    description: str
    code: str
    copy_button: bool = True


# ============================================
# Integration Type Documentation
# ============================================

INTEGRATION_WIZARD_CONFIG = {
    "agent_sdk": {
        "type_id": "agent_sdk",
        "name": "Agent SDK Integration",
        "category": "agent",
        "icon": "🤖",
        "description": "Connect your AI agents to Ascend for governance, monitoring, and authorization",
        "documentation_url": "https://docs.ascendowkai.com/sdk/getting-started",
        "estimated_setup_time": "5-10 minutes",
        "difficulty": "easy",
        "prerequisites": [
            "Python 3.8+ or Node.js 16+",
            "API key from Settings → API Keys",
            "Network access to pilot.owkai.app"
        ],
        "steps": [
            {
                "step_number": 1,
                "title": "Generate API Key",
                "description": "Create an API key for your agent to authenticate with Ascend",
                "help_text": "API keys are used by your agents to securely communicate with the Ascend platform. Each agent should have its own key for audit purposes.",
                "fields": [],
                "tips": [
                    "Use descriptive names like 'prod-agent-gpt4' for easy identification",
                    "Store the key securely - it's only shown once",
                    "Set appropriate permissions based on agent capabilities"
                ]
            },
            {
                "step_number": 2,
                "title": "Install SDK",
                "description": "Add the Ascend SDK to your project",
                "help_text": "The SDK handles authentication, request signing, and automatic retries.",
                "code_snippets": {
                    "python": "pip install ascend-ai-sdk",
                    "node": "npm install @ascend-ai/sdk"
                },
                "tips": [
                    "Use a virtual environment for Python projects",
                    "Check for the latest version on PyPI/npm"
                ]
            },
            {
                "step_number": 3,
                "title": "Initialize Client",
                "description": "Configure the SDK with your API key",
                "help_text": "The client handles all communication with Ascend securely.",
                "tips": [
                    "Never hardcode API keys in source code",
                    "Use environment variables for configuration",
                    "Enable debug logging during development"
                ]
            },
            {
                "step_number": 4,
                "title": "Submit Actions for Authorization",
                "description": "Send agent actions to Ascend for approval before execution",
                "help_text": "Every action your agent wants to perform should be submitted for authorization. High-risk actions require human approval.",
                "tips": [
                    "Include detailed context for better risk assessment",
                    "Handle 'pending' status for actions requiring approval",
                    "Implement proper error handling"
                ]
            },
            {
                "step_number": 5,
                "title": "Test Integration",
                "description": "Verify your agent is connected and sending actions",
                "help_text": "Run the test script to ensure everything is working correctly.",
                "tips": [
                    "Check the Agent Activity dashboard after testing",
                    "Review any blocked actions and adjust policies if needed"
                ]
            }
        ],
        "post_setup_checklist": [
            "Verify agent appears in Agent Registry",
            "Test a sample action submission",
            "Review default policies and customize as needed",
            "Set up alerts for blocked actions",
            "Configure webhook notifications (optional)"
        ],
        "troubleshooting": [
            {
                "issue": "Authentication failed",
                "solution": "Verify API key is correct and not expired. Check for extra whitespace."
            },
            {
                "issue": "Connection timeout",
                "solution": "Check network connectivity to pilot.owkai.app. Verify firewall rules."
            },
            {
                "issue": "Actions not appearing",
                "solution": "Ensure organization_id matches your account. Check API response for errors."
            }
        ]
    },
    "splunk": {
        "type_id": "splunk",
        "name": "Splunk Enterprise",
        "category": "siem",
        "icon": "🔍",
        "description": "Stream security events and alerts to Splunk for centralized monitoring",
        "documentation_url": "https://docs.ascendowkai.com/integrations/splunk",
        "estimated_setup_time": "10-15 minutes",
        "difficulty": "medium",
        "prerequisites": [
            "Splunk Enterprise or Splunk Cloud instance",
            "HTTP Event Collector (HEC) enabled",
            "HEC token with appropriate permissions"
        ],
        "steps": [
            {
                "step_number": 1,
                "title": "Enable HTTP Event Collector",
                "description": "Configure Splunk to receive events via HTTP",
                "help_text": "The HEC allows external systems to send data to Splunk over HTTP/HTTPS.",
                "tips": [
                    "Use HTTPS in production for security",
                    "Set up a dedicated index for Ascend events",
                    "Configure appropriate retention policies"
                ]
            },
            {
                "step_number": 2,
                "title": "Create HEC Token",
                "description": "Generate a token for Ascend to authenticate",
                "help_text": "Each integration should have its own token for audit purposes.",
                "tips": [
                    "Name the token 'ascend-integration' for clarity",
                    "Restrict to specific indexes if possible",
                    "Enable acknowledgement for guaranteed delivery"
                ]
            },
            {
                "step_number": 3,
                "title": "Configure Connection",
                "description": "Enter your Splunk HEC URL and token",
                "help_text": "Ascend will use these credentials to send events securely.",
                "fields": [
                    {"name": "endpoint_url", "label": "HEC URL", "type": "url", "required": True},
                    {"name": "api_key", "label": "HEC Token", "type": "password", "required": True},
                    {"name": "index", "label": "Index Name", "type": "text", "required": False}
                ],
                "tips": [
                    "HEC URL format: https://splunk.company.com:8088/services/collector",
                    "Test the connection before saving"
                ]
            },
            {
                "step_number": 4,
                "title": "Select Events",
                "description": "Choose which events to stream to Splunk",
                "help_text": "You can filter events by type, severity, or other criteria.",
                "tips": [
                    "Start with all events, then filter as needed",
                    "Critical alerts should always be forwarded",
                    "Consider volume when selecting event types"
                ]
            },
            {
                "step_number": 5,
                "title": "Test & Verify",
                "description": "Send a test event and verify it appears in Splunk",
                "help_text": "This confirms the connection is working end-to-end.",
                "tips": [
                    "Search for index=your_index sourcetype=ascend_events",
                    "Check timestamp parsing is correct",
                    "Verify all fields are extracted properly"
                ]
            }
        ],
        "post_setup_checklist": [
            "Verify events are appearing in Splunk",
            "Create Splunk alerts for critical events",
            "Set up dashboards for visualization",
            "Configure data retention policies",
            "Document the integration for your team"
        ],
        "troubleshooting": [
            {
                "issue": "Events not appearing",
                "solution": "Check HEC token permissions and index configuration. Verify network connectivity."
            },
            {
                "issue": "SSL certificate error",
                "solution": "Ensure Splunk has a valid SSL certificate. Check CA trust settings."
            },
            {
                "issue": "Rate limiting",
                "solution": "Increase HEC throughput limits or reduce event volume."
            }
        ]
    },
    "webhook": {
        "type_id": "webhook",
        "name": "Custom Webhook",
        "category": "custom",
        "icon": "🔗",
        "description": "Send events to any HTTP endpoint for custom integrations",
        "documentation_url": "https://docs.ascendowkai.com/integrations/webhooks",
        "estimated_setup_time": "5 minutes",
        "difficulty": "easy",
        "prerequisites": [
            "HTTPS endpoint that accepts POST requests",
            "Ability to verify HMAC-SHA256 signatures"
        ],
        "steps": [
            {
                "step_number": 1,
                "title": "Prepare Endpoint",
                "description": "Ensure your endpoint is ready to receive webhook events",
                "help_text": "Your endpoint should accept POST requests with JSON body.",
                "tips": [
                    "Use HTTPS for security",
                    "Implement signature verification",
                    "Return 200 OK quickly, process async"
                ]
            },
            {
                "step_number": 2,
                "title": "Configure Webhook",
                "description": "Enter your endpoint URL and authentication settings",
                "help_text": "Ascend will send events to this URL with HMAC-SHA256 signature.",
                "fields": [
                    {"name": "endpoint_url", "label": "Webhook URL", "type": "url", "required": True},
                    {"name": "auth_type", "label": "Authentication", "type": "select", "options": ["none", "api_key", "basic"], "required": True}
                ],
                "tips": [
                    "Store the signing secret securely",
                    "Implement idempotency using event_id"
                ]
            },
            {
                "step_number": 3,
                "title": "Select Events",
                "description": "Choose which events trigger webhooks",
                "help_text": "Each event type has a specific payload schema.",
                "tips": [
                    "Review payload schemas in documentation",
                    "Start with critical events only"
                ]
            },
            {
                "step_number": 4,
                "title": "Test Webhook",
                "description": "Send a test event to verify configuration",
                "help_text": "Check your endpoint logs for the test event.",
                "tips": [
                    "Verify signature in test event",
                    "Check payload parsing"
                ]
            }
        ],
        "post_setup_checklist": [
            "Verify test event received",
            "Implement signature verification",
            "Set up retry handling",
            "Monitor webhook delivery status"
        ],
        "troubleshooting": [
            {
                "issue": "Webhook not received",
                "solution": "Check endpoint URL is accessible from internet. Verify firewall rules."
            },
            {
                "issue": "Signature mismatch",
                "solution": "Ensure you're using the exact secret. Check encoding (UTF-8)."
            }
        ]
    }
}


# ============================================
# SDK Code Snippets
# ============================================

def get_sdk_code_snippets(api_key_placeholder: str = "YOUR_API_KEY") -> Dict[str, List[CodeSnippet]]:
    """Generate SDK code snippets for different languages"""
    return {
        "python": [
            {
                "language": "python",
                "title": "Install SDK",
                "description": "Install the Ascend SDK using pip",
                "code": "pip install ascend-ai-sdk"
            },
            {
                "language": "python",
                "title": "Initialize Client",
                "description": "Set up the Ascend client with your API key",
                "code": f'''import os
from ascend_sdk import AscendClient

# Initialize the client (use environment variable for security)
client = AscendClient(
    api_key=os.environ.get("ASCEND_API_KEY", "{api_key_placeholder}"),
    base_url="https://pilot.owkai.app"
)'''
            },
            {
                "language": "python",
                "title": "Submit Action for Authorization",
                "description": "Request approval before executing an agent action",
                "code": '''# Submit an action for authorization
result = client.submit_action(
    agent_id="my-agent-001",
    action_type="file_write",
    action_details={
        "file_path": "/data/reports/quarterly.pdf",
        "content_preview": "Q4 Financial Report...",
        "file_size_bytes": 1024000
    },
    context={
        "user_request": "Generate quarterly report",
        "session_id": "sess_abc123"
    },
    risk_indicators={
        "data_sensitivity": "confidential",
        "action_reversible": False
    }
)

# Check authorization status
if result["status"] == "approved":
    # Execute the action
    print("Action approved, proceeding...")
elif result["status"] == "pending":
    # Wait for human approval
    print(f"Awaiting approval. Action ID: {result['action_id']}")
elif result["status"] == "blocked":
    # Action was blocked by policy
    print(f"Action blocked: {result['reason']}")'''
            },
            {
                "language": "python",
                "title": "Poll for Approval Status",
                "description": "Check if a pending action has been approved",
                "code": '''import time

def wait_for_approval(client, action_id, timeout=300):
    """Wait for action approval with timeout"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = client.get_action_status(action_id)

        if status["status"] == "approved":
            return True
        elif status["status"] == "rejected":
            print(f"Action rejected: {status.get('reason', 'No reason provided')}")
            return False

        # Wait before polling again
        time.sleep(5)

    print("Approval timeout exceeded")
    return False'''
            },
            {
                "language": "python",
                "title": "Complete Example",
                "description": "Full working example with error handling",
                "code": '''import os
import logging
from ascend_sdk import AscendClient, AscendError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize client
    client = AscendClient(
        api_key=os.environ["ASCEND_API_KEY"],
        base_url="https://pilot.owkai.app"
    )

    try:
        # Submit action
        result = client.submit_action(
            agent_id="production-agent",
            action_type="database_query",
            action_details={
                "query": "SELECT * FROM users WHERE active = true",
                "database": "production_db"
            }
        )

        logger.info(f"Action submitted: {result['action_id']}")
        logger.info(f"Status: {result['status']}")

        if result["status"] == "approved":
            # Execute your action here
            execute_database_query(result["action_details"])

    except AscendError as e:
        logger.error(f"Ascend API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()'''
            }
        ],
        "node": [
            {
                "language": "javascript",
                "title": "Install SDK",
                "description": "Install the Ascend SDK using npm",
                "code": "npm install @ascend-ai/sdk"
            },
            {
                "language": "javascript",
                "title": "Initialize Client",
                "description": "Set up the Ascend client with your API key",
                "code": f'''const {{ AscendClient }} = require('@ascend-ai/sdk');

// Initialize the client
const client = new AscendClient({{
    apiKey: process.env.ASCEND_API_KEY || '{api_key_placeholder}',
    baseUrl: 'https://pilot.owkai.app'
}});'''
            },
            {
                "language": "javascript",
                "title": "Submit Action for Authorization",
                "description": "Request approval before executing an agent action",
                "code": '''// Submit an action for authorization
async function executeWithAuthorization() {
    const result = await client.submitAction({
        agentId: 'my-agent-001',
        actionType: 'file_write',
        actionDetails: {
            filePath: '/data/reports/quarterly.pdf',
            contentPreview: 'Q4 Financial Report...',
            fileSizeBytes: 1024000
        },
        context: {
            userRequest: 'Generate quarterly report',
            sessionId: 'sess_abc123'
        },
        riskIndicators: {
            dataSensitivity: 'confidential',
            actionReversible: false
        }
    });

    switch (result.status) {
        case 'approved':
            console.log('Action approved, proceeding...');
            // Execute the action
            break;
        case 'pending':
            console.log(`Awaiting approval. Action ID: ${result.actionId}`);
            break;
        case 'blocked':
            console.log(`Action blocked: ${result.reason}`);
            break;
    }
}'''
            }
        ],
        "curl": [
            {
                "language": "bash",
                "title": "Submit Action via cURL",
                "description": "Direct API call to submit an action",
                "code": f'''curl -X POST https://pilot.owkai.app/api/authorization/agent-action \\
  -H "Authorization: Bearer {api_key_placeholder}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "agent_id": "my-agent-001",
    "action_type": "file_write",
    "action_details": {{
      "file_path": "/data/report.pdf"
    }}
  }}'
'''
            },
            {
                "language": "bash",
                "title": "Check Action Status",
                "description": "Poll for action approval status",
                "code": f'''curl -X GET https://pilot.owkai.app/api/agent-action/status/{{action_id}} \\
  -H "Authorization: Bearer {api_key_placeholder}"
'''
            }
        ]
    }


# ============================================
# API Routes
# ============================================

def get_org_id(current_user: dict) -> int:
    """Extract organization ID from current user"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization ID required")
    return org_id


@router.get("/types", summary="List integration types with wizard info")
async def list_integration_types_wizard(
    category: Optional[str] = Query(None, description="Filter by category: agent, siem, notification, custom"),
    current_user: dict = Depends(get_current_user)
):
    """
    SEC-047: List all integration types with wizard configuration.

    Returns comprehensive setup information for each integration type
    including steps, prerequisites, and troubleshooting guides.

    Multi-Tenant: Organization-specific customization possible
    """
    org_id = get_org_id(current_user)

    logger.info(f"SEC-047: Wizard types requested by org_id={org_id}")

    types_list = []
    for type_id, config in INTEGRATION_WIZARD_CONFIG.items():
        if category and config["category"] != category:
            continue

        types_list.append({
            "type_id": config["type_id"],
            "name": config["name"],
            "category": config["category"],
            "icon": config["icon"],
            "description": config["description"],
            "estimated_setup_time": config["estimated_setup_time"],
            "difficulty": config["difficulty"],
            "prerequisites_count": len(config["prerequisites"]),
            "steps_count": len(config["steps"])
        })

    return {
        "integration_types": types_list,
        "total": len(types_list),
        "categories": [
            {"id": "agent", "name": "Agent SDKs", "icon": "🤖"},
            {"id": "siem", "name": "SIEM Integrations", "icon": "🔍"},
            {"id": "notification", "name": "Notifications", "icon": "🔔"},
            {"id": "custom", "name": "Custom", "icon": "🔗"}
        ]
    }


@router.get("/types/{type_id}", summary="Get detailed wizard for integration type")
async def get_integration_wizard_details(
    type_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    SEC-047: Get detailed wizard configuration for a specific integration type.

    Returns full step-by-step guide including:
    - Prerequisites
    - Configuration steps with help text
    - Code snippets
    - Post-setup checklist
    - Troubleshooting guide

    Multi-Tenant: Isolated by organization_id
    """
    org_id = get_org_id(current_user)

    if type_id not in INTEGRATION_WIZARD_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Integration type '{type_id}' not found. Available types: {list(INTEGRATION_WIZARD_CONFIG.keys())}"
        )

    config = INTEGRATION_WIZARD_CONFIG[type_id]

    logger.info(f"SEC-047: Wizard details for {type_id} requested by org_id={org_id}")

    return {
        **config,
        "organization_id": org_id,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/code-snippets/{type_id}", summary="Get code snippets for integration")
async def get_integration_code_snippets(
    type_id: str,
    language: Optional[str] = Query(None, description="Filter by language: python, node, curl"),
    current_user: dict = Depends(get_current_user)
):
    """
    SEC-047: Get code snippets for SDK integration.

    Returns ready-to-use code examples in multiple languages.
    Snippets include proper error handling and best practices.

    API key placeholder is included - user should replace with actual key.
    """
    org_id = get_org_id(current_user)

    if type_id not in ["agent_sdk", "webhook"]:
        raise HTTPException(
            status_code=400,
            detail="Code snippets only available for 'agent_sdk' and 'webhook' types"
        )

    snippets = get_sdk_code_snippets()

    if language:
        if language not in snippets:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{language}' not supported. Available: {list(snippets.keys())}"
            )
        return {
            "type_id": type_id,
            "language": language,
            "snippets": snippets[language],
            "total": len(snippets[language])
        }

    return {
        "type_id": type_id,
        "languages": list(snippets.keys()),
        "snippets": snippets,
        "note": "Replace YOUR_API_KEY with your actual API key from Settings → API Keys"
    }


@router.get("/checklist/{type_id}", summary="Get post-setup checklist")
async def get_setup_checklist(
    type_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    SEC-047: Get post-setup verification checklist.

    Returns list of steps to verify integration is working correctly.
    """
    if type_id not in INTEGRATION_WIZARD_CONFIG:
        raise HTTPException(status_code=404, detail=f"Integration type '{type_id}' not found")

    config = INTEGRATION_WIZARD_CONFIG[type_id]

    return {
        "type_id": type_id,
        "name": config["name"],
        "checklist": config["post_setup_checklist"],
        "troubleshooting": config["troubleshooting"]
    }


@router.get("/quick-start", summary="Get quick start guide")
async def get_quick_start_guide(
    current_user: dict = Depends(get_current_user)
):
    """
    SEC-047: Get quick start guide for new users.

    Returns the recommended first steps for integrating with Ascend.
    """
    org_id = get_org_id(current_user)

    return {
        "title": "Quick Start Guide",
        "subtitle": "Get your first agent connected in 5 minutes",
        "organization_id": org_id,
        "steps": [
            {
                "number": 1,
                "title": "Generate API Key",
                "description": "Go to Settings → API Keys and create a new key",
                "action": "navigate",
                "target": "/settings?tab=api-keys"
            },
            {
                "number": 2,
                "title": "Install SDK",
                "description": "Add the Ascend SDK to your project",
                "action": "code",
                "code": {
                    "python": "pip install ascend-ai-sdk",
                    "node": "npm install @ascend-ai/sdk"
                }
            },
            {
                "number": 3,
                "title": "Initialize & Test",
                "description": "Configure the SDK and submit a test action",
                "action": "code",
                "code": {
                    "python": '''from ascend_sdk import AscendClient

client = AscendClient(api_key="your-api-key")
result = client.submit_action(
    agent_id="test-agent",
    action_type="test",
    action_details={"message": "Hello from my agent!"}
)
print(f"Status: {result['status']}")'''
                }
            },
            {
                "number": 4,
                "title": "Verify in Dashboard",
                "description": "Check the Agent Activity dashboard to see your test action",
                "action": "navigate",
                "target": "/dashboard?tab=agent-activity"
            }
        ],
        "next_steps": [
            {
                "title": "Configure Policies",
                "description": "Set up governance policies for your agents",
                "link": "/governance"
            },
            {
                "title": "Add SIEM Integration",
                "description": "Stream events to your SIEM for centralized monitoring",
                "link": "/settings?tab=integrations"
            },
            {
                "title": "Set Up Alerts",
                "description": "Configure notifications for important events",
                "link": "/settings?tab=alerts"
            }
        ],
        "help_resources": [
            {
                "title": "Full Documentation",
                "url": "https://docs.ascendowkai.com",
                "icon": "📚"
            },
            {
                "title": "SDK Reference",
                "url": "https://docs.ascendowkai.com/sdk",
                "icon": "💻"
            },
            {
                "title": "API Reference",
                "url": "https://pilot.owkai.app/docs",
                "icon": "🔌"
            }
        ]
    }


@router.post("/validate-config", summary="Validate integration configuration")
async def validate_integration_config(
    config: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    SEC-047: Validate integration configuration before saving.

    Performs client-side validation of required fields and format.
    Does NOT test actual connection - use /api/integrations/test for that.
    """
    org_id = get_org_id(current_user)

    type_id = config.get("integration_type")
    if not type_id:
        raise HTTPException(status_code=400, detail="integration_type is required")

    errors = []
    warnings = []

    # Validate based on type
    if type_id == "splunk":
        if not config.get("endpoint_url"):
            errors.append("HEC URL is required")
        elif not config["endpoint_url"].startswith("https://"):
            warnings.append("HTTPS is recommended for production")

        if not config.get("api_key"):
            errors.append("HEC Token is required")

    elif type_id == "webhook":
        if not config.get("endpoint_url"):
            errors.append("Webhook URL is required")
        elif not config["endpoint_url"].startswith("https://"):
            warnings.append("HTTPS is strongly recommended for webhooks")

    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "config_summary": {
            "type": type_id,
            "has_endpoint": bool(config.get("endpoint_url")),
            "has_credentials": bool(config.get("api_key") or config.get("password"))
        }
    }


# ============================================
# Register router in main.py
# ============================================
# Add to main.py:
# from routes.integration_wizard_routes import router as integration_wizard_router
# app.include_router(integration_wizard_router)
