"""Check the actual Workflow model definition"""
from models import Workflow
import inspect

print("=== WORKFLOW MODEL DEFINITION ===")
print()

# Get the model's columns
print("Model attributes:")
for attr in dir(Workflow):
    if not attr.startswith('_') and not callable(getattr(Workflow, attr)):
        print(f"  • {attr}")

print()
print("Checking __init__ signature:")
try:
    sig = inspect.signature(Workflow.__init__)
    print(f"  {sig}")
except:
    print("  (Could not inspect __init__)")

# Try to see the table definition
print()
print("Table columns from __table__:")
if hasattr(Workflow, '__table__'):
    for col in Workflow.__table__.columns:
        print(f"  • {col.name}: {col.type} (nullable={col.nullable})")
