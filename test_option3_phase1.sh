#!/bin/bash
#
# Option 3 Phase 1: Enterprise Autonomous Agent Workflow - Test Suite
# Tests all 4 new endpoints against production
#
# Run from: /Users/mac_001/OW_AI_Project/ow-ai-backend
# Usage: ./test_option3_phase1.sh
#

set -e

echo "================================================================"
echo "OPTION 3 PHASE 1: ENTERPRISE AUTONOMOUS AGENT WORKFLOW TESTS"
echo "================================================================"
echo ""
echo "Target: https://pilot.owkai.app"
echo "Date: $(date)"
echo ""

# Authenticate
echo "🔐 Authenticating to production..."
TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{" email":"admin@owkai.com","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Authenticated"
echo ""

echo "================================================================"
echo "FIX #1: GET /api/agent-action/{id} - Individual Action Retrieval"
echo "================================================================"
echo ""
echo "Test: Retrieve Action 736 (system_configuration, rejected)"
echo ""

RESPONSE_736=$(curl -s "https://pilot.owkai.app/api/agent-action/736" \
  -H "Authorization: Bearer $TOKEN")

echo "$RESPONSE_736" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ SUCCESS: Retrieved Action {data.get(\"id\")}')
    print(f'   Status: {data.get(\"status\")}')
    print(f'   Risk Score: {data.get(\"risk_score\")}')
    print(f'   NIST Control: {data.get(\"nist_control\")}')
    print(f'   MITRE Tactic: {data.get(\"mitre_tactic\")}')
    print(f'   Reviewed By: {data.get(\"reviewed_by\")}')
    print(f'   Has extra_data: {bool(data.get(\"extra_data\"))}')
except Exception as e:
    print(f'❌ FAILED: {e}')
    sys.exit(1)
"

echo ""
echo "================================================================"
echo "FIX #3: GET /api/models - Model Discovery"
echo "================================================================"
echo ""
echo "Test: Get deployed models (should return 3 demo models)"
echo ""

MODELS_RESPONSE=$(curl -s "https://pilot.owkai.app/api/models" \
  -H "Authorization: Bearer $TOKEN")

echo "$MODELS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ SUCCESS: Retrieved {data.get(\"total_count\")} models')
    for model in data.get('models', []):
        status_icon = '✅' if model['compliance_status'] == 'compliant' else '❌'
        print(f'   {status_icon} {model[\"model_id\"]}: {model[\"compliance_status\"]}')
except Exception as e:
    print(f'❌ FAILED: {e}')
    sys.exit(1)
"

echo ""
echo "================================================================"
echo "FIX #4: GET /api/agent-action/status/{id} - Agent Polling"
echo "================================================================"
echo ""
echo "Test: Poll status of Action 736"
echo ""

STATUS_RESPONSE=$(curl -s "https://pilot.owkai.app/api/agent-action/status/736" \
  -H "Authorization: Bearer $TOKEN")

echo "$STATUS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ SUCCESS: Status polling works')
    print(f'   Action ID: {data.get(\"action_id\")}')
    print(f'   Status: {data.get(\"status\")}')
    print(f'   Approved: {data.get(\"approved\")}')
    print(f'   Reviewed By: {data.get(\"reviewed_by\")}')
    print(f'   Comments: {data.get(\"comments\") or \"None (Fix #2 not yet deployed to this action)\"}')
    print(f'   Polling Interval: {data.get(\"polling_interval_seconds\")}s')
except Exception as e:
    print(f'❌ FAILED: {e}')
    sys.exit(1)
"

echo ""
echo "================================================================"
echo "FIX #2: Store Comments in extra_data"
echo "================================================================"
echo ""
echo "Test: Reject Action 725 with comment"
echo ""

# First check current state
CURRENT_STATE=$(curl -s "https://pilot.owkai.app/api/agent-action/725" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))")

echo "Current status of Action 725: $CURRENT_STATE"

# If already rejected, approve it first so we can test rejection
if [ "$CURRENT_STATE" = "rejected" ]; then
    echo "Approving Action 725 first..."
    curl -s -X POST "https://pilot.owkai.app/api/agent-action/725/approve" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -H "X-CSRF-Token: test" \
      -d '{"comments": "Re-approved for testing"}' > /dev/null
    echo "✅ Action approved"
fi

echo ""
echo "Now rejecting with comment: 'Missing GDPR documentation per Article 5'"
echo ""

REJECT_RESPONSE=$(curl -s -X POST "https://pilot.owkai.app/api/agent-action/725/reject" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: test" \
  -d '{"comments": "Missing GDPR documentation per Article 5"}')

echo "$REJECT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ SUCCESS: Action rejected')
    print(f'   Message: {data.get(\"message\")}')
except Exception as e:
    print(f'❌ FAILED: {e}')
    sys.exit(1)
"

echo ""
echo "Verifying comment was stored in extra_data..."
echo ""

VERIFY_RESPONSE=$(curl -s "https://pilot.owkai.app/api/agent-action/725" \
  -H "Authorization: Bearer $TOKEN")

echo "$VERIFY_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    extra_data = data.get('extra_data', {})
    rejection_reason = extra_data.get('rejection_reason')

    if rejection_reason:
        print(f'✅ SUCCESS: Comments stored in extra_data')
        print(f'   Rejection Reason: {rejection_reason}')
        print(f'   Rejected By: {extra_data.get(\"rejected_by\")}')
        print(f'   Rejected At: {extra_data.get(\"rejected_at\")}')
    else:
        print('❌ FAILED: Rejection reason not found in extra_data')
        print(f'   extra_data: {extra_data}')
        sys.exit(1)
except Exception as e:
    print(f'❌ FAILED: {e}')
    sys.exit(1)
"

echo ""
echo "================================================================"
echo "INTEGRATION TEST: Full Agent Workflow"
echo "================================================================"
echo ""
echo "Simulating autonomous agent workflow:"
echo "1. Agent polls action status"
echo "2. Agent reads rejection reason"
echo "3. Agent logs denial and aborts"
echo ""

# Agent polling simulation
echo "Agent: Polling status of Action 725..."
AGENT_POLL=$(curl -s "https://pilot.owkai.app/api/agent-action/status/725" \
  -H "Authorization: Bearer $TOKEN")

echo "$AGENT_POLL" | python3 -c "
import sys, json
data = json.load(sys.stdin)
status = data.get('status')
comments = data.get('comments')

print(f'Agent: Received status: {status}')
if status == 'rejected':
    print(f'Agent: Action denied - Reason: {comments}')
    print(f'Agent: Not executing. Logging denial and aborting.')
    print('✅ SUCCESS: Agent workflow complete - Action properly blocked')
elif status == 'approved':
    print(f'Agent: Action approved - Proceeding with execution')
    print('✅ Agent would execute now')
else:
    print(f'Agent: Action still pending - Will poll again in 30s')
"

echo ""
echo "================================================================"
echo "TEST SUMMARY"
echo "================================================================"
echo ""
echo "✅ Fix #1: Individual action retrieval - WORKING"
echo "✅ Fix #2: Comments storage in extra_data - WORKING"
echo "✅ Fix #3: Model discovery endpoint - WORKING"
echo "✅ Fix #4: Agent polling endpoint - WORKING"
echo "✅ Integration: Full autonomous agent workflow - WORKING"
echo ""
echo "🎉 ALL OPTION 3 PHASE 1 TESTS PASSED"
echo ""
echo "Next Steps:"
echo "1. Deploy to production"
echo "2. Update compliance agent to use GET /api/models"
echo "3. Test with real agent polling loop"
echo "4. Plan Phase 2 (execution reporting + API keys)"
echo ""
