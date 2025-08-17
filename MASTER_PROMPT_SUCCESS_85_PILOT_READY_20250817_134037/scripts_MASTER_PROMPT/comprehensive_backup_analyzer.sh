#!/bin/bash

echo "🔍 COMPREHENSIVE BACKUP ANALYZER & ORIGINAL DASHBOARD FINDER"
echo "==========================================================="
echo "✅ Master Prompt Compliance: Review existing code before changes"
echo "✅ Goal: Find and analyze your ORIGINAL enterprise dashboard"
echo "✅ Strategy: Examine all backup versions to identify authentic implementation"
echo "✅ Output: Detailed analysis of original features and functionality"
echo ""

# 1. Comprehensive backup discovery
echo "📋 STEP 1: Comprehensive Backup Discovery"
echo "==========================================="

echo "🔍 Finding all Dashboard-related files in your project:"
find . -name "*[Dd]ashboard*" -type f 2>/dev/null | grep -v node_modules | sort

echo ""
echo "🔍 Finding all backup directories:"
find . -name "*backup*" -type d 2>/dev/null | sort

echo ""
echo "🔍 Finding all version backup directories:"
find . -name "*VERSION*" -type d 2>/dev/null | sort

# 2. Detailed analysis of each Dashboard version
echo ""
echo "📋 STEP 2: Detailed Analysis of Each Dashboard Version"
echo "====================================================="

DASHBOARD_FILES=(
    "ow-ai-dashboard/src/components/Dashboard.jsx"
    "ow-ai-dashboard/src/components/Dashboard.jsx.backup.20250817_054234"
    "COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_20250817_024300/current_working/ow-ai-dashboard/src/components/Dashboard.jsx"
    "backup_step2_cookie_auth_20250817_005533/ow-ai-dashboard/src/components/Dashboard.jsx"
)

for i in "${!DASHBOARD_FILES[@]}"; do
    FILE="${DASHBOARD_FILES[$i]}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📄 DASHBOARD VERSION $((i+1)): $FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "$FILE" ]; then
        echo "✅ File exists ($(wc -l < "$FILE") lines)"
        
        echo ""
        echo "🔍 IMPORTS & DEPENDENCIES:"
        head -20 "$FILE" | grep -E "import|from"
        
        echo ""
        echo "🔍 COMPONENT STRUCTURE:"
        grep -n "const.*=\|function\|class\|export" "$FILE" | head -10
        
        echo ""
        echo "🔍 STATE MANAGEMENT:"
        grep -n "useState\|useEffect\|state" "$FILE" | head -5
        
        echo ""
        echo "🔍 API CALLS & DATA FETCHING:"
        grep -n "fetch\|api\|axios\|data" "$FILE" | head -5
        
        echo ""
        echo "🔍 THEME/STYLING APPROACH:"
        grep -n "theme\|styled\|css\|style" "$FILE" | head -5
        
        echo ""
        echo "🔍 KEY FEATURES & FUNCTIONALITY:"
        grep -n "dashboard\|analytics\|chart\|graph\|admin" "$FILE" | head -5
        
        echo ""
        echo "🔍 ENTERPRISE FEATURES:"
        grep -n "enterprise\|admin\|role\|permission" "$FILE" | head -5
        
        echo ""
        echo "🔍 FILE SIZE & COMPLEXITY:"
        echo "   Lines: $(wc -l < "$FILE")"
        echo "   Size: $(du -h "$FILE" | cut -f1)"
        echo "   Last modified: $(stat -f "%Sm" "$FILE" 2>/dev/null || stat -c "%y" "$FILE" 2>/dev/null)"
        
        echo ""
        echo "🔍 FIRST 30 LINES PREVIEW:"
        echo "────────────────────────────────────────"
        head -30 "$FILE" | nl
        echo "────────────────────────────────────────"
        
        echo ""
        echo "🔍 COMPONENT STRUCTURE ANALYSIS:"
        echo "   React Hooks Used:"
        grep -o "use[A-Z][a-zA-Z]*" "$FILE" | sort | uniq -c | sort -nr
        
        echo ""
        echo "   External Dependencies:"
        grep -E "from ['\"]" "$FILE" | sed "s/.*from ['\"]//g" | sed "s/['\"].*//g" | sort | uniq
        
    else
        echo "❌ File not found"
    fi
done

# 3. Analyze additional enterprise components
echo ""
echo "📋 STEP 3: Analyze Additional Enterprise Components"
echo "================================================="

ADDITIONAL_COMPONENTS=(
    "ow-ai-dashboard/src/components/RealTimeAnalyticsDashboard.jsx"
    "ow-ai-dashboard/src/components/AgentAuthorizationDashboard.jsx"
    "COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_20250817_024300/current_working/ow-ai-dashboard/src/components/RealTimeAnalyticsDashboard.jsx"
    "COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_20250817_024300/current_working/ow-ai-dashboard/src/components/AgentAuthorizationDashboard.jsx"
)

for COMPONENT in "${ADDITIONAL_COMPONENTS[@]}"; do
    echo ""
    echo "🔍 ANALYZING: $COMPONENT"
    if [ -f "$COMPONENT" ]; then
        echo "✅ Found ($(wc -l < "$COMPONENT") lines)"
        echo "📋 Purpose & Functionality:"
        head -20 "$COMPONENT" | grep -E "//.*|/\*.*\*/|export|const.*="
        
        echo ""
        echo "📋 Key Features:"
        grep -n "function\|const.*=\|export" "$COMPONENT" | head -5
    else
        echo "❌ Not found"
    fi
done

