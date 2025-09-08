with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Fix the function signature with proper dependency injection
old_signature = """async def authorize_enterprise_action_synchronized(
    action_id: int,
    request: Request,
    db: Session,
    admin_user: dict,
    execute_immediately: bool = True
):"""

new_signature = """async def authorize_enterprise_action_synchronized(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    execute_immediately: bool = True
):"""

content = content.replace(old_signature, new_signature)

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("Fixed dependency injection")
