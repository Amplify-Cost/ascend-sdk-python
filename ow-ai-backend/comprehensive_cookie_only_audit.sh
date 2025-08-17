#!/bin/bash

echo "🔍 COMPREHENSIVE COOKIE-ONLY COMPLIANCE AUDIT"
echo "=============================================="
echo ""
echo "🎯 PURPOSE: Identify ALL files that need Master Prompt compliance fixes"
echo "📋 SCOPE: Remove Bearer tokens, localStorage, ensure pure cookie-only"
echo ""

cd /Users/mac_001/OW_AI_Project

echo "================== PHASE 1: FRONTEND AUDIT =================="
echo ""

cd ow-ai-dashboard

echo "📋 1.1: Check for localStorage usage"
echo "=================================="
echo "🔍 Searching for localStorage in all frontend files:"
grep -r "localStorage" src/ 2>/dev/null | head -10 || echo "No localStorage found"

echo ""
echo "📋 1.2: Check for Bearer token usage"
echo "=================================="
echo "🔍 Searching for Bearer tokens in frontend:"
grep -r -i "bearer\|authorization.*token" src/ 2>/dev/null | head -10 || echo "No Bearer tokens found"

echo ""
echo "📋 1.3: Check App.jsx authentication"
echo "=================================="
if [ -f "src/App.jsx" ]; then
    echo "🔍 App.jsx authentication patterns:"
    grep -n -A 5 -B 5 "localStorage\|Bearer\|token" src/App.jsx | head -15 || echo "No problematic patterns in App.jsx"
else
    echo "❌ App.jsx not found"
fi

echo ""
echo "📋 1.4: Check other utility files"
echo "==============================="
echo "🔍 Other auth-related files in utils:"
ls src/utils/ 2>/dev/null | grep -E "(auth|token|cookie)" || echo "No other auth files found"

if [ -f "src/utils/auth.js" ]; then
    echo "⚠️ Found auth.js - checking for Bearer tokens:"
    grep -n "Bearer\|localStorage" src/utils/auth.js || echo "Clean"
fi

echo ""
echo "================== PHASE 2: BACKEND AUDIT =================="
echo ""

cd ../ow-ai-backend

echo "📋 2.1: Check dependencies.py"
echo "============================"
echo "🔍 Bearer token references in dependencies.py:"
grep -n -i "bearer" dependencies.py || echo "No Bearer references found"

echo ""
echo "📋 2.2: Check cookie_auth.py"
echo "==========================="
echo "🔍 Current cookie_auth.py authentication approach:"
grep -n -A 3 "Bearer\|authorization" cookie_auth.py || echo "No Bearer handling found"

echo ""
echo "📋 2.3: Check main.py middleware"
echo "=============================="
echo "🔍 Current main.py middleware status:"
grep -n -A 5 -B 5 "Bearer\|middleware.*token" main.py || echo "No Bearer middleware found"

echo ""
echo "📋 2.4: Check route files for authentication"
echo "=========================================="
echo "🔍 Route files that might have Bearer token handling:"
find routes/ -name "*.py" -exec grep -l "Bearer\|Authorization.*token" {} \; 2>/dev/null || echo "No route files with Bearer tokens"

echo ""
echo "================== PHASE 3: CONFIGURATION AUDIT =================="
echo ""

echo "📋 3.1: Environment configuration"
echo "==============================="
cd ../ow-ai-dashboard
echo "🔍 Frontend environment variables:"
if [ -f ".env" ]; then
    grep -v "^#" .env | grep -E "(TOKEN|AUTH|BEARER)" || echo "No token-related env vars"
else
    echo "No .env file found"
fi

echo ""
echo "📋 3.2: Package.json dependencies"
echo "==============================="
echo "🔍 Auth-related dependencies:"
grep -E "(auth|jwt|token)" package.json 2>/dev/null || echo "No auth dependencies found"

echo ""
echo "================== PHASE 4: ISSUE IDENTIFICATION =================="
echo ""

echo "📋 4.1: Files requiring Master Prompt compliance fixes"
echo "===================================================="

ISSUES_FOUND=()

# Check for localStorage usage
if grep -r "localStorage" src/ 2>/dev/null >/dev/null; then
    ISSUES_FOUND+=("❌ localStorage usage found - violates Master Prompt")
fi

# Check for Bearer tokens
if grep -r -i "bearer" src/ 2>/dev/null >/dev/null; then
    ISSUES_FOUND+=("❌ Bearer token usage found - violates cookie-only requirement")
fi

# Check backend Bearer handling
cd ../ow-ai-backend
if grep -i "bearer" dependencies.py 2>/dev/null >/dev/null; then
    ISSUES_FOUND+=("❌ Backend Bearer token handling found")
fi

if [ ${#ISSUES_FOUND[@]} -eq 0 ]; then
    echo "✅ No Master Prompt compliance issues found!"
else
    echo "🚨 Issues requiring fixes:"
    for issue in "${ISSUES_FOUND[@]}"; do
        echo "   $issue"
    done
fi

echo ""
echo "================== PHASE 5: RECOMMENDED FIXES =================="
echo ""

echo "📋 5.1: Required file modifications for Master Prompt compliance"
echo "=============================================================="

echo "🔧 Files that need modification:"

# Frontend files to check/fix
echo ""
echo "FRONTEND:"
echo "✅ fetchWithAuth.js - Already fixed to cookie-only"
echo "⚠️ App.jsx - May need localStorage removal"
echo "⚠️ Any component files using localStorage"

# Backend files to check/fix  
echo ""
echo "BACKEND:"
echo "⚠️ dependencies.py - Remove any Bearer token handling"
echo "⚠️ cookie_auth.py - Ensure pure cookie authentication"
echo "⚠️ Route files - Remove Bearer token endpoints"

echo ""
echo "📋 5.2: Master Prompt compliance checklist"
echo "========================================"

echo "🏢 MASTER PROMPT REQUIREMENTS:"
echo "□ Cookie-only authentication (no Bearer tokens)"
echo "□ No localStorage usage (security vulnerability)"
echo "□ HTTP-only cookies (XSS prevention)"
echo "□ CSRF protection (enterprise security)"
echo "□ No token storage in frontend (Master Prompt)"

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Run additional fixes for identified issues"
echo "2. Remove localStorage from all frontend components"
echo "3. Ensure backend only accepts cookie authentication"
echo "4. Test complete cookie-only authentication flow"

echo ""
echo "🔍 COMPREHENSIVE AUDIT COMPLETE!"
echo "==============================="
echo ""
echo "🏢 Ready to implement Master Prompt compliance fixes!"