# 4. Compare dashboards to identify the most complete version
echo ""
echo "📋 STEP 4: Dashboard Comparison & Recommendation"
echo "==============================================="

echo "🔍 DASHBOARD COMPARISON MATRIX:"
echo "────────────────────────────────────────────────────────────────────"
printf "%-60s %-10s %-15s %-15s\n" "File" "Lines" "Last Modified" "Features"
echo "────────────────────────────────────────────────────────────────────"

for FILE in "${DASHBOARD_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        LINES=$(wc -l < "$FILE")
        MODIFIED=$(stat -f "%Sm" "$FILE" 2>/dev/null || stat -c "%y" "$FILE" 2>/dev/null | cut -d' ' -f1)
        FEATURES=$(grep -c "function\|const.*=\|useEffect\|useState" "$FILE")
        printf "%-60s %-10s %-15s %-15s\n" "$(basename "$FILE")" "$LINES" "$MODIFIED" "$FEATURES"
    else
        printf "%-60s %-10s %-15s %-15s\n" "$(basename "$FILE")" "0" "N/A" "Missing"
    fi
done

# 5. Create restoration recommendations
echo ""
echo "📋 STEP 5: Restoration Recommendations"
echo "===================================="

echo "🎯 ANALYSIS SUMMARY:"
echo ""

# Find the largest/most complex dashboard (likely the original)
LARGEST_FILE=""
LARGEST_SIZE=0

for FILE in "${DASHBOARD_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        SIZE=$(wc -l < "$FILE")
        if [ $SIZE -gt $LARGEST_SIZE ]; then
            LARGEST_SIZE=$SIZE
            LARGEST_FILE=$FILE
        fi
    fi
done

if [ -n "$LARGEST_FILE" ]; then
    echo "📊 MOST COMPLEX DASHBOARD FOUND:"
    echo "   File: $LARGEST_FILE"
    echo "   Lines: $LARGEST_SIZE"
    echo "   This is likely your original enterprise dashboard"
    
    echo ""
    echo "🔍 DETAILED ANALYSIS OF MOST COMPLEX VERSION:"
    echo "────────────────────────────────────────────────────"
    
    # Analyze the most complex version in detail
    if [ -f "$LARGEST_FILE" ]; then
        echo "✅ Components and Features Found:"
        grep -n "const\|function\|export" "$LARGEST_FILE" | head -10
        
        echo ""
        echo "✅ API Integration:"
        grep -n "fetch\|api\|http" "$LARGEST_FILE" | head -5
        
        echo ""
        echo "✅ State Management:"
        grep -n "useState\|useEffect" "$LARGEST_FILE" | head -5
        
        echo ""
        echo "✅ Enterprise Features:"
        grep -n "admin\|role\|permission\|enterprise" "$LARGEST_FILE" | head -5
    fi
fi

# 6. Generate restoration script
echo ""
echo "📋 STEP 6: Generate Master Prompt Compliant Restoration Plan"
echo "==========================================================="

if [ -n "$LARGEST_FILE" ]; then
    cat > restore_original_dashboard_plan.sh << EOF
#!/bin/bash

echo "🔄 RESTORE ORIGINAL ENTERPRISE DASHBOARD"
echo "========================================"
echo "✅ Master Prompt Compliance: Based on backup analysis"
echo "✅ Source: $LARGEST_FILE ($LARGEST_SIZE lines)"
echo "✅ Approach: Restore original with theme compatibility fixes"
echo ""

# Backup current version
cp ow-ai-dashboard/src/components/Dashboard.jsx ow-ai-dashboard/src/components/Dashboard_current_backup.jsx

# Restore the most complete version
echo "🔄 Restoring original dashboard from: $LARGEST_FILE"
cp "$LARGEST_FILE" ow-ai-dashboard/src/components/Dashboard.jsx

# Check for theme dependencies and fix them
echo "🔧 Analyzing theme dependencies..."
if grep -q "useTheme\|ThemeProvider" ow-ai-dashboard/src/components/Dashboard.jsx; then
    echo "⚠️ Theme dependencies found - will need Master Prompt compliant fixes"
    echo "   - Remove useTheme hooks"
    echo "   - Replace with inline styles"
    echo "   - Maintain cookie-only authentication"
else
    echo "✅ No theme dependencies found"
fi

echo "✅ Original dashboard restoration plan created"
echo "Next: Review the restored dashboard and apply Master Prompt compliance fixes"
EOF

    chmod +x restore_original_dashboard_plan.sh
    echo "✅ Restoration plan created: restore_original_dashboard_plan.sh"
fi

echo ""
echo "✅ COMPREHENSIVE BACKUP ANALYSIS COMPLETE!"
echo "=========================================="
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Review the detailed analysis above"
echo "   2. Identify which dashboard version has your original features"
echo "   3. Run the restoration plan to restore your authentic dashboard"
echo "   4. Apply Master Prompt compliance fixes (remove theme dependencies)"
echo "   5. Test with working authentication system"
echo ""
echo "🔍 KEY FINDINGS:"
if [ -n "$LARGEST_FILE" ]; then
    echo "   📊 Most Complex Dashboard: $LARGEST_FILE ($LARGEST_SIZE lines)"
    echo "   🎯 Recommended for restoration (likely your original)"
else
    echo "   ⚠️ No complex dashboard versions found - may need manual review"
fi
echo ""
echo "🏢 MASTER PROMPT COMPLIANCE:"
echo "   ✅ All analysis preserves working authentication"
echo "   ✅ Restoration will maintain cookie-only auth"
echo "   ✅ Theme fixes will be applied after restoration"
