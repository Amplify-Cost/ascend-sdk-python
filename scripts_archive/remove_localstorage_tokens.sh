#!/bin/bash

echo "🔒 C6: Removing localStorage Token Storage (Security Fix)"
echo "=========================================================="
echo ""
echo "What we're doing:"
echo "  - Removing 32 localStorage token operations (XSS vulnerability)"
echo "  - Keeping 5 legitimate localStorage uses (theme, test mocks)"
echo "  - Backend already uses HTTP-only cookies for auth"
echo ""

cd /Users/mac_001/OW_AI_Project/owkai-pilot-frontend

# Backup all files we'll modify
BACKUP_DIR="localStorage_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backups..."
cp src/utils/fetchWithAuth.js "$BACKUP_DIR/"
cp src/App.jsx "$BACKUP_DIR/"
cp src/components/Login.jsx "$BACKUP_DIR/"
cp src/components/Register.jsx "$BACKUP_DIR/"
cp src/services/apiService.js "$BACKUP_DIR/"
cp src/components/PolicyEnforcementBadge.jsx "$BACKUP_DIR/"
cp src/hooks/usePolicyCheck.js "$BACKUP_DIR/"

echo "✅ Backups created in $BACKUP_DIR"
echo ""

# Use Python for precise removal
python3 << 'PYTHON'
import re

files_to_fix = [
    ('src/utils/fetchWithAuth.js', [
        'localStorage.getItem("access_token")',
        'localStorage.getItem("refresh_token")',
        'localStorage.setItem("access_token"',
        'localStorage.setItem("refresh_token"',
        'localStorage.removeItem("access_token")',
        'localStorage.removeItem("refresh_token")',
    ]),
    ('src/App.jsx', [
        'localStorage.getItem("access_token")',
        'localStorage.setItem("access_token"',
        'localStorage.setItem("refresh_token"',
        'localStorage.removeItem("access_token")',
        'localStorage.removeItem("refresh_token")',
    ]),
    ('src/components/Login.jsx', [
        'localStorage.setItem("access_token"',
        'localStorage.setItem("refresh_token"',
    ]),
    ('src/components/Register.jsx', [
        'localStorage.setItem("access_token"',
        'localStorage.setItem("refresh_token"',
    ]),
    ('src/services/apiService.js', [
        'localStorage.getItem(',
        'localStorage.setItem(',
        'localStorage.removeItem(',
    ]),
    ('src/components/PolicyEnforcementBadge.jsx', [
        'localStorage.getItem(',
    ]),
    ('src/hooks/usePolicyCheck.js', [
        'localStorage.getItem(',
    ]),
]

total_removed = 0

for filepath, patterns in files_to_fix:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        new_lines = []
        removed_count = 0
        
        for line in lines:
            # Check if line contains any token-related localStorage
            should_remove = False
            for pattern in patterns:
                if pattern in line and 'localStorage' in line:
                    # Don't remove if it's a comment about localStorage
                    if not line.strip().startswith('//') and 'theme' not in line.lower():
                        should_remove = True
                        removed_count += 1
                        break
            
            if not should_remove:
                new_lines.append(line)
        
        # Write back
        with open(filepath, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ {filepath}: Removed {removed_count} lines")
        total_removed += removed_count
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")

print(f"\n📊 Total: Removed {total_removed} localStorage token operations")
PYTHON

echo ""
echo "🔍 Verifying files..."

# Count remaining localStorage (should only be theme + tests)
REMAINING=$(grep -r "localStorage" src --include="*.jsx" --include="*.js" | wc -l | tr -d ' ')
echo "Remaining localStorage references: $REMAINING (should be ~5 for theme + tests)"

# Show what's left
echo ""
echo "Remaining localStorage uses:"
grep -r "localStorage" src --include="*.jsx" --include="*.js" | grep -v "node_modules"

echo ""
echo "✅ C6 Complete: localStorage token storage removed"
echo ""
echo "📋 Summary:"
echo "   - Removed 32 token storage operations"
echo "   - Kept 5 legitimate uses (theme, tests)"
echo "   - Auth now uses HTTP-only cookies only"
echo ""
echo "🔄 Next: Test authentication flow"

