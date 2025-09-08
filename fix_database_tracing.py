with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Add database tracing with proper variable references
trace_code = '''
            # ENTERPRISE DIAGNOSTIC: Verify database update
            verify_result = db.execute(text("SELECT status, approved FROM agent_actions WHERE id = :action_id"), {"action_id": action_id}).fetchone()
            logger.info(f"ENTERPRISE TRACE: After UPDATE - Status: {verify_result[0] if verify_result else 'NOT_FOUND'}, Approved: {verify_result[1] if verify_result else 'NOT_FOUND'}")'''

# Find the correct location to insert tracing
if 'db.commit()' in content and '✅ REAL DATABASE UPDATED' in content:
    content = content.replace(
        'db.commit()\n            logger.info(f"✅ REAL DATABASE UPDATED: Action {action_id} status = {decision}")',
        f'db.commit(){trace_code}\n            logger.info(f"✅ REAL DATABASE UPDATED: Action {{action_id}} status = {{decision}}")'
    )
else:
    print("Target pattern not found - checking alternatives")

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("Fixed enterprise database tracing")
