#!/bin/bash

echo "🚨 Testing Alert Management System"
echo "================================="

# Get token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@owkai.com", "password": "admin123"}' | jq -r '.access_token')

echo "1. Testing Alert Display - Get All Alerts..."
ALERTS_LIST=$(curl -s -X GET "http://localhost:8000/alerts" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Alerts retrieved: $(echo "$ALERTS_LIST" | head -c 200)..."

echo "2. Testing Active Alerts..."
ACTIVE_ALERTS=$(curl -s -X GET "http://localhost:8000/alerts/active" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Active alerts: $(echo "$ACTIVE_ALERTS" | head -c 200)..."

echo "3. Testing Alert Summary..."
ALERT_SUMMARY=$(curl -s -X POST "http://localhost:8000/alerts/summary" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Alert summary: $(echo "$ALERT_SUMMARY" | head -c 200)..."

# Use a fixed alert ID for testing
ALERT_ID="3001"

echo "4. Testing Alert Acknowledgment..."
ACK_RESULT=$(curl -s -X POST "http://localhost:8000/alerts/$ALERT_ID/acknowledge" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment": "Acknowledged by admin for testing"}')
echo "✅ Alert acknowledgment: $(echo "$ACK_RESULT" | head -c 100)..."

echo "5. Testing Alert Escalation..."
ESCALATE_RESULT=$(curl -s -X POST "http://localhost:8000/alerts/$ALERT_ID/escalate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Requires immediate attention", "escalation_level": "high"}')
echo "✅ Alert escalation: $(echo "$ESCALATE_RESULT" | head -c 100)..."

echo "6. Testing Alert Resolution..."
RESOLVE_RESULT=$(curl -s -X POST "http://localhost:8000/alerts/$ALERT_ID/resolve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resolution": "Issue resolved by admin", "resolution_type": "manual"}')
echo "✅ Alert resolution: $(echo "$RESOLVE_RESULT" | head -c 100)..."

echo "🎉 Alert Management Testing Complete!"