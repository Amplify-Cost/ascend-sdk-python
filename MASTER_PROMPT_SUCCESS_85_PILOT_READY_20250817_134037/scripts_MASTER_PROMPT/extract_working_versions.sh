#!/bin/bash

echo "🎯 EXTRACTING YOUR KNOWN WORKING DASHBOARD & BACKEND"
echo "=================================================="
echo "🎯 Master Prompt Compliance: Review existing implementation, then apply cookie-only auth"
echo "📦 Source: ow-ai-dashboard.zip + ow-ai-backend.zip (your working versions)"
echo ""

echo "📋 STEP 1: Backup current state"
echo "=============================="

# Backup current versions
echo "🔄 Backing up current dashboard and backend..."
if [ -d "ow-ai-dashboard" ]; then
    mv ow-ai-dashboard ow-ai-dashboard.current-backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Dashboard backed up"
fi

if [ -d "ow-ai-backend" ]; then
    mv ow-ai-backend ow-ai-backend.current-backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backend backed up"
fi

echo ""
echo "📋 STEP 2: Extract working dashboard"
echo "=================================="

if [ -f "ow-ai-dashboard.zip" ]; then
    echo "📦 Found ow-ai-dashboard.zip"
    echo "🔄 Extracting working dashboard..."
    
    unzip -q ow-ai-dashboard.zip
    echo "✅ Dashboard extracted"
    
    echo "🔍 Dashboard structure:"
    find ow-ai-dashboard -name "*.jsx" -o -name "*.js" | grep -E "(Dashboard|Sidebar|App)" | head -10
    
    echo ""
    echo "📊 Dashboard analysis:"
    if [ -f "ow-ai-dashboard/src/components/Dashboard.jsx" ]; then
        DASH_LINES=$(wc -l < ow-ai-dashboard/src/components/Dashboard.jsx)
        echo "   📄 Dashboard.jsx: $DASH_LINES lines"
        
        echo "   🔍 Dashboard preview (first 10 lines):"
        head -10 ow-ai-dashboard/src/components/Dashboard.jsx | sed 's/^/      /'
    fi
    
    if [ -f "ow-ai-dashboard/src/components/Sidebar.jsx" ]; then
        SIDEBAR_LINES=$(wc -l < ow-ai-dashboard/src/components/Sidebar.jsx)
        echo "   📄 Sidebar.jsx: $SIDEBAR_LINES lines"
        
        echo "   🔍 Checking for tab definitions:"
        grep -n "label\|tab\|Authorization\|Alert\|Smart" ow-ai-dashboard/src/components/Sidebar.jsx | head -5 | sed 's/^/      /'
    fi
    
else
    echo "❌ ow-ai-dashboard.zip not found in current directory"
    echo "🔍 Available ZIP files:"
    ls -la *.zip 2>/dev/null || echo "   No ZIP files found"
    exit 1
fi

echo ""
echo "📋 STEP 3: Extract working backend"
echo "=============================="

if [ -f "ow-ai-backend.zip" ]; then
    echo "📦 Found ow-ai-backend.zip"
    echo "🔄 Extracting working backend..."
    
    unzip -q ow-ai-backend.zip
    echo "✅ Backend extracted"
    
    echo "🔍 Backend structure:"
    find ow-ai-backend -name "*.py" | grep -E "(main|auth|analytics|agent)" | head -10
    
    echo ""
    echo "📊 Backend analysis:"
    if [ -f "ow-ai-backend/main.py" ]; then
        MAIN_LINES=$(wc -l < ow-ai-backend/main.py)
        echo "   📄 main.py: $MAIN_LINES lines"
        
        echo "   🔍 API routes:"
        grep -n "@app\.\|@router\.\|APIRouter\|app\.include" ow-ai-backend/main.py | head -5 | sed 's/^/      /'
    fi
    
    echo "   🔍 Available API files:"
    find ow-ai-backend -name "*.py" -exec grep -l "@router\|@app\|APIRouter" {} \; | head -5 | sed 's/^/      /'
    
