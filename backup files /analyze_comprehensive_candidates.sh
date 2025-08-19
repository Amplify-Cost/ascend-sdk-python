#!/bin/bash

echo "🔍 ANALYZING COMPREHENSIVE DASHBOARD CANDIDATES"
echo "=============================================="
echo "🎯 Target: Dashboard with sidebar + 11 tabs + Smart Rule Route + AI Recommendations"
echo ""

echo "📋 STEP 1: Detailed Analysis of Top Candidates"
echo "============================================="

# Top candidates identified from search
candidates=(
    "ow-ai-dashboard/src/components/AgentAuthorizationDashboard.jsx"
    "ow-ai-dashboard/src/components/AIAlertManagementSystem.jsx" 
    "ow-ai-dashboard/src/components/EnterpriseUserManagement.jsx"
    "COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_20250817_024300/current_working/ow-ai-dashboard/src/components/AgentAuthorizationDashboard.jsx"
    "extracted_comprehensive_dashboard/ow-ai-dashboard/src/components/AgentAuthorizationDashboard.jsx"
)

for candidate in "${candidates[@]}"; do
    if [ -f "$candidate" ]; then
        lines=$(wc -l < "$candidate" 2>/dev/null || echo "0")
        echo ""
        echo "🔍 ANALYZING: $(basename "$candidate") ($lines lines)"
        echo "═══════════════════════════════════════════════════════════"
        
        echo "📊 ENTERPRISE FEATURE ANALYSIS:"
        
        # Count comprehensive dashboard features
        sidebar_count=$(grep -c -i "sidebar\|sidenav\|navigation.*menu" "$candidate" 2>/dev/null || echo "0")
        tab_count=$(grep -c -i "activeTab\|setActiveTab\|tab.*nav\|tab.*switch" "$candidate" 2>/dev/null || echo "0")
        smart_rule_count=$(grep -c -i "smart.*rule\|rule.*route\|smart.*route" "$candidate" 2>/dev/null || echo "0")
        ai_recommend_count=$(grep -c -i "ai.*recommend\|recommendation\|samry" "$candidate" 2>/dev/null || echo "0")
        ab_test_count=$(grep -c -i "a.*b.*test\|ab.*test\|experiment" "$candidate" 2>/dev/null || echo "0")
        mcp_count=$(grep -c -i "mcp\|protocol.*monitor" "$candidate" 2>/dev/null || echo "0")
        agent_count=$(grep -c -i "agent.*oversight\|agent.*monitor\|agent.*management" "$candidate" 2>/dev/null || echo "0")
        
        total_score=$((sidebar_count + tab_count + smart_rule_count + ai_recommend_count + ab_test_count + mcp_count + agent_count))
        
        echo "   🏪 Sidebar/Navigation: $sidebar_count mentions"
        echo "   📑 Tab Management: $tab_count mentions"  
        echo "   ⚡ Smart Rule Route: $smart_rule_count mentions"
        echo "   🤖 AI Recommendations: $ai_recommend_count mentions"
        echo "   🧪 A/B Testing: $ab_test_count mentions"
        echo "   🔧 MCP Monitoring: $mcp_count mentions"
        echo "   👥 Agent Systems: $agent_count mentions"
        echo "   🎯 TOTAL FEATURE SCORE: $total_score"
        
        # Determine candidate strength
        if [ $total_score -gt 20 ] && [ $lines -gt 2000 ]; then
            echo "   ⭐⭐⭐ EXCELLENT COMPREHENSIVE DASHBOARD CANDIDATE! ⭐⭐⭐"
            candidate_strength="EXCELLENT"
        elif [ $total_score -gt 10 ] && [ $lines -gt 1000 ]; then
            echo "   ⭐⭐ STRONG COMPREHENSIVE DASHBOARD CANDIDATE! ⭐⭐"
            candidate_strength="STRONG"
        elif [ $total_score -gt 5 ] && [ $lines -gt 800 ]; then
            echo "   ⭐ GOOD DASHBOARD CANDIDATE! ⭐"
            candidate_strength="GOOD"
        else
            echo "   ❓ LIMITED COMPREHENSIVE FEATURES"
            candidate_strength="LIMITED"
        fi
        
        echo ""
        echo "🔍 NAVIGATION STRUCTURE PREVIEW:"
        echo "─────────────────────────────────"
        grep -n -i "sidebar\|navigation\|activeTab\|tab.*nav" "$candidate" 2>/dev/null | head -8
        
        echo ""
        echo "🎯 ENTERPRISE FEATURES PREVIEW:"
        echo "─────────────────────────────────"
        grep -n -i "smart.*rule\|ai.*recommend\|a.*b.*test\|mcp\|agent.*oversight" "$candidate" 2>/dev/null | head -5
        
        echo ""
        echo "📱 COMPONENT STRUCTURE PREVIEW (first 25 lines):"
        echo "─────────────────────────────────────────────────"
        head -25 "$candidate" | nl
        
        # Save excellent candidates
        if [ "$candidate_strength" = "EXCELLENT" ] || [ "$candidate_strength" = "STRONG" ]; then
            echo ""
            echo "💾 SAVING CANDIDATE: Copying to restoration candidates..."
            cp "$candidate" "./comprehensive_candidate_$(basename "$candidate" .jsx)_${lines}lines_score${total_score}.jsx"
            echo "   ✅ Saved as: comprehensive_candidate_$(basename "$candidate" .jsx)_${lines}lines_score${total_score}.jsx"
        fi
        
        echo "═══════════════════════════════════════════════════════════"
    fi
