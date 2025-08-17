#!/usr/bin/env python3
"""
Railway Startup Script - Master Prompt Compliant
CRITICAL: Ensures proper healthcheck response for Railway
"""
import os
import sys
import logging
import time
import signal
from pathlib import Path

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    logging.info("🛑 Graceful shutdown initiated")
    sys.exit(0)

def main():
    """
    Master Prompt Compliant Railway Startup
    CRITICAL: Must start server and respond to healthchecks
    """
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        logging.info("🏢 Starting OW-AI Enterprise Backend (Railway Production)")
        logging.info("🎯 Master Prompt Compliance: Enterprise deployment standards")
        logging.info("🏥 Railway healthcheck optimization enabled")
        
        # Validate critical environment variables
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logging.error(f"❌ Missing required environment variables: {missing_vars}")
            logging.error("🔧 Please set these in Railway Variables tab")
            sys.exit(1)
        
        # Change to backend directory if needed
        backend_path = Path(__file__).parent / 'ow-ai-backend'
        if backend_path.exists():
            os.chdir(backend_path)
            logging.info(f"✅ Changed to backend directory: {backend_path}")
        else:
            logging.info("✅ Already in correct directory")
        
        # Set environment for Railway
        os.environ['RAILWAY_DEPLOYMENT'] = 'true'
        os.environ['HEALTHCHECK_ENABLED'] = 'true'
        
        # Import and run the enterprise backend
        logging.info("🚀 Loading enterprise modules...")
        
        # Start uvicorn with Railway-optimized configuration
        import uvicorn
        
        port = int(os.getenv('PORT', 8000))
        host = "0.0.0.0"
        
        logging.info(f"🌐 Starting server on {host}:{port}")
        logging.info("🏢 Enterprise features: Enabled")
        logging.info("🔐 Authentication: Cookie-only (Master Prompt compliant)")
        logging.info("🏥 Railway healthcheck: /health endpoint active")
        
        # CRITICAL: Railway-specific uvicorn configuration
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            # CRITICAL Railway settings:
            timeout_keep_alive=5,  # Keep connections alive
            timeout_graceful_shutdown=30,  # Graceful shutdown
            loop="asyncio",  # Stable event loop
            # No reload in production
            reload=False
        )
        
    except Exception as e:
        logging.error(f"❌ Startup failed: {e}")
        logging.error("🔧 Check Railway logs for detailed error information")
        # Don't exit immediately, give Railway time to report the error
        time.sleep(10)
        sys.exit(1)

if __name__ == "__main__":
    main()
