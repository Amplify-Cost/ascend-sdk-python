#!/bin/bash

echo "🔍 FINDING YOUR ORIGINAL SIDEBAR DASHBOARD WITH 11 TABS"
echo "======================================================"
echo "🎯 Looking for: Main dashboard with sidebar navigation and ~11 tabs"
echo "📋 AgentAuthorizationDashboard should be ONE tab, not the main dashboard"
echo ""

echo "📋 STEP 1: Search for Sidebar Navigation Components"
echo "================================================"

# Look for files with sidebar and navigation patterns
echo "🔍 Files with sidebar navigation patterns:"
find . -type f \( -name "*.jsx" -o -name "*.js" \) -exec grep -l -i "sidebar\|sidenav\|navigation.*menu\|nav.*menu" {} \; 2>/dev/null | head -10

echo ""
echo "🔍 Files with tab switching and routing:"
find . -type f \( -name "*.jsx" -o -name "*.js" \) -exec grep -l -E "(Route|Switch|tab.*nav|nav.*tab)" {} \; 2>/dev/null | head -10

echo ""
echo "📋 STEP 2: Look for Main Dashboard with Tab Structure"
echo "==================================================="

# Search for files that might contain multiple tab definitions
echo "🔍 Searching for files with multiple tab definitions..."

for file in $(find . -name "*.jsx" -o -name "*.js" | grep -i dashboard | head -10); do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        
        # Look for tab-related content
        tab_count=$(grep -c -i "tab\|route\|switch" "$file" 2>/dev/null || echo "0")
        sidebar_mentions=$(grep -c -i "sidebar\|navigation" "$file" 2>/dev/null || echo "0")
        
        if [ $lines -gt 500 ] && [ $tab_count -gt 10 ]; then
            echo ""
            echo "🎯 POTENTIAL MAIN DASHBOARD: $file"
            echo "   📊 Size: $lines lines"
            echo "   📑 Tab mentions: $tab_count"
            echo "   🏪 Sidebar mentions: $sidebar_mentions"
            
            echo "   🔍 Component preview:"
            head -20 "$file" | grep -E "(function|const|class|export|import)" | head -5
            
            echo "   🔍 Navigation structure:"
            grep -n -i "sidebar\|navigation\|tab.*nav\|route" "$file" | head -10
        fi
    fi
done

echo ""
echo "📋 STEP 3: Check Backup Directories for Comprehensive Dashboard"
echo "============================================================="

# Check backup directories for larger dashboard files
backup_dirs=$(find . -type d -name "*backup*" -o -name "*BACKUP*" -o -name "*version*" 2>/dev/null)

for backup_dir in $backup_dirs; do
    echo ""
    echo "📁 Checking backup directory: $backup_dir"
    
    dashboard_files=$(find "$backup_dir" -name "*Dashboard*" -type f \( -name "*.jsx" -o -name "*.js" \) 2>/dev/null)
    
    for file in $dashboard_files; do
        if [ -f "$file" ]; then
            lines=$(wc -l < "$file" 2>/dev/null || echo "0")
            tab_count=$(grep -c -i "tab\|route\|switch" "$file" 2>/dev/null || echo "0")
            sidebar_mentions=$(grep -c -i "sidebar\|navigation" "$file" 2>/dev/null || echo "0")
            
            if [ $lines -gt 800 ]; then
                echo "   📄 $file - $lines lines, Tabs: $tab_count, Sidebar: $sidebar_mentions"
                
                # Check if it imports AgentAuthorizationDashboard
                agent_import=$(grep -c "AgentAuthorizationDashboard" "$file" 2>/dev/null || echo "0")
                if [ $agent_import -gt 0 ]; then
                    echo "      ⭐ IMPORTS AgentAuthorizationDashboard - LIKELY YOUR MAIN DASHBOARD!"
                fi
            fi
        fi
    done
done

echo ""
echo "📋 STEP 4: Look for Components that Import AgentAuthorizationDashboard"
echo "=================================================================="

