#!/usr/bin/env python3
"""
Simplified Enterprise Local Startup
Master Prompt Compliant: Production-identical with simplified configuration
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        logger.info("✅ Environment variables loaded from .env")
    else:
        logger.warning("⚠️ No .env file found, using system environment")

def validate_environment():
    """Validate required environment variables"""
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("❌ Missing required variables: %s", missing_vars)
        return False
    
    logger.info("✅ Environment validation passed")
    return True

def main():
    """Start the enterprise backend"""
    logger.info("🏢 Starting OW-AI Enterprise Backend (Local Production Mode)")
    logger.info("=" * 60)
    
    # Load and validate environment
    load_environment()
    if not validate_environment():
        sys.exit(1)
    
    # Show configuration
    logger.info("🔍 Configuration:")
    logger.info("   Database: %s", os.getenv('DATABASE_URL', 'Not set')[:50] + "...")
    logger.info("   Environment: %s", os.getenv('ENVIRONMENT', 'development'))
    logger.info("   Algorithm: %s", os.getenv('ALGORITHM', 'HS256'))
    
    # Start the application
    try:
        logger.info("🚀 Starting FastAPI application...")
        import main
        logger.info("✅ Enterprise backend started successfully")
    except Exception as e:
        logger.error("❌ Failed to start application: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
