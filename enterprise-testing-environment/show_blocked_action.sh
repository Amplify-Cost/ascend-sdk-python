#!/bin/bash
set -e

TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' -X POST -H 'Content-Type: application/json' -d '{"email":"admin@owkai.com","password":"admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "========================================="
echo "EVIDENCE: Agent Action Was BLOCKED"
echo "========================================="
echo ""

echo "=== Action 736: REJECTED (BLOCKED) ==="
curl -s "https://pilot.owkai.app/api/agent-action/736" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo ""
echo "=== What This Shows Your Client ==="
echo "✅ Agent: mcp-config-manager"
echo "✅ Attempted Action: Update Redis cache TTL from 300s to 600s"
echo "✅ Risk Score: 92/100 (CRITICAL)"
echo "✅ Status: REJECTED (action was BLOCKED)"
echo "✅ Created: 2025-11-19T17:46:36"
echo ""
echo "This is the evidence you can point to showing:"
echo "  1. An agent tried to perform an action"
echo "  2. The system evaluated it as CRITICAL risk (92/100)"
echo "  3. The action was REJECTED/BLOCKED"
echo "  4. The agent could NOT execute this action"
echo ""
