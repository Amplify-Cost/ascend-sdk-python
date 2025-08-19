
import models  # ✅ Import the entire module ONCE
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import Base, engine, get_db
from schemas import AgentActionOut
from auth_utils import verify_token

from routes.auth_routes import router as auth_router
from routes.agent_routes import router as agent_router
from routes.log_routes import router as log_router
from routes.rule_routes import router as rule_router
from routes.alert_routes import router as alert_router
from routes.support_routes import router as support_router

# ---------------------------
# Configure Logging
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)
logger.info("Starting OW-AI backend...")

# ---------------------------
# Initialize FastAPI app
# ---------------------------
app = FastAPI(
# JWT Manager initialization for RS256
from .jwt_manager import init_jwt_manager

@app.on_event("startup")
async def startup_jwt_manager():
    """Initialize JWT manager on startup"""
    try:
        init_jwt_manager(
            secret_name=os.getenv("JWT_SECRETS_NAME", "ow-ai/jwt-keys"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            issuer=os.getenv("JWT_ISSUER", "http://localhost:8000"),
            audience=os.getenv("JWT_AUDIENCE", "ow-ai-api")
        )
        print("✅ JWT Manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize JWT Manager: {e}")
        raise

# Include JWKS routes
from .jwks_routes import router as jwks_router
app.include_router(jwks_router, tags=["authentication"])

    title="OW-AI Governance Platform",
    description="Enterprise-grade API for secure agent behavior logging, rule enforcement, audit trails, and security insights.",
    version="1.0.0",
    contact={"name": "OW-AI Security Team", "email": "security@ow-ai.com"},
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
)

# ---------------------------
# CORS Setup
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Replace with frontend origin in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Database Table Creation
# ---------------------------
Base.metadata.create_all(bind=engine)
logger.info("✅ Database tables created")

# ---------------------------
# Health Check
# ---------------------------
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "OW-AI backend is running"}

# ---------------------------
# Register Routers
# ---------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(agent_router, tags=["Agent Actions"])
app.include_router(log_router, tags=["Logs"])
app.include_router(rule_router, tags=["Rules"])
app.include_router(alert_router, tags=["Alerts"])
app.include_router(support_router, prefix="/support", tags=["Support"])

# ---------------------------
# Get Agent Actions
# ---------------------------
@app.get("/agent-actions", response_model=List[AgentActionOut], tags=["Agent Actions"])
def get_agent_actions(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    query = db.query(models.AgentAction)
    if agent_id:
        query = query.filter(models.AgentAction.agent_id == agent_id)
    return query.order_by(models.AgentAction.timestamp.desc()).all()

# ---------------------------
# High-Risk Actions Stub
# ---------------------------
@app.get("/agent-actions/high-risk", tags=["Agent Actions"])
def get_high_risk_actions():
    return [{
        "agent_id": "test-agent-123",
        "action": "unauthorized access",
        "risk_level": "high"
    }]

# ---------------------------
# Mark Action as False Positive
# ---------------------------
@app.post("/agent-actions/{action_id}/false-positive", tags=["Agent Actions"])
def mark_false_positive(
    action_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    action = db.query(models.AgentAction).filter(models.AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")
    action.is_false_positive = True
    db.commit()
    return {"message": "Marked as false positive"}
