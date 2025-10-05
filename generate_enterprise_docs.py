"""
Generate Enterprise-Level Documentation
Analyzes actual codebase to create technical documentation
"""
import os
import re
from pathlib import Path

def analyze_routes():
    """Analyze all API routes"""
    routes = []
    route_files = Path('routes').glob('*.py')
    
    for file in route_files:
        if 'backup' in str(file) or '.bak' in str(file):
            continue
            
        with open(file, 'r') as f:
            content = f.read()
            
        # Find router prefix
        prefix_match = re.search(r'router = APIRouter\(prefix=["\']([^"\']+)', content)
        prefix = prefix_match.group(1) if prefix_match else ''
        
        # Find all endpoints
        endpoints = re.findall(r'@router\.(get|post|put|delete)\(["\']([^"\']+)', content)
        
        for method, path in endpoints:
            routes.append({
                'file': file.name,
                'method': method.upper(),
                'path': prefix + path,
                'full_path': prefix + path
            })
    
    return sorted(routes, key=lambda x: x['full_path'])

def analyze_services():
    """Analyze service layer"""
    services = []
    service_files = Path('services').glob('*.py')
    
    for file in service_files:
        if file.name.startswith('__') or '.bak' in str(file):
            continue
            
        with open(file, 'r') as f:
            content = f.read()
        
        # Find class definitions
        classes = re.findall(r'class (\w+).*?:\s*"""(.*?)"""', content, re.DOTALL)
        
        for class_name, docstring in classes:
            services.append({
                'file': file.name,
                'name': class_name,
                'description': docstring.strip().split('\n')[0]
            })
    
    return services

def analyze_database():
    """Analyze database schema from SQL and Python"""
    tables = []
    
    # Check for SQL files
    for sql_file in Path('.').glob('*.sql'):
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Find CREATE TABLE statements
        table_matches = re.findall(r'CREATE TABLE.*?(\w+)\s*\((.*?)\);', content, re.DOTALL | re.IGNORECASE)
        
        for table_name, columns in table_matches:
            if table_name.lower() in ['if', 'not', 'exists']:
                continue
            tables.append(table_name)
    
    return sorted(set(tables))

# Generate documentation
print("# OW-AI Platform - Enterprise Technical Documentation\n")
print("Generated from production codebase\n")
print("---\n")

print("## 1. API Endpoints\n")
routes = analyze_routes()
print(f"**Total Endpoints:** {len(routes)}\n")

current_prefix = None
for route in routes:
    if route['full_path'].split('/')[1] if len(route['full_path'].split('/')) > 1 else None != current_prefix:
        current_prefix = route['full_path'].split('/')[1] if len(route['full_path'].split('/')) > 1 else None
        print(f"\n### {current_prefix.title() if current_prefix else 'Root'} Endpoints\n")
    
    print(f"- **{route['method']}** `{route['full_path']}`")

print("\n---\n")

print("## 2. Service Layer\n")
services = analyze_services()
print(f"**Total Services:** {len(services)}\n")

for service in services:
    print(f"### {service['name']}")
    print(f"*File:* `services/{service['file']}`")
    print(f"\n{service['description']}\n")

print("---\n")

print("## 3. Database Schema\n")
tables = analyze_database()
print(f"**Total Tables:** {len(tables)}\n")

for table in tables:
    print(f"- `{table}`")

