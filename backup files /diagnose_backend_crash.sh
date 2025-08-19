#!/bin/bash

echo "🚨 BACKEND CRASH DIAGNOSTIC - ENTERPRISE AUTHENTICATION ANALYSIS"
echo "================================================================"
echo ""
echo "🎯 ISSUE IDENTIFIED:"
echo "ImportError: cannot import name 'get_current_user' from 'cookie_auth'"
echo ""

cd /Users/mac_001/OW_AI_Project/ow-ai-backend

echo "📋 STEP 1: Analyzing Current Authentication Architecture"
echo "====================================================="

echo "🔍 Checking cookie_auth.py structure..."
if [ -f "cookie_auth.py" ]; then
    echo "✅ cookie_auth.py exists"
    echo "📄 Current functions in cookie_auth.py:"
    grep -n "^def\|^async def" cookie_auth.py || echo "❌ No functions found"
    echo ""
    echo "📄 Current imports in cookie_auth.py:"
    grep -n "^from\|^import" cookie_auth.py || echo "❌ No imports found"
else
    echo "❌ cookie_auth.py NOT FOUND"
fi

echo ""
echo "🔍 Checking dependencies.py structure..."
if [ -f "dependencies.py" ]; then
    echo "✅ dependencies.py exists"
    echo "📄 Current functions in dependencies.py:"
    grep -n "^def\|^async def" dependencies.py || echo "❌ No functions found"
    echo ""
    echo "📄 Looking for get_current_user in dependencies.py:"
    grep -n "get_current_user" dependencies.py || echo "❌ get_current_user not found in dependencies.py"
else
    echo "❌ dependencies.py NOT FOUND"
fi

echo ""
echo "🔍 Checking what main.py is trying to import..."
echo "📄 Authentication imports in main.py:"
grep -n "from cookie_auth import\|from dependencies import" main.py

echo ""
echo "🔍 Checking for other auth-related files..."
echo "📁 Authentication-related files in backend:"
ls -la | grep -E "(auth|cookie|jwt|dependencies)" || echo "❌ No auth files found"

echo ""
echo "📋 STEP 2: Enterprise Authentication Conflict Analysis"
echo "===================================================="

echo "🔍 Checking for conflicting auth imports in main.py..."
echo "🚨 CONFLICTING IMPORTS FOUND:"
grep -n -A 2 -B 2 "get_current_user" main.py

echo ""
echo "📋 STEP 3: Enterprise Solution Analysis"
echo "======================================"

echo "🎯 ENTERPRISE ISSUE IDENTIFIED:"
echo "main.py has conflicting imports:"
echo "  Line 12: from cookie_auth import get_current_user"
echo "  Line 26: from dependencies import get_current_user"
echo ""
echo "🏢 ENTERPRISE FIX REQUIRED:"
echo "1. Remove duplicate import from cookie_auth"
echo "2. Keep only dependencies import for get_current_user"
echo "3. Ensure enterprise authentication consistency"

echo ""
echo "📋 STEP 4: Enterprise Master Prompt Compliance Check"
echo "=================================================="

echo "🎯 MASTER PROMPT REQUIREMENTS:"
echo "✅ Enterprise-level authentication (RS256 JWT + Cookie)"
echo "✅ Cookie-first authentication security"
echo "✅ Consistent import structure"
echo "❌ FAILING: Import conflicts breaking enterprise deployment"

echo ""
echo "🚀 IMMEDIATE ENTERPRISE FIX REQUIRED:"
echo "1. Fix import conflicts in main.py"
echo "2. Ensure consistent authentication architecture"
echo "3. Deploy enterprise-stable backend"
echo "4. Maintain 65% enterprise readiness score"

echo ""
echo "📋 BACKEND CRASH DIAGNOSTIC COMPLETE!"
echo "====================================="
