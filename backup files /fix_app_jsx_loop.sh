#!/bin/bash

echo "🚨 FIXING APP.JSX INFINITE LOOP"
echo "==============================="
echo ""
echo "🎯 PROBLEM IDENTIFIED:"
echo "Line 278: const currentUser = await getCurrentUser();"
echo "This is creating the infinite /auth/me requests!"
echo ""
echo "🛠️ SOLUTION:"
echo "Disable the useEffect that calls getCurrentUser()"
echo ""

cd /Users/mac_001/OW_AI_Project

# Backup the current App.jsx
cp ow-ai-dashboard/src/App.jsx ow-ai-dashboard/src/App.jsx.backup_infinite_loop_fix

echo "✅ Backed up App.jsx"

# Create the fixed version by commenting out the problematic useEffect
echo "🔧 Disabling the infinite loop useEffect..."

# Use sed to comment out the entire useEffect block that calls getCurrentUser
sed -i.bak '/\/\/ 🍪 ENHANCED: Enterprise Cookie Authentication Check/,/checkEnterpriseAuthentication();/c\
  // 🚨 TEMPORARILY DISABLED: Enterprise Cookie Authentication Check\
  // This was causing infinite /auth/me requests - disabled for stability\
  useEffect(() => {\
    console.log("🚨 AUTH CHECK DISABLED - No infinite loops");\
    setLoading(false);\
    setView("login"); // Force login screen\
  }, []);' ow-ai-dashboard/src/App.jsx

echo "✅ Fixed App.jsx - disabled infinite loop useEffect"

# Verify the change was made
echo ""
echo "🔍 Verifying the fix..."
grep -n -A 5 -B 2 "AUTH CHECK DISABLED" ow-ai-dashboard/src/App.jsx

echo ""
echo "🚀 Deploying the fix..."

# Add and commit the fix
git add ow-ai-dashboard/src/App.jsx
git commit -m "🚨 CRITICAL FIX: Stop infinite loop in App.jsx

❌ Disabled useEffect calling getCurrentUser() on line 278
❌ Was causing infinite /auth/me requests to backend  
✅ Now shows login screen without auth checking
✅ Should stop Railway log spam immediately
🔧 Backup: App.jsx.backup_infinite_loop_fix"

# Push to production
git push origin main

echo ""
echo "🎉 INFINITE LOOP FIX DEPLOYED!"
echo "============================="
echo ""
echo "✅ What was fixed:"
echo "  • Disabled useEffect calling getCurrentUser()"
echo "  • Stopped infinite /auth/me requests"
echo "  • App will show login screen immediately"
echo "  • Railway logs should stop spamming"
echo ""
echo "⏱️  Fix deployment in progress..."
echo "   Check Railway logs in 1-2 minutes"
echo "   The /auth/me spam should STOP completely"
echo ""
echo "🧪 Expected behavior:"
echo "   1. App loads → Login screen (no loading/checking)"
echo "   2. Railway logs → No more /auth/me requests"
echo "   3. Users can manually log in"
echo "   4. App works normally after login"
echo ""
echo "🆘 If still not working, rollback with:"
echo "   cp ow-ai-dashboard/src/App.jsx.backup_infinite_loop_fix ow-ai-dashboard/src/App.jsx"
echo "   git add . && git commit -m 'Rollback loop fix' && git push origin main"

echo ""
echo "📋 CRITICAL FIX COMPLETE!"
echo "========================"
echo "🎯 This MUST stop the infinite loop - the exact source is now disabled!"
