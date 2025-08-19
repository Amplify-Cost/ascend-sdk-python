#!/bin/bash

echo "🔍 FIND COMPREHENSIVE DASHBOARD WITH SIDEBAR & 11 TABS"
echo "====================================================="
echo "✅ Target: Large dashboard with sidebar navigation and ~11 tabs"
echo "✅ Features: Multiple tabs, sub-tabs, comprehensive enterprise UI"
echo "✅ Master Prompt: Review existing comprehensive implementation"
echo ""

# 1. Find largest Dashboard files (comprehensive ones will be bigger)
echo "📋 STEP 1: Find Largest Dashboard Files"
echo "======================================"

echo "🔍 Ranking ALL Dashboard files by size (largest first):"
find . -name "*[Dd]ashboard*" -type f 2>/dev/null | grep -v node_modules | while read file; do
    if [ -f "$file" ]; then
        LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
        BYTES=$(wc -c < "$file" 2>/dev/null || echo "0")
        echo "$LINES|$BYTES|$file"
    fi
done | sort -t'|' -k1 -nr | head -15 | while IFS='|' read lines bytes file; do
    echo "📄 $file"
    echo "   📊 Lines: $lines, Size: $(echo "$bytes" | awk '{print int($1/1024)"KB"}')"
    echo "   📅 Modified: $(stat -f "%Sm" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d' ' -f1-2)"
    echo ""
done

# 2. Search for sidebar and navigation patterns
echo "📋 STEP 2: Search for Sidebar Navigation Patterns"
echo "================================================"

echo "🔍 Searching for sidebar and tab navigation code:"

NAVIGATION_KEYWORDS=("sidebar" "Sidebar" "navigation" "Navigation" "nav" "Nav" "tabs" "Tabs" "tab" "Tab" "menu" "Menu" "route" "Route" "switch" "Switch")

find . -name "*[Dd]ashboard*" -type f 2>/dev/null | grep -v node_modules | while read file; do
    if [ -f "$file" ]; then
        SIDEBAR_SCORE=0
        FEATURES=""
        
        # Check for sidebar patterns
        if grep -qi "sidebar\|side-bar\|sideBar" "$file"; then
            SIDEBAR_COUNT=$(grep -ci "sidebar\|side-bar\|sideBar" "$file")
            SIDEBAR_SCORE=$((SIDEBAR_SCORE + SIDEBAR_COUNT * 5))
            FEATURES="$FEATURES Sidebar($SIDEBAR_COUNT)"
        fi
        
        # Check for navigation patterns
        if grep -qi "navigation\|nav.*menu\|nav.*bar" "$file"; then
            NAV_COUNT=$(grep -ci "navigation\|nav.*menu\|nav.*bar" "$file")
            SIDEBAR_SCORE=$((SIDEBAR_SCORE + NAV_COUNT * 3))
            FEATURES="$FEATURES Navigation($NAV_COUNT)"
        fi
        
        # Check for multiple tabs
        if grep -qi "tab\|tabs" "$file"; then
            TAB_COUNT=$(grep -ci "tab\|tabs" "$file")
            SIDEBAR_SCORE=$((SIDEBAR_SCORE + TAB_COUNT * 2))
            FEATURES="$FEATURES Tabs($TAB_COUNT)"
        fi
        
        # Check for routing/switching
        if grep -qi "route\|routes\|switch\|router" "$file"; then
            ROUTE_COUNT=$(grep -ci "route\|routes\|switch\|router" "$file")
            SIDEBAR_SCORE=$((SIDEBAR_SCORE + ROUTE_COUNT))
            FEATURES="$FEATURES Routing($ROUTE_COUNT)"
        fi
        
        # Only show files with significant navigation features
        if [ "$SIDEBAR_SCORE" -gt 10 ]; then
            LINES=$(wc -l < "$file")
            echo ""
            echo "🎯 NAVIGATION CANDIDATE: $file"
            echo "   📊 Lines: $LINES, Navigation Score: $SIDEBAR_SCORE"
            echo "   🎯 Features:$FEATURES"
            echo "   📅 Modified: $(stat -f "%Sm" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null)"
        fi
    fi
done

# 3. Deep analysis of top candidates
echo ""
echo "📋 STEP 3: Deep Analysis of Top Candidates"
echo "========================================="

echo "🔍 Analyzing largest Dashboard files for comprehensive features:"

find . -name "*[Dd]ashboard*" -type f 2>/dev/null | grep -v node_modules | while read file; do
    if [ -f "$file" ]; then
        LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
        echo "$LINES|$file"
    fi
