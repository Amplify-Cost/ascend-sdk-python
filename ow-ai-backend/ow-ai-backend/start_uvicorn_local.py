#!/usr/bin/env python3
"""
Local Uvicorn Startup Script - Master Prompt Compliant
Ensures proper local environment configuration before starting server
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

def start_local_server():
    """Start enterprise backend with proper local configuration"""
    
    print("🏢 STARTING OW-AI ENTERPRISE BACKEND (UVICORN LOCAL MODE)")
    print("=========================================================")
    
    # Load environment variables from .env file FIRST
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
    else:
        print(f"⚠️  No .env file found at: {env_path}")
    
    # Verify critical environment variables are set
    required_vars = ['SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("🔧 Ensure your .env file contains these variables")
        return False
    
    print("✅ All required environment variables found")
    print("🚀 Starting FastAPI server with Uvicorn...")
    
    # Start uvicorn server with proper configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    success = start_local_server()
    if not success:
        sys.exit(1)
