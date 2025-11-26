#!/usr/bin/env python3
"""
OW-AI Integration Example 4: FastAPI Middleware for API Governance

USE CASE: API backend that needs to govern agent/automated requests
          with enterprise security, rate limiting, and audit trails.

This example shows how to:
1. Create FastAPI middleware that intercepts requests
2. Identify and govern AI agent requests vs human requests
3. Apply risk-based routing and approval workflows
4. Log all actions for compliance audit

ARCHITECTURE:
    External Request → FastAPI Middleware → OW-AI Governance
                                                   ↓
                            Risk Assessment → Policy Check
                                                   ↓
                            Route Handler (if approved)
                                                   ↓
                            Response + Audit Log

GOVERNANCE RULES:
    ┌──────────────────────────────────────────────────────────┐
    │ Request Header: X-Agent-ID                               │
    │ → Indicates request is from AI agent                     │
    │ → All agent requests are governed                        │
    │                                                          │
    │ Request Header: X-Bypass-Governance                      │
    │ → Only honored for pre-approved service accounts         │
    │ → Requires API key with bypass permission                │
    │                                                          │
    │ Endpoint Risk Levels:                                    │
    │ → GET /api/*           : LOW (auto-approve)              │
    │ → POST /api/read/*     : LOW (auto-approve)              │
    │ → POST /api/*          : MEDIUM (evaluate)               │
    │ → PUT /api/*           : MEDIUM (evaluate)               │
    │ → DELETE /api/*        : HIGH (requires approval)        │
    │ → POST /api/admin/*    : CRITICAL (executive approval)   │
    └──────────────────────────────────────────────────────────┘

Engineer: OW-AI Enterprise
"""

import os
import time
import json
import hashlib
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime, UTC
from dataclasses import dataclass, field
from enum import Enum

# FastAPI imports
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
import httpx

# ============================================
# CONFIGURATION
# ============================================

OWAI_API_KEY = os.environ.get("OWKAI_API_KEY", "owkai_admin_your_key_here")
OWAI_BASE_URL = os.environ.get("OWAI_BASE_URL", "https://pilot.owkai.app")

# Service accounts that can bypass governance (for internal services)
BYPASS_ALLOWED_KEYS = set(os.environ.get("BYPASS_ALLOWED_KEYS", "").split(","))


# ============================================
# RISK LEVEL DEFINITIONS
# ============================================

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EndpointRisk:
    """Risk assessment for an endpoint."""
    level: RiskLevel
    score: int
    requires_approval: bool
    description: str


# Endpoint risk mappings
ENDPOINT_RISK_MAP: Dict[str, EndpointRisk] = {
    # Read operations - LOW risk
    "GET:*": EndpointRisk(RiskLevel.LOW, 15, False, "Read operation"),
    "POST:/api/search": EndpointRisk(RiskLevel.LOW, 20, False, "Search operation"),
    "POST:/api/query": EndpointRisk(RiskLevel.LOW, 25, False, "Query operation"),

    # Standard write operations - MEDIUM risk
    "POST:*": EndpointRisk(RiskLevel.MEDIUM, 50, False, "Create operation"),
    "PUT:*": EndpointRisk(RiskLevel.MEDIUM, 55, False, "Update operation"),
    "PATCH:*": EndpointRisk(RiskLevel.MEDIUM, 50, False, "Partial update"),

    # Destructive operations - HIGH risk
    "DELETE:*": EndpointRisk(RiskLevel.HIGH, 75, True, "Delete operation"),
    "POST:/api/bulk-delete": EndpointRisk(RiskLevel.HIGH, 85, True, "Bulk delete"),
    "POST:/api/export": EndpointRisk(RiskLevel.HIGH, 70, True, "Data export"),

    # Admin operations - CRITICAL risk
    "POST:/api/admin/*": EndpointRisk(RiskLevel.CRITICAL, 95, True, "Admin operation"),
    "DELETE:/api/admin/*": EndpointRisk(RiskLevel.CRITICAL, 98, True, "Admin delete"),
    "POST:/api/users/delete-all": EndpointRisk(RiskLevel.CRITICAL, 100, True, "Mass deletion"),
}


def get_endpoint_risk(method: str, path: str) -> EndpointRisk:
    """
    Determine risk level for an endpoint.

    Checks specific patterns first, then falls back to method-based defaults.
    """
    # Check specific endpoint patterns
    for pattern, risk in ENDPOINT_RISK_MAP.items():
        pattern_method, pattern_path = pattern.split(":", 1)

        if method != pattern_method and pattern_method != "*":
            continue

        if pattern_path == "*":
            continue  # Skip wildcards for now

        if pattern_path.endswith("/*"):
            prefix = pattern_path[:-2]
            if path.startswith(prefix):
                return risk
        elif path == pattern_path:
            return risk

    # Fall back to method-based default
    method_default = f"{method}:*"
    if method_default in ENDPOINT_RISK_MAP:
        return ENDPOINT_RISK_MAP[method_default]

    # Ultimate fallback
    return EndpointRisk(RiskLevel.MEDIUM, 50, False, "Unknown endpoint")


