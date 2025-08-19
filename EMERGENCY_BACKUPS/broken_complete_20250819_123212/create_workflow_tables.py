# create_workflow_tables.py
from models import Base, Workflow, WorkflowExecution, WorkflowStep
from database import engine

if __name__ == "__main__":
    print("Creating workflow tables...")
    try:
        # This will only create tables that don't exist yet
        Base.metadata.create_all(bind=engine)
        print("✅ Workflow tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        workflow_tables = ['workflows', 'workflow_executions', 'workflow_steps']
        for table in workflow_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' NOT created")
                
    except Exception as e:
        print(f"❌ Error creating tables: {e}")