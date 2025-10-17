import time
deployment_marker = f"# FORCE_REBUILD_{int(time.time())}"

with open('main.py', 'r') as f:
    content = f.read()

# Add deployment marker at the top
lines = content.split('\n')
lines.insert(1, deployment_marker)
content = '\n'.join(lines)

with open('main.py', 'w') as f:
    f.write(content)

print(f"Added deployment marker: {deployment_marker}")
