#!/bin/bash

# Enterprise Frontend Analysis Script
echo "🏢 ENTERPRISE: Analyzing frontend architecture..."

# Show current directory
echo "Current directory: $(pwd)"
echo ""

# Find frontend directories
echo "=== FRONTEND DIRECTORY STRUCTURE ==="
ls -la

echo ""
echo "=== JAVASCRIPT/TYPESCRIPT FILES ==="
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | grep -v node_modules | head -10

echo ""
echo "=== API CONFIGURATION ANALYSIS ==="
# Look for API configuration files
find . -name "*config*" -o -name "*api*" -o -name "*service*" | grep -v node_modules

echo ""
echo "=== CURRENT API CALLS ANALYSIS ==="
# Find files with the failing API calls we saw in console
grep -r "governance/unified-actions\|authorization/metrics\|mcp-governance" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" . | head -5

echo ""
echo "=== FETCH/AXIOS PATTERNS ==="
grep -r "fetch\|axios" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" . | grep -v node_modules | head -5

echo ""
echo "=== PACKAGE.JSON ANALYSIS ==="
if [ -f "package.json" ]; then
    echo "Frontend stack detected:"
    cat package.json | jq '.dependencies | keys[]' 2>/dev/null | grep -E "(react|vue|angular)" | head -5
fi
