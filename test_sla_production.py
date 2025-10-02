"""
Manual test script for SLA Monitor on production database
Run this to test escalation on the 4 overdue workflows
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.sla_monitor import SLAMonitor
import os

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

# Create database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def test_sla_monitor():
    """Test SLA Monitor on production data"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Testing SLA Monitor on Production Database")
        print("=" * 60)
        
        # Create SLA Monitor instance
        monitor = SLAMonitor()
        
        # Run check
        print("\n1. Running SLA check...")
        results = monitor.run_check(db)
        
        print(f"\n✅ Results:")
        print(f"   - Overdue workflows found: {results['overdue']}")
        print(f"   - Escalated: {results['escalated']}")
        print(f"   - Executive alerts: {results['alerted']}")
        
        # Get SLA metrics
        print("\n2. Getting SLA metrics...")
        metrics = monitor.get_sla_metrics(db)
        
        print(f"\n📊 SLA Metrics:")
        print(f"   - Total workflows: {metrics['total_workflows']}")
        print(f"   - Overdue: {metrics['overdue']}")
        print(f"   - On time: {metrics['on_time']}")
        print(f"   - Completed: {metrics['completed']}")
        print(f"   - Compliance rate: {metrics['compliance_rate']}%")
        
        print("\n" + "=" * 60)
        print("✅ SLA Monitor test completed successfully")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_sla_monitor()
