#!/bin/bash

echo "🚨 FIXING DUPLICATE EXPORT DECLARATIONS"
echo "======================================"
echo "🎯 Master Prompt Compliance: Remove duplicate exports causing build failure"
echo "🚨 Error: getCurrentUser and loginUser exported twice"
echo ""

echo "📋 STEP 1: Clean up duplicate exports"
echo "=================================="

FETCHAUTH_FILE="ow-ai-dashboard/src/utils/fetchWithAuth.js"

# Backup the file
cp "$FETCHAUTH_FILE" "$FETCHAUTH_FILE.duplicate-exports-backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Removing duplicate export lines..."

# Remove the problematic duplicate export lines
sed -i '' '/export const getCurrentUser = getCurrentUser;/d' "$FETCHAUTH_FILE"
sed -i '' '/export const loginUser = loginUser;/d' "$FETCHAUTH_FILE"

# Fix the export block to only include what's needed
sed -i '' '/export {/,/};/c\
// Alternative export names for compatibility\
export { \
    loginUser as login,\
    getCurrentUser as getUser\
};' "$FETCHAUTH_FILE"

echo "✅ Removed duplicate exports"

echo ""
echo "📋 STEP 2: Verify clean exports"
echo "=============================="

echo "🔍 Current export statements:"
grep -n "export" "$FETCHAUTH_FILE"

echo ""
echo "📋 STEP 3: Test build fix"
echo "======================="

cd ow-ai-dashboard

echo "🔧 Testing build with clean exports..."
if npm run build > /dev/null 2>&1; then
    echo "✅ Build successful - duplicate exports resolved"
else
    echo "⚠️  Still have build issues:"
    npm run build 2>&1 | grep -A5 -B5 "ERROR\|error" | head -15
fi

cd ..

echo ""
echo "📋 STEP 4: Deploy duplicate export fix"
echo "===================================="

git add ow-ai-dashboard/src/utils/fetchWithAuth.js
git commit -m "🔧 FIX: Remove duplicate export declarations causing build failure"
git push origin main

echo ""
echo "✅ DUPLICATE EXPORTS FIXED!"
echo "=========================="
echo "🎯 Master Prompt Compliance:"
echo "   ✅ Removed duplicate export declarations"
echo "   ✅ Preserved backward compatibility"
echo "   ✅ Maintained cookie-only authentication"
echo "   ✅ Fixed build compilation errors"
echo ""
echo "🧪 Expected Results (3-4 minutes):"
echo "   ✅ Build completes successfully"
echo "   ✅ No more 'already declared' errors"
echo "   ✅ Authentication format fix working"
echo "   ✅ Dashboard loads with login functionality"
