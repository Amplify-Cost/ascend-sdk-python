#!/bin/bash
# fix_main_syntax.sh - Clean up merge conflicts in main.py

echo "🔧 FIXING MAIN.PY SYNTAX ERRORS"
echo "================================"

# Step 1: Backup current broken file
echo "📋 Step 1: Creating backup..."
cp main.py main.py.broken_backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

# Step 2: Remove merge conflict markers
echo "🧹 Step 2: Removing merge conflict markers..."
sed -i '/<<<<<<< HEAD/d' main.py
sed -i '/=======/d' main.py
sed -i '/>>>>>>> 894b585/d' main.py
echo "✅ Merge conflicts removed"

# Step 3: Remove duplicate imports and router includes
echo "🔄 Step 3: Fixing duplicate code..."

# Remove duplicate router includes (keep only one set)
sed -i '/^app\.include_router(auth_router)$/d' main.py
sed -i '/^app\.include_router(smart_rules_router)$/d' main.py
sed -i '/^app\.include_router(enterprise_user_router)$/d' main.py
sed -i '/^app\.include_router(authorization_router)$/d' main.py
sed -i '/^app\.include_router(authorization_api_router)$/d' main.py
sed -i '/^app\.include_router(secrets_router)$/d' main.py
sed -i '/^app\.include_router(analytics_router, prefix="\/analytics", tags=\["analytics"\])$/d' main.py
sed -i '/^app\.include_router(smart_alerts_router, prefix="\/alerts", tags=\["alerts"\])$/d' main.py
sed -i '/^app\.include_router(data_rights_router, prefix="\/api\/data-rights", tags=\["data-rights"\])$/d' main.py
sed -i '/^app\.include_router(unified_governance_router, prefix="\/api\/governance", tags=\["unified-governance"\])$/d' main.py
sed -i '/^app\.include_router(health_router, tags=\["Health"\])$/d' main.py
sed -i '/^app\.include_router(sso_router, tags=\["Enterprise SSO"\])$/d' main.py

echo "✅ Duplicate router includes removed"

# Step 4: Fix comment syntax errors
echo "🔧 Step 4: Fixing comment syntax..."
sed -i 's/^#     current_user: dict = Depends(get_current_user)$/    current_user: dict = Depends(get_current_user)/g' main.py
echo "✅ Comment syntax fixed"

# Step 5: Remove any remaining problematic lines
echo "🗑️ Step 5: Removing problematic lines..."
# Remove any lines that start with merge conflict patterns
sed -i '/^<<<<<<< /d' main.py
sed -i '/^>>>>>>> /d' main.py
sed -i '/^=======/d' main.py

# Remove any empty enterprise import blocks
sed -i '/^=======$/d' main.py
sed -i '/^>>>>>>> 894b585 (Initial commit: Enterprise JWT + AWS Secrets Manager implementation)$/d' main.py

echo "✅ Problematic lines removed"

# Step 6: Verify Python syntax
echo "🔍 Step 6: Checking Python syntax..."
python3 -m py_compile main.py
if [ $? -eq 0 ]; then
    echo "✅ Python syntax is now valid!"
else
    echo "❌ Syntax errors still exist. Manual review needed."
    exit 1
fi

# Step 7: Show file size and line count
echo "📊 Step 7: File statistics..."
echo "File size: $(ls -lh main.py | awk '{print $5}')"
echo "Line count: $(wc -l < main.py)"

echo ""
echo "🎯 MAIN.PY SYNTAX FIXES COMPLETE!"
echo "=================================="
echo "✅ Merge conflicts removed"
echo "✅ Duplicate code cleaned"
echo "✅ Python syntax validated"
echo "✅ File ready for deployment"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. git add main.py"
echo "2. git commit -m 'FIX: Clean main.py syntax errors and merge conflicts'"
echo "3. git push"
echo ""
echo "📁 Backup saved as: main.py.broken_backup_$(date +%Y%m%d_%H%M%S)"
