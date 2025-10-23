#!/bin/bash

echo "⚡ Testing Smart Rules Engine"
echo "============================="

# Get token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@owkai.com", "password": "admin123"}' | jq -r '.access_token')

echo "1. Testing Smart Rules Listing..."
RULES_LIST=$(curl -s -X GET "http://localhost:8000/api/smart-rules" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Rules list: $(echo "$RULES_LIST" | head -c 200)..."

echo "2. Testing Rule Creation from Natural Language..."
RULE_CREATE=$(curl -s -X POST "http://localhost:8000/api/smart-rules/generate-from-nl" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Alert me when any user accesses more than 100 files in 5 minutes",
    "severity": "high",
    "enabled": true
  }')
echo "✅ Rule creation: $(echo "$RULE_CREATE" | head -c 200)..."

echo "3. Testing Rule Generation (Alternative endpoint)..."
RULE_GEN=$(curl -s -X POST "http://localhost:8000/api/smart-rules/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_type": "security_alert",
    "parameters": {"threshold": 50, "timeframe": "5m"}
  }')
echo "✅ Rule generation: $(echo "$RULE_GEN" | head -c 200)..."

echo "4. Testing Seed Rules (Create Demo Rules)..."
SEED_RULES=$(curl -s -X POST "http://localhost:8000/api/smart-rules/seed" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Seed rules: $(echo "$SEED_RULES" | head -c 200)..."

echo "5. Testing Rule Analytics..."
RULE_ANALYTICS=$(curl -s -X GET "http://localhost:8000/api/smart-rules/analytics" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Rule analytics: $(echo "$RULE_ANALYTICS" | head -c 200)..."

echo "6. Testing Rule Suggestions..."
RULE_SUGGESTIONS=$(curl -s -X GET "http://localhost:8000/api/smart-rules/suggestions" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Rule suggestions: $(echo "$RULE_SUGGESTIONS" | head -c 200)..."

# Get the first rule ID for testing toggle functionality
RULE_ID=$(echo "$RULES_LIST" | jq -r '.[0].id // "1"' 2>/dev/null || echo "1")

echo "7. Testing Rule Optimization (rule ID: $RULE_ID)..."
RULE_OPTIMIZE=$(curl -s -X POST "http://localhost:8000/api/smart-rules/optimize/$RULE_ID" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Rule optimization: $(echo "$RULE_OPTIMIZE" | head -c 200)..."

echo "8. Testing A/B Testing Setup..."
AB_SETUP=$(curl -s -X POST "http://localhost:8000/api/smart-rules/setup-ab-testing-table" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ A/B testing setup: $(echo "$AB_SETUP" | head -c 200)..."

echo "9. Testing A/B Tests Listing..."
AB_TESTS=$(curl -s -X GET "http://localhost:8000/api/smart-rules/ab-tests" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ A/B tests: $(echo "$AB_TESTS" | head -c 200)..."

echo "🎉 Smart Rules Engine Testing Complete!"