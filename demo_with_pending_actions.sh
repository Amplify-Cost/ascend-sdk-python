#!/bin/bash
###############################################################################
# ENTERPRISE DEMO - Actions that REQUIRE APPROVAL
#
# This creates actions that don't match auto-approval playbooks
# so they appear in the Authorization Center as PENDING
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

API_URL="${1:-https://pilot.owkai.app}"

echo -e "${MAGENTA}${BOLD}================================================================================"
echo -e "  🏢 OW-KAI AUTHORIZATION CENTER DEMO"
echo -e "  Creating Actions That REQUIRE Manual Approval"
echo -e "================================================================================${NC}"
echo ""

# Authenticate
echo -e "${CYAN}🔐 Authenticating...${NC}"
AUTH_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@owkai.com","password":"admin123"}')

TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [[ -z "$TOKEN" ]]; then
    echo -e "${RED}❌ Authentication failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Authenticated!${NC}"
echo ""

# Scenario 1: Medium-risk action (should NOT match any playbook)
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  📋 Creating MEDIUM-risk action (requires manual approval)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ACTION1=$(curl -s -X POST "${API_URL}/api/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "config-manager-agent",
        "action_type": "config_update",
        "description": "Updating production configuration settings for email notification service. Changes: SMTP server, port, and authentication credentials."
    }')

echo "$ACTION1" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'${GREEN}✅ Created Action #{data.get(\"id\")}${NC}')
    print(f'  Agent: {data.get(\"agent_id\")}')
    print(f'  Type: {data.get(\"action_type\")}')
    print(f'  Status: ${YELLOW}${BOLD}{data.get(\"status\", \"N/A\").upper()}${NC}')
    risk_score = data.get('risk_score', 0)
    risk_level = data.get('risk_level', 'UNKNOWN')
    print(f'  Risk: ${CYAN}{risk_level} (Score: {risk_score})${NC}')
    print(f'')
    if data.get('status') == 'pending':
        print(f'${GREEN}✓ Action is PENDING - will appear in Authorization Center!${NC}')
    elif data.get('status') == 'approved':
        print(f'${YELLOW}⚠ Action was AUTO-APPROVED by playbook (won\\'t appear in queue)${NC}')
except Exception as e:
    print(f'${RED}Error: {e}${NC}')
    print(sys.stdin.read())
"

echo ""
read -p "Press ENTER to continue..."

# Scenario 2: User permission change (should require approval)
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  👤 Creating USER PERMISSION change (requires manual approval)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ACTION2=$(curl -s -X POST "${API_URL}/api/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "iam-manager-agent",
        "action_type": "user_permission_change",
        "description": "Elevating user john.smith@company.com from VIEWER to ADMIN role. Requested by: sarah.jones@company.com. Reason: Temporary admin access for Q4 audit preparation."
    }')

echo "$ACTION2" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'${GREEN}✅ Created Action #{data.get(\"id\")}${NC}')
    print(f'  Agent: {data.get(\"agent_id\")}')
    print(f'  Type: {data.get(\"action_type\")}')
    print(f'  Status: ${YELLOW}${BOLD}{data.get(\"status\", \"N/A\").upper()}${NC}')
    risk_score = data.get('risk_score', 0)
    risk_level = data.get('risk_level', 'UNKNOWN')
    print(f'  Risk: ${YELLOW}{risk_level} (Score: {risk_score})${NC}')
    print(f'')
    if data.get('status') == 'pending':
        print(f'${GREEN}✓ Action is PENDING - will appear in Authorization Center!${NC}')
    elif data.get('status') == 'approved':
        print(f'${YELLOW}⚠ Action was AUTO-APPROVED by playbook (won\\'t appear in queue)${NC}')
except Exception as e:
    print(f'${RED}Error: {e}${NC}')
"

echo ""
read -p "Press ENTER to continue..."

# Scenario 3: API key generation (security-sensitive)
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  🔑 Creating API KEY generation (requires manual approval)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ACTION3=$(curl -s -X POST "${API_URL}/api/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "api-management-agent",
        "action_type": "api_key_generation",
        "description": "Generating new production API key for third-party integration with Salesforce CRM. Permissions: READ/WRITE access to customer data, contacts, and opportunities. Expiration: 90 days."
    }')

echo "$ACTION3" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'${GREEN}✅ Created Action #{data.get(\"id\")}${NC}')
    print(f'  Agent: {data.get(\"agent_id\")}')
    print(f'  Type: {data.get(\"action_type\")}')
    print(f'  Status: ${YELLOW}${BOLD}{data.get(\"status\", \"N/A\").upper()}${NC}')
    risk_score = data.get('risk_score', 0)
    risk_level = data.get('risk_level', 'UNKNOWN')
    print(f'  Risk: ${YELLOW}{risk_level} (Score: {risk_score})${NC}')
    print(f'')
    if data.get('status') == 'pending':
        print(f'${GREEN}✓ Action is PENDING - will appear in Authorization Center!${NC}')
    elif data.get('status') == 'approved':
        print(f'${YELLOW}⚠ Action was AUTO-APPROVED by playbook (won\\'t appear in queue)${NC}')
except Exception as e:
    print(f'${RED}Error: {e}${NC}')
"

echo ""

# Check Authorization Center
echo -e "${MAGENTA}${BOLD}================================================================================"
echo -e "  ✅ DEMO COMPLETE"
echo -e "================================================================================${NC}"
echo ""
echo -e "${BOLD}Checking Authorization Center queue...${NC}"
echo ""

PENDING=$(curl -s -X GET "${API_URL}/api/governance/pending-actions" \
    -H "Authorization: Bearer $TOKEN")

echo "$PENDING" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('total', 0)
print(f'${BOLD}Pending Actions in Queue: ${total}${NC}')
if total > 0:
    print(f'${GREEN}✓ Actions are now visible in Authorization Center!${NC}')
    print(f'')
    for action in data.get('actions', [])[:5]:
        print(f\"  • Action #{action.get('id')}: {action.get('action_type')} ({action.get('risk_level')})\")
else:
    print(f'${YELLOW}⚠ No pending actions found. They may have been auto-approved by playbooks.${NC}')
    print(f'${YELLOW}  Check the AI Alert Management tab to see approved actions.${NC}')
"

echo ""
echo -e "${CYAN}${BOLD}View in Authorization Center:${NC}"
echo -e "  ${API_URL}/authorization"
echo ""
echo -e "${CYAN}${BOLD}Note:${NC} If actions don't appear, it means playbooks auto-approved them."
echo -e "  Solution: Disable auto-approval playbooks or create actions with action_types"
echo -e "  that don't match existing playbook triggers."
echo ""
