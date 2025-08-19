#!/bin/bash
# tools/diagnose_and_fix_auth.sh
# Enterprise-grade fix for cookie auth issues

set -e

echo "🔍 DIAGNOSING COOKIE AUTH ISSUES"
echo "================================="

# Check what's being imported in App.jsx
echo "1️⃣  Checking App.jsx imports..."
if grep -n "getCurrentUser" ow-ai-dashboard/src/App.jsx; then
    echo "❌ Found getCurrentUser import in App.jsx"
    echo "This needs to be removed or the function needs to be added to fetchWithAuth.js"
else
    echo "✅ No getCurrentUser import found"
fi

# Check fetchWithAuth.js exports
echo ""
echo "2️⃣  Checking fetchWithAuth.js exports..."
if [[ -f "ow-ai-dashboard/src/utils/fetchWithAuth.js" ]]; then
    echo "Exports found:"
    grep -n "export" ow-ai-dashboard/src/utils/fetchWithAuth.js || echo "No exports found"
else
    echo "❌ fetchWithAuth.js not found!"
fi

# Check for any remaining Authorization headers
echo ""
echo "3️⃣  Checking for Authorization headers in frontend..."
grep -r "Authorization" ow-ai-dashboard/src/ --include="*.js" --include="*.jsx" | head -5 || echo "✅ No Authorization headers found"

# Check what the backend expects
echo ""
echo "4️⃣  Backend cookie auth status..."
echo "The backend is rejecting Bearer tokens (good for cookie auth)"
echo "But we need to ensure the frontend isn't sending them"

echo ""
echo "🔧 FIXES NEEDED:"
echo "1. Fix App.jsx import error"
echo "2. Ensure fetchWithAuth.js has all required exports"
echo "3. Verify no Authorization headers are being sent"