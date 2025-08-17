# ow-ai-sdk/main.py - Enterprise SDK Server
"""
OW-AI SDK Server
Provides client libraries and examples for enterprise integration
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OW-AI SDK Portal",
    description="Enterprise SDK and client libraries for OW-AI integration",
    version="1.0.0",
    docs_url="/sdk/docs",
    redoc_url="/sdk/redoc"
)

# CORS for SDK downloads
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Serve static SDK files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found - creating it")
    os.makedirs("static", exist_ok=True)

@app.get("/")
def sdk_portal():
    """SDK Portal Landing Page"""
    return {
        "message": "OW-AI Enterprise SDK Portal",
        "version": "1.0.0",
        "available_sdks": {
            "python": "/sdk/python",
            "javascript": "/sdk/javascript", 
            "typescript": "/sdk/typescript"
        },
        "documentation": "/sdk/docs",
        "examples": "/sdk/examples",
        "jwks_endpoint": "https://api.ow-ai.com/.well-known/jwks.json"
    }

@app.get("/sdk/python")
def python_sdk():
    """Python SDK Information"""
    return {
        "name": "ow-ai-python-sdk",
        "version": "1.0.0",
        "install": "pip install ow-ai-sdk",
        "documentation": "/sdk/python/docs",
        "examples": "/sdk/python/examples",
        "authentication": "RS256 JWT with JWKS",
        "quick_start": {
            "import": "from ow_ai_sdk import OWAIClient",
            "usage": "client = OWAIClient(api_key='your-key', base_url='https://api.ow-ai.com')"
        }
    }

@app.get("/sdk/javascript")
def javascript_sdk():
    """JavaScript SDK Information"""
    return {
        "name": "@ow-ai/sdk",
        "version": "1.0.0", 
        "install": "npm install @ow-ai/sdk",
        "documentation": "/sdk/javascript/docs",
        "examples": "/sdk/javascript/examples",
        "authentication": "RS256 JWT with JWKS",
        "quick_start": {
            "import": "import { OWAIClient } from '@ow-ai/sdk'",
            "usage": "const client = new OWAIClient({ apiKey: 'your-key', baseUrl: 'https://api.ow-ai.com' })"
        }
    }

@app.get("/sdk/examples")
def sdk_examples():
    """SDK Usage Examples"""
    return {
        "authentication": {
            "description": "Enterprise RS256 JWT authentication",
            "jwks_endpoint": "/.well-known/jwks.json",
            "example": "client.authenticate(api_key='your-enterprise-key')"
        },
        "agent_monitoring": {
            "description": "Submit agent actions for monitoring",
            "endpoint": "/agent-actions",
            "example": "client.submit_agent_action(action_data)"
        },
        "rule_management": {
            "description": "Manage governance rules",
            "endpoint": "/rules", 
            "example": "client.create_rule(rule_definition)"
        },
        "audit_trails": {
            "description": "Retrieve audit logs",
            "endpoint": "/logs",
            "example": "client.get_audit_trail(filters)"
        }
    }

@app.get("/sdk/status")
def sdk_status():
    """SDK Service Health Check"""
    return {
        "status": "healthy",
        "sdk_portal": "operational",
        "main_api": "https://api.ow-ai.com/health",
        "jwks_endpoint": "https://api.ow-ai.com/.well-known/jwks.json",
        "enterprise_features": "enabled"
    }

@app.get("/health")
def health_check():
    """Health check for SDK portal"""
    return {"status": "ok", "service": "ow-ai-sdk-portal"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
