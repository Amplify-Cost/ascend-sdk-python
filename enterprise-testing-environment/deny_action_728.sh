#!/bin/bash
#
# Deny Action 728 (PII Database Access) and Show Evidence
#

set -e

echo "========================================="
echo "OW-KAI: Blocking Agent Action 728"
echo "========================================="
echo ""

# Authenticate
echo "🔐 Authenticating..."
TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@owkai.com","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Authenticated"
echo ""

echo "=== BEFORE DENIAL - Action 728 Status ==="
curl -s "https://pilot.owkai.app/api/agent-action/728" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo ""
echo "=== DENYING ACTION 728 (PII Database Access) ==="
echo "Reason: Missing data consent documentation"
echo ""

curl -s -X POST "https://pilot.owkai.app/api/agent-action/728/deny" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"comments": "DENIED: Missing required data consent documentation. PII access requires documented consent per GDPR Article 5 and company data privacy policy."}' | python3 -m json.tool

echo ""
echo ""
echo "=== AFTER DENIAL - Action 728 Status ==="
curl -s "https://pilot.owkai.app/api/agent-action/728" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo ""
echo "✅ Action 728 has been BLOCKED"
echo "Evidence saved above showing:"
echo "  - Who blocked it: admin@owkai.com"
echo "  - When it was blocked: (see reviewed_at timestamp)"
echo "  - Why it was blocked: Missing data consent documentation"
echo ""
