#!/usr/bin/env python3
"""
ASCEND Webhook Handler Example
==============================

This example demonstrates how to:
1. Configure webhooks with ASCEND SDK
2. Receive and verify webhook signatures
3. Handle different event types
4. Process approval notifications

Prerequisites:
- Python 3.8+
- pip install ascend-sdk fastapi uvicorn

Usage:
    # Start webhook receiver
    uvicorn 06_webhook_handler:app --port 8080

    # In another terminal, configure webhook
    python 06_webhook_handler.py --configure

Security: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 8.2

Author: Ascend Engineering Team
"""

import os
import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Webhook secret (should match what's configured in ASCEND)
WEBHOOK_SECRET = os.getenv("ASCEND_WEBHOOK_SECRET", "your-webhook-secret")

app = FastAPI(title="ASCEND Webhook Handler")


# ============================================================
# Webhook Event Models
# ============================================================

class WebhookEvent(BaseModel):
    """ASCEND webhook event payload."""
    event_type: str
    event_id: str
    timestamp: str
    organization_id: int
    data: dict


# ============================================================
# Signature Verification
# ============================================================

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    timestamp: str,
    secret: str
) -> bool:
    """
    Verify ASCEND webhook signature using HMAC-SHA256.

    ASCEND signs webhooks with: HMAC-SHA256(timestamp.payload, secret)
    The signature header format is: v1=<hex_signature>
    """
    if not signature.startswith("v1="):
        logger.warning("Invalid signature format")
        return False

    expected_sig = signature[3:]  # Remove "v1=" prefix

    # Compute expected signature
    message = f"{timestamp}.{payload.decode('utf-8')}"
    computed_sig = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_sig, expected_sig)


# ============================================================
# Event Handlers
# ============================================================

async def handle_action_evaluated(data: dict):
    """Handle action.evaluated event."""
    logger.info(f"Action evaluated: {data.get('action_id')}")
    logger.info(f"  Decision: {data.get('decision')}")
    logger.info(f"  Risk Score: {data.get('risk_score')}")

    # Your business logic here
    # e.g., Update local cache, trigger notifications


async def handle_action_approved(data: dict):
    """Handle action.approved event."""
    logger.info(f"Action approved: {data.get('action_id')}")
    logger.info(f"  Approved by: {data.get('approved_by')}")

    # Resume the pending action
    # e.g., Notify the waiting agent to proceed


async def handle_action_denied(data: dict):
    """Handle action.denied event."""
    logger.info(f"Action denied: {data.get('action_id')}")
    logger.info(f"  Reason: {data.get('reason')}")
    logger.info(f"  Policy violations: {data.get('policy_violations')}")

    # Handle denial
    # e.g., Log to audit, notify user, trigger alternative flow


async def handle_action_completed(data: dict):
    """Handle action.completed event."""
    logger.info(f"Action completed: {data.get('action_id')}")
    logger.info(f"  Duration: {data.get('duration_ms')}ms")

    # Track completion metrics
    # e.g., Update dashboards, compute SLAs


async def handle_action_failed(data: dict):
    """Handle action.failed event."""
    logger.error(f"Action failed: {data.get('action_id')}")
    logger.error(f"  Error: {data.get('error')}")

    # Handle failure
    # e.g., Trigger alerts, initiate recovery


EVENT_HANDLERS = {
    "action.evaluated": handle_action_evaluated,
    "action.approved": handle_action_approved,
    "action.denied": handle_action_denied,
    "action.completed": handle_action_completed,
    "action.failed": handle_action_failed,
}


# ============================================================
# Webhook Endpoint
# ============================================================

@app.post("/webhooks/ascend")
async def receive_webhook(
    request: Request,
    x_ascend_signature: Optional[str] = Header(None, alias="X-Ascend-Signature"),
    x_ascend_timestamp: Optional[str] = Header(None, alias="X-Ascend-Timestamp"),
):
    """
    Receive and process ASCEND webhooks.

    Headers:
    - X-Ascend-Signature: v1=<hmac_sha256_hex>
    - X-Ascend-Timestamp: Unix timestamp when webhook was sent
    """
    # Get raw payload
    payload = await request.body()

    # Verify signature
    if x_ascend_signature and x_ascend_timestamp:
        if not verify_webhook_signature(
            payload, x_ascend_signature, x_ascend_timestamp, WEBHOOK_SECRET
        ):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        logger.warning("Missing signature headers - proceeding without verification")

    # Parse event
    try:
        event_data = json.loads(payload)
        event = WebhookEvent(**event_data)
    except Exception as e:
        logger.error(f"Failed to parse webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Log event
    logger.info(f"Received webhook: {event.event_type} ({event.event_id})")

    # Route to handler
    handler = EVENT_HANDLERS.get(event.event_type)
    if handler:
        await handler(event.data)
    else:
        logger.warning(f"No handler for event type: {event.event_type}")

    # Return success
    return {"status": "received", "event_id": event.event_id}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ascend-webhook-handler"}


# ============================================================
# Webhook Configuration Script
# ============================================================

def configure_webhook():
    """Configure webhook with ASCEND SDK."""
    from owkai_sdk import AscendClient

    client = AscendClient(
        api_key=os.getenv("ASCEND_API_KEY"),
        agent_id="webhook-handler",
        agent_name="Webhook Handler Service",
    )

    # Configure webhook
    result = client.configure_webhook(
        url="https://your-server.com/webhooks/ascend",
        events=[
            "action.evaluated",
            "action.approved",
            "action.denied",
            "action.completed",
            "action.failed",
        ],
        secret=WEBHOOK_SECRET,
    )

    print(f"Webhook configured: {result}")
    return result


if __name__ == "__main__":
    import sys

    if "--configure" in sys.argv:
        configure_webhook()
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8080)
