#!/bin/bash
###############################################################################
# ENTERPRISE MCP/AGENT ACTION DEMO - SIMPLIFIED VERSION
# Run this to see the system perform in real-time
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
echo -e "  🏢 OW-KAI ENTERPRISE MCP/AGENT ACTION LIVE DEMO"
echo -e "================================================================================${NC}"
echo ""
echo -e "${BOLD}Environment:${NC} $API_URL"
echo ""

# Step 1: Authenticate
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  🔐 STEP 1: Authentication${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

AUTH_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@owkai.com","password":"admin123"}')

TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [[ -z "$TOKEN" ]]; then
    echo -e "${RED}❌ Authentication failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Authenticated successfully!${NC}"
echo -e "Token: ${TOKEN:0:30}..."
echo ""
echo "Press ENTER to continue..."
read -r

# Scenario 1: Low-Risk
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  📊 SCENARIO 1: Low-Risk Database Read${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Creating agent action: Database read for analytics..."
echo -e "${YELLOW}Expected Outcome: MEDIUM risk, auto-approved${NC}"
echo ""

ACTION1=$(curl -s -X POST "${API_URL}/api/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "analytics-dashboard-agent-001",
        "action_type": "database_read",
        "description": "Querying customer analytics view for monthly revenue dashboard. Read-only operation on analytics.customer_summary table."
    }')

echo "$ACTION1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'${GREEN}✅ Action Created! ID: {data.get(\"id\")}${NC}')
print(f'')
print(f'${BOLD}Action Details:${NC}')
print(f'  Agent: {data.get(\"agent_id\")}')
print(f'  Type: {data.get(\"action_type\")}')
print(f'  Status: {data.get(\"status\")}')
risk_score = data.get('risk_score', 0)
risk_level = data.get('risk_level', 'UNKNOWN')
if risk_level == 'CRITICAL':
    print(f'  Risk: ${RED}${BOLD}⚠️  {risk_level} (Score: {risk_score})${NC}')
elif risk_level == 'HIGH':
    print(f'  Risk: ${YELLOW}${BOLD}⚡ {risk_level} (Score: {risk_score})${NC}')
elif risk_level == 'MEDIUM':
    print(f'  Risk: ${CYAN}${BOLD}◉ {risk_level} (Score: {risk_score})${NC}')
else:
    print(f'  Risk: ${GREEN}${BOLD}✓ {risk_level} (Score: {risk_score})${NC}')
"

echo ""
echo "Press ENTER to continue..."
read -r

# Scenario 2: High-Risk HIPAA
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  🏥 SCENARIO 2: High-Risk Patient Data (HIPAA)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Creating agent action: Access patient medical records..."
echo -e "${YELLOW}Expected Outcome: HIGH risk, requires approval${NC}"
echo -e "${YELLOW}Compliance: HIPAA audit trail${NC}"
echo ""

ACTION2=$(curl -s -X POST "${API_URL}/api/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "ehr-integration-agent-002",
        "action_type": "patient_data_access",
        "description": "Accessing patient medical records (Patient ID: PT-2024-889456). Full medical history requested for emergency care consultation by Dr. Sarah Johnson at Memorial Hospital ER."
    }')

echo "$ACTION2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'${GREEN}✅ Action Created! ID: {data.get(\"id\")}${NC}')
print(f'')
print(f'${BOLD}Action Details:${NC}')
print(f'  Agent: {data.get(\"agent_id\")}')
print(f'  Type: {data.get(\"action_type\")}')
print(f'  Status: {data.get(\"status\")}')
risk_score = data.get('risk_score', 0)
risk_level = data.get('risk_level', 'UNKNOWN')
if risk_level == 'CRITICAL':
    print(f'  Risk: ${RED}${BOLD}⚠️  {risk_level} (Score: {risk_score})${NC}')
elif risk_level == 'HIGH':
    print(f'  Risk: ${YELLOW}${BOLD}⚡ {risk_level} (Score: {risk_score})${NC}')
else:
    print(f'  Risk: {risk_level} (Score: {risk_score})')
"

echo ""
echo -e "${YELLOW}🔒 HIPAA compliance: Action requires audit trail and approval${NC}"
echo ""
echo "Press ENTER to continue..."
read -r

# Scenario 3: Critical Financial
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  💰 SCENARIO 3: Critical Financial Transaction${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Creating agent action: Process $125,000 wire transfer..."
echo -e "${RED}Expected Outcome: CRITICAL risk, executive approval required${NC}"
echo -e "${RED}Compliance: PCI-DSS + SOX${NC}"
echo ""

ACTION3=$(curl -s -X POST "${API_URL}/api/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "payment-processor-agent-003",
        "action_type": "financial_transaction",
        "description": "Processing wire transfer of $125,000.00 USD to Acme Corp for Q4 Enterprise Software License payment. Dual authorization required for high-value transaction."
    }')

echo "$ACTION3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'${GREEN}✅ Action Created! ID: {data.get(\"id\")}${NC}')
print(f'')
print(f'${RED}${BOLD}⚠️  CRITICAL FINANCIAL TRANSACTION${NC}')
print(f'${BOLD}Action Details:${NC}')
print(f'  Agent: {data.get(\"agent_id\")}')
print(f'  Type: {data.get(\"action_type\")}')
print(f'  Amount: ${BOLD}\$125,000.00 USD${NC}')
print(f'  Status: ${YELLOW}${BOLD}{data.get(\"status\", \"N/A\").upper()}${NC}')
risk_score = data.get('risk_score', 0)
risk_level = data.get('risk_level', 'UNKNOWN')
print(f'  Risk: ${RED}${BOLD}⚠️  {risk_level} (Score: {risk_score})${NC}')
print(f'  Compliance: ${BOLD}PCI-DSS, SOX${NC}')
"

echo ""
echo -e "${RED}💳 PCI-DSS: Payment data handling requires secure audit trail${NC}"
echo -e "${RED}📊 SOX: Financial transaction requires dual authorization${NC}"
echo ""
echo "Press ENTER to continue..."
read -r

# Scenario 4: Infrastructure
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  ☁️  SCENARIO 4: Critical Infrastructure Change${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Creating agent action: Terminate AWS EC2 instances..."
echo -e "${RED}Expected Outcome: CRITICAL risk, infrastructure approval${NC}"
echo ""

ACTION4=$(curl -s -X POST "${API_URL}/api/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "infrastructure-mgmt-agent-005",
        "action_type": "aws_ec2_terminate",
        "description": "Terminating AWS EC2 instances i-0123456789abcdef0 and i-0fedcba9876543210 in staging environment. Reason: Cost optimization for unused staging instances. Backup verified and data retention confirmed."
    }')

echo "$ACTION4" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'${GREEN}✅ Action Created! ID: {data.get(\"id\")}${NC}')
print(f'')
print(f'${RED}${BOLD}⚠️  CRITICAL INFRASTRUCTURE ACTION${NC}')
print(f'${BOLD}Action Details:${NC}')
print(f'  Agent: {data.get(\"agent_id\")}')
print(f'  Type: {data.get(\"action_type\")}')
print(f'  Status: ${YELLOW}${BOLD}{data.get(\"status\", \"N/A\").upper()}${NC}')
risk_score = data.get('risk_score', 0)
risk_level = data.get('risk_level', 'UNKNOWN')
print(f'  Risk: ${RED}${BOLD}⚠️  {risk_level} (Score: {risk_score})${NC}')
"

echo ""
echo -e "${YELLOW}☁️  Infrastructure changes require senior approval${NC}"
echo ""

# Summary
echo -e "${MAGENTA}${BOLD}================================================================================"
echo -e "  ✅ DEMO COMPLETE"
echo -e "================================================================================${NC}"
echo ""
echo -e "${BOLD}What You Just Saw:${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} ${BOLD}4 different risk scenarios${NC} (MEDIUM → CRITICAL)"
echo -e "  ${GREEN}✓${NC} ${BOLD}Real-time risk assessment${NC} using CVSS v2.0"
echo -e "  ${GREEN}✓${NC} ${BOLD}Compliance automation${NC} (HIPAA, PCI-DSS, SOX)"
echo -e "  ${GREEN}✓${NC} ${BOLD}Immutable audit trails${NC} with hash-chaining"
echo ""
echo -e "${CYAN}${BOLD}All actions are now visible in the Authorization Center UI!${NC}"
echo -e "Visit: ${API_URL}/authorization"
echo ""
