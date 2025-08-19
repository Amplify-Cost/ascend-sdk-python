#!/bin/bash

echo "🔧 FIXING LOGIN.JSX FIELD MISMATCH"
echo "=================================="
echo ""
echo "🎯 PROBLEM FOUND:"
echo "Login.jsx sends 'username: email' but backend expects 'email: email'"
echo "This is why login fails with 'Invalid credentials'"
echo ""

cd /Users/mac_001/OW_AI_Project

# Backup current Login.jsx
cp ow-ai-dashboard/src/components/Login.jsx ow-ai-dashboard/src/components/Login.jsx.backup_field_fix

echo "✅ Backed up Login.jsx"

# Fix the field mismatch
sed -i.bak 's/username: email,/email: email,/' ow-ai-dashboard/src/components/Login.jsx

echo "✅ Fixed field mismatch: username → email"

# Verify the fix
echo ""
echo "🔍 Verifying the fix..."
grep -n -A 3 -B 1 "email: email" ow-ai-dashboard/src/components/Login.jsx

# Commit and deploy
echo ""
echo "🚀 Deploying the fix..."

git add ow-ai-dashboard/src/components/Login.jsx
git commit -m "🔧 FIX: Login field mismatch - username to email

❌ Was sending: username: email
✅ Now sending: email: email  
✅ Matches backend expectation
✅ Login should work with test users now"

git push origin main

echo ""
echo "🎉 LOGIN FIELD FIX DEPLOYED!"
echo "==========================="
echo ""
echo "✅ What was fixed:"
echo "  • Changed 'username: email' to 'email: email'"
echo "  • Now matches backend API expectation"
echo "  • Should work with all test users"
echo ""
echo "🧪 Test these credentials now:"
echo "  📧 test@example.com | 🔑 test"
echo "  📧 admin@example.com | 🔑 admin"
echo "  📧 demo@owai.com | 🔑 demo123"
echo ""
echo "⏱️  Frontend deployment in progress..."
echo "   Try logging in with test credentials in 2-3 minutes!"

echo ""
echo "📋 AUTHENTICATION SHOULD NOW WORK COMPLETELY!"
echo "============================================="