else
    echo "❌ ow-ai-backend.zip not found in current directory"
    exit 1
fi

echo ""
echo "📋 STEP 4: Check for comprehensive dashboard features"
echo "================================================"

echo "🔍 Checking dashboard for comprehensive features..."

# Check for sidebar with multiple tabs
if [ -f "ow-ai-dashboard/src/components/Sidebar.jsx" ]; then
    TABS_COUNT=$(grep -c "tab\|Tab" ow-ai-dashboard/src/components/Sidebar.jsx 2>/dev/null || echo "0")
    AUTH_CENTER=$(grep -c "Authorization\|authorization" ow-ai-dashboard/src/components/Sidebar.jsx 2>/dev/null || echo "0")
    AI_ALERTS=$(grep -c "Alert\|alert" ow-ai-dashboard/src/components/Sidebar.jsx 2>/dev/null || echo "0")
    SMART_RULES=$(grep -c "Smart\|Rule" ow-ai-dashboard/src/components/Sidebar.jsx 2>/dev/null || echo "0")
    
    echo "📊 Sidebar features:"
    echo "   📑 Tab references: $TABS_COUNT"
    echo "   🔐 Authorization Center: $AUTH_CENTER"
    echo "   🚨 AI Alerts: $AI_ALERTS"
    echo "   📏 Smart Rules: $SMART_RULES"
fi

# Check App.jsx for comprehensive imports
if [ -f "ow-ai-dashboard/src/App.jsx" ]; then
    echo ""
    echo "🔍 App.jsx component imports:"
    grep "^import.*components" ow-ai-dashboard/src/App.jsx | head -10 | sed 's/^/   /'
fi

echo ""
echo "📋 STEP 5: Check backend for analytics endpoint"
echo "============================================"

echo "🔍 Checking if backend has /analytics/trends endpoint..."

# Search for analytics routes
ANALYTICS_FILES=$(find ow-ai-backend -name "*.py" -exec grep -l "analytics\|trends" {} \; 2>/dev/null)

if [ -n "$ANALYTICS_FILES" ]; then
    echo "✅ Found analytics-related files:"
    echo "$ANALYTICS_FILES" | sed 's/^/   /'
    
    echo ""
    echo "🔍 Analytics endpoints:"
    for file in $ANALYTICS_FILES; do
        echo "   📄 $file:"
        grep -n "trends\|analytics" "$file" | head -3 | sed 's/^/      /'
    done
else
    echo "⚠️  No analytics endpoints found - will need to create"
fi

echo ""
echo "📋 STEP 6: Master Prompt compliance assessment"
echo "==========================================="

echo "🔍 Checking for theme dependencies..."
THEME_USAGE=$(find ow-ai-dashboard/src -name "*.jsx" -exec grep -c "useTheme\|ThemeContext" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
echo "📊 Theme dependencies found: $THEME_USAGE"

echo ""
echo "🔍 Checking for localStorage usage..."
LOCALSTORAGE_USAGE=$(find ow-ai-dashboard/src -name "*.jsx" -o -name "*.js" -exec grep -c "localStorage" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
echo "📊 localStorage usage found: $LOCALSTORAGE_USAGE"

echo ""
echo "✅ WORKING VERSIONS EXTRACTED!"
echo "============================"
echo "🎯 Next steps for Master Prompt compliance:"
echo ""
if [ "$THEME_USAGE" -gt 0 ]; then
    echo "   🔧 Apply theme fixes (remove useTheme dependencies)"
fi
if [ "$LOCALSTORAGE_USAGE" -gt 0 ]; then
    echo "   🍪 Convert localStorage to cookie-only authentication"
fi
if [ -z "$ANALYTICS_FILES" ]; then
    echo "   📊 Add missing /analytics/trends endpoint to backend"
fi
echo ""
echo "🎯 Ready to apply Master Prompt compliance fixes to your working versions!"