done | sort -t'|' -k1 -nr | head -5 | while IFS='|' read lines file; do
    if [ "$lines" -gt 800 ]; then  # Focus on substantial files
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 COMPREHENSIVE ANALYSIS: $file"
        echo "   📊 Lines: $lines"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        echo "🔍 IMPORTS & DEPENDENCIES:"
        head -30 "$file" | grep -E "import|from" | head -10
        
        echo ""
        echo "🔍 SIDEBAR/NAVIGATION EVIDENCE:"
        grep -ni "sidebar\|navigation\|nav\|menu" "$file" | head -5
        
        echo ""
        echo "🔍 TAB STRUCTURE:"
        grep -ni "tab\|Tab" "$file" | head -8
        
        echo ""
        echo "🔍 ROUTING/SWITCHING:"
        grep -ni "route\|Route\|switch\|Switch" "$file" | head -5
        
        echo ""
        echo "🔍 COMPONENT STRUCTURE:"
        grep -n "const.*=\|function\|export.*function\|class" "$file" | head -10
        
        echo ""
        echo "🔍 STATE MANAGEMENT:"
        grep -n "useState\|useEffect\|useState\|state" "$file" | head -8
        
        echo ""
        echo "🔍 FIRST 50 LINES PREVIEW:"
        echo "────────────────────────────────────────────────────────────────"
        head -50 "$file" | nl
        echo "────────────────────────────────────────────────────────────────"
        
        # Count different types of functionality
        echo ""
        echo "🔍 FUNCTIONALITY ANALYSIS:"
        echo "   Sidebar mentions: $(grep -ci "sidebar\|side-bar" "$file" 2>/dev/null || echo "0")"
        echo "   Tab mentions: $(grep -ci "tab" "$file" 2>/dev/null || echo "0")"
        echo "   Route mentions: $(grep -ci "route\|Route" "$file" 2>/dev/null || echo "0")"
        echo "   Component exports: $(grep -c "export.*function\|export.*const\|export default" "$file" 2>/dev/null || echo "0")"
        echo "   React hooks: $(grep -c "useState\|useEffect\|useContext\|useReducer" "$file" 2>/dev/null || echo "0")"
        echo "   Event handlers: $(grep -c "onClick\|onChange\|onSubmit\|handle" "$file" 2>/dev/null || echo "0")"
        
        echo ""
        echo "🔍 LOOKING FOR 11+ TABS PATTERN:"
        # Search for arrays or objects that might contain tab definitions
        grep -A 20 -B 5 "\[.*{.*name\|tabs.*=\|\{.*title.*\}\|menuItems\|navigation.*items" "$file" | head -30
    fi
done

# 4. Search in backup directories specifically
echo ""
echo "📋 STEP 4: Search Backup Directories for Comprehensive Dashboard"
echo "=============================================================="

BACKUP_LOCATIONS=(
    "COMPLETE_VERSION_BACKUPS"
    "backup_step2_cookie_auth_20250817_005533"
    "backup_integration_fix_20250817_020851"
    "backup_hs256_to_rs256_20250816_234920"
)

for backup_dir in "${BACKUP_LOCATIONS[@]}"; do
    if [ -d "$backup_dir" ]; then
        echo ""
        echo "🔍 SEARCHING: $backup_dir"
        echo "──────────────────────────────────────────────────────────"
        
        find "$backup_dir" -name "*[Dd]ashboard*" -type f 2>/dev/null | while read file; do
            if [ -f "$file" ]; then
                LINES=$(wc -l < "$file")
                if [ "$LINES" -gt 1000 ]; then  # Focus on very large files
                    echo "📄 LARGE FILE FOUND: $file"
                    echo "   📊 Lines: $LINES"
                    echo "   📅 Modified: $(stat -f "%Sm" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null)"
                    
                    # Quick comprehensive feature check
                    SIDEBAR_COUNT=$(grep -ci "sidebar\|navigation" "$file" 2>/dev/null || echo "0")
                    TAB_COUNT=$(grep -ci "tab" "$file" 2>/dev/null || echo "0")
                    ROUTE_COUNT=$(grep -ci "route" "$file" 2>/dev/null || echo "0")
                    COMPONENT_COUNT=$(grep -c "const.*=\|function" "$file" 2>/dev/null || echo "0")
                    
                    echo "   🎯 Sidebar/Nav: $SIDEBAR_COUNT, Tabs: $TAB_COUNT, Routes: $ROUTE_COUNT, Components: $COMPONENT_COUNT"
                    
                    if [ "$SIDEBAR_COUNT" -gt 5 ] && [ "$TAB_COUNT" -gt 10 ]; then
                        echo "   ⭐ POTENTIAL COMPREHENSIVE DASHBOARD MATCH!"
                        echo "   📋 Quick preview:"
                        head -20 "$file" | grep -E "import|export|const|function" | head -5 | sed 's/^/      /'
                    fi
                    echo ""
                fi
            fi
        done
    fi
done

# 5. Final recommendation
echo ""
echo "📋 STEP 5: Final Recommendation"
echo "=============================="

echo "🎯 COMPREHENSIVE DASHBOARD IDENTIFICATION:"
echo ""
echo "Looking for dashboard with:"
echo "   ✅ 1500+ lines of code (comprehensive implementation)"
echo "   ✅ Sidebar navigation with ~11 tabs"
echo "   ✅ Sub-tabs within main tabs"
echo "   ✅ Multiple route/switch statements"
echo "   ✅ Extensive component structure"
echo ""
echo "🔍 Based on analysis above, the comprehensive dashboard should be:"
echo "   - One of the largest files (2000+ lines likely)"
echo "   - High sidebar/navigation mentions"
echo "   - Multiple tab references (11+)"
echo "   - Complex routing structure"
echo ""
echo "✅ Use the analysis above to identify your comprehensive dashboard"
echo "✅ The file with the highest combination of size + navigation features"
echo "✅ Should be in one of the backup directories from recent dates"
