import os
from database import Base, engine
from models import  AgentLog, AgentAction, Alert

DB_FILE = "agent_logs.db"

def reset_database():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"🗑️ Deleted old {DB_FILE}")
    else:
        print("ℹ️ No existing database found. Creating new one...")

    Base.metadata.create_all(bind=engine)
    print("✅ Database has been reset and tables created.")

if __name__ == "__main__":
    reset_database()
