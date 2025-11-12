#!/bin/bash
# Quick Start Demo - Complete Customer Onboarding & Testing
# This script demonstrates the full platform workflow end-to-end

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="https://pilot.owkai.app"
CUSTOMER_NAME="${1:-Acme Corporation}"
CUSTOMER_DOMAIN="${2:-acme-demo.com}"
ADMIN_EMAIL="ceo@${CUSTOMER_DOMAIN}"
REDACTED-CREDENTIAL="Demo2024!"

echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo -e "${CYAN}${BOLD}        OW-KAI PLATFORM - COMPLETE DEMO WORKFLOW${NC}"
echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo ""
echo -e "${BOLD}Customer:${NC} $CUSTOMER_NAME"
echo -e "${BOLD}Domain:${NC} $CUSTOMER_DOMAIN"
echo -e "${BOLD}Admin Email:${NC} $ADMIN_EMAIL"
echo ""

# Step 1: Create Organization
echo -e "${BLUE}${BOLD}[Step 1/6]${NC} Creating new organization..."
python3 customer_onboarding_simulation.py \
  --customer "$CUSTOMER_NAME" \
  --domain "$CUSTOMER_DOMAIN" || {
    echo -e "${RED}Failed to create organization${NC}"
    exit 1
}
echo -e "${GREEN}✅ Organization created successfully${NC}"
echo ""

# Step 2: Login and Get Token
echo -e "${BLUE}${BOLD}[Step 2/6]${NC} Authenticating as admin..."
TOKEN=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$REDACTED-CREDENTIAL\"
  }" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed - trying without /api prefix...${NC}"
    TOKEN=$(curl -s -X POST "${BASE_URL}/auth/login" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"$ADMIN_EMAIL\",
        \"password\": \"$REDACTED-CREDENTIAL\"
      }" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
fi

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ Authenticated successfully${NC}"
    echo -e "${CYAN}Token: ${TOKEN:0:30}...${NC}"
else
    echo -e "${YELLOW}⚠️  Could not get token via API${NC}"
    echo -e "${CYAN}ℹ️  Login manually at: ${BASE_URL}${NC}"
    echo -e "${CYAN}ℹ️  Email: $ADMIN_EMAIL${NC}"
    echo -e "${CYAN}ℹ️  Password: $REDACTED-CREDENTIAL${NC}"
fi
echo ""

# Step 3: Verify in Browser
echo -e "${BLUE}${BOLD}[Step 3/6]${NC} Opening platform in browser..."
echo -e "${CYAN}ℹ️  Login with these credentials:${NC}"
echo -e "   Email: ${GREEN}${ADMIN_EMAIL}${NC}"
echo -e "   Password: ${GREEN}${REDACTED-CREDENTIAL}${NC}"
echo ""

# Try to open browser (macOS)
if command -v open &> /dev/null; then
    open "${BASE_URL}"
    echo -e "${GREEN}✅ Browser opened${NC}"
else
    echo -e "${YELLOW}⚠️  Please open manually: ${BASE_URL}${NC}"
fi
echo ""

# Step 4: Show What to Test
echo -e "${BLUE}${BOLD}[Step 4/6]${NC} What to test in the platform..."
echo ""
echo -e "${CYAN}✅ Dashboard:${NC}"
echo "   - View analytics and metrics"
echo "   - Check pending actions counter"
echo ""
echo -e "${CYAN}✅ Authorization Center:${NC}"
echo "   - Review pending actions (should see 3 from simulation)"
echo "   - Try approving/rejecting an action"
echo "   - Test different approval levels"
echo ""
echo -e "${CYAN}✅ AI Alert Management:${NC}"
echo "   - View security alerts (should see 12 from simulation)"
echo "   - Click 'Generate AI Brief'"
echo "   - Verify real data (not hardcoded)"
echo "   - Acknowledge or escalate alerts"
echo ""
echo -e "${CYAN}✅ Smart Rules:${NC}"
echo "   - View existing rules"
echo "   - Check A/B tests tab"
echo ""
echo -e "${CYAN}✅ Activity Feed:${NC}"
echo "   - Review recent agent actions"
echo "   - Verify no 500 errors"
echo ""

