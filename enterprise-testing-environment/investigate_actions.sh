#!/bin/bash
set -e

TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' -X POST -H 'Content-Type: application/json' -d '{"email":"admin@owkai.com","password":"admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "=== Investigating Available Actions in OW-KAI ==="
echo ""

echo "1. /api/governance/pending-actions:"
curl -s "https://pilot.owkai.app/api/governance/pending-actions" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -50

echo ""
echo "2. /api/agent-activity:"
curl -s "https://pilot.owkai.app/api/agent-activity?limit=10" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -50

echo ""
echo "3. /api/governance/unified-actions:"
curl -s "https://pilot.owkai.app/api/governance/unified-actions?limit=10" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -50
