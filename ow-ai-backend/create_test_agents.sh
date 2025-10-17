#!/bin/bash

echo "=========================================="
echo "Creating Test Agents for Policy Testing"
echo "=========================================="
echo ""

# Get auth token
TOKEN=$(curl -s -X POST https://pilot.owkai.app/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@owkai.com", "password": "admin123"}' | jq -r '.access_token')

# Agent 1: LOW RISK - Read public data
echo "1. Creating LOW RISK agent action..."
LOW_RISK=$(curl -s -X POST https://pilot.owkai.app/api/agent-actions/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "analytics-bot-001",
    "action_type": "database_read",
    "resource": "public.sales_reports",
    "justification": "Generate monthly sales dashboard for public metrics",
    "metadata": {
      "estimated_records": 500,
      "data_classification": "public"
    }
  }')

echo "$LOW_RISK" | jq '{
  action_id: .id,
  risk_score: .risk_score,
  policy_applied: .policy_applied,
  status: .status,
  workflow_required: .workflow_required
}'
echo ""

# Agent 2: MEDIUM RISK - Update non-sensitive data
echo "2. Creating MEDIUM RISK agent action..."
MEDIUM_RISK=$(curl -s -X POST https://pilot.owkai.app/api/agent-actions/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "content-manager-bot",
    "action_type": "database_write",
    "resource": "marketing.blog_posts",
    "justification": "Update blog post metadata for SEO optimization",
    "metadata": {
      "estimated_records": 50,
      "data_classification": "internal"
    }
  }')

echo "$MEDIUM_RISK" | jq '{
  action_id: .id,
  risk_score: .risk_score,
  policy_applied: .policy_applied,
  status: .status,
  approval_required: .approval_required,
  required_approval_level: .required_approval_level
}'
echo ""

# Agent 3: HIGH RISK - Access customer PII
echo "3. Creating HIGH RISK agent action..."
HIGH_RISK=$(curl -s -X POST https://pilot.owkai.app/api/agent-actions/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "marketing-ai-gpt4",
    "action_type": "database_read",
    "resource": "customers.personal_data",
    "justification": "Extract email addresses for Q4 promotional campaign targeting",
    "metadata": {
      "estimated_records": 15000,
      "data_classification": "pii",
      "contains_email": true,
      "gdpr_applicable": true
    }
  }')

echo "$HIGH_RISK" | jq '{
  action_id: .id,
  risk_score: .risk_score,
  policy_applied: .policy_applied,
  status: .status,
  approval_required: .approval_required,
  required_approval_level: .required_approval_level,
  workflow_stage: .workflow_stage
}'
echo ""

# Agent 4: CRITICAL RISK - Delete financial records
echo "4. Creating CRITICAL RISK agent action..."
CRITICAL_RISK=$(curl -s -X POST https://pilot.owkai.app/api/agent-actions/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "cleanup-automation-bot",
    "action_type": "database_delete",
    "resource": "finance.transaction_records",
    "justification": "Archive old financial records from 2020 to cold storage",
    "metadata": {
      "estimated_records": 50000,
      "data_classification": "financial",
      "regulatory_retention": true,
      "sox_compliance_required": true
    }
  }')

echo "$CRITICAL_RISK" | jq '{
  action_id: .id,
  risk_score: .risk_score,
  policy_applied: .policy_applied,
  status: .status,
  approval_required: .approval_required,
  required_approval_level: .required_approval_level,
  blocked: .blocked
}'
echo ""

echo "=========================================="
echo "EXPECTED POLICY DECISIONS:"
echo "=========================================="
echo "Agent 1 (LOW): Auto-approved (score 0-49)"
echo "Agent 2 (MEDIUM): 1-level approval (score 50-69)"
echo "Agent 3 (HIGH): 2-level approval (score 70-89)"
echo "Agent 4 (CRITICAL): Blocked + 3-level approval (score 90-100)"
echo ""
echo "Run this to check workflow status:"
echo "curl -s https://pilot.owkai.app/api/workflows/pending -H 'Authorization: Bearer $TOKEN' | jq"
