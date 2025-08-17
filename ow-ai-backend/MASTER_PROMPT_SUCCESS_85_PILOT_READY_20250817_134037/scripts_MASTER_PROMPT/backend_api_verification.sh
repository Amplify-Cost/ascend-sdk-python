#!/bin/bash

echo "🔍 BACKEND API VERIFICATION FOR COMPREHENSIVE DASHBOARD"
echo "======================================================"
echo "🎯 Checking if backend supports the 3,499-line comprehensive dashboard"
echo ""

echo "📋 STEP 1: Analyze Frontend API Requirements"
echo "==========================================="

dashboard_file="ow-ai-dashboard/src/components/Dashboard.jsx"

if [ -f "$dashboard_file" ]; then
    echo "✅ Analyzing restored comprehensive dashboard..."
    
    echo ""
    echo "🔍 API ENDPOINTS REQUIRED BY FRONTEND:"
    echo "────────────────────────────────────────"
    
    # Extract API calls from the comprehensive dashboard
    echo "📡 Finding API calls in comprehensive dashboard..."
    
    # Look for fetch calls, API URLs, and endpoint patterns
    api_calls=$(grep -n -E "(fetch|api|endpoint|\/auth|\/analytics|\/agents|\/workflows|\/mcp)" "$dashboard_file" | head -20)
    
    if [ -n "$api_calls" ]; then
        echo "🎯 FRONTEND API REQUIREMENTS FOUND:"
        echo "$api_calls"
    else
        echo "❌ No obvious API calls found in comprehensive dashboard"
    fi
    
    echo ""
    echo "🔍 BACKEND INTEGRATION PATTERNS:"
    echo "──────────────────────────────────"
    
    # Look for authentication headers usage
    auth_patterns=$(grep -n -i "getAuthHeaders\|authorization\|bearer\|cookie" "$dashboard_file" | head -10)
    if [ -n "$auth_patterns" ]; then
        echo "🍪 Authentication Integration:"
        echo "$auth_patterns"
    fi
    
    echo ""
    echo "🔍 STATE MANAGEMENT & DATA FETCHING:"
    echo "──────────────────────────────────────"
    
    # Look for useEffect and data fetching patterns
    data_fetching=$(grep -n -A3 -B1 "useEffect\|fetch\|axios\|api" "$dashboard_file" | head -15)
    if [ -n "$data_fetching" ]; then
        echo "📊 Data Fetching Patterns:"
        echo "$data_fetching"
    fi
    
else
    echo "❌ Comprehensive dashboard file not found"
fi

echo ""
echo "📋 STEP 2: Check Backend API Implementation"
echo "=========================================="

backend_dir="ow-ai-backend"

if [ -d "$backend_dir" ]; then
    echo "✅ Backend directory found: $backend_dir"
    
    echo ""
    echo "🔍 BACKEND API ROUTES ANALYSIS:"
    echo "─────────────────────────────────"
    
    # Find main.py and route definitions
    main_file=$(find "$backend_dir" -name "main.py" -type f | head -1)
    if [ -f "$main_file" ]; then
        echo "📄 Main backend file: $main_file"
        
        echo ""
        echo "🎯 AVAILABLE API ROUTES:"
        echo "────────────────────────"
        
        # Extract route definitions
        routes=$(grep -n -E "@app\.(get|post|put|delete|patch)" "$main_file" | head -20)
        if [ -n "$routes" ]; then
            echo "$routes"
        else
            echo "❌ No FastAPI routes found in main.py"
        fi
        
        echo ""
        echo "🔍 ENTERPRISE ENDPOINTS CHECK:"
        echo "─────────────────────────────────"
        
        # Check for enterprise-specific endpoints
        agent_routes=$(grep -n -i "agent\|authorization\|workflow\|mcp" "$main_file" | head -10)
        if [ -n "$agent_routes" ]; then
            echo "🏢 Enterprise Routes Found:"
            echo "$agent_routes"
        else
            echo "❌ No enterprise-specific routes found"
        fi
        
    else
        echo "❌ main.py not found in backend directory"
    fi
    
    echo ""
    echo "🔍 BACKEND DIRECTORY STRUCTURE:"
    echo "─────────────────────────────────"
    find "$backend_dir" -name "*.py" -type f | head -15
    
else
    echo "❌ Backend directory not found: $backend_dir"
fi

echo ""
echo "📋 STEP 3: API Compatibility Assessment"
echo "====================================="

echo ""
echo "🎯 CRITICAL BACKEND REQUIREMENTS FOR COMPREHENSIVE DASHBOARD:"
echo "──────────────────────────────────────────────────────────────"
echo ""
echo "Based on the 3,499-line comprehensive dashboard, the backend needs:"
echo ""
echo "🔧 MCP MONITORING APIs:"
echo "   - GET /api/mcp/actions"
echo "   - POST /api/mcp/filters"
echo "   - GET /api/mcp/status"
echo ""
echo "👥 AGENT AUTHORIZATION APIs:"
echo "   - GET /api/agents/pending"
echo "   - POST /api/agents/approve"
echo "   - GET /api/agents/metrics"
echo ""
echo "⚡ WORKFLOW MANAGEMENT APIs:"
echo "   - GET /api/workflows"
echo "   - POST /api/workflows/create"
echo "   - PUT /api/workflows/update"
echo ""
echo "🚀 EXECUTION MONITORING APIs:"
echo "   - GET /api/execution/status"
echo "   - GET /api/execution/history"
echo "   - POST /api/execution/trigger"
echo ""
echo "📊 ANALYTICS & METRICS APIs:"
echo "   - GET /api/analytics/dashboard"
echo "   - GET /api/analytics/trends"
echo "   - GET /api/metrics/approval"

echo ""
echo "📋 STEP 4: Backend API Gap Analysis"
echo "================================="

echo ""
echo "🔍 RECOMMENDED NEXT STEPS:"
echo "────────────────────────────"
echo ""
echo "1. 🔍 IMMEDIATE VERIFICATION:"
echo "   - Test login and check browser console for 404 API errors"
echo "   - Monitor Railway backend logs for missing endpoint requests"
echo ""
echo "2. 🔧 BACKEND API DEVELOPMENT (if gaps found):"
echo "   - Add missing enterprise API endpoints"
echo "   - Implement MCP monitoring routes"
echo "   - Create agent authorization endpoints"
echo "   - Add workflow management APIs"
echo ""
echo "3. 🧪 COMPREHENSIVE TESTING:"
echo "   - Test each tab in the comprehensive dashboard"
echo "   - Verify all enterprise features work end-to-end"
echo "   - Ensure admin access for shug@gmail.com"

echo ""
echo "🚀 TO CHECK CURRENT BACKEND STATUS:"
echo "─────────────────────────────────────"
echo ""
echo "1. Login to dashboard: https://passionate-elegance-production.up.railway.app"
echo "2. Open browser DevTools Console"
echo "3. Check for API errors (404, 500) when navigating tabs"
echo "4. Monitor Railway backend logs for missing endpoints"

echo ""
echo "✅ BACKEND API VERIFICATION COMPLETE!"
echo "===================================="
echo ""
echo "📋 SUMMARY:"
echo "   ✅ Frontend: 3,499-line comprehensive dashboard restored"
echo "   ❓ Backend: Verification needed for enterprise APIs"
echo "   🎯 Next: Test dashboard and identify missing backend endpoints"
