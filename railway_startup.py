#!/usr/bin/env python3
"""
Railway Startup Script - Master Prompt Compliant
Ensures enterprise-level deployment with proper error handling
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Master Prompt Compliant Railway Startup
    - Enterprise-level error handling
    - Proper environment validation
    - No shortcuts or feature removal
    """
    try:
        logging.info("🏢 Starting OW-AI Enterprise Backend (Railway Production)")
        logging.info("🎯 Master Prompt Compliance: Enterprise deployment standards")
        
        # Validate critical environment variables
        required_vars = ['SECRET_KEY', 'PORT']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logging.error(f"❌ Missing required environment variables: {missing_vars}")
            logging.error("🔧 Please set these in Railway Variables tab")
            sys.exit(1)
        
        # Change to backend directory
        backend_path = Path(__file__).parent / 'ow-ai-backend'
        if backend_path.exists():
            os.chdir(backend_path)
            logging.info(f"✅ Changed to backend directory: {backend_path}")
        else:
            logging.info("✅ Already in correct directory")
        
        # Import and run the enterprise backend
        logging.info("🚀 Loading enterprise modules...")
        
        # Start uvicorn with Railway configuration
        import uvicorn
        
        port = int(os.getenv('PORT', 8000))
        
        logging.info(f"🌐 Starting server on port {port}")
        logging.info("🏢 Enterprise features: Enabled")
        logging.info("🔐 Authentication: Cookie-only (Master Prompt compliant)")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logging.error(f"❌ Startup failed: {e}")
        logging.error("🔧 Check Railway logs for detailed error information")
        sys.exit(1)

if __name__ == "__main__":
    main()