echo "🔍 Files that import AgentAuthorizationDashboard:"
grep -r "AgentAuthorizationDashboard" --include="*.jsx" --include="*.js" . 2>/dev/null | grep import

echo ""
echo "📋 STEP 5: Search for Layout Components"
echo "====================================="

echo "🔍 Looking for layout/container components:"
find . -type f \( -name "*Layout*" -o -name "*Container*" -o -name "*Main*" \) \( -name "*.jsx" -o -name "*.js" \) 2>/dev/null

echo ""
echo "📋 STEP 6: Check App.jsx for Dashboard Routing"
echo "============================================="

app_files=$(find . -name "App.jsx" -o -name "App.js" 2>/dev/null)
for app_file in $app_files; do
    if [ -f "$app_file" ]; then
        echo "🔍 Checking $app_file for dashboard routing:"
        grep -n -A5 -B5 -i "dashboard\|route\|switch" "$app_file" 2>/dev/null | head -20
    fi
done

echo ""
echo "📋 STEP 7: Search Current Directory Structure"
echo "==========================================="

echo "🔍 Current dashboard-related files:"
find . -name "*[Dd]ashboard*" -type f | head -20

echo ""
echo "🎯 RECOMMENDATIONS:"
echo "=================="
echo ""
echo "Based on what you described, we need to find:"
echo "1. 📱 Main dashboard component with sidebar navigation"
echo "2. 🔄 Tab switching logic for ~11 different tabs" 
echo "3. 📋 Route/component mapping where AgentAuthorizationDashboard is just one tab"
echo "4. 🎯 Comprehensive layout that loads different components per tab"
echo ""
echo "The AgentAuthorizationDashboard.jsx (3,499 lines) should be a CHILD component,"
echo "not the main dashboard. Your real main dashboard probably:"
echo "- Has sidebar navigation JSX"
echo "- Maps tabs to different components"
echo "- Includes AgentAuthorizationDashboard as one option"
echo "- Is likely 1000-2000 lines with navigation logic"

echo ""
echo "✅ COMPREHENSIVE DASHBOARD SEARCH COMPLETE!"
echo "=========================================="#!/bin/bash

echo "🔍 FINDING YOUR ORIGINAL SIDEBAR DASHBOARD WITH 11 TABS"
echo "======================================================"
echo "🎯 Looking for: Main dashboard with sidebar navigation and ~11 tabs"
echo "📋 AgentAuthorizationDashboard should be ONE tab, not the main dashboard"
echo ""

echo "📋 STEP 1: Search for Sidebar Navigation Components"
echo "================================================"

# Look for files with sidebar and navigation patterns
echo "🔍 Files with sidebar navigation patterns:"
find . -type f \( -name "*.jsx" -o -name "*.js" \) -exec grep -l -i "sidebar\|sidenav\|navigation.*menu\|nav.*menu" {} \; 2>/dev/null | head -10

echo ""
echo "🔍 Files with tab switching and routing:"
find . -type f \( -name "*.jsx" -o -name "*.js" \) -exec grep -l -E "(Route|Switch|tab.*nav|nav.*tab)" {} \; 2>/dev/null | head -10

echo ""
echo "📋 STEP 2: Look for Main Dashboard with Tab Structure"
echo "==================================================="

# Search for files that might contain multiple tab definitions
echo "🔍 Searching for files with multiple tab definitions..."

for file in $(find . -name "*.jsx" -o -name "*.js" | grep -i dashboard | head -10); do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        
        # Look for tab-related content
        tab_count=$(grep -c -i "tab\|route\|switch" "$file" 2>/dev/null || echo "0")
        sidebar_mentions=$(grep -c -i "sidebar\|navigation" "$file" 2>/dev/null || echo "0")
        
        if [ $lines -gt 500 ] && [ $tab_count -gt 10 ]; then
            echo ""
            echo "🎯 POTENTIAL MAIN DASHBOARD: $file"
            echo "   📊 Size: $lines lines"
            echo "   📑 Tab mentions: $tab_count"
            echo "   🏪 Sidebar mentions: $sidebar_mentions"
            
            echo "   🔍 Component preview:"
            head -20 "$file" | grep -E "(function|const|class|export|import)" | head -5
            
            echo "   🔍 Navigation structure:"
            grep -n -i "sidebar\|navigation\|tab.*nav\|route" "$file" | head -10
        fi
    fi
