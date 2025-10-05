with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# Find the datetime calculation section
old_code = '''        sla_hours_remaining = None
        if wf.started_at:
            deadline = wf.started_at + timedelta(hours=24)
            sla_hours_remaining = (deadline - datetime.utcnow()).total_seconds() / 3600'''

new_code = '''        sla_hours_remaining = None
        if wf.started_at:
            deadline = wf.started_at + timedelta(hours=24)
            now = datetime.now(UTC) if wf.started_at.tzinfo else datetime.utcnow()
            sla_hours_remaining = (deadline - now).total_seconds() / 3600'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Fixed datetime timezone issue")
else:
    print("❌ Code pattern not found")
    exit(1)

with open('routes/unified_governance_routes.py', 'w') as f:
    f.write(content)
