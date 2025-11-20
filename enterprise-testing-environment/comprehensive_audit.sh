#!/bin/bash
#
# Comprehensive Enterprise Audit Script
# Audits production system before implementing Option 3 enterprise solution
#

set -e

echo "================================================================"
echo "COMPREHENSIVE ENTERPRISE PRODUCTION AUDIT"
echo "================================================================"
echo ""
echo "Target: https://pilot.owkai.app"
echo "Purpose: Full system audit before Option 3 implementation"
echo "Date: $(date)"
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

echo "================================================================"
echo "PART 1: DISCOVER ALL PRODUCTION ENDPOINTS"
echo "================================================================"
echo ""

echo "Testing Analytics Endpoints:"
echo "1. GET /api/analytics/dashboard:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/analytics/dashboard" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "2. GET /api/analytics/summary:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/analytics/summary" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "3. GET /api/analytics/metrics:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/analytics/metrics" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "Testing Governance Endpoints:"
echo "4. GET /api/governance/policies:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/governance/policies" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "5. GET /api/governance/unified-actions:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/governance/unified-actions" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "Testing Workflow Endpoints:"
echo "6. GET /api/workflows:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/workflows" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "Testing Alert Endpoints:"
echo "7. GET /api/alerts:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/alerts" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "Testing Smart Rules Endpoints:"
echo "8. GET /api/smart-rules:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/smart-rules" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "Testing Authorization Endpoints:"
echo "9. GET /api/authorization/pending:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/authorization/pending" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "Testing MCP Endpoints:"
echo "10. GET /api/mcp/servers:"
curl -s -w "\nHTTP:%{http_code}" "https://pilot.owkai.app/api/mcp/servers" -H "Authorization: Bearer $TOKEN" | head -20

echo ""
echo "================================================================"
echo "PART 2: DATABASE SCHEMA DISCOVERY"
echo "================================================================"
echo ""

echo "Listing all tables:"
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "\dt" | head -100

echo ""
echo "Analyzing agent_actions relationships:"
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE confrelid = 'agent_actions'::regclass
   OR conrelid = 'agent_actions'::regclass;
"

echo ""
echo "================================================================"
echo "PART 3: ANALYTICS TAB DISCOVERY"
echo "================================================================"
echo ""

echo "Checking what analytics data is available:"
curl -s "https://pilot.owkai.app/api/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('Analytics Dashboard Structure:')
    print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f'Error parsing analytics: {e}')
"

echo ""
echo "================================================================"
echo "PART 4: FEATURE DEPENDENCY MAP"
echo "================================================================"
echo ""

echo "Checking workflow dependencies on agent_actions:"
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT COUNT(*) as workflow_count,
       COUNT(DISTINCT action_id) as actions_with_workflows
FROM workflow_executions
WHERE action_id IS NOT NULL;
"

echo ""
echo "Checking alert dependencies:"
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT COUNT(*) as alert_count,
       COUNT(DISTINCT agent_action_id) as actions_with_alerts
FROM alerts
WHERE agent_action_id IS NOT NULL;
"

echo ""
echo "Checking playbook dependencies:"
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT COUNT(*) as playbook_exec_count,
       COUNT(DISTINCT triggered_by_action_id) as actions_triggering_playbooks
FROM playbook_execution_logs
WHERE triggered_by_action_id IS NOT NULL;
"

echo ""
echo "================================================================"
echo "AUDIT COMPLETE"
echo "================================================================"
