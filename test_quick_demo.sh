#!/bin/bash
###############################################################################
# Quick Demo Test - No user input required
###############################################################################

set -e

API_URL="${1:-https://pilot.owkai.app}"

echo "🔐 Authenticating..."
AUTH_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@owkai.com","password":"admin123"}')

TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [[ -z "$TOKEN" ]]; then
    echo "❌ Authentication failed!"
    echo "$AUTH_RESPONSE" | python3 -m json.tool
    exit 1
fi

echo "✅ Authenticated! Token: ${TOKEN:0:30}..."
echo ""

echo "📊 Creating LOW-RISK action (database_read)..."
ACTION1=$(curl -s -X POST "${API_URL}/api/agent/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_name": "analytics-agent",
        "action_type": "database_read",
        "resource": "customer_analytics",
        "details": {"query": "SELECT * FROM analytics"}
    }')

echo "$ACTION1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Created Action #{data.get(\"id\")}: {data.get(\"action_type\")}')
print(f'   Risk: {data.get(\"risk_level\")} (Score: {data.get(\"risk_score\")})')
print(f'   Status: {data.get(\"status\")}')
"

echo ""
echo "🏥 Creating HIGH-RISK action (patient_data_access)..."
ACTION2=$(curl -s -X POST "${API_URL}/api/agent/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_name": "ehr-agent",
        "action_type": "patient_data_access",
        "resource": "patient_medical_records",
        "details": {"patient_id": "PT-2024-12345"}
    }')

echo "$ACTION2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Created Action #{data.get(\"id\")}: {data.get(\"action_type\")}')
print(f'   Risk: {data.get(\"risk_level\")} (Score: {data.get(\"risk_score\")})')
print(f'   Status: {data.get(\"status\")}')
"

echo ""
echo "💰 Creating CRITICAL-RISK action (financial_transaction)..."
ACTION3=$(curl -s -X POST "${API_URL}/api/agent/agent-action" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "agent_name": "payment-agent",
        "action_type": "financial_transaction",
        "resource": "payment_gateway",
        "details": {"amount": 125000, "currency": "USD"}
    }')

echo "$ACTION3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Created Action #{data.get(\"id\")}: {data.get(\"action_type\")}')
print(f'   Risk: {data.get(\"risk_level\")} (Score: {data.get(\"risk_score\")}')
print(f'   Status: {data.get(\"status\")}')
"

echo ""
echo "✅ Demo complete! All actions created successfully."
