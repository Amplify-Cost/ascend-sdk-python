#!/bin/bash

echo "🔍 QUICK AUTH LOOP DIAGNOSTIC"
echo "============================="

# Check current directory
echo "📍 Current location: $(pwd)"

# 1. Check main auth files only
echo ""
echo "🔐 AUTH BACKEND CHECK:"
echo "----------------------"
if [ -f "main.py" ]; then
    echo "✅ main.py found"
    echo "🔍 Auth endpoints:"
    grep -n "auth" main.py | head -5
else
    echo "❌ main.py not found"
fi

# 2. Check frontend auth logic
echo ""
echo "🌐 FRONTEND AUTH CHECK:"
echo "----------------------"
if [ -f "ow-ai-dashboard/src/App.jsx" ]; then
    echo "✅ App.jsx found"
    echo "🔍 Auth state management:"
    grep -n "auth\|user\|login" ow-ai-dashboard/src/App.jsx | head -5
else
    echo "❌ App.jsx not found"
fi

# 3. Check fetchWithAuth
echo ""
echo "🍪 COOKIE AUTH CHECK:"
echo "--------------------"
if [ -f "ow-ai-dashboard/src/fetchWithAuth.js" ]; then
    echo "✅ fetchWithAuth.js found"
    echo "🔍 Cookie handling:"
    grep -n "cookie\|credential" ow-ai-dashboard/src/fetchWithAuth.js | head -3
else
    echo "❌ fetchWithAuth.js not found"
fi

# 4. Quick CORS check
echo ""
echo "🌍 CORS CONFIG CHECK:"
echo "--------------------"
if [ -f "main.py" ]; then
    echo "🔍 CORS origins:"
    grep -n "add_middleware\|CORSMiddleware\|passionate-elegance" main.py | head -3
fi

# 5. Check for authentication infinite loops
echo ""
echo "🔄 LOOP PREVENTION CHECK:"
echo "------------------------"
if [ -f "ow-ai-dashboard/src/App.jsx" ]; then
    echo "🔍 useEffect dependencies:"
    grep -A2 -B2 "useEffect" ow-ai-dashboard/src/App.jsx | head -6
fi

echo ""
echo "✅ QUICK DIAGNOSTIC COMPLETE!"
echo "Share this output for targeted enterprise fix."