# ============================================
# OW-AI GOVERNANCE CLIENT
# ============================================

class OWAIGovernanceMiddlewareClient:
    """Async client for OW-AI governance in middleware context."""

    def __init__(self):
        self.base_url = OWAI_BASE_URL.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {OWAI_API_KEY}",
                "Content-Type": "application/json"
            }
        )

    async def evaluate_request(
        self,
        method: str,
        path: str,
        agent_id: str,
        body: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        risk: Optional[EndpointRisk] = None
    ) -> Dict[str, Any]:
        """
        Submit API request to OW-AI for governance evaluation.

        Returns:
            {
                "decision": "ALLOW" | "DENY" | "REQUIRE_APPROVAL",
                "action_id": 123,
                "risk_score": 75,
                "reason": "..."
            }
        """
        payload = {
            "agent_id": agent_id,
            "action_type": f"api_{method.lower()}",
            "description": f"{method} {path}",
            "tool_name": "fastapi",
            "target_system": "api-server",
            "risk_context": {
                "method": method,
                "path": path,
                "has_body": body is not None,
                "endpoint_risk_level": risk.level.value if risk else "unknown",
                "endpoint_risk_score": risk.score if risk else 50
            }
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/authorization/agent-action",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            # Determine decision based on risk and approval
            if result.get("requires_approval"):
                return {
                    "decision": "REQUIRE_APPROVAL",
                    "action_id": result.get("action_id"),
                    "risk_score": result.get("risk_score"),
                    "reason": "Manual approval required"
                }
            else:
                return {
                    "decision": "ALLOW",
                    "action_id": result.get("action_id"),
                    "risk_score": result.get("risk_score"),
                    "reason": "Auto-approved"
                }

        except Exception as e:
            # Fail-open or fail-closed based on configuration
            return {
                "decision": "DENY",
                "action_id": None,
                "risk_score": 100,
                "reason": f"Governance check failed: {str(e)}"
            }

    async def wait_for_approval(self, action_id: int, timeout: int = 60) -> bool:
        """Poll for approval status (with short timeout for API context)."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/agent-action/status/{action_id}"
                )
                response.raise_for_status()
                status = response.json()

                if status.get("status") == "approved":
                    return True
                elif status.get("status") == "rejected":
                    return False

                await asyncio.sleep(2)

            except Exception:
                await asyncio.sleep(2)

        return False

    async def close(self):
        await self.client.aclose()


# Global governance client
governance_client = OWAIGovernanceMiddlewareClient()


# ============================================
# FASTAPI MIDDLEWARE
# ============================================

class OWAIGovernanceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces OW-AI governance on agent requests.

    Features:
    - Identifies agent requests via X-Agent-ID header
    - Evaluates risk based on endpoint and method
    - Routes to approval workflow if required
    - Logs all actions for audit compliance
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request through governance pipeline."""

        start_time = time.time()

        # Extract governance-relevant headers
        agent_id = request.headers.get("X-Agent-ID")
        bypass_key = request.headers.get("X-Bypass-Governance")
        request_id = request.headers.get("X-Request-ID", self._generate_request_id())

        # Skip governance for non-agent requests
        if not agent_id:
            return await call_next(request)

        # Check bypass permission
        if bypass_key and bypass_key in BYPASS_ALLOWED_KEYS:
            response = await call_next(request)
            response.headers["X-Governance-Status"] = "bypassed"
            return response

        # Get endpoint risk assessment
        method = request.method
        path = request.url.path
        risk = get_endpoint_risk(method, path)

        # Log governance check
        print(f"🔒 [Governance] Agent: {agent_id}, {method} {path}, Risk: {risk.level.value}")

        # For low-risk operations, skip OW-AI call (performance optimization)
        if risk.level == RiskLevel.LOW and not risk.requires_approval:
            response = await call_next(request)
            response.headers["X-Governance-Status"] = "auto-approved"
            response.headers["X-Risk-Level"] = risk.level.value
            return response

        # Evaluate with OW-AI
        try:
            body = None
            if method in ("POST", "PUT", "PATCH"):
                body = await self._get_request_body(request)

            evaluation = await governance_client.evaluate_request(
                method=method,
                path=path,
                agent_id=agent_id,
                body=body,
                risk=risk
            )

            decision = evaluation.get("decision", "DENY")
            action_id = evaluation.get("action_id")

            print(f"📊 [Governance] Decision: {decision}, Action ID: {action_id}")

            if decision == "DENY":
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Request blocked by governance policy",
                        "reason": evaluation.get("reason"),
                        "action_id": action_id,
                        "risk_score": evaluation.get("risk_score")
                    },
                    headers={
                        "X-Governance-Status": "denied",
                        "X-Action-ID": str(action_id) if action_id else ""
                    }
                )

            elif decision == "REQUIRE_APPROVAL":
                # For synchronous API, we can wait briefly or return pending
                print(f"⏳ [Governance] Waiting for approval (action_id: {action_id})")

                approved = await governance_client.wait_for_approval(
                    action_id,
                    timeout=30  # Short timeout for API context
                )

                if not approved:
                    return JSONResponse(
                        status_code=202,  # Accepted but pending
                        content={
                            "status": "pending_approval",
                            "message": "Request requires approval. Check back later.",
                            "action_id": action_id,
                            "check_status_url": f"/api/governance/status/{action_id}"
                        },
                        headers={
                            "X-Governance-Status": "pending",
                            "X-Action-ID": str(action_id)
                        }
                    )

                print(f"✅ [Governance] Approved!")

            # Execute the actual request
            response = await call_next(request)

            # Add governance headers to response
            response.headers["X-Governance-Status"] = "approved"
            response.headers["X-Action-ID"] = str(action_id) if action_id else ""
            response.headers["X-Risk-Level"] = risk.level.value
            response.headers["X-Processing-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

            return response

        except Exception as e:
            print(f"❌ [Governance] Error: {e}")

            # Fail-closed: deny on governance error
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Governance service unavailable",
                    "details": str(e)
                },
                headers={"X-Governance-Status": "error"}
            )

    async def _get_request_body(self, request: Request) -> Optional[Dict]:
        """Safely extract request body."""
        try:
            body = await request.body()
            if body:
                return json.loads(body)
        except Exception:
            pass
        return None

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        timestamp = str(time.time()).encode()
        return hashlib.sha256(timestamp).hexdigest()[:16]


