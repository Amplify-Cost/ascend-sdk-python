from dotenv import load_dotenv
import openai
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from database import Base, engine
from routes.auth_routes import router as auth_router
from routes.main_routes import router as main_router
from routes.analytics_routes import router as analytics_router
from routes.agent_routes import router as agent_router
from routes.rule_routes import router as rule_router
from routes.alert_summary import router as alert_summary_router
from routes.alert_routes import router as alerts_router
from routes.smart_rules_routes import router as smart_rule_router

# Setup OAuth2 security scheme so Swagger shows the "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI(
    title="OW-AI Backend API",
    description="Use the Authorize button above to authenticate with your Bearer token.",
    version="1.0.0"
)

# Initialize DB
Base.metadata.create_all(bind=engine)

# CORS settings
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://passionate-elegance-production.up.railway.app",  # ✅ Allow deployed frontend
    "https://*.railway.app"  # Optional: wildcard for previews
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again soon."})

import logging
logging.basicConfig(level=logging.INFO)
logging.info("✅ FastAPI app started successfully.")

# Include all routers
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(analytics_router)
app.include_router(agent_router)
app.include_router(rule_router)
app.include_router(alert_summary_router)
app.include_router(alerts_router)
app.include_router(smart_rule_router)

# Health check
@app.get("/")
def health_check():
    return {"status": "OW-AI Backend is running"}

# Analytics mock data endpoint
@app.get("/analytics/trends")
def get_analytics_trends():
    return {
        "high_risk_daily": [
            {"date": "2025-06-18", "count": 4},
            {"date": "2025-06-19", "count": 7},
            {"date": "2025-06-20", "count": 5}
        ],
        "top_agents": [
            {"agent": "Agent001", "count": 10},
            {"agent": "Agent002", "count": 8}
        ],
        "top_tools": [
            {"tool": "ToolA", "count": 6},
            {"tool": "ToolB", "count": 4}
        ],
        "enriched_actions": [
            {
                "agent_id": "Agent001",
                "risk_level": "High",
                "mitre_tactic": "Initial Access",
                "nist_control": "AC-2",
                "recommendation": "Review and limit access controls"
            },
            {
                "agent_id": "Agent002",
                "risk_level": "Medium",
                "mitre_tactic": "Privilege Escalation",
                "nist_control": "AU-6",
                "recommendation": "Monitor privilege use"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Launching FastAPI with uvicorn manually...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
