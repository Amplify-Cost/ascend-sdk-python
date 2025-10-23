with open('routes/authorization_routes.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Remove non-printable characters
import string
printable = set(string.printable)
content = ''.join(filter(lambda x: x in printable, content))

# Write back clean file
with open('routes/authorization_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Cleaned authorization_routes.py")
