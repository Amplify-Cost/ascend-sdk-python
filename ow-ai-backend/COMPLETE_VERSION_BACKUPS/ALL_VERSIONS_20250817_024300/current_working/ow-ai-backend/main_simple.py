"""
Simplified main.py for cookie authentication testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import our simple components
from simple_auth_routes import router as auth_router
from local_jwt_manager import get_jwt_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cookie Auth Test",
    description="Testing cookie-based authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Cookie Auth Test Server", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok", "auth": "cookie-test"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
