from models import Alert
from sqlalchemy import inspect

# Get the Alert model columns
mapper = inspect(Alert)
columns = {column.key: str(column.type) for column in mapper.columns}

print("Alert Model Fields:")
print("-" * 40)
for field, field_type in columns.items():
    print(f"  {field}: {field_type}")
print("-" * 40)

# Check if we need to add missing fields
required_fields = ['title', 'message', 'severity', 'type', 'source']
missing = [f for f in required_fields if f not in columns]
if missing:
    print(f"⚠️  Missing fields: {missing}")
else:
    print("✅ All required fields present")
