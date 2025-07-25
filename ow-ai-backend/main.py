# main.py - UPDATED VERSION WITH SCHEMA FIX
from dotenv import load_dotenv
import openai
import os
import logging
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# ✅ FIXED: Correct SQLAlchemy imports
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from config import ALLOWED_ORIGINS, OPENAI_API_KEY, DATABASE_URL

# Import models - UPDATED TO INCLUDE PendingAgentAction
from models import AgentAction, Alert, PendingAgentAction

# Import routers - UPDATED TO INCLUDE AUTHORIZATION ROUTES
from routes.auth_routes import router as auth_router
from routes.main_routes import router as main_router
from routes.analytics_routes import router as analytics_router
from routes.agent_routes import router as agent_router
from routes.rule_routes import router as rule_router
from routes.alert_summary import router as alert_summary_router
from routes.alert_routes import router as alerts_router
from routes.smart_rules_routes import router as smart_rule_router
from routes.authorization_routes import router as authorization_router




# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log") if os.getenv("LOG_TO_FILE") == "true" else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = OPENAI_API_KEY

# Initialize FastAPI app
app = FastAPI(
    title="OW-AI Backend API",
    description="AI-powered security monitoring platform with NIST/MITRE compliance and Agent Authorization",
    version="1.1.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Security middleware (ORDER MATTERS!)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "passionate-elegance-production.up.railway.app",
        "owai-production.up.railway.app",
        "localhost"
    ]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS configuration
cors_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
cors_origins_alt = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if os.getenv("CORS_ALLOWED_ORIGINS") else []

all_origins = list(set(cors_origins + cors_origins_alt))
all_origins = [origin.strip() for origin in all_origins if origin.strip()]

if not all_origins:
    all_origins = [
        "https://passionate-elegance-production.up.railway.app",
        "https://owai-production.up.railway.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ]

print(f"🚀 CORS Origins: {all_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token"
    ],
    expose_headers=["*"]
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code} error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Database initialization
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(analytics_router, prefix="/analytics")
app.include_router(agent_router)
app.include_router(rule_router)
app.include_router(alert_summary_router)
app.include_router(alerts_router)
app.include_router(smart_rule_router)
app.include_router(authorization_router)



# OPTIONS handler for CORS preflight
@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
        }
    )

