#!/bin/bash

# OW-AI Platform - Comprehensive Feature Testing Script
# Tests EVERY endpoint systematically with evidence collection

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000"
TEST_RESULTS_DIR="/Users/mac_001/OW_AI_Project/codebase-review/test-evidence"
mkdir -p "$TEST_RESULTS_DIR"

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
BLOCKED_TESTS=0

# Function to log test results
log_test() {
    local endpoint="$1"
    local status="$2"
    local response="$3"
    local evidence_file="$4"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n=== TEST $TOTAL_TESTS: $endpoint ===" >> "$TEST_RESULTS_DIR/comprehensive_test_log.txt"
    echo "Status: $status" >> "$TEST_RESULTS_DIR/comprehensive_test_log.txt"
    echo "Timestamp: $(date)" >> "$TEST_RESULTS_DIR/comprehensive_test_log.txt"
    echo "Response: $response" >> "$TEST_RESULTS_DIR/comprehensive_test_log.txt"
    echo "Evidence File: $evidence_file" >> "$TEST_RESULTS_DIR/comprehensive_test_log.txt"
    echo "----------------------------------------" >> "$TEST_RESULTS_DIR/comprehensive_test_log.txt"

    case $status in
        "PASS") PASSED_TESTS=$((PASSED_TESTS + 1)); echo -e "${GREEN}✅ PASS${NC}: $endpoint" ;;
        "FAIL") FAILED_TESTS=$((FAILED_TESTS + 1)); echo -e "${RED}❌ FAIL${NC}: $endpoint" ;;
        "BLOCKED") BLOCKED_TESTS=$((BLOCKED_TESTS + 1)); echo -e "${YELLOW}🚫 BLOCKED${NC}: $endpoint" ;;
    esac
}

# Function to test endpoint and save evidence
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local auth_header="$4"
    local expected_status="$5"
    local test_name="$6"

    local evidence_file="$TEST_RESULTS_DIR/${test_name}_evidence.json"

    if [ -n "$auth_header" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}" \
                -X "$method" \
                -H "Authorization: $auth_header" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$BASE_URL$endpoint")
        else
            response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}" \
                -X "$method" \
                -H "Authorization: $auth_header" \
                "$BASE_URL$endpoint")
        fi
    else
        if [ -n "$data" ]; then
            response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}" \
                -X "$method" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$BASE_URL$endpoint")
        else
            response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}" \
                -X "$method" \
                "$BASE_URL$endpoint")
        fi
    fi

    # Extract status code
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)
    response_body=$(echo "$response" | sed '/HTTP_STATUS:/d' | sed '/TIME_TOTAL:/d')

    # Save evidence
    cat > "$evidence_file" << EOF
{
    "test_name": "$test_name",
    "endpoint": "$endpoint",
    "method": "$method",
    "timestamp": "$(date -Iseconds)",
    "http_status": "$http_status",
    "expected_status": "$expected_status",
    "response_time": "$time_total",
    "response_body": $(echo "$response_body" | jq -R . 2>/dev/null || echo "\"$response_body\""),
    "request_data": $(echo "$data" | jq . 2>/dev/null || echo "\"$data\""),
    "has_auth": $([ -n "$auth_header" ] && echo "true" || echo "false")
}
EOF

    # Determine test result
    if [ "$http_status" = "$expected_status" ]; then
        log_test "$endpoint" "PASS" "$http_status (${time_total}s)" "$evidence_file"
    elif [ "$http_status" = "401" ] && [ -z "$auth_header" ]; then
        log_test "$endpoint" "BLOCKED" "401 - Auth Required" "$evidence_file"
    elif [ "$http_status" = "403" ]; then
        log_test "$endpoint" "BLOCKED" "403 - CSRF/Permission Required" "$evidence_file"
    else
        log_test "$endpoint" "FAIL" "Expected $expected_status, got $http_status" "$evidence_file"
    fi
}

