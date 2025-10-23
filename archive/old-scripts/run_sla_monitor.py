#!/usr/bin/env python3
"""
SLA Monitor - Scheduled Task Entry Point
Runs every 15 minutes to check and escalate overdue workflows
"""
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.sla_monitor import SLAMonitor
from database import SQLALCHEMY_DATABASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run SLA Monitor check"""
    try:
        logger.info("🔍 Starting SLA Monitor check...")
        
        # Create database session
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # Run the monitor
            monitor = SLAMonitor()
            result = monitor.run_check(db)
            
            logger.info(f"✅ SLA Monitor completed: {result}")
            logger.info(f"   Escalated: {result['escalated']}")
            logger.info(f"   Alerted: {result['alerted']}")
            logger.info(f"   Checked: {result['checked']}")
            
            return 0
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ SLA Monitor failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
