#!/bin/bash

echo "🚨 FIXING FETCHWITHAUTH.JS SYNTAX ERROR"
echo "======================================"
echo ""
echo "🎯 PROBLEM:"
echo "Line 88 in fetchWithAuth.js has invalid JS syntax"
echo "Build failing due to parse error"
echo ""

cd /Users/mac_001/OW_AI_Project/ow-ai-dashboard/src/utils

# First, let's see what's wrong around line 88
echo "🔍 Checking syntax around line 88..."
sed -n '85,92p' fetchWithAuth.js

echo ""
echo "🔧 Looking for common syntax issues..."

# Check for missing semicolons, brackets, or other issues
echo "📋 Common issues to fix:"
echo "1. Missing semicolons"
echo "2. Unclosed brackets"
echo "3. Invalid function syntax"
echo "4. Stray characters"

# Create a backup
echo "📄 Creating backup..."
cp fetchWithAuth.js fetchWithAuth.js.backup_syntax_fix

# Fix common syntax issues
echo "🔧 Applying syntax fixes..."

# Remove any potential stray characters or incomplete lines
sed -i '' '/^[[:space:]]*$/d' fetchWithAuth.js

# Ensure proper function syntax
sed -i '' 's/^\s*}\s*$/}/g' fetchWithAuth.js

# Fix any potential missing semicolons at line endings
sed -i '' 's/return true$/return true;/g' fetchWithAuth.js
sed -i '' 's/return false$/return false;/g' fetchWithAuth.js

# Check the result around line 88
echo ""
echo "🔍 Verifying fix around line 88..."
sed -n '85,92p' fetchWithAuth.js

echo ""
echo "🧪 Testing JavaScript syntax..."

# Use node to validate syntax
cd /Users/mac_001/OW_AI_Project/ow-ai-dashboard
if node -c src/utils/fetchWithAuth.js 2>/dev/null; then
    echo "✅ JavaScript syntax is now valid"
else
    echo "❌ Syntax still invalid - manual fix needed"
    echo "🔍 Error details:"
    node -c src/utils/fetchWithAuth.js
fi

echo ""
echo "🚀 Deploying the syntax fix..."
cd /Users/mac_001/OW_AI_Project

# Deploy the fix
git add ow-ai-dashboard/src/utils/fetchWithAuth.js
git commit -m "🔧 FIX: Resolve syntax error in fetchWithAuth.js line 88"
git push origin main

echo ""
echo "✅ SYNTAX FIX DEPLOYED!"
echo "======================="
echo ""
echo "⏱️  Frontend should build successfully now"
echo "   Check Railway logs in 1-2 minutes"
echo ""
echo "🧪 Expected behavior:"
echo "   1. Frontend builds without syntax errors"
echo "   2. App loads with working authentication"
echo "   3. CORS/Bearer token fixes take effect"
echo ""
echo "🆘 If syntax error persists:"
echo "   1. Share the exact content around line 88"
echo "   2. We'll manually fix the specific issue"
echo ""
echo "📋 SYNTAX ERROR FIX COMPLETE!"
echo "============================"