# ✅ NEW: Database schema fix endpoint
@app.post("/admin/fix-database-schema")
async def fix_database_schema():
    """Fix database schema by removing tenant_id column"""
    try:
        engine_fix = create_engine(DATABASE_URL)
        results = []
        
        with engine_fix.connect() as conn:
            # 1. Remove tenant_id column from pending_agent_actions if it exists
            try:
                conn.execute(text("""
                    ALTER TABLE pending_agent_actions 
                    DROP COLUMN IF EXISTS tenant_id
                """))
                results.append("✅ Removed tenant_id column from pending_agent_actions")
            except Exception as e:
                results.append(f"⚠️ tenant_id column removal: {str(e)}")
            
            # 2. Remove tenant_id column from agent_actions if it exists
            try:
                conn.execute(text("""
                    ALTER TABLE agent_actions 
                    DROP COLUMN IF EXISTS tenant_id
                """))
                results.append("✅ Removed tenant_id column from agent_actions")
            except Exception as e:
                results.append(f"⚠️ agent_actions tenant_id removal: {str(e)}")
            
            # 3. Remove tenant_id column from alerts if it exists
            try:
                conn.execute(text("""
                    ALTER TABLE alerts 
                    DROP COLUMN IF EXISTS tenant_id
                """))
                results.append("✅ Removed tenant_id column from alerts")
            except Exception as e:
                results.append(f"⚠️ alerts tenant_id removal: {str(e)}")
            
            conn.commit()
        
        logger.info("Database schema fix completed successfully")
        return {
            "status": "success",
            "message": "Database schema fixed successfully",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Database schema fix failed: {str(e)}")
        return {
            "status": "error", 
            "message": f"Database schema fix failed: {str(e)}"
        }

# ✅ EXISTING: Database fix endpoint
@app.post("/admin/fix-database")
async def fix_database():
    """Fix database by adding missing columns and tables"""
    try:
        engine_fix = create_engine(DATABASE_URL)
        results = []
        
        with engine_fix.connect() as conn:
            # 1. Add status column to alerts table
            try:
                conn.execute(text("""
                    ALTER TABLE alerts 
                    ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'new'
                """))
                results.append("✅ Added status column to alerts table")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    results.append("✅ Status column already exists in alerts")
                else:
                    results.append(f"⚠️ alerts status column: {str(e)}")
            
            # 2. Create pending_agent_actions table WITHOUT tenant_id
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS pending_agent_actions (
                        id SERIAL PRIMARY KEY,
                        agent_id VARCHAR NOT NULL,
                        action_type VARCHAR NOT NULL,
                        description TEXT,
                        tool_name VARCHAR,
                        risk_level VARCHAR,
                        action_payload TEXT,
                        target_system VARCHAR,
                        authorization_status VARCHAR DEFAULT 'pending',
                        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        reviewed_by VARCHAR,
                        reviewed_at TIMESTAMP,
                        review_notes TEXT,
                        ai_risk_score INTEGER,
                        nist_control VARCHAR,
                        mitre_tactic VARCHAR,
                        mitre_technique VARCHAR,
                        executed_at TIMESTAMP,
                        execution_result TEXT,
                        execution_status VARCHAR
                    )
                """))
                results.append("✅ Created pending_agent_actions table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    results.append("✅ pending_agent_actions table already exists")
                else:
                    results.append(f"⚠️ pending_agent_actions: {str(e)}")
            
            # 3. Add indexes for performance
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pending_actions_status 
                    ON pending_agent_actions(authorization_status)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pending_actions_agent_id 
                    ON pending_agent_actions(agent_id)
                """))
                results.append("✅ Added database indexes")
            except Exception as e:
                results.append(f"⚠️ indexes: {str(e)}")
            
            conn.commit()
        
        logger.info("Database fix completed successfully")
        return {
            "status": "success",
            "message": "Database fixed successfully",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Database fix failed: {str(e)}")
        return {
            "status": "error", 
            "message": f"Database fix failed: {str(e)}"
        }

# Debug endpoints
@app.get("/debug/env")
async def debug_env():
    return {
        "allowed_origins": os.getenv("ALLOWED_ORIGINS"),
        "cors_allowed_origins": os.getenv("CORS_ALLOWED_ORIGINS"), 
        "secret_key_exists": bool(os.getenv("SECRET_KEY")),
        "openai_key_exists": bool(os.getenv("OPENAI_API_KEY")),
        "environment": os.getenv("ENVIRONMENT"),
        "cors_origins_loaded": all_origins,
        "authorization_system": "enabled"
    }

@app.get("/debug/database-check")
async def debug_database_check():
    try:
        db: Session = next(get_db())
        
        agent_actions_count = db.query(AgentAction).count()
        alerts_count = db.query(Alert).count()
        
        try:
            pending_actions_count = db.query(PendingAgentAction).count()
        except Exception:
            pending_actions_count = 0
        
        sample_action = db.query(AgentAction).first()
        sample_alert = db.query(Alert).first()
        
        try:
            sample_pending = db.query(PendingAgentAction).first()
        except Exception:
            sample_pending = None
        
        db.close()
        
        return {
            "status": "connected",
            "agent_actions_count": agent_actions_count,
            "alerts_count": alerts_count,
            "pending_actions_count": pending_actions_count,
            "has_agent_actions": agent_actions_count > 0,
            "has_alerts": alerts_count > 0,
            "has_pending_actions": pending_actions_count > 0,
            "sample_action_id": sample_action.id if sample_action else None,
            "sample_alert_id": sample_alert.id if sample_alert else None,
            "sample_pending_id": sample_pending.id if sample_pending else None,
            "authorization_system_status": "operational"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# Health check
@app.get("/health")
async def health_check():
    try:
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))
        
        try:
            auth_table_check = db.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'pending_agent_actions'
            """)).fetchone()[0]
        except Exception:
            auth_table_check = 0
        
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.1.0",
            "database": "connected",
            "authorization_system": "enabled" if auth_table_check > 0 else "not_installed",
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/")
async def root():
    return {
        "message": "OW-AI Backend API is running", 
        "status": "ok",
        "version": "1.1.0",
        "features": [
            "Agent Action Monitoring",
            "AI-Powered Risk Assessment", 
            "NIST/MITRE Framework Mapping",
            "Real-time Alert Generation",
            "Smart Rule Generation",
            "Human Authorization System"
        ]
    }

@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting OW-AI Backend API with Authorization System...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


@app.post("/admin/fix-user-schema")
async def fix_user_schema():
    """Fix user table schema by adding missing columns"""
    try:
        engine_fix = create_engine(DATABASE_URL)
        results = []
        
        with engine_fix.connect() as conn:
            # Add missing columns to users table
            user_columns = [
                ("approval_level", "INTEGER DEFAULT 1"),
                ("is_emergency_approver", "BOOLEAN DEFAULT FALSE"),
                ("max_risk_approval", "INTEGER DEFAULT 50")
            ]
            
            for column_name, column_def in user_columns:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_def}
                    """))
                    results.append(f"✅ Added {column_name} column to users table")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        results.append(f"✅ {column_name} column already exists")
                    else:
                        results.append(f"⚠️ {column_name} column: {str(e)}")
            
            # Add missing columns to pending_agent_actions table  
            pending_columns = [
                ("ai_risk_score", "INTEGER"),
                ("contextual_risk_factors", "TEXT"),
                ("required_approval_level", "INTEGER DEFAULT 1"),
                ("current_approval_level", "INTEGER DEFAULT 0"),
                ("workflow_stage", "VARCHAR DEFAULT 'initial'"),
                ("auto_approve_at", "TIMESTAMP"),
                ("approval_chain", "TEXT"),
                ("required_approvers", "TEXT"),
                ("pending_approvers", "TEXT"),
                ("primary_approver_id", "INTEGER"),
                ("approved_by_user_id", "INTEGER"),
                ("conditional_approval", "BOOLEAN DEFAULT FALSE"),
                ("conditions", "TEXT"),
                ("approval_duration", "INTEGER"),
                ("approval_scope", "TEXT"),
                ("compliance_frameworks", "TEXT"),
                ("audit_trail", "TEXT"),
                ("emergency_approver_id", "INTEGER"),
                ("break_glass_used", "BOOLEAN DEFAULT FALSE"),
                ("execution_duration", "REAL"),
                ("affected_resources", "TEXT")
            ]
            
            for column_name, column_def in pending_columns:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE pending_agent_actions 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_def}
                    """))
                    results.append(f"✅ Added {column_name} to pending_agent_actions")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        results.append(f"✅ {column_name} already exists in pending_agent_actions")
                    else:
                        results.append(f"⚠️ {column_name}: {str(e)}")
            
            # Add missing column to alerts table
            try:
                conn.execute(text("""
                    ALTER TABLE alerts 
                    ADD COLUMN IF NOT EXISTS pending_action_id INTEGER
                """))
                results.append("✅ Added pending_action_id to alerts table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    results.append("✅ pending_action_id already exists in alerts")
                else:
                    results.append(f"⚠️ pending_action_id: {str(e)}")
            
            conn.commit()
        
        logger.info("User schema fix completed successfully")
        return {
            "status": "success",
            "message": "User schema fixed successfully",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"User schema fix failed: {str(e)}")
        return {
            "status": "error", 
            "message": f"User schema fix failed: {str(e)}"
        }