done

echo ""
echo "📋 STEP 3: Check Backup Directories for Comprehensive Dashboard"
echo "============================================================="

# Check backup directories for larger dashboard files
backup_dirs=$(find . -type d -name "*backup*" -o -name "*BACKUP*" -o -name "*version*" 2>/dev/null)

for backup_dir in $backup_dirs; do
    echo ""
    echo "📁 Checking backup directory: $backup_dir"
    
    dashboard_files=$(find "$backup_dir" -name "*Dashboard*" -type f \( -name "*.jsx" -o -name "*.js" \) 2>/dev/null)
    
    for file in $dashboard_files; do
        if [ -f "$file" ]; then
            lines=$(wc -l < "$file" 2>/dev/null || echo "0")
            tab_count=$(grep -c -i "tab\|route\|switch" "$file" 2>/dev/null || echo "0")
            sidebar_mentions=$(grep -c -i "sidebar\|navigation" "$file" 2>/dev/null || echo "0")
            
            if [ $lines -gt 800 ]; then
                echo "   📄 $file - $lines lines, Tabs: $tab_count, Sidebar: $sidebar_mentions"
                
                # Check if it imports AgentAuthorizationDashboard
                agent_import=$(grep -c "AgentAuthorizationDashboard" "$file" 2>/dev/null || echo "0")
                if [ $agent_import -gt 0 ]; then
                    echo "      ⭐ IMPORTS AgentAuthorizationDashboard - LIKELY YOUR MAIN DASHBOARD!"
                fi
            fi
        fi
    done
done

echo ""
echo "📋 STEP 4: Look for Components that Import AgentAuthorizationDashboard"
echo "=================================================================="

echo "🔍 Files that import AgentAuthorizationDashboard:"
grep -r "AgentAuthorizationDashboard" --include="*.jsx" --include="*.js" . 2>/dev/null | grep import

echo ""
echo "📋 STEP 5: Search for Layout Components"
echo "====================================="

echo "🔍 Looking for layout/container components:"
find . -type f \( -name "*Layout*" -o -name "*Container*" -o -name "*Main*" \) \( -name "*.jsx" -o -name "*.js" \) 2>/dev/null

echo ""
echo "📋 STEP 6: Check App.jsx for Dashboard Routing"
echo "============================================="

app_files=$(find . -name "App.jsx" -o -name "App.js" 2>/dev/null)
for app_file in $app_files; do
    if [ -f "$app_file" ]; then
        echo "🔍 Checking $app_file for dashboard routing:"
        grep -n -A5 -B5 -i "dashboard\|route\|switch" "$app_file" 2>/dev/null | head -20
    fi
done

echo ""
echo "📋 STEP 7: Search Current Directory Structure"
echo "==========================================="

echo "🔍 Current dashboard-related files:"
find . -name "*[Dd]ashboard*" -type f | head -20

echo ""
echo "🎯 RECOMMENDATIONS:"
echo "=================="
echo ""
echo "Based on what you described, we need to find:"
echo "1. 📱 Main dashboard component with sidebar navigation"
echo "2. 🔄 Tab switching logic for ~11 different tabs" 
echo "3. 📋 Route/component mapping where AgentAuthorizationDashboard is just one tab"
echo "4. 🎯 Comprehensive layout that loads different components per tab"
echo ""
echo "The AgentAuthorizationDashboard.jsx (3,499 lines) should be a CHILD component,"
echo "not the main dashboard. Your real main dashboard probably:"
echo "- Has sidebar navigation JSX"
echo "- Maps tabs to different components"
echo "- Includes AgentAuthorizationDashboard as one option"
echo "- Is likely 1000-2000 lines with navigation logic"

echo ""
echo "✅ COMPREHENSIVE DASHBOARD SEARCH COMPLETE!"
echo "=========================================="3






