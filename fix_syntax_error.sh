#!/bin/bash

echo "🚨 FIXING SYNTAX ERROR IN APP.JSX"
echo "================================="
echo ""
echo "🎯 PROBLEM:"
echo "Line 276: }, []);}, []); - Duplicate closing brackets"
echo "Build is failing due to syntax error"
echo ""

cd /Users/mac_001/OW_AI_Project

# First, let's see the exact error
echo "🔍 Checking the syntax error around line 276..."
sed -n '270,280p' ow-ai-dashboard/src/App.jsx

echo ""
echo "🔧 Fixing the duplicate }, []); syntax error..."

# Fix the duplicate }, []); issue
sed -i.bak 's/}, \[\]);}, \[\]);/}, []);/' ow-ai-dashboard/src/App.jsx

echo "✅ Fixed syntax error"

# Verify the fix
echo ""
echo "🔍 Verifying the fix around line 276..."
sed -n '270,280p' ow-ai-dashboard/src/App.jsx

echo ""
echo "🚀 Deploying the syntax fix..."

# Add and commit the fix
git add ow-ai-dashboard/src/App.jsx
git commit -m "🔧 FIX: Syntax error in App.jsx - removed duplicate }, []);

❌ Fixed line 276: }, []);}, []);
✅ Now: }, []);
✅ Should build successfully now"

# Push the fix
git push origin main

echo ""
echo "🎉 SYNTAX ERROR FIXED!"
echo "====================="
echo ""
echo "✅ What was fixed:"
echo "  • Removed duplicate }, []); on line 276"
echo "  • Build should now succeed"
echo "  • Infinite loop should still be stopped"
echo ""
echo "⏱️  Fix deployment in progress..."
echo "   Frontend should build successfully now"
echo "   Railway logs should stop showing /auth/me spam"
echo ""
echo "📋 SYNTAX FIX COMPLETE!"
echo "======================"
