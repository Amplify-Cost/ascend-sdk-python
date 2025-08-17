#!/bin/bash

echo "🔍 DEEP SEARCH FOR YOUR COMPREHENSIVE DASHBOARD"
echo "==============================================="
echo "🎯 Looking for: Dashboard with sidebar + 11 tabs + Smart Rule Route + AI Recommendations"
echo "📍 Searching: All files, all locations, all patterns"
echo ""

echo "📋 STEP 1: Comprehensive file search (all dashboard patterns)"
echo "-----------------------------------------------------------"

# Search for ALL files that might be your comprehensive dashboard
echo "🔍 Searching for Dashboard files with various patterns..."

# Find all possible dashboard files
find . -type f \( -name "*dashboard*" -o -name "*Dashboard*" -o -name "*DASHBOARD*" \) \( -name "*.jsx" -o -name "*.js" -o -name "*.tsx" -o -name "*.ts" \) -exec ls -la {} \; | sort -k5 -nr

echo ""
echo "📋 STEP 2: Extract and analyze ALL files from ZIP archives"
echo "--------------------------------------------------------"

# Extract all ZIP files to find hidden comprehensive dashboards
for zipfile in $(find . -name "*.zip" -type f); do
    echo "📦 Analyzing ZIP: $zipfile"
    
    # Create unique extraction directory
    extract_dir="temp_extract_$(basename "$zipfile" .zip)_$(date +%s)"
    mkdir -p "$extract_dir"
    
    # Extract ZIP
    unzip -q "$zipfile" -d "$extract_dir/" 2>/dev/null
    
    # Find all dashboard-like files in extraction
    dashboard_candidates=$(find "$extract_dir" -type f \( -name "*dashboard*" -o -name "*Dashboard*" \) \( -name "*.jsx" -o -name "*.js" \) 2>/dev/null)
    
    for candidate in $dashboard_candidates; do
        if [ -f "$candidate" ]; then
            lines=$(wc -l < "$candidate" 2>/dev/null || echo "0")
            size=$(ls -la "$candidate" 2>/dev/null | awk '{print $5}' || echo "0")
            
            echo "   📄 Found: $(basename "$candidate") - $lines lines, ${size}bytes"
            
            # Analyze for comprehensive features
            if [ $lines -gt 800 ]; then
                echo "      🎯 ANALYZING COMPREHENSIVE FEATURES..."
                
                # Check for comprehensive dashboard indicators
                sidebar_mentions=$(grep -c -i "sidebar\|sidenav" "$candidate" 2>/dev/null || echo "0")
                tab_mentions=$(grep -c -i "tab.*nav\|navigation.*tab\|activeTab\|setActiveTab" "$candidate" 2>/dev/null || echo "0")
                smart_rule=$(grep -c -i "smart.*rule\|rule.*route\|smart.*route" "$candidate" 2>/dev/null || echo "0")
                ai_recommend=$(grep -c -i "ai.*recommend\|recommendation\|samry" "$candidate" 2>/dev/null || echo "0")
                ab_testing=$(grep -c -i "a.*b.*test\|ab.*test\|experiment" "$candidate" 2>/dev/null || echo "0")
                mcp_monitor=$(grep -c -i "mcp\|protocol.*monitor" "$candidate" 2>/dev/null || echo "0")
                agent_oversight=$(grep -c -i "agent.*oversight\|agent.*monitor\|agent.*management" "$candidate" 2>/dev/null || echo "0")
                
                total_score=$((sidebar_mentions + tab_mentions + smart_rule + ai_recommend + ab_testing + mcp_monitor + agent_oversight))
                
                echo "      📊 Feature Analysis:"
                echo "         Sidebar: $sidebar_mentions | Tabs: $tab_mentions | Smart Rule: $smart_rule"
                echo "         AI Recommend: $ai_recommend | A/B Test: $ab_testing | MCP: $mcp_monitor | Agent: $agent_oversight"
                echo "         🎯 TOTAL SCORE: $total_score"
                
                if [ $total_score -gt 15 ] && [ $lines -gt 1500 ]; then
                    echo "      ⭐⭐⭐ STRONG COMPREHENSIVE DASHBOARD CANDIDATE! ⭐⭐⭐"
                    echo "      📋 Saving as potential comprehensive dashboard..."
                    
                    # Copy to main directory for analysis
                    comprehensive_candidate="comprehensive_dashboard_candidate_${lines}lines_score${total_score}.jsx"
                    cp "$candidate" "./$comprehensive_candidate"
                    echo "      ✅ Saved as: $comprehensive_candidate"
                    
                elif [ $total_score -gt 8 ] && [ $lines -gt 1000 ]; then
                    echo "      ⭐⭐ GOOD COMPREHENSIVE DASHBOARD CANDIDATE! ⭐⭐"
                    moderate_candidate="dashboard_candidate_${lines}lines_score${total_score}.jsx"
                    cp "$candidate" "./$moderate_candidate"
                    echo "      ✅ Saved as: $moderate_candidate"
                fi
            fi
        fi
    done
    
    # Clean up extraction directory
    rm -rf "$extract_dir"
