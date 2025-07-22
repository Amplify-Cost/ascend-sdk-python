from dotenv import load_dotenv
import openai
import os

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

# ✅ Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Define allowed origins explicitly
origins = [
    "https://passionate-elegance-production.up.railway.app", 
    "https://owai-production.up.railway.app"
]

print("✅ CORS Allowed Origins:", origins)

# ✅ Initialize FastAPI app
app = FastAPI(
    title="OW-AI Backend API",
    description="Use the Authorize button above to authenticate with your Bearer token.",
    version="1.0.0"
)

# 🔐 CORS middleware must be added BEFORE any routes are included!
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ✅ Add rate limiting middleware
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again soon."})

# ✅ OAuth2 token scheme for protected routes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ✅ DB initialization
Base.metadata.create_all(bind=engine)

# ✅ Register routers with correct prefixes
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(analytics_router, prefix="/analytics")  # <-- ensure prefix here
app.include_router(agent_router)
app.include_router(rule_router)
app.include_router(alert_summary_router)
app.include_router(alerts_router)
app.include_router(smart_rule_router)

# ✅ Health check route
@app.get("/")
def health_check():
    return {"status": "OW-AI Backend is running"}

# ✅ Local dev launcher
if __name__ == "__main__":
    import uvicorn
    print("🚀 Launching FastAPI with uvicorn manually...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
