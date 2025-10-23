"""
Enterprise Codebase Audit
Analyze and categorize all files for proper organization
"""
import os
from collections import defaultdict
from pathlib import Path

print("=" * 80)
print("🏢 ENTERPRISE CODEBASE AUDIT")
print("=" * 80)
print()

# Category definitions
categories = {
    'core_app': [],           # Essential application files
    'config': [],             # Configuration files
    'infrastructure': [],     # Core infrastructure (models, routes, services, etc)
    'scripts': [],            # Utility scripts
    'backups': [],            # Backup files
    'temp': [],               # Temporary/test files
    'docs': [],               # Documentation
    'deployment': [],         # Deployment related
    'database': [],           # Database files
}

# Patterns for categorization
patterns = {
    'core_app': ['main.py', 'requirements.txt', 'README.md', '__init__.py'],
    'config': ['.env', 'config.py', '.ini', 'Dockerfile'],
    'infrastructure': ['core/', 'models/', 'routes/', 'services/', 'schemas/', 'middleware/'],
    'backups': ['.backup', '.bak', '.old', 'backup_'],
    'temp': ['test_', 'temp_', 'check_', 'debug_', 'diagnose_', 'try_', 'fix_', 'add_'],
    'docs': ['.md', '.html', '.txt', 'README', 'SUMMARY'],
    'deployment': ['Dockerfile', '.json', 'deploy_', 'aws_', 'migration-'],
    'database': ['.db', '.sql', 'alembic/', 'migrations/'],
}

# Scan directory
for item in os.listdir('.'):
    if item.startswith('.'):
        continue
    
    path = Path(item)
    categorized = False
    
    # Check patterns
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            if pattern in item.lower() or (path.is_dir() and f"{item}/" in pattern_list):
                categories[category].append(item)
                categorized = True
                break
        if categorized:
            break
    
    if not categorized:
        categories['scripts'].append(item)

# Display results
print("📊 CODEBASE ANALYSIS\n")

for category, files in categories.items():
    if files:
        print(f"\n{'='*80}")
        print(f"📁 {category.upper().replace('_', ' ')}: {len(files)} items")
        print(f"{'='*80}")
        
        # Show first 10 items
        for i, item in enumerate(sorted(files)[:10]):
            path = Path(item)
            if path.is_dir():
                print(f"  📂 {item}/")
            else:
                size = path.stat().st_size if path.exists() else 0
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                print(f"  📄 {item} ({size_str})")
        
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")

# Summary
print("\n" + "="*80)
print("📈 SUMMARY")
print("="*80)
total_files = sum(len(files) for files in categories.values())
print(f"Total items: {total_files}")
print(f"\nBreakdown:")
for cat, files in categories.items():
    if files:
        pct = (len(files) / total_files * 100)
        print(f"  {cat.replace('_', ' ').title():.<30} {len(files):>3} ({pct:>5.1f}%)")

print("\n" + "="*80)
print("💡 RECOMMENDATION: Clean up temporary and backup files")
print("="*80)
