"""
Generate safe cleanup recommendations with verification
"""
from pathlib import Path
import os

print("🗑️  SAFE CLEANUP RECOMMENDATIONS")
print("=" * 80)

# Categories of files to review
cleanup_categories = {
    'backup_files': [],
    'broken_files': [],
    'deprecated_files': [],
    'test_files': [],
    'duplicate_docs': []
}

# Scan backend
backend_files = list(Path('.').glob('**/*.py')) + list(Path('.').glob('**/*.md'))

for file in backend_files:
    if '.git' in str(file) or 'venv' in str(file) or 'node_modules' in str(file):
        continue
    
    filename = file.name.lower()
    
    if any(x in filename for x in ['backup', '.bak', '.old']):
        cleanup_categories['backup_files'].append(str(file))
    elif 'broken' in filename:
        cleanup_categories['broken_files'].append(str(file))
    elif 'deprecated' in filename:
        cleanup_categories['deprecated_files'].append(str(file))
    elif filename.startswith('test_') and file.parent.name != 'tests':
        cleanup_categories['test_files'].append(str(file))

# Find duplicate docs
docs = list(Path('.').glob('**/*.md')) + list(Path('.').glob('**/*.html'))
doc_names = {}
for doc in docs:
    if doc.name in doc_names:
        cleanup_categories['duplicate_docs'].append(str(doc))
    else:
        doc_names[doc.name] = str(doc)

# Report
print("\n📦 BACKUP FILES (Safe to delete after verification):")
for f in sorted(cleanup_categories['backup_files'])[:20]:  # Show first 20
    print(f"  • {f}")
if len(cleanup_categories['backup_files']) > 20:
    print(f"  ... and {len(cleanup_categories['backup_files']) - 20} more")

print(f"\n🗑️  BROKEN FILES (Can be deleted):")
for f in sorted(cleanup_categories['broken_files']):
    print(f"  • {f}")

print(f"\n⚠️  DEPRECATED FILES (Review then delete):")
for f in sorted(cleanup_categories['deprecated_files']):
    print(f"  • {f}")

print(f"\n🧪 TEST FILES IN WRONG LOCATION:")
for f in sorted(cleanup_categories['test_files']):
    print(f"  • {f}")

# Generate cleanup script
with open('SAFE_CLEANUP_SCRIPT.sh', 'w') as f:
    f.write("#!/bin/bash\n")
    f.write("# Safe cleanup script - Run after verification\n")
    f.write("# Review each section before uncommenting\n\n")
    
    f.write("# Backup files\n")
    f.write("# mkdir -p .cleanup_archive/backups\n")
    for file in cleanup_categories['backup_files']:
        f.write(f"# mv '{file}' .cleanup_archive/backups/\n")
    
    f.write("\n# Broken files\n")
    for file in cleanup_categories['broken_files']:
        f.write(f"# rm '{file}'\n")

print(f"\n✅ Cleanup script generated: SAFE_CLEANUP_SCRIPT.sh")
print(f"   Total files identified for cleanup: {sum(len(v) for v in cleanup_categories.values())}")
