with open('main.py', 'r') as f:
    lines = f.readlines()

# Find the function
for i, line in enumerate(lines):
    if '@app.post("/agent-actions")' in line:
        print(f"=== FUNCTION STARTS AT LINE {i+1} ===\n")
        
        # Show next 200 lines with structure markers
        depth = 0
        for j in range(i, min(len(lines), i+200)):
            line_text = lines[j].rstrip()
            
            # Track try/except structure
            if 'try:' in line_text:
                depth += 1
                print(f"{j+1:4d} {'  '*depth}[TRY #{depth}] {line_text}")
            elif 'except' in line_text:
                print(f"{j+1:4d} {'  '*depth}[EXCEPT #{depth}] {line_text}")
                depth -= 1
            elif 'return {' in line_text:
                print(f"{j+1:4d} {'  '*depth}[RETURN] {line_text}")
            elif '# ===' in line_text or 'ORCHESTRATION' in line_text:
                print(f"{j+1:4d} {'  '*depth}>>> {line_text}")
            elif line_text.startswith('@app.'):
                print(f"\n=== NEXT FUNCTION AT LINE {j+1} ===")
                break
        break
