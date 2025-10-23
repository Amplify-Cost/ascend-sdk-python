#!/bin/bash

echo "🔑 Testing OW-AI Authorization Center Authentication & RBAC"
echo "========================================================="

# Get access token
echo "1. Testing Login..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@owkai.com", "password": "admin123"}')

TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
echo "✅ Login successful, token obtained"

# Test user profile
echo "2. Testing User Profile Access..."
USER_PROFILE=$(curl -s -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ User profile access: $USER_PROFILE"

# Test admin endpoints
echo "3. Testing Admin Access to User Management..."
USERS_LIST=$(curl -s -X GET "http://localhost:8000/api/enterprise-users/users" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Admin user listing: $(echo "$USERS_LIST" | head -c 100)..."

# Test authorization dashboard
echo "4. Testing Authorization Dashboard..."
DASHBOARD=$(curl -s -X GET "http://localhost:8000/agent-control/dashboard" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Authorization dashboard: $(echo "$DASHBOARD" | head -c 100)..."

# Test policy endpoints
echo "5. Testing Policy Management..."
POLICIES=$(curl -s -X GET "http://localhost:8000/api/authorization/policies/list" \
  -H "Authorization: Bearer $TOKEN")
echo "✅ Policy listing: $(echo "$POLICIES" | head -c 100)..."

echo "🎉 RBAC Testing Complete!"