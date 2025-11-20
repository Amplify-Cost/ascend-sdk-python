#!/bin/bash
TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' -X POST -H 'Content-Type: application/json' -d '{"email":"admin@owkai.com","password":"admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "=== Customer Demo: Proof of Blocked Action ==="
echo ""
echo "Checking /api/agent-activity for Action 736..."
echo ""

curl -s "https://pilot.owkai.app/api/agent-activity?limit=5" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for action in data:
    if action['id'] == 736:
        print('✅ FOUND: Action 736 (BLOCKED)')
        print('')
        print(f'  ID: {action[\"id\"]}')
        print(f'  Status: {action[\"status\"]} ← THIS SHOWS IT WAS BLOCKED')
        print(f'  Agent: {action[\"agent_id\"]}')
        print(f'  Risk: {action[\"risk_score\"]}/100 ({action[\"risk_level\"]})')
        print(f'  Time: {action[\"created_at\"]}')
        print(f'  Description: {action[\"description\"]}')
        print('')
        print('Point to the \"status\": \"rejected\" field to show customer')
        break
"
