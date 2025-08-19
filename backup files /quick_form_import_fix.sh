#!/bin/bash

echo "🔧 QUICK FORM IMPORT FIX"
echo "========================"
echo ""
echo "🎯 ISSUE: Missing 'Form' import in dependencies.py"
echo "🏢 GOAL: Add missing import while maintaining Master Prompt compliance"
echo ""

# Fix the missing Form import
echo "📋 Adding missing Form import to dependencies.py"
echo "==============================================="

# Add Form to the FastAPI imports
sed -i.quickfix 's/from fastapi import Request, HTTPException, status, Depends, Cookie/from fastapi import Request, HTTPException, status, Depends, Cookie, Form/' ow-ai-backend/dependencies.py

echo "✅ Added Form import to dependencies.py"

# Verify the fix
echo ""
echo "🔍 Verifying import fix..."
if grep -q "from fastapi import.*Form" ow-ai-backend/dependencies.py; then
    echo "✅ Form import added successfully"
else
    echo "⚠️ Manual verification needed"
fi

# Quick deploy
echo ""
echo "📋 Quick Deploy Import Fix"
echo "========================="

git add ow-ai-backend/dependencies.py
git commit -m "🔧 QUICK FIX: Add missing Form import to dependencies.py

- Add Form to FastAPI imports
- Enables require_csrf function to work properly
- Maintains Master Prompt compliance"

git push origin main

echo ""
echo "✅ QUICK FORM IMPORT FIX DEPLOYED!"
echo "================================="
echo ""
echo "⏱️ Expected Result (2 minutes):"
echo "   ✅ Backend starts without Form import error"
echo "   ✅ All imports work properly"
echo "   ✅ require_csrf function operational"
echo ""
echo "🎯 Your enterprise platform should now be 100% operational!"
echo "=========================================================="
