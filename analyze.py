with open('main.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '# === ENTERPRISE ORCHESTRATION' in line:
        print(f"Orchestration starts: line {i+1}")
        for j in range(i, min(len(lines), i+100)):
            if 'return {' in lines[j]:
                print(f"Orchestration ends: line {j}")
                break
        break
