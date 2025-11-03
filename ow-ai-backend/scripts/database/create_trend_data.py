from datetime import datetime, timedelta, UTC
from database import SessionLocal
from models import AgentAction
import random

db = SessionLocal()

print("🔧 Creating varied test data for trend visualization...")

# Clear old high-risk test actions
db.query(AgentAction).filter(
    AgentAction.agent_id.in_(['BackupManager_AI', 'SecurityScanner_AI', 'PaymentProcessor_AI'])
).delete()
db.commit()

# Create varied high-risk actions over last 7 days
agents = ['SecurityScanner_AI', 'BackupManager_AI', 'PaymentProcessor_AI']
tools = ['Nessus', 'AWS S3', 'Stripe API']
action_types = ['firewall_modification', 'delete_files', 'financial_transaction']

# Generate data with a trend: low → high → low
day_counts = [2, 4, 7, 12, 15, 10, 6]  # Shows a trend!

for day_offset in range(7):
    date = datetime.now(UTC) - timedelta(days=6-day_offset)
    count = day_counts[day_offset]
    
    for i in range(count):
        agent_idx = i % len(agents)
        action = AgentAction(
            agent_id=agents[agent_idx],
            action_type=action_types[agent_idx],
            tool_name=tools[agent_idx],
            risk_level='high',
            timestamp=date + timedelta(hours=i),
            summary=f"Test action for trend day {day_offset + 1}",
            status='pending'
        )
        db.add(action)
    
    print(f"📅 {date.date()}: Created {count} high-risk actions")

db.commit()
print("✅ Trend data created successfully!")
print("\nExpected trend: 2 → 4 → 7 → 12 → 15 → 10 → 6")

db.close()
