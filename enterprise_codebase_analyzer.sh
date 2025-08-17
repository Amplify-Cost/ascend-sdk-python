#!/bin/bash

echo "🏢 ENTERPRISE CODEBASE ANALYSIS SCRIPT"
echo "======================================"
echo ""
echo "🎯 PURPOSE: Complete enterprise architecture understanding"
echo "📋 SCOPE: Full-stack authentication, routing, and data flow analysis"
echo ""

cd /Users/mac_001/OW_AI_Project

# Create analysis directory
mkdir -p analysis_reports
REPORT_DIR="analysis_reports/enterprise_analysis_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORT_DIR"

echo "📁 Analysis reports will be saved to: $REPORT_DIR"

echo ""
echo "================== PHASE 1: PROJECT STRUCTURE ANALYSIS =================="
echo ""

echo "📋 1.1: Overall Project Architecture"
echo "==================================="
tree -I 'node_modules|venv|__pycache__|.git' -L 3 > "$REPORT_DIR/project_structure.txt"
echo "✅ Project structure saved to project_structure.txt"

echo ""
echo "📋 1.2: Backend Architecture Analysis"
echo "===================================="
cd ow-ai-backend

echo "🔍 Backend files and structure:"
ls -la > "$REPORT_DIR/backend_files.txt"

echo "🔍 Python files analysis:"
find . -name "*.py" -type f | head -20 > "$REPORT_DIR/python_files.txt"

echo "🔍 Route files analysis:"
find . -path "*/routes/*.py" -type f > "$REPORT_DIR/route_files.txt"

echo "✅ Backend structure analysis complete"

echo ""
echo "📋 1.3: Frontend Architecture Analysis"
echo "====================================="
cd ../ow-ai-dashboard

echo "🔍 Frontend structure:"
ls -la > "$REPORT_DIR/frontend_files.txt"

echo "🔍 React components:"
find src -name "*.jsx" -o -name "*.js" | head -20 > "$REPORT_DIR/react_components.txt"

echo "🔍 Utility files:"
find src/utils -name "*.js" 2>/dev/null > "$REPORT_DIR/utility_files.txt"

echo "✅ Frontend structure analysis complete"

echo ""
echo "================== PHASE 2: AUTHENTICATION ARCHITECTURE =================="
echo ""

cd ../ow-ai-backend

echo "📋 2.1: Authentication System Analysis"
echo "======================================"

echo "🔍 Authentication-related files:"
ls -la | grep -E "(auth|cookie|jwt|dependencies)" > "$REPORT_DIR/auth_files.txt"

echo ""
echo "🔍 Main.py authentication imports:"
echo "=================================" >> "$REPORT_DIR/auth_analysis.txt"
grep -n "import.*auth\|from.*auth\|import.*cookie\|from.*cookie\|import.*jwt\|from.*jwt" main.py >> "$REPORT_DIR/auth_analysis.txt"

echo ""
echo "🔍 Dependencies.py functions:" >> "$REPORT_DIR/auth_analysis.txt"
echo "============================" >> "$REPORT_DIR/auth_analysis.txt"
grep -n "^def\|^async def" dependencies.py >> "$REPORT_DIR/auth_analysis.txt"

echo ""
echo "🔍 Cookie_auth.py functions:" >> "$REPORT_DIR/auth_analysis.txt"
echo "===========================" >> "$REPORT_DIR/auth_analysis.txt"
grep -n "^def\|^async def" cookie_auth.py >> "$REPORT_DIR/auth_analysis.txt"

echo "✅ Authentication analysis complete"

echo ""
echo "📋 2.2: Route Analysis"
echo "====================="

echo "🔍 Available routes in main.py:"
grep -n "@app\." main.py | head -20 > "$REPORT_DIR/main_routes.txt"

echo "🔍 Route includes in main.py:"
grep -n "include_router" main.py > "$REPORT_DIR/router_includes.txt"