done

echo ""
echo "📋 STEP 3: Analyze all extracted comprehensive dashboard candidates"
echo "================================================================"

# Analyze all saved candidates
for candidate in comprehensive_dashboard_candidate_*.jsx dashboard_candidate_*.jsx; do
    if [ -f "$candidate" ]; then
        lines=$(wc -l < "$candidate" 2>/dev/null || echo "0")
        echo ""
        echo "🔍 DETAILED ANALYSIS: $candidate ($lines lines)"
        echo "═══════════════════════════════════════════════"
        
        echo "📱 Navigation Structure:"
        grep -n -A2 -B2 -i "sidebar\|navigation.*menu\|nav.*bar" "$candidate" 2>/dev/null | head -10
        
        echo ""
        echo "📑 Tab Structure:"
        grep -n -i "tab.*nav\|activeTab\|setActiveTab\|tab.*switch" "$candidate" 2>/dev/null | head -10
        
        echo ""
        echo "🎯 Enterprise Features Found:"
        echo "   Smart Rule Route: $(grep -n -i "smart.*rule\|rule.*route" "$candidate" 2>/dev/null | wc -l) references"
        echo "   AI Recommendations: $(grep -n -i "ai.*recommend\|recommendation" "$candidate" 2>/dev/null | wc -l) references"
        echo "   A/B Testing: $(grep -n -i "a.*b.*test\|experiment" "$candidate" 2>/dev/null | wc -l) references"
        echo "   MCP Monitoring: $(grep -n -i "mcp\|protocol" "$candidate" 2>/dev/null | wc -l) references"
        echo "   Agent Systems: $(grep -n -i "agent.*oversight\|agent.*monitor" "$candidate" 2>/dev/null | wc -l) references"
        
        echo ""
        echo "🔍 Component Preview (first 30 lines):"
        echo "────────────────────────────────────────"
        head -30 "$candidate" | nl
        echo "────────────────────────────────────────"
    fi
done

echo ""
echo "📋 STEP 4: Search for alternative comprehensive dashboard locations"
echo "================================================================"

# Check for other comprehensive dashboard patterns
echo "🔍 Searching for files with 'comprehensive' or 'main' dashboard patterns..."
find . -type f \( -name "*comprehensive*" -o -name "*main*dashboard*" -o -name "*full*dashboard*" \) \( -name "*.jsx" -o -name "*.js" \) -exec ls -la {} \; 2>/dev/null

echo ""
echo "🔍 Searching current directory for large React components (1000+ lines)..."
find . -type f \( -name "*.jsx" -o -name "*.js" \) -exec sh -c 'lines=$(wc -l < "$1" 2>/dev/null); if [ "$lines" -gt 1000 ]; then echo "📄 $1 - $lines lines"; fi' _ {} \; 2>/dev/null

echo ""
echo "📋 STEP 5: Manual verification recommendations"
echo "============================================"

echo "🎯 NEXT STEPS TO FIND YOUR COMPREHENSIVE DASHBOARD:"
echo ""
echo "1. ✅ Review the candidates above - look for files with:"
echo "   - 1500+ lines"
echo "   - High feature scores (15+)"
echo "   - Multiple enterprise features"
echo ""
echo "2. 🔍 Check if any saved candidates match your memory:"
echo "   - Sidebar navigation with ~11 tabs"
echo "   - Smart Rule Route functionality"
echo "   - AI Recommendations section"
echo "   - A/B Testing capabilities"
echo ""
echo "3. 📋 If found, we'll restore with Master Prompt compliance:"
echo "   - Remove theme dependencies"
echo "   - Maintain cookie-only authentication"
echo "   - Preserve all enterprise features"
echo ""

# List all candidates found
candidates=$(ls comprehensive_dashboard_candidate_*.jsx dashboard_candidate_*.jsx 2>/dev/null)
if [ -n "$candidates" ]; then
    echo "📁 DASHBOARD CANDIDATES FOUND:"
    for candidate in $candidates; do
        lines=$(wc -l < "$candidate" 2>/dev/null || echo "0")
        echo "   📄 $candidate ($lines lines)"
    done
    echo ""
    echo "🎯 To restore a candidate, run:"
    echo "   cp [candidate_filename] ow-ai-dashboard/src/components/Dashboard.jsx"
    echo "   git add ow-ai-dashboard/src/components/Dashboard.jsx"
    echo "   git commit -m \"Restore comprehensive dashboard\""
    echo "   git push origin main"
else
    echo "❌ No comprehensive dashboard candidates found."
    echo "   Your original dashboard may be in a different location or format."
fi

echo ""
echo "✅ DEEP COMPREHENSIVE DASHBOARD SEARCH COMPLETE!"
echo "==============================================="
