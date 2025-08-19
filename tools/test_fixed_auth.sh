#!/bin/bash
# tools/test_fixed_auth.sh
# Test that the auth fixes work properly

set -e

echo "🧪 TESTING FIXED AUTHENTICATION"
echo "==============================="

FETCHAUTH_FILE="ow-ai-dashboard/src/utils/fetchWithAuth.js"
APP_FILE="ow-ai-dashboard/src/App.jsx"

echo ""
echo "1️⃣  Checking fetchWithAuth.js syntax..."
if node -c "$FETCHAUTH_FILE" 2>/dev/null; then
    echo "✅ fetchWithAuth.js syntax valid"
else
    echo "❌ fetchWithAuth.js has syntax errors"
    node -c "$FETCHAUTH_FILE"
    exit 1
fi

echo ""
echo "2️⃣  Checking required exports..."
if grep -q "export async function getCurrentUser" "$FETCHAUTH_FILE"; then
    echo "✅ getCurrentUser export found"
else
    echo "❌ getCurrentUser export missing"
fi

if grep -q "export async function logout" "$FETCHAUTH_FILE"; then
    echo "✅ logout export found"
else
    echo "❌ logout export missing"
fi

if grep -q "export async function fetchWithAuth" "$FETCHAUTH_FILE"; then
    echo "✅ fetchWithAuth export found"
else
    echo "❌ fetchWithAuth export missing"
fi

echo ""
echo "3️⃣  Checking App.jsx imports..."
if grep -q "import { fetchWithAuth, logout, getCurrentUser }" "$APP_FILE"; then
    echo "✅ App.jsx imports match available exports"
else
    echo "⚠️  App.jsx import statement doesn't match"
    grep -n "import.*fetchWithAuth" "$APP_FILE" || echo "No fetchWithAuth imports found"
fi

echo ""
echo "4️⃣  Testing frontend build..."
cd ow-ai-dashboard
if npm run build --silent >/dev/null 2>&1; then
    echo "✅ Frontend builds successfully"
else
    echo "❌ Frontend build failed - running with output:"
    npm run build
fi

echo ""
echo "🎯 Ready to test locally:"
echo "  1. Backend: cd ow-ai-backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo "  2. Frontend: cd ow-ai-dashboard && npm run dev"
echo "  3. Open browser to http://localhost:5175"