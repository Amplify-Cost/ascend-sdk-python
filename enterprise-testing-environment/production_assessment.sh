#!/bin/bash
#
# Production Environment Assessment
# Tests actual production behavior and data
#

set -e

echo "=============================================="
echo "PRODUCTION ENVIRONMENT ASSESSMENT"
echo "Target: https://pilot.owkai.app"
echo "=============================================="
echo ""

# Authenticate
echo "🔐 Authenticating to production..."
TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@owkai.com","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Authenticated to production"
echo ""

echo "================================================"
echo "PART 1: Current Production Endpoint Testing"
echo "================================================"
echo ""

echo "1. Testing GET /api/agent-action/736 (individual action):"
RESPONSE_736=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "https://pilot.owkai.app/api/agent-action/736" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE_736"
echo ""

echo "2. Testing GET /api/agent-activity (all actions):"
curl -s "https://pilot.owkai.app/api/agent-activity?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total actions: {len(data)}')
if len(data) > 0:
    print(f'First action: ID={data[0][\"id\"]}, status={data[0][\"status\"]}, reviewed_by={data[0].get(\"reviewed_by\", \"NULL\")}')
    print(f'Has extra_data: {\"extra_data\" in data[0]}')
    if 'extra_data' in data[0] and data[0]['extra_data']:
        print(f'Extra data keys: {list(data[0][\"extra_data\"].keys())}')
"
echo ""

echo "3. Testing GET /api/governance/pending-actions:"
curl -s "https://pilot.owkai.app/api/governance/pending-actions" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total pending: {data.get(\"total\", 0)}')
print(f'Agent actions: {data.get(\"counts\", {}).get(\"agent_actions\", 0)}')
"
echo ""

echo "4. Testing GET /api/governance/unified-actions (what agents currently use):"
curl -s "https://pilot.owkai.app/api/governance/unified-actions?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total unified actions: {data.get(\"total\", 0)}')
print(f'Has more: {data.get(\"has_more\", False)}')
"
echo ""

echo "5. Testing GET /api/models (check if exists):"
MODELS_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "https://pilot.owkai.app/api/models" \
  -H "Authorization: Bearer $TOKEN")
echo "$MODELS_RESPONSE"
echo ""

echo "================================================"
echo "PART 2: Production Database State"
echo "================================================"
echo ""

echo "Connecting to production database..."
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
-- Current action statistics
SELECT
    status,
    COUNT(*) as count,
    COUNT(reviewed_by) as has_reviewer,
    COUNT(reviewed_at) as has_review_time,
    COUNT(extra_data) as has_extra_data
FROM agent_actions
GROUP BY status
ORDER BY count DESC;
"

echo ""
echo "Sample of actions with review data:"
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT
    id,
    status,
    reviewed_by,
    reviewed_at,
    extra_data IS NOT NULL as has_metadata,
    extra_data::text as metadata_preview
FROM agent_actions
WHERE status IN ('rejected', 'approved', 'executed')
LIMIT 5;
"

echo ""
echo "================================================"
echo "PART 3: Production Issues Validation"
echo "================================================"
echo ""

echo "Issue #1: Individual action endpoint returns 404?"
if echo "$RESPONSE_736" | grep -q "HTTP_STATUS:404"; then
    echo "❌ CONFIRMED: GET /agent-action/{id} returns 404"
else
    echo "✅ WORKS: GET /agent-action/{id} returns data"
fi
echo ""

echo "Issue #2: Missing approval metadata?"
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT
    COUNT(*) as total_reviewed_actions,
    COUNT(reviewed_by) as has_reviewer,
    COUNT(reviewed_at) as has_timestamp,
    COUNT(CASE WHEN extra_data IS NOT NULL AND extra_data::text LIKE '%rejection_reason%' THEN 1 END) as has_rejection_reason,
    COUNT(CASE WHEN extra_data IS NOT NULL AND extra_data::text LIKE '%approval_comments%' THEN 1 END) as has_approval_comments
FROM agent_actions
WHERE status IN ('approved', 'rejected');
" | tee /tmp/metadata_check.txt

if grep -q " 0" /tmp/metadata_check.txt; then
    echo "⚠️  Some metadata fields are not populated"
else
    echo "✅ Metadata fields are populated"
fi
echo ""

echo "Issue #3: /api/models endpoint exists?"
if echo "$MODELS_RESPONSE" | grep -q "HTTP_STATUS:404"; then
    echo "❌ CONFIRMED: GET /models endpoint does not exist (404)"
else
    echo "✅ WORKS: GET /models endpoint exists"
fi
echo ""

echo "Issue #4: Agent polling endpoint exists?"
STATUS_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "https://pilot.owkai.app/api/agent-action/status/736" \
  -H "Authorization: Bearer $TOKEN")
if echo "$STATUS_RESPONSE" | grep -q "HTTP_STATUS:404"; then
    echo "❌ CONFIRMED: GET /agent-action/status/{id} does not exist (404)"
else
    echo "✅ WORKS: GET /agent-action/status/{id} endpoint exists"
fi
echo ""

echo "================================================"
echo "PART 4: Production Deployment Info"
echo "================================================"
echo ""

echo "Current deployed backend commit:"
curl -s "https://pilot.owkai.app/api/health" | python3 -m json.tool || echo "Health endpoint not available"

echo ""
echo "=============================================="
echo "PRODUCTION ASSESSMENT COMPLETE"
echo "=============================================="
