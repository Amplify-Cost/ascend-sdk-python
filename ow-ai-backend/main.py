# main.py - CLEAN VERSION
from dotenv import load_dotenv
import openai
import os
import logging
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from database import Base, engine, get_db
from config import ALLOWED_ORIGINS, OPENAI_API_KEY

# Import routers
from routes.auth_routes import router as auth_router
from routes.main_routes import router as main_router
from routes.analytics_routes import router as analytics_router
from routes.agent_routes import router as agent_router
from routes.rule_routes import router as rule_router
from routes.alert_summary import router as alert_summary_router
from routes.alert_routes import router as alerts_router
from routes.smart_rules_routes import router as smart_rule_router

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
    description="AI-powered security monitoring platform with NIST/MITRE compliance",
    version="1.0.0",
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

# CORS configuration - Load from environment
cors_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
cors_origins_alt = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if os.getenv("CORS_ALLOWED_ORIGINS") else []

# Combine both possible environment variable names
all_origins = list(set(cors_origins + cors_origins_alt))
all_origins = [origin.strip() for origin in all_origins if origin.strip()]

# Fallback origins if none are set
if not all_origins:
    all_origins = [
        "https://passionate-elegance-production.up.railway.app",
        "https://owai-production.up.railway.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ]

print(f"🚀 CORS Origins: {all_origins}")

# Add CORS middleware
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

# Register routers (CLEAN - NO DUPLICATES)
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(analytics_router, prefix="/analytics")
app.include_router(agent_router)
app.include_router(rule_router)
app.include_router(alert_summary_router)
app.include_router(alerts_router)
app.include_router(smart_rule_router)

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

# Debug endpoint (temporary)
@app.get("/debug/env")
async def debug_env():
    return {
        "allowed_origins": os.getenv("ALLOWED_ORIGINS"),
        "cors_allowed_origins": os.getenv("CORS_ALLOWED_ORIGINS"), 
        "secret_key_exists": bool(os.getenv("SECRET_KEY")),
        "openai_key_exists": bool(os.getenv("OPENAI_API_KEY")),
        "environment": os.getenv("ENVIRONMENT"),
        "cors_origins_loaded": all_origins
    }

# Health check
@app.get("/health")
async def health_check():
    try:
        from sqlalchemy.orm import Session
        db: Session = next(get_db())
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": "connected",
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Database connection failed"
            }
        )

@app.get("/")
async def root():
    return {"message": "OW-AI Backend API is running", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting OW-AI Backend API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)