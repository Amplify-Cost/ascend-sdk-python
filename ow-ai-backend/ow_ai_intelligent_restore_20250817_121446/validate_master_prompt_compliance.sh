#!/bin/bash

echo "📋 MASTER PROMPT COMPLIANCE VALIDATOR"
echo "===================================="
echo "🎯 Validating alignment with Master Prompt rules"

validate_rule_2_cookie_auth() {
    echo ""
    echo "🍪 RULE 2: Cookie-Only Authentication"
    echo "===================================="
    
    # Check backend
    echo "📊 Backend Analysis:"
    if [ -f "../main.py" ]; then
        localStorage_backend=$(grep -c "localStorage" "../main.py" 2>/dev/null || echo "0")
        if [ $localStorage_backend -eq 0 ]; then
            echo "   ✅ No localStorage in backend"
        else
            echo "   ❌ localStorage found in backend: $localStorage_backend instances"
        fi
        
        if grep -q "credentials.*include\|cookie.*auth\|HttpOnly" "../main.py" 2>/dev/null; then
            echo "   ✅ Cookie authentication patterns found"
        else
            echo "   ⚠️ Cookie authentication needs implementation"
        fi
    fi
    
    # Check frontend
    echo "📊 Frontend Analysis:"
    for frontend_dir in "../ow-ai-dashboard" "../frontend" "../src"; do
        if [ -d "$frontend_dir" ]; then
            localStorage_frontend=$(find "$frontend_dir" -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | xargs grep -c "localStorage" 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
            if [ $localStorage_frontend -eq 0 ]; then
                echo "   ✅ No localStorage in frontend"
            else
                echo "   ❌ localStorage found in frontend: $localStorage_frontend instances"
            fi
            break
        fi
    done
}

validate_rule_4_enterprise_features() {
    echo ""
    echo "🏢 RULE 4: Enterprise-Level Fixes Only"
    echo "====================================="
    
    if [ -f "../main.py" ]; then
        endpoints=$(grep -c "@app\." "../main.py" 2>/dev/null || echo "0")
        echo "📊 Total endpoints: $endpoints"
        
        # Check specific enterprise features
        echo "🔍 Enterprise features:"
        
        features=("smart.*rules:Smart Rules" "analytics:Analytics" "governance:Governance" "alert:Alerts" "user.*management:User Management")
        
        present_count=0
        for feature_pattern in "${features[@]}"; do
            pattern="${feature_pattern%%:*}"
            name="${feature_pattern##*:}"
            
            if grep -q "$pattern" "../main.py" 2>/dev/null; then
                echo "   ✅ $name"
                ((present_count++))
            else
                echo "   ❌ $name"
            fi
        done
        
        echo ""
        echo "📊 Enterprise Feature Score: $present_count/5"
        
        if [ $present_count -ge 4 ]; then
            echo "   ✅ Comprehensive enterprise features"
        else
            echo "   ⚠️ Enterprise features incomplete"
        fi
        
        if [ $endpoints -gt 20 ]; then
            echo "   ✅ Rich API endpoint coverage"
        else
            echo "   ⚠️ Limited API endpoints"
        fi
    fi
}

calculate_pilot_readiness() {
    echo ""
    echo "🎯 PILOT READINESS ASSESSMENT"
    echo "============================"
    
    score=0
    max_score=100
    
    # Rule 2 compliance (30 points)
    localStorage_total=0
    if [ -f "../main.py" ]; then
        localStorage_total=$((localStorage_total + $(grep -c "localStorage" "../main.py" 2>/dev/null || echo "0")))
    fi
    
    for frontend_dir in "../ow-ai-dashboard" "../frontend" "../src"; do
        if [ -d "$frontend_dir" ]; then
            localStorage_total=$((localStorage_total + $(find "$frontend_dir" -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | xargs grep -c "localStorage" 2>/dev/null | awk '{sum+=$1} END {print sum+0}')))
            break
        fi
    done
    
    if [ $localStorage_total -eq 0 ]; then
        score=$((score + 30))
        echo "📊 Cookie-only auth: ✅ 30/30 points"
    else
        echo "📊 Cookie-only auth: ❌ 0/30 points ($localStorage_total localStorage instances)"
    fi
    
    # Enterprise features (40 points)
    if [ -f "../main.py" ]; then
        enterprise_features=0
        for pattern in "smart.*rules" "analytics" "governance" "alert" "user.*management"; do
            if grep -q "$pattern" "../main.py" 2>/dev/null; then
                ((enterprise_features++))
            fi
        done
        
        enterprise_score=$((enterprise_features * 8))
        score=$((score + enterprise_score))
        echo "📊 Enterprise features: $([ $enterprise_features -ge 4 ] && echo "✅" || echo "⚠️") $enterprise_score/40 points ($enterprise_features/5 features)"
    fi
    
    # API coverage (20 points)
    if [ -f "../main.py" ]; then
        endpoints=$(grep -c "@app\." "../main.py" 2>/dev/null || echo "0")
        if [ $endpoints -gt 20 ]; then
            score=$((score + 20))
            echo "📊 API coverage: ✅ 20/20 points ($endpoints endpoints)"
        elif [ $endpoints -gt 10 ]; then
            score=$((score + 10))
            echo "📊 API coverage: ⚠️ 10/20 points ($endpoints endpoints)"
        else
            echo "📊 API coverage: ❌ 0/20 points ($endpoints endpoints)"
        fi
    fi
    
    # Security & compliance (10 points)
    if [ -f "../main.py" ] && grep -q "cookie.*auth\|HttpOnly\|secure" "../main.py" 2>/dev/null; then
        score=$((score + 10))
        echo "📊 Security: ✅ 10/10 points"
    else
        echo "📊 Security: ❌ 0/10 points"
    fi
    
    echo ""
    echo "🎯 OVERALL PILOT READINESS: $score% ($score/$max_score points)"
    
    if [ $score -ge 85 ]; then
        echo "✅ PILOT READY! Exceeds 85% threshold"
    elif [ $score -ge 75 ]; then
        echo "⚠️ NEARLY READY! Close to 85% threshold"
    else
        echo "❌ NOT READY! Needs more work to reach 85%"
    fi
}

# Main validation
main() {
    validate_rule_2_cookie_auth
    validate_rule_4_enterprise_features
    calculate_pilot_readiness
    
    echo ""
    echo "📋 COMPLIANCE SUMMARY"
    echo "===================="
    echo "Use this report to identify remaining issues before Railway deployment"
}

main "$@"
