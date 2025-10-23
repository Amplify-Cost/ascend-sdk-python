import os
import re

print("=== DATABASE SCHEMA ANALYSIS ===\n")

# Find SQLAlchemy models
model_files = []
for root, dirs, files in os.walk('.'):
    if 'venv' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                if 'Base' in content and 'Column' in content:
                    model_files.append(filepath)

print(f"Found {len(model_files)} model files\n")

for filepath in model_files[:5]:
    print(f"\nAnalyzing: {filepath}")
    with open(filepath, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'class' in line and '(Base)' in line:
                print(f"  Model: {line.strip()}")
                # Show next 10 lines (fields)
                for j in range(i+1, min(i+11, len(lines))):
                    if 'Column' in lines[j]:
                        print(f"    {lines[j].strip()}")
                    elif 'class' in lines[j]:
                        break