done

echo ""
echo "📋 STEP 2: Identify Best Comprehensive Dashboard"
echo "=============================================="

echo "🏆 RANKING CANDIDATES BY COMPREHENSIVE FEATURES:"
echo ""

# List all saved candidates with scores
saved_candidates=$(ls comprehensive_candidate_*.jsx 2>/dev/null)
if [ -n "$saved_candidates" ]; then
    echo "📁 COMPREHENSIVE DASHBOARD CANDIDATES FOUND:"
    for candidate in $saved_candidates; do
        if [ -f "$candidate" ]; then
            lines=$(echo "$candidate" | grep -o '[0-9]*lines' | sed 's/lines//')
            score=$(echo "$candidate" | grep -o 'score[0-9]*' | sed 's/score//')
            echo "   📄 $candidate"
            echo "      📊 Lines: $lines | 🎯 Feature Score: $score"
            
            # Quick feature check
            if [ -n "$lines" ] && [ "$lines" -gt 2000 ] && [ -n "$score" ] && [ "$score" -gt 15 ]; then
                echo "      ⭐⭐⭐ HIGHLY RECOMMENDED FOR RESTORATION ⭐⭐⭐"
                best_candidate="$candidate"
            fi
        fi
    done
    
    echo ""
    echo "📋 STEP 3: Restoration Recommendation"
    echo "==================================="
    
    if [ -n "$best_candidate" ]; then
        echo "🎯 RECOMMENDED COMPREHENSIVE DASHBOARD: $best_candidate"
        echo ""
        echo "🔧 READY FOR MASTER PROMPT COMPLIANT RESTORATION:"
        echo "   ✅ Contains comprehensive enterprise features"
        echo "   ✅ High feature score (15+ points)"
        echo "   ✅ Large implementation (2000+ lines)"
        echo "   ✅ Likely your original dashboard with sidebar + tabs"
        echo ""
        echo "🚀 TO RESTORE YOUR COMPREHENSIVE DASHBOARD:"
        echo "   1. Backup current dashboard:"
        echo "      cp ow-ai-dashboard/src/components/Dashboard.jsx ow-ai-dashboard/src/components/Dashboard.jsx.backup.$(date +%Y%m%d_%H%M%S)"
        echo ""
        echo "   2. Restore comprehensive dashboard:"
        echo "      cp $best_candidate ow-ai-dashboard/src/components/Dashboard.jsx"
        echo ""
        echo "   3. Apply Master Prompt compliance fixes:"
        echo "      sed -i 's/useTheme()/null/g' ow-ai-dashboard/src/components/Dashboard.jsx"
        echo "      sed -i '/import.*theme\\|import.*Theme/d' ow-ai-dashboard/src/components/Dashboard.jsx"
        echo ""
        echo "   4. Deploy with authentication preserved:"
        echo "      git add ow-ai-dashboard/src/components/Dashboard.jsx"
        echo "      git commit -m '🏢 RESTORE COMPREHENSIVE DASHBOARD: Original enterprise features + Master Prompt compliance'"
        echo "      git push origin main"
        echo ""
        echo "⏱️ EXPECTED RESULTS (4 minutes):"
        echo "   ✅ Your original comprehensive dashboard with all enterprise features"
        echo "   ✅ Sidebar navigation with multiple tabs"
        echo "   ✅ Smart Rule Route, AI Recommendations, A/B Testing, MCP, Agent oversight"
        echo "   ✅ Working authentication (preserved cookie-based login)"
        echo "   ✅ Master Prompt compliance (no theme errors)"
        
    else
        echo "❌ No highly recommended candidate found."
        echo "   Review the candidates above and choose the one that matches your memory"
        echo "   of the original comprehensive dashboard."
    fi
    
else
    echo "❌ No comprehensive dashboard candidates were saved."
    echo ""
    echo "🔍 MANUAL ANALYSIS REQUIRED:"
    echo "   Based on the search results, your best candidates are:"
    echo "   1. AgentAuthorizationDashboard.jsx (3,499 lines) - Highest probability"
    echo "   2. AIAlertManagementSystem.jsx (1,427 lines)"
    echo "   3. EnterpriseUserManagement.jsx (1,342 lines)"
    echo ""
    echo "   Review these files manually to identify your comprehensive dashboard"
    echo "   with sidebar navigation and 11+ tabs."
fi

echo ""
echo "✅ COMPREHENSIVE DASHBOARD ANALYSIS COMPLETE!"
echo "============================================"
