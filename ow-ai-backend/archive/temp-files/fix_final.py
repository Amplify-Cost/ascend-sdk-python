with open('main.py', 'r') as f:
    lines = f.readlines()

# Find the return at line 1403
for i in range(1400, 1410):
    if i < len(lines) and 'return {' in lines[i] and '"status": "success"' in ''.join(lines[i:i+10]):
        # Add except block before return
        indent = '            '  # 12 spaces to match the return
        except_lines = [
            f'{indent}except Exception as e:\n',
            f'{indent}    logger.error(f"Action processing error: {{e}}")\n',
            f'{indent}    db.rollback()\n',
            f'{indent}    raise HTTPException(status_code=500, detail=str(e))\n',
            f'\n'
        ]
        
        # Insert before return
        for j, line in enumerate(except_lines):
            lines.insert(i + j, line)
        
        print(f"Added except block at line {i}")
        break

with open('main.py', 'w') as f:
    f.writelines(lines)
