# Add comprehensive database tracing to the authorization function

with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Add database tracing after the UPDATE statement
trace_code = '''
            # ENTERPRISE DIAGNOSTIC: Verify database update
            verify_result = db.execute(text("SELECT status, approved FROM agent_actions WHERE id = :action_id"), {"action_id": action_id}).fetchone()
            logger.info(f"ENTERPRISE TRACE: After UPDATE - Status: {verify_result[0] if verify_result else 'NOT_FOUND'}, Approved: {verify_result[1] if verify_result else 'NOT_FOUND'}")'''

# Insert after the db.commit() line
content = content.replace(
    'db.commit()\n            logger.info(f"✅ REAL DATABASE UPDATED: Action {action_id} status = {decision}")',
    f'db.commit(){trace_code}\n            logger.info(f"✅ REAL DATABASE UPDATED: Action {action_id} status = {decision}")'
)

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("Added enterprise database tracing")
