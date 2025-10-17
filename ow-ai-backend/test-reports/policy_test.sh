#!/bin/bash

echo "📋 Testing Policy Management"
echo "============================="

# Get token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@owkai.com", "password": "admin123"}' | jq -r '.access_token')

echo "1. Testing Policy Creation from Natural Language..."
POLICY_CREATE=$(curl -s -X POST "http://localhost:8000/api/authorization/policies/create-from-natural-language" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Block any file access to sensitive data without manager approval",
    "context": {
      "environment": "production",
      "department": "engineering"
    }
  }')
echo "✅ Policy creation result: $(echo "$POLICY_CREATE" | head -c 150)..."

echo "2. Testing Real-time Policy Evaluation..."
POLICY_EVAL=$(curl -s -X POST "http://localhost:8000/api/authorization/policies/evaluate-realtime" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "file_access",
    "resource": "/secure/customer_data.db",
    "namespace": "database",
    "environment": "production",
    "user_context": {
      "user_id": "user123",
      "user_email": "test@company.com",
      "user_role": "analyst"
    }
  }')
echo "✅ Policy evaluation result: $(echo "$POLICY_EVAL" | head -c 150)..."

echo "3. Testing Policy Engine Metrics..."
POLICY_METRICS=$(curl -s -X GET "http://localhost:8000/api/authorization/policies/engine-metrics" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Policy metrics: $(echo "$POLICY_METRICS" | head -c 150)..."

echo "🎉 Policy Management Testing Complete!"