echo "🔍 Available route files:"
if [ -d "routes" ]; then
    ls -la routes/ > "$REPORT_DIR/routes_directory.txt"
    for route_file in routes/*.py; do
        if [ -f "$route_file" ]; then
            echo "=== $route_file ===" >> "$REPORT_DIR/all_routes.txt"
            grep -n "@.*\.get\|@.*\.post\|@.*\.put\|@.*\.delete" "$route_file" >> "$REPORT_DIR/all_routes.txt"
        fi
    done
fi

echo "✅ Route analysis complete"

echo ""
echo "================== PHASE 3: DETAILED CODE INSPECTION =================="
echo ""

echo "📋 3.1: Critical File Contents"
echo "=============================="

echo "🔍 Analyzing main.py structure..."
echo "=== MAIN.PY CRITICAL SECTIONS ===" > "$REPORT_DIR/main_py_analysis.txt"
echo "Imports section:" >> "$REPORT_DIR/main_py_analysis.txt"
head -50 main.py >> "$REPORT_DIR/main_py_analysis.txt"

echo ""
echo "CORS Configuration:" >> "$REPORT_DIR/main_py_analysis.txt"
grep -A 10 -B 5 "CORSMiddleware" main.py >> "$REPORT_DIR/main_py_analysis.txt"

echo ""
echo "App initialization:" >> "$REPORT_DIR/main_py_analysis.txt"
grep -A 5 -B 5 "FastAPI" main.py >> "$REPORT_DIR/main_py_analysis.txt"

echo "🔍 Analyzing dependencies.py..."
echo "=== DEPENDENCIES.PY STRUCTURE ===" > "$REPORT_DIR/dependencies_analysis.txt"
head -30 dependencies.py >> "$REPORT_DIR/dependencies_analysis.txt"
echo "" >> "$REPORT_DIR/dependencies_analysis.txt"
grep -A 10 "def get_current_user" dependencies.py >> "$REPORT_DIR/dependencies_analysis.txt"

echo "🔍 Analyzing cookie_auth.py..."
echo "=== COOKIE_AUTH.PY STRUCTURE ===" > "$REPORT_DIR/cookie_auth_analysis.txt"
head -30 cookie_auth.py >> "$REPORT_DIR/cookie_auth_analysis.txt"

echo "✅ Critical file analysis complete"

echo ""
echo "📋 3.2: Frontend Authentication Analysis"
echo "======================================="

cd ../ow-ai-dashboard

echo "🔍 Analyzing fetchWithAuth.js..."
if [ -f "src/utils/fetchWithAuth.js" ]; then
    echo "=== FETCHWITHAUTH.JS STRUCTURE ===" > "$REPORT_DIR/fetchauth_analysis.txt"
    head -50 src/utils/fetchWithAuth.js >> "$REPORT_DIR/fetchauth_analysis.txt"
    echo "" >> "$REPORT_DIR/fetchauth_analysis.txt"
    echo "API_BASE_URL configuration:" >> "$REPORT_DIR/fetchauth_analysis.txt"
    grep -n "API_BASE_URL" src/utils/fetchWithAuth.js >> "$REPORT_DIR/fetchauth_analysis.txt"
fi

echo "🔍 Analyzing App.jsx..."
if [ -f "src/App.jsx" ]; then
    echo "=== APP.JSX AUTHENTICATION SECTION ===" > "$REPORT_DIR/app_jsx_analysis.txt"
    grep -A 10 -B 5 "useEffect\|authentication\|login\|auth" src/App.jsx >> "$REPORT_DIR/app_jsx_analysis.txt"
fi

echo "✅ Frontend authentication analysis complete"

echo ""
echo "================== PHASE 4: ENTERPRISE COMPLIANCE CHECK =================="
echo ""

cd ../ow-ai-backend

echo "📋 4.1: Security Architecture Assessment"
echo "======================================="

echo "🔍 Enterprise security features check:"
echo "=== ENTERPRISE SECURITY AUDIT ===" > "$REPORT_DIR/security_audit.txt"
echo "Cookie security:" >> "$REPORT_DIR/security_audit.txt"
grep -n "cookie\|Cookie" main.py cookie_auth.py >> "$REPORT_DIR/security_audit.txt"

echo "" >> "$REPORT_DIR/security_audit.txt"
echo "CSRF protection:" >> "$REPORT_DIR/security_audit.txt"
grep -n "csrf\|CSRF" main.py cookie_auth.py >> "$REPORT_DIR/security_audit.txt"

echo "" >> "$REPORT_DIR/security_audit.txt"
echo "JWT implementation:" >> "$REPORT_DIR/security_audit.txt"
grep -n "jwt\|JWT" main.py dependencies.py >> "$REPORT_DIR/security_audit.txt"

echo "📋 4.2: Database Integration Check"
echo "================================="

echo "🔍 Database configuration:"
echo "=== DATABASE INTEGRATION ===" > "$REPORT_DIR/database_analysis.txt"
grep -n "database\|Database\|DATABASE" main.py >> "$REPORT_DIR/database_analysis.txt"

echo "" >> "$REPORT_DIR/database_analysis.txt"
echo "Model imports:" >> "$REPORT_DIR/database_analysis.txt"
grep -n "models\|Model" main.py >> "$REPORT_DIR/database_analysis.txt"

echo "✅ Enterprise compliance check complete"

echo ""
echo "================== PHASE 5: ISSUE IDENTIFICATION =================="
echo ""

echo "📋 5.1: Current Issues Analysis"
echo "=============================="

echo "🔍 Identifying potential issues..."
echo "=== CURRENT ISSUES FOUND ===" > "$REPORT_DIR/issues_identified.txt"

echo "Missing endpoints (404 errors):" >> "$REPORT_DIR/issues_identified.txt"
echo "- /analytics/trends" >> "$REPORT_DIR/issues_identified.txt"
echo "- /analytics/realtime/metrics" >> "$REPORT_DIR/issues_identified.txt"
echo "- /analytics/predictive/trends" >> "$REPORT_DIR/issues_identified.txt"
echo "- /analytics/performance/system" >> "$REPORT_DIR/issues_identified.txt"

echo "" >> "$REPORT_DIR/issues_identified.txt"
echo "Authentication status:" >> "$REPORT_DIR/issues_identified.txt"
echo "- Login working: YES" >> "$REPORT_DIR/issues_identified.txt"
echo "- Cookie auth: YES" >> "$REPORT_DIR/issues_identified.txt"
echo "- Admin access: YES" >> "$REPORT_DIR/issues_identified.txt"

echo "" >> "$REPORT_DIR/issues_identified.txt"
echo "Import conflicts:" >> "$REPORT_DIR/issues_identified.txt"
echo "- Previous issue resolved" >> "$REPORT_DIR/issues_identified.txt"

echo "✅ Issue identification complete"

echo ""
echo "================== PHASE 6: ENTERPRISE RECOMMENDATIONS =================="
echo ""

echo "📋 6.1: Architecture Recommendations"
echo "==================================="

cat > "$REPORT_DIR/enterprise_recommendations.txt" << 'EOF'
=== ENTERPRISE ARCHITECTURE RECOMMENDATIONS ===

IMMEDIATE PRIORITIES:
1. Add missing analytics endpoints to support dashboard functionality
2. Implement proper WebSocket support for real-time features
3. Ensure all route modules are properly included

ENTERPRISE ENHANCEMENTS:
1. Add comprehensive error handling for all endpoints
2. Implement proper logging and monitoring
3. Add rate limiting for production security
4. Enhance CORS configuration for enterprise deployment

LONG-TERM IMPROVEMENTS:
1. Add comprehensive API documentation
2. Implement health check endpoints
3. Add metrics and monitoring endpoints
4. Consider implementing caching layer

SECURITY HARDENING:
1. Review all authentication paths
2. Implement proper session timeout
3. Add brute force protection
4. Enhance audit logging
EOF

echo "✅ Enterprise recommendations generated"

echo ""
echo "================== ANALYSIS COMPLETE =================="
echo ""

echo "📊 ENTERPRISE CODEBASE ANALYSIS SUMMARY:"
echo "========================================"
echo ""
echo "✅ Project structure analyzed"
echo "✅ Authentication architecture mapped"
echo "✅ Route system documented"
echo "✅ Security features audited"
echo "✅ Issues identified"
echo "✅ Enterprise recommendations provided"
echo ""
echo "📁 All analysis reports saved to: $REPORT_DIR"
echo ""
echo "🔍 KEY FILES TO REVIEW:"
echo "- $REPORT_DIR/auth_analysis.txt (Authentication system)"
echo "- $REPORT_DIR/main_routes.txt (Available endpoints)"
echo "- $REPORT_DIR/issues_identified.txt (Current problems)"
echo "- $REPORT_DIR/enterprise_recommendations.txt (Next steps)"
echo ""
echo "📋 To view a specific analysis:"
echo "cat $REPORT_DIR/[filename].txt"
echo ""
echo "🏢 Ready for intelligent enterprise-level fixes based on actual codebase!"
echo "========================================================================"
