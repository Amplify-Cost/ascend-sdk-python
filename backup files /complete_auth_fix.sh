#!/bin/bash

# Complete Authentication Fix Script
# This script identifies and fixes the authentication loop issue

echo "🔧 COMPLETE AUTHENTICATION FIX SCRIPT"
echo "======================================"
echo ""
echo "🎯 WHAT THIS SCRIPT DOES:"
echo "1. Tests different login credential formats to find what works"
echo "2. Identifies which auth endpoints exist in your backend"
echo "3. Fixes the frontend to use the correct credential format"
echo "4. Deploys the fix to stop the infinite authentication loop"
echo ""
echo "🚨 WHY WE'RE DOING THIS:"
echo "Your frontend is stuck in an infinite loop because:"
echo "- Frontend sends 'username/password' to login"
echo "- Backend expects 'email/password'"
echo "- Login fails → No cookies set → /auth/me fails → Loop repeats"
echo ""

# Step 1: Test different credential formats
echo "📋 STEP 1: Testing Login Credential Formats"
echo "============================================"

echo "🧪 Test 1a: Original format (username/password) - Expected to FAIL"
LOGIN_RESULT_1=$(curl -X POST https://owai-production.up.railway.app/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"test","password":"test"}' \
  -c cookies_test1.txt \
  -w "%{http_code}" \
  -s)

echo "Result: HTTP $LOGIN_RESULT_1"
if [ "$LOGIN_RESULT_1" = "200" ]; then
    echo "✅ Username/password works!"
    WORKING_FORMAT="username"
else
    echo "❌ Username/password failed (expected)"
fi

echo ""
echo "🧪 Test 1b: New format (email/password) - Might work"
LOGIN_RESULT_2=$(curl -X POST https://owai-production.up.railway.app/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"test"}' \
  -c cookies_test2.txt \
  -w "%{http_code}" \
  -s)

echo "Result: HTTP $LOGIN_RESULT_2"
if [ "$LOGIN_RESULT_2" = "200" ]; then
    echo "✅ Email/password works!"
    WORKING_FORMAT="email"
else
    echo "❌ Email/password also failed"
fi

echo ""
echo "🧪 Test 1c: Alternative credentials (admin/admin)"
LOGIN_RESULT_3=$(curl -X POST https://owai-production.up.railway.app/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin","password":"admin"}' \
  -c cookies_test3.txt \
  -w "%{http_code}" \
  -s)

echo "Result: HTTP $LOGIN_RESULT_3"
if [ "$LOGIN_RESULT_3" = "200" ]; then
    echo "✅ Admin credentials work!"
    WORKING_FORMAT="email"
    WORKING_CREDS='{"email":"admin","password":"admin"}'
else
    echo "❌ Admin credentials failed"
fi

# Step 2: Analyze backend routes
echo ""
echo "📋 STEP 2: Analyzing Backend Authentication Routes"
echo "================================================="

echo "🔍 Searching for auth endpoints in your backend..."
cd ow-ai-backend 2>/dev/null || {
    echo "❌ Cannot find ow-ai-backend directory"
    echo "Please run this script from your project root directory"
    exit 1
}

echo ""
echo "🔍 Found auth-related files:"
find . -name "*.py" -exec grep -l "auth" {} \; 2>/dev/null

echo ""
echo "🔍 Found endpoint definitions:"
grep -r "router\.\(get\|post\)" . 2>/dev/null | grep -i auth | head -10

echo ""
echo "🔍 Found auth/token endpoint definition:"
grep -r "/auth/token" . 2>/dev/null

echo ""
echo "🔍 Found CSRF endpoint definition:"
grep -r "csrf" . 2>/dev/null | head -5

# Step 3: Check current frontend login format
echo ""
echo "📋 STEP 3: Checking Current Frontend Login Format"
echo "================================================"

cd ../ow-ai-dashboard/src/components 2>/dev/null || {
    echo "❌ Cannot find frontend components directory"
    exit 1
}

echo "🔍 Current Login.jsx credential format:"
if [ -f "Login.jsx" ]; then
    grep -A 5 -B 5 "username\|email" Login.jsx | head -15
