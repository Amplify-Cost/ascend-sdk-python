#!/bin/bash
#
# Enterprise AI Governance - Diverse Action Testing Script
# This script creates multiple different action types to test the approval workflow
#

set -e

echo "==========================================="
echo "OW-KAI Enterprise Action Testing"
echo "Creating Diverse AI Agent & MCP Actions"
echo "==========================================="
echo ""

# Get authentication token
echo "🔐 Authenticating..."
TOKEN=$(curl -s 'https://pilot.owkai.app/api/auth/token' \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@owkai.com","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Authenticated"
echo ""

# Function to create an action
create_action() {
    local agent_id="$1"
    local action_type="$2"
    local description="$3"
    local model_name="$4"
    local risk_level="$5"

    echo "Creating: $description"

    RESPONSE=$(curl -s 'https://pilot.owkai.app/api/agent-action' \
      -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H 'Content-Type: application/json' \
      -d "{
        \"agent_id\": \"$agent_id\",
        \"action_type\": \"$action_type\",
        \"action_source\": \"agent\",
        \"description\": \"$description\",
        \"model_name\": \"$model_name\",
        \"risk_level\": \"$risk_level\"
      }")

    ACTION_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'error'))")

    if [ "$ACTION_ID" != "error" ]; then
        echo "  ✅ Created Action ID: $ACTION_ID"
    else
        echo "  ❌ Failed: $RESPONSE"
    fi

    echo ""
}

echo "================================================"
echo "SCENARIO 1: Model Deployment Actions"
echo "================================================"
echo ""

create_action \
  "ml-ops-agent-prod" \
  "model_deployment" \
  "Deploy fraud-detection-v2.1 model to production environment" \
  "fraud-detection-v2.1" \
  "high"

create_action \
  "ml-ops-agent-prod" \
  "model_update" \
  "Update customer-churn-predictor model configuration (threshold: 0.75 → 0.80)" \
  "customer-churn-predictor" \
  "medium"

create_action \
  "ml-ops-agent-staging" \
  "model_rollback" \
  "Rollback recommendation-engine to v1.8 due to accuracy issues" \
  "recommendation-engine" \
  "high"

echo "================================================"
echo "SCENARIO 2: Data Access Actions"
echo "================================================"
echo ""

create_action \
  "data-science-agent" \
  "data_access" \
  "Access PII database for model training (customer names, addresses, SSN)" \
  "training-data-collector" \
  "critical"

create_action \
  "analytics-agent" \
  "data_export" \
  "Export 50K customer transaction records for fraud analysis" \
  "transaction-analyzer" \
  "high"

create_action \
  "ml-training-agent" \
  "database_query" \
  "Query medical records database for HIPAA-compliant ML training" \
  "healthcare-predictor" \
  "critical"

echo "================================================"
echo "SCENARIO 3: Infrastructure Changes"
echo "================================================"
echo ""

create_action \
  "devops-automation-agent" \
  "infrastructure_change" \
  "Modify security group to allow external API access on port 8443" \
  "api-gateway-sg" \
  "high"

create_action \
  "iam-management-agent" \
  "permission_change" \
  "Grant s3:PutObject permission to ml-training-role for prod bucket" \
  "s3-access-policy" \
  "high"

create_action \
  "encryption-agent" \
  "key_rotation" \
  "Rotate encryption keys for customer-data KMS key" \
  "kms-customer-master-key" \
  "medium"

echo "================================================"
echo "SCENARIO 4: MCP Server Actions"
echo "================================================"
echo ""

create_action \
  "mcp-database-server" \
  "database_write" \
  "Execute database migration: Add 'risk_score' column to users table" \
  "postgres-prod-db" \
  "critical"

create_action \
  "mcp-api-client" \
  "external_api_call" \
  "Call Experian Credit Bureau API to verify customer creditworthiness" \
  "credit-verification-service" \
  "high"

create_action \
  "mcp-config-manager" \
  "system_configuration" \
  "Update Redis cache TTL from 300s to 600s for session management" \
  "redis-session-cache" \
  "low"

echo "================================================"
echo "SCENARIO 5: Compliance & Security Actions"
echo "================================================"
echo ""

create_action \
  "security-audit-agent" \
  "security_scan" \
  "Run penetration test on customer-facing API endpoints" \
  "api-security-scanner" \
  "medium"

create_action \
  "gdpr-compliance-agent" \
  "data_deletion" \
  "Delete personal data for 15 customers who requested right to be forgotten" \
  "gdpr-deletion-service" \
  "high"

create_action \
  "sox-compliance-agent" \
  "audit_log_export" \
  "Export financial transaction logs for SOX compliance audit (Q4 2024)" \
  "financial-audit-exporter" \
  "medium"

echo ""
echo "==========================================="
echo "✅ Test Actions Created Successfully!"
echo "==========================================="
echo ""
echo "Next Steps:"
echo "1. Go to https://pilot.owkai.app/authorization-center"
echo "2. Review the pending actions"
echo "3. Approve some, deny others"
echo "4. Observe different risk levels, NIST controls, MITRE techniques"
echo ""
echo "Example approvals:"
echo "  - Approve: model deployments, low-risk config changes"
echo "  - Deny: PII access without proper justification"
echo "  - Escalate: Critical database migrations"
echo ""