# Step 5: Database Verification
echo -e "${BLUE}${BOLD}[Step 5/6]${NC} Verifying data in production database..."
export PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL'
PSQL="/opt/homebrew/opt/postgresql@14/bin/psql -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com -p 5432 -U owkai_admin -d owkai_pilot"

echo ""
echo -e "${CYAN}Users created:${NC}"
$PSQL -c "SELECT id, email, role, approval_level FROM users WHERE email LIKE '%${CUSTOMER_DOMAIN}' ORDER BY id;" -t

echo ""
echo -e "${CYAN}Resources summary:${NC}"
$PSQL -c "
SELECT 'Users' as type, COUNT(*) as count FROM users WHERE email LIKE '%${CUSTOMER_DOMAIN}'
UNION ALL
SELECT 'Agent Actions', COUNT(*) FROM agent_actions WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE '%${CUSTOMER_DOMAIN}'
)
UNION ALL
SELECT 'Pending Actions', COUNT(*) FROM agent_actions WHERE status = 'pending_approval' AND user_id IN (
  SELECT id FROM users WHERE email LIKE '%${CUSTOMER_DOMAIN}'
);
" -t

echo ""
echo -e "${GREEN}✅ Database verification complete${NC}"
echo ""

# Step 6: Summary
echo -e "${BLUE}${BOLD}[Step 6/6]${NC} Testing Summary"
echo ""
echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo -e "${CYAN}${BOLD}                         WHAT WAS CREATED${NC}"
echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo ""
echo -e "${GREEN}✅ Organization:${NC} $CUSTOMER_NAME"
echo -e "${GREEN}✅ Users:${NC} 4 (CEO, Manager, 2 Engineers)"
echo -e "${GREEN}✅ Agent Actions:${NC} 15 (varied statuses)"
echo -e "${GREEN}✅ Security Alerts:${NC} 12 (critical, high, medium)"
echo -e "${GREEN}✅ Pending Actions:${NC} 3 (ready for approval testing)"
echo ""
echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo -e "${CYAN}${BOLD}                         NEXT STEPS${NC}"
echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo ""
echo -e "${YELLOW}1.${NC} Login to: ${CYAN}${BASE_URL}${NC}"
echo -e "   Email: ${GREEN}${ADMIN_EMAIL}${NC}"
echo -e "   Password: ${GREEN}${REDACTED-CREDENTIAL}${NC}"
echo ""
echo -e "${YELLOW}2.${NC} Navigate through each module:"
echo "   - Dashboard"
echo "   - Authorization Center"
echo "   - AI Alert Management"
echo "   - Smart Rules"
echo "   - Activity Feed"
echo ""
echo -e "${YELLOW}3.${NC} Test workflows:"
echo "   - Approve/reject pending actions"
echo "   - Acknowledge/escalate alerts"
echo "   - Generate AI insights"
echo ""
echo -e "${YELLOW}4.${NC} Verify zero errors:"
echo "   - Open browser DevTools → Console"
echo "   - Should see: ${GREEN}✅ Data loaded${NC}, ${GREEN}✅ API response${NC}"
echo "   - Should NOT see: ${RED}❌ 500 errors${NC}, ${RED}❌ Failed to load${NC}"
echo ""
echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo -e "${GREEN}${BOLD}🎉 DEMO SETUP COMPLETE!${NC}"
echo -e "${CYAN}${BOLD}=====================================================================${NC}"
echo ""
echo -e "${CYAN}Documentation:${NC}"
echo "  - Full Guide: COMPLETE_CUSTOMER_ONBOARDING_WORKFLOW.md"
echo "  - Quick Test: CUSTOMER_ONBOARDING_TEST_GUIDE.md"
echo ""
echo -e "${CYAN}To create another organization:${NC}"
echo "  ./quick_start_demo.sh \"Your Company\" \"yourcompany-demo.com\""
echo ""
