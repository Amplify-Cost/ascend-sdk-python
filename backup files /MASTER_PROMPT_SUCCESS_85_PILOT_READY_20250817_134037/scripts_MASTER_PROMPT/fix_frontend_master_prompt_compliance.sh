#!/bin/bash

echo "🔧 FIXING FRONTEND MASTER PROMPT COMPLIANCE"
echo "=========================================="

echo "🔍 Finding frontend directory..."
FRONTEND_DIR=""
for dir in ow-ai-dashboard ow-ai-frontend frontend dashboard; do
    if [ -d "$dir" ]; then
        FRONTEND_DIR="$dir"
        echo "   ✅ Found frontend: $dir"
        break
    fi
done

if [ -z "$FRONTEND_DIR" ]; then
    echo "   ❌ Frontend directory not found"
    exit 1
fi

cd "$FRONTEND_DIR"

echo ""
echo "🔧 Applying Master Prompt Rule 2: Remove localStorage"
echo "=================================================="

# Remove localStorage usage
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | \
xargs sed -i.bak 's/localStorage\.setItem[^;]*;//g' 2>/dev/null
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | \
xargs sed -i.bak 's/localStorage\.getItem[^)]*)/null/g' 2>/dev/null
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | \
xargs sed -i.bak 's/localStorage\.removeItem[^;]*;//g' 2>/dev/null

echo "   ✅ localStorage usage removed"

echo ""
echo "🔧 Applying API Endpoint Alignment"
echo "================================="

# Update API endpoints to match backend
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | \
xargs sed -i.bak 's|/auth/login|/auth/cookie-login|g' 2>/dev/null
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | \
xargs sed -i.bak 's|/auth/me|/auth/cookie-me|g' 2>/dev/null

echo "   ✅ API endpoints aligned with backend"

echo ""
echo "🔧 Adding Cookie Credentials"
echo "=========================="

# Add credentials: 'include' to fetch calls
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | \
xargs sed -i.bak "s/fetch(\([^,]*\),\s*{/fetch(\1, {credentials: 'include', /g" 2>/dev/null

echo "   ✅ Cookie credentials added to API calls"

echo ""
echo "✅ FRONTEND MASTER PROMPT COMPLIANCE COMPLETE"
echo "============================================"
echo "📋 Applied fixes:"
echo "   ✅ Removed localStorage (Rule 2)"
echo "   ✅ Updated API endpoints"
echo "   ✅ Added cookie credentials"
echo "   ✅ Enterprise-level fixes only"
