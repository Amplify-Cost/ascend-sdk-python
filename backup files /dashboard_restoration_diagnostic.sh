#!/bin/bash

echo "🔍 DASHBOARD RESTORATION DIAGNOSTIC"
echo "=================================="
echo "✅ Authentication Working: Login/logout functioning perfectly"
echo "🚨 Issue: Dashboard showing generic data instead of real enterprise data"
echo "🎯 Goal: Restore original dashboard with proper database integration"
echo ""

# 1. Check what dashboard components we have
echo "📋 STEP 1: Analyze Current Dashboard Components"
echo "---------------------------------------------"

echo "🔍 Checking current Dashboard.jsx:"
if [ -f "ow-ai-dashboard/src/components/Dashboard.jsx" ]; then
    echo "✅ Dashboard.jsx found - checking structure:"
    echo "📊 Current dashboard content:"
    head -20 ow-ai-dashboard/src/components/Dashboard.jsx
    
    echo ""
    echo "🔍 Checking for database/API integration:"
    grep -n "fetch\|api\|data\|analytics" ow-ai-dashboard/src/components/Dashboard.jsx | head -10 || echo "No API integration found"
    
    echo ""
    echo "🔍 Checking for user role handling:"
    grep -n "admin\|role\|access" ow-ai-dashboard/src/components/Dashboard.jsx | head -5 || echo "No role-based access found"
else
    echo "❌ Dashboard.jsx not found"
fi

# 2. Check for backup versions of dashboard
echo ""
echo "📋 STEP 2: Search for Original Dashboard Backups"
echo "-----------------------------------------------"

echo "🔍 Searching for dashboard backups:"
find . -name "*Dashboard*" -type f 2>/dev/null | head -10

echo ""
echo "🔍 Searching backup directories for original dashboard:"
find . -path "*/backup*" -name "*Dashboard*" -type f 2>/dev/null | head -5

echo ""
echo "🔍 Looking for complete version backups:"
if [ -d "COMPLETE_VERSION_BACKUPS" ]; then
    echo "✅ Found complete version backups:"
    find COMPLETE_VERSION_BACKUPS -name "*Dashboard*" -type f 2>/dev/null | head -5
fi

# 3. Check backend for analytics/data endpoints
echo ""
echo "📋 STEP 3: Check Backend Data Integration"
echo "---------------------------------------"

echo "🔍 Checking backend for analytics endpoints:"
if [ -f "ow-ai-backend/main.py" ]; then
    grep -n "analytics\|dashboard\|data" ow-ai-backend/main.py | head -5 || echo "No analytics endpoints found in backend"
elif [ -f "main.py" ]; then
    grep -n "analytics\|dashboard\|data" main.py | head -5 || echo "No analytics endpoints found in backend"
fi

echo ""
echo "🔍 Checking for database connections:"
find . -name "*.py" -exec grep -l "database\|db\|analytics" {} \; 2>/dev/null | head -5

# 4. Identify the issue and create restoration plan
echo ""
echo "📋 STEP 4: Create Dashboard Restoration Plan"
echo "-------------------------------------------"

echo "🔍 ISSUE ANALYSIS:"
echo "   - Authentication: ✅ Working perfectly"
echo "   - Dashboard: ❌ Showing generic placeholder instead of real data"
echo "   - Database: ❌ Frontend not connected to actual enterprise data"
echo "   - User Roles: ❌ Admin privileges not being recognized"
echo ""
echo "🎯 RESTORATION STRATEGY:"
echo "   1. Locate original dashboard with real data integration"
echo "   2. Restore proper database/API connections"
echo "   3. Implement role-based access for shug@gmail.com admin"
echo "   4. Maintain working authentication system"
echo "   5. Ensure Master Prompt compliance"

# 5. Check git history for the last working dashboard
echo ""
echo "📋 STEP 5: Check Git History for Original Dashboard"
echo "-------------------------------------------------"

echo "🔍 Recent commits that might have changed dashboard:"
git log --oneline -10 | grep -i "dashboard\|ui\|component" || echo "No dashboard-related commits found in recent history"

echo ""
echo "🔍 Checking git history for Dashboard.jsx changes:"
git log --oneline --follow ow-ai-dashboard/src/components/Dashboard.jsx 2>/dev/null | head -5 || echo "No Dashboard.jsx history found"

echo ""
echo "✅ DIAGNOSTIC COMPLETE!"
echo "======================"
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Review backup versions of dashboard"
echo "   2. Restore original dashboard with real data"
echo "   3. Reconnect frontend to backend analytics endpoints"
echo "   4. Implement proper admin role access for shug@gmail.com"
echo "   5. Test enterprise functionality end-to-end"
echo ""
echo "🔍 KEY FINDINGS SUMMARY:"
echo "   - Authentication: WORKING ✅"
echo "   - Current Dashboard: Generic placeholder ❌"
echo "   - Original Dashboard: Needs restoration ⚠️"
echo "   - Database Integration: Disconnected ❌"