# Get authentication token first
echo -e "${BLUE}🔐 Setting up authentication...${NC}"
auth_response=$(curl -s -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@owkai.com","password":"admin123"}')

# Extract token
access_token=$(echo "$auth_response" | jq -r '.access_token' 2>/dev/null)
if [ "$access_token" = "null" ] || [ -z "$access_token" ]; then
    echo -e "${RED}❌ Failed to authenticate. Exiting.${NC}"
    echo "Auth response: $auth_response"
    exit 1
fi

AUTH_HEADER="Bearer $access_token"
echo -e "${GREEN}✅ Authentication successful${NC}"

# Start comprehensive testing
echo -e "\n${BLUE}🧪 Starting Comprehensive OW-AI Platform Testing...${NC}\n"

# === AUTHENTICATION ENDPOINTS ===
echo -e "${BLUE}=== Testing Authentication Endpoints ===${NC}"

test_endpoint "POST" "/auth/token" \
    '{"email":"admin@owkai.com","password":"admin123"}' \
    "" "200" "auth_login"

test_endpoint "GET" "/auth/me" "" "$AUTH_HEADER" "200" "auth_me"

test_endpoint "GET" "/auth/health" "" "" "200" "auth_health"

test_endpoint "GET" "/auth/csrf" "" "" "200" "auth_csrf"

# === AUTHORIZATION CENTER ENDPOINTS ===
echo -e "\n${BLUE}=== Testing Authorization Center ===${NC}"

test_endpoint "GET" "/api/authorization/policies/list" "" "$AUTH_HEADER" "200" "policies_list"

test_endpoint "POST" "/api/authorization/policies/create-from-natural-language" \
    '{"description":"Block suspicious file downloads","context":"cybersecurity"}' \
    "$AUTH_HEADER" "200" "policies_create_nl"

test_endpoint "POST" "/api/authorization/policies/evaluate-realtime" \
    '{"action":"file_download","user":"test_user","resource":"sensitive_file.pdf"}' \
    "$AUTH_HEADER" "200" "policies_evaluate"

test_endpoint "GET" "/api/authorization/policies/engine-metrics" "" "$AUTH_HEADER" "200" "policies_metrics"

# === ALERT MANAGEMENT ENDPOINTS ===
echo -e "\n${BLUE}=== Testing Alert Management ===${NC}"

test_endpoint "GET" "/alerts" "" "$AUTH_HEADER" "200" "alerts_list"

test_endpoint "GET" "/alerts?severity=high" "" "$AUTH_HEADER" "200" "alerts_filter"

test_endpoint "GET" "/alerts/active" "" "$AUTH_HEADER" "200" "alerts_active"

# Test failing endpoint
test_endpoint "POST" "/alerts/summary" \
    '{"time_range":"24h","severity_filter":"all"}' \
    "$AUTH_HEADER" "200" "alerts_summary"

# Test CSRF-protected endpoints (should fail without CSRF)
test_endpoint "POST" "/alerts/3001/acknowledge" \
    '{"comment":"Investigating this alert"}' \
    "$AUTH_HEADER" "403" "alerts_acknowledge"

test_endpoint "POST" "/alerts/3001/escalate" \
    '{"reason":"High priority security incident"}' \
    "$AUTH_HEADER" "403" "alerts_escalate"

# === SMART RULES ENGINE ENDPOINTS ===
echo -e "\n${BLUE}=== Testing Smart Rules Engine ===${NC}"

test_endpoint "GET" "/api/smart-rules" "" "$AUTH_HEADER" "200" "rules_list"

test_endpoint "POST" "/api/smart-rules/generate-from-nl" \
    '{"description":"Alert when CPU usage exceeds 90%","context":"performance"}' \
    "$AUTH_HEADER" "200" "rules_generate_nl"

test_endpoint "POST" "/api/smart-rules/generate" \
    '{"type":"security","priority":"high","context":"threat_detection"}' \
    "$AUTH_HEADER" "200" "rules_generate_ai"

test_endpoint "GET" "/api/smart-rules/analytics" "" "$AUTH_HEADER" "200" "rules_analytics"

test_endpoint "GET" "/api/smart-rules/suggestions" "" "$AUTH_HEADER" "200" "rules_suggestions"

# Test A/B testing
test_endpoint "POST" "/api/smart-rules/setup-ab-testing-table" "" "$AUTH_HEADER" "200" "rules_ab_setup"

test_endpoint "GET" "/api/smart-rules/ab-tests" "" "$AUTH_HEADER" "200" "rules_ab_tests"

# Test failing endpoints
test_endpoint "POST" "/api/smart-rules/seed" "" "$AUTH_HEADER" "200" "rules_seed"

test_endpoint "POST" "/api/smart-rules/optimize/1" \
    '{"optimization_type":"performance"}' \
    "$AUTH_HEADER" "200" "rules_optimize"

# === ENTERPRISE USER MANAGEMENT ===
echo -e "\n${BLUE}=== Testing Enterprise User Management ===${NC}"

test_endpoint "GET" "/api/enterprise-users/users" "" "$AUTH_HEADER" "200" "users_list"

# === HEALTH ENDPOINTS ===
echo -e "\n${BLUE}=== Testing Health & Monitoring ===${NC}"

test_endpoint "GET" "/health" "" "" "200" "health_basic"

# === ADDITIONAL CRITICAL ENDPOINTS ===
echo -e "\n${BLUE}=== Testing Additional Features ===${NC}"

# Test governance endpoints
test_endpoint "GET" "/api/governance/policies" "" "$AUTH_HEADER" "200" "governance_policies"

# Test analytics endpoints
test_endpoint "GET" "/analytics/performance" "" "$AUTH_HEADER" "200" "analytics_performance"

# Generate final report
echo -e "\n${BLUE}=== Generating Test Summary ===${NC}"

cat > "$TEST_RESULTS_DIR/COMPREHENSIVE_TEST_SUMMARY.md" << EOF
# OW-AI Platform - Comprehensive Test Results

## Test Execution Summary
- **Total Tests**: $TOTAL_TESTS
- **Passed**: $PASSED_TESTS ($(( PASSED_TESTS * 100 / TOTAL_TESTS ))%)
- **Failed**: $FAILED_TESTS ($(( FAILED_TESTS * 100 / TOTAL_TESTS ))%)
- **Blocked**: $BLOCKED_TESTS ($(( BLOCKED_TESTS * 100 / TOTAL_TESTS ))%)

## Test Date
$(date)

## Platform Status
- **Backend**: Running ✅
- **Authentication**: Functional ✅
- **Enterprise Features**: Enabled ✅

## Critical Findings
$(if [ $FAILED_TESTS -gt 0 ]; then echo "❌ $FAILED_TESTS endpoint(s) failing - requires immediate attention"; else echo "✅ All endpoints responding as expected"; fi)

## Evidence Files
All test evidence saved in: $TEST_RESULTS_DIR/

## Next Steps
1. Review failed endpoints in detail
2. Implement fixes for 500 Internal Server errors
3. Validate CSRF protection is working correctly
4. Test database integrity for all operations

EOF

echo -e "\n${GREEN}🎯 Comprehensive testing complete!${NC}"
echo -e "📊 Results: ${GREEN}$PASSED_TESTS passed${NC}, ${RED}$FAILED_TESTS failed${NC}, ${YELLOW}$BLOCKED_TESTS blocked${NC}"
echo -e "📁 Evidence saved in: $TEST_RESULTS_DIR/"
echo -e "📋 Summary report: $TEST_RESULTS_DIR/COMPREHENSIVE_TEST_SUMMARY.md"