# ============================================
# FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title="OW-AI Governed API",
    description="Example API with OW-AI enterprise governance middleware",
    version="1.0.0"
)

# Add governance middleware
app.add_middleware(OWAIGovernanceMiddleware)


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/api/users")
async def list_users():
    """List users - LOW RISK (auto-approved for agents)."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
    }


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID - LOW RISK."""
    return {"id": user_id, "name": "Alice", "email": "alice@example.com"}


@app.post("/api/users")
async def create_user(request: Request):
    """Create user - MEDIUM RISK (evaluated)."""
    body = await request.json()
    return {
        "status": "created",
        "user": {
            "id": 123,
            **body
        }
    }


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, request: Request):
    """Update user - MEDIUM RISK (evaluated)."""
    body = await request.json()
    return {
        "status": "updated",
        "user_id": user_id,
        "changes": body
    }


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """Delete user - HIGH RISK (requires approval)."""
    return {
        "status": "deleted",
        "user_id": user_id,
        "message": "User permanently deleted"
    }


@app.post("/api/bulk-delete")
async def bulk_delete(request: Request):
    """Bulk delete - HIGH RISK (requires approval)."""
    body = await request.json()
    return {
        "status": "deleted",
        "count": len(body.get("ids", [])),
        "message": "Items permanently deleted"
    }


@app.post("/api/admin/reset-database")
async def reset_database():
    """Reset database - CRITICAL RISK (requires executive approval)."""
    return {
        "status": "reset",
        "message": "Database reset to default state",
        "warning": "All data has been erased"
    }


@app.get("/api/governance/status/{action_id}")
async def check_governance_status(action_id: int):
    """Check status of a pending governance action."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OWAI_BASE_URL}/api/agent-action/status/{action_id}",
                headers={"Authorization": f"Bearer {OWAI_API_KEY}"}
            )
            return response.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint (not governed)."""
    return {"status": "healthy", "governance": "enabled"}


# ============================================
# TESTING
# ============================================

def test_middleware():
    """Test the middleware functionality."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     OW-AI Integration Example: FastAPI Middleware             ║
║                                                               ║
║     This example demonstrates API governance middleware       ║
║     that intercepts and governs agent requests.               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    import uvicorn

    print("\n📋 Endpoint Risk Levels:")
    print("-" * 60)
    print("GET /api/*           : LOW (auto-approve)")
    print("POST /api/*          : MEDIUM (evaluate)")
    print("DELETE /api/*        : HIGH (requires approval)")
    print("POST /api/admin/*    : CRITICAL (executive approval)")

    print("\n🔑 Agent Request Headers:")
    print("-" * 60)
    print("X-Agent-ID: your-agent-id    (identifies agent requests)")
    print("X-Bypass-Governance: key     (for trusted service accounts)")

    print("\n📝 Example Requests:")
    print("-" * 60)
    print("# Low-risk (auto-approved):")
    print('curl -H "X-Agent-ID: test-agent" http://localhost:8000/api/users')
    print("")
    print("# High-risk (requires approval):")
    print('curl -X DELETE -H "X-Agent-ID: test-agent" http://localhost:8000/api/users/1')

    print("\n🚀 Starting server on http://localhost:8000")
    print("-" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    test_middleware()
