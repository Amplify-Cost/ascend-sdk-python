with open('main.py', 'r') as f:
    lines = f.readlines()

start = None
end = None

for i, line in enumerate(lines):
    if '# === ENTERPRISE ORCHESTRATION' in line:
        start = i
        for j in range(i, min(len(lines), i+100)):
            if 'return {' in lines[j]:
                end = j
                break
        break

if start and end:
    indent = '                '
    new = f'''{indent}# === ENTERPRISE ORCHESTRATION (Service Layer) ===
{indent}try:
{indent}    from services.orchestration_service import get_orchestration_service
{indent}    orch = get_orchestration_service(db)
{indent}    result = orch.orchestrate_action(
{indent}        action_id=action_id,
{indent}        risk_level=risk_level,
{indent}        risk_score=action.risk_score,
{indent}        action_type=data["action_type"]
{indent}    )
{indent}    if result.get("alert_created"):
{indent}        logger.info(f"Alert created for action {{action_id}}")
{indent}except Exception as e:
{indent}    logger.warning(f"Orchestration failed: {{e}}")
{indent}
'''
    
    new_lines = lines[:start] + [new] + lines[end:]
    with open('main.py', 'w') as f:
        f.writelines(new_lines)
    print("Done")
