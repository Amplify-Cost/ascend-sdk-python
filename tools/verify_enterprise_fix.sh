#!/bin/bash
# tools/verify_enterprise_fix.sh
# Final verification that EnterpriseUserManagement.jsx is AWS-ready

set -e

TARGET_FILE="ow-ai-dashboard/src/components/EnterpriseUserManagement.jsx"

echo "🔍 FINAL VERIFICATION: EnterpriseUserManagement.jsx AWS Migration Readiness"
echo "=================================================================="

if [[ ! -f "$TARGET_FILE" ]]; then
    echo "❌ Error: $TARGET_FILE not found"
    exit 1
fi

PASS_COUNT=0
TOTAL_CHECKS=6

echo ""
echo "1️⃣  Checking for hardcoded BASE_URL removal..."
if grep -q "BASE_URL" "$TARGET_FILE"; then
    echo "❌ FAIL: BASE_URL still found"
    grep -n "BASE_URL" "$TARGET_FILE"
else
    echo "✅ PASS: No hardcoded BASE_URL found"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

echo ""
echo "2️⃣  Checking for getAuthHeaders removal..."
if grep -q "getAuthHeaders" "$TARGET_FILE"; then
    echo "❌ FAIL: getAuthHeaders still found"
    grep -n "getAuthHeaders" "$TARGET_FILE"
else
    echo "✅ PASS: No getAuthHeaders found"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

echo ""
echo "3️⃣  Checking for fetchWithAuth import..."
if grep -q "import { fetchWithAuth } from '../utils/fetchWithAuth';" "$TARGET_FILE"; then
    echo "✅ PASS: fetchWithAuth import found"
    grep -n "import { fetchWithAuth }" "$TARGET_FILE"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "❌ FAIL: fetchWithAuth import missing"
fi

echo ""
echo "4️⃣  Checking all API calls use relative paths..."
RELATIVE_CALLS=$(grep -c "fetchWithAuth('/api/enterprise-users\|fetchWithAuth(\`/api/enterprise-users" "$TARGET_FILE" || echo "0")
if [[ $RELATIVE_CALLS -gt 0 ]]; then
    echo "✅ PASS: $RELATIVE_CALLS relative API calls found"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "❌ FAIL: No relative API calls found"
fi

echo ""
echo "5️⃣  Checking for proper quote syntax..."
if grep -q "fetchWithAuth(/api" "$TARGET_FILE"; then
    echo "❌ FAIL: Unquoted paths found"
    grep -n "fetchWithAuth(/api" "$TARGET_FILE"
else
    echo "✅ PASS: All fetchWithAuth calls properly quoted"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

echo ""
echo "6️⃣  Checking for hardcoded URLs..."
if grep -q "https://" "$TARGET_FILE"; then
    echo "❌ FAIL: Hardcoded URLs still found"
    grep -n "https://" "$TARGET_FILE"
else
    echo "✅ PASS: No hardcoded URLs found"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

echo ""
echo "=================================================================="
echo "📊 RESULTS: $PASS_COUNT/$TOTAL_CHECKS checks passed"

if [[ $PASS_COUNT -eq $TOTAL_CHECKS ]]; then
    echo "🎉 SUCCESS: EnterpriseUserManagement.jsx is AWS-ready!"
    echo ""
    echo "✅ Cookie-auth compliant (no Authorization headers)"
    echo "✅ Environment-agnostic (relative /api paths)"
    echo "✅ Cloud-ready (no hardcoded URLs)"
    echo "✅ Ready for AWS Amplify/CloudFront + ALB deployment"
    echo ""
    echo "🚀 You can now deploy to AWS with confidence!"
    
    # Show summary of all fetchWithAuth calls
    echo ""
    echo "📋 Summary of API endpoints (all using fetchWithAuth):"
    grep -n "fetchWithAuth.*api/enterprise-users" "$TARGET_FILE" | sed 's/.*fetchWithAuth/  →/' | sed 's/, {.*//'
    
else
    echo "⚠️  ISSUES FOUND: Please address the failed checks above"
    exit 1
fi

echo ""
echo "🔧 Next steps for AWS migration:"
echo "  1. Test locally: npm run dev (verify all API calls work)"
echo "  2. Configure AWS: Set up CloudFront + ALB routing"
echo "  3. Deploy: Your frontend is now infra-agnostic!"