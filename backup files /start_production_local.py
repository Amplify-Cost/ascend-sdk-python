#!/usr/bin/env python3
"""
Production-Identical Local Development Startup
Master Prompt Compliant: Exact mirror of Railway production environment
"""

import os
import sys
import logging
from pathlib import Path

# Configure production-identical logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('.enterprise/logs/owai-local.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def load_production_environment():
    """Load production-identical environment variables"""
    env_file = Path('.railway/secrets/local.env')
    
    if not env_file.exists():
        logger.error("❌ Production environment file not found: %s", env_file)
        sys.exit(1)
    
    # Load environment variables
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    logger.info("✅ Production-identical environment loaded")

def validate_production_secrets():
    """Validate all required production secrets are present"""
    required_secrets = [
        'SECRET_KEY', 'ALGORITHM', 'DATABASE_URL', 'OPENAI_API_KEY',
        'JWT_PRIVATE_KEY_PATH', 'JWT_PUBLIC_KEY_PATH'
    ]
    
    missing_secrets = []
    for secret in required_secrets:
        if not os.getenv(secret):
            missing_secrets.append(secret)
    
    if missing_secrets:
        logger.error("❌ Missing required production secrets: %s", missing_secrets)
        sys.exit(1)
    
    logger.info("✅ All production secrets validated")

def setup_production_directories():
    """Create production-identical directory structure"""
    directories = [
        '.enterprise/logs',
        '.enterprise/cache',
        '.enterprise/uploads',
        '.enterprise/exports'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ Production directory structure created")

def main():
    """Start the production-identical local environment"""
    logger.info("🏢 Starting OW-AI Enterprise Backend (Production-Identical Local)")
    logger.info("=" * 70)
    
    # Setup
    setup_production_directories()
    load_production_environment()
    validate_production_secrets()
    
    # Environment info
    logger.info("🔍 Production Environment Configuration:")
    logger.info("   Environment: %s", os.getenv('ENVIRONMENT', 'Unknown'))
    logger.info("   Algorithm: %s", os.getenv('ALGORITHM', 'Unknown'))
    logger.info("   Database: %s", os.getenv('DATABASE_URL', 'Unknown')[:50] + "...")
    logger.info("   Debug: %s", os.getenv('DEBUG', 'false'))
    logger.info("   Log Level: %s", os.getenv('LOG_LEVEL', 'INFO'))
    
    # Import and start the main application
    try:
        logger.info("🚀 Importing main application...")
        import main
        logger.info("✅ OW-AI Enterprise Backend started successfully")
    except ImportError as e:
        logger.error("❌ Could not import main application: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("❌ Error starting application: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