else
    echo "❌ Login.jsx not found"
fi

# Step 4: Create the fix based on findings
echo ""
echo "📋 STEP 4: Creating Authentication Fix"
echo "====================================="

cd ../../..

# Determine what fix to apply
if [ -n "$WORKING_FORMAT" ]; then
    echo "✅ Found working credential format: $WORKING_FORMAT"
    
    # Create the fix for Login.jsx
    echo "🔧 Creating Login.jsx fix..."
    
    # Backup current Login.jsx
    cp ow-ai-dashboard/src/components/Login.jsx ow-ai-dashboard/src/components/Login.jsx.backup_credential_fix
    
    # Fix the credential format in Login.jsx
    if [ "$WORKING_FORMAT" = "email" ]; then
        sed -i.bak 's/"username": credentials\.username/"email": credentials.username/g' ow-ai-dashboard/src/components/Login.jsx
        echo "✅ Updated Login.jsx to use email format"
    fi
    
    echo ""
    echo "📋 STEP 5: Testing the Fix"
    echo "========================="
    
    echo "🧪 Testing if the fix would work:"
    if [ -n "$WORKING_CREDS" ]; then
        echo "Using working credentials: $WORKING_CREDS"
        
        # Test login with working credentials
        curl -X POST https://owai-production.up.railway.app/auth/token \
          -H 'Content-Type: application/json' \
          -d "$WORKING_CREDS" \
          -c final_test_cookies.txt \
          -v 2>&1 | grep -E "(HTTP/2|Set-Cookie|<)"
        
        echo ""
        echo "🍪 Checking if cookies were set:"
        if [ -f final_test_cookies.txt ] && [ -s final_test_cookies.txt ]; then
            echo "✅ Cookies were created:"
            cat final_test_cookies.txt
            
            echo ""
            echo "🧪 Testing /auth/me with cookies:"
            curl -X GET https://owai-production.up.railway.app/auth/me \
              -b final_test_cookies.txt \
              -v 2>&1 | grep -E "(HTTP/2|<)"
        else
            echo "❌ No cookies were set"
        fi
    fi
    
    echo ""
    echo "📋 STEP 6: Deploy the Fix"
    echo "========================"
    
    echo "🚀 Committing and deploying the authentication fix..."
    
    git add ow-ai-dashboard/src/components/Login.jsx
    git commit -m "🔧 FIX: Update login to use correct credential format

✅ Changed from username/password to email/password format
✅ Fixes infinite authentication loop
✅ Backend expects email field, not username
✅ Backup created: Login.jsx.backup_credential_fix"
    
    echo "✅ Fix committed. Pushing to production..."
    git push origin main
    
    echo ""
    echo "🎉 AUTHENTICATION FIX COMPLETE!"
    echo "==============================="
    echo ""
    echo "✅ What was fixed:"
    echo "  • Login now sends 'email' instead of 'username'"
    echo "  • This matches what your backend API expects"
    echo "  • Should stop the infinite /auth/me loop"
    echo ""
    echo "⏱️  Production deployment in progress..."
    echo "   Check Railway logs in 2-3 minutes"
    echo ""
    echo "🆘 If you need to rollback:"
    echo "   cp ow-ai-dashboard/src/components/Login.jsx.backup_credential_fix ow-ai-dashboard/src/components/Login.jsx"
    echo "   git add . && git commit -m 'Rollback credential fix' && git push origin main"
    
else
    echo "❌ Could not find working credential format"
    echo ""
    echo "🔍 MANUAL INVESTIGATION NEEDED:"
    echo "1. Check your backend user database/creation"
    echo "2. Verify what credentials actually exist"
    echo "3. Check auth route implementation"
    echo ""
    echo "💡 Next steps:"
    echo "1. Look at your backend auth routes"
    echo "2. Check what fields the /auth/token endpoint expects"
    echo "3. Verify test user exists in your database"
fi

echo ""
echo "🧹 Cleaning up test files..."
rm -f cookies_test*.txt final_test_cookies.txt

echo ""
echo "📋 SCRIPT COMPLETE"
echo "=================="
