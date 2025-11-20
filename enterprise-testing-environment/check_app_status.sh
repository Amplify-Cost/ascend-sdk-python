#!/bin/bash

TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' -X POST -H 'Content-Type: application/json' -d '{"email":"admin@owkai.com","password":"admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "=== OW-KAI Application Status ==="
echo ""

echo "1. Pending Actions:"
curl -s "https://pilot.owkai.app/api/governance/pending-actions" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -20

echo ""
echo "2. Agent Activity Summary:"
curl -s "https://pilot.owkai.app/api/agent-activity?limit=100" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total Actions: {len(data)}')
statuses = {}
for a in data:
    status = a.get('status', 'unknown')
    statuses[status] = statuses.get(status, 0) + 1
print('Status Breakdown:')
for k, v in sorted(statuses.items()):
    print(f'  {k}: {v}')
"
