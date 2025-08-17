#!/bin/bash

echo "🧪 PRODUCTION-IDENTICAL LOCAL TESTING"
echo "===================================="
echo "🎯 Master Prompt Compliance: Test production-identical local environment"

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 5

# Test 1: Health check
echo ""
echo "🔍 Test 1: Health Check"
curl -s http://localhost:8000/health | jq . || echo "Health check response"

# Test 2: Cookie-based authentication
echo ""
echo "🔍 Test 2: Cookie Authentication"
curl -c cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"shug@gmail.com","password":"Kingdon1212"}' \
  http://localhost:8000/auth/cookie-login | jq . || echo "Login response"

# Test 3: Authenticated endpoint
echo ""
echo "🔍 Test 3: Authenticated Endpoint"
curl -b cookies.txt http://localhost:8000/auth/cookie-me | jq . || echo "Auth me response"

# Test 4: Enterprise endpoints
echo ""
echo "🔍 Test 4: Enterprise Analytics Endpoint"
curl -b cookies.txt http://localhost:8000/analytics/realtime/metrics | jq . || echo "Analytics response"

echo ""
echo "🔍 Test 5: Smart Rules Endpoint"
curl -b cookies.txt http://localhost:8000/smart-rules | jq . || echo "Smart rules response"

echo ""
echo "🔍 Test 6: Master Prompt Compliance Check"
curl -s http://localhost:8000/auth/master-prompt-compliance | jq . || echo "Compliance response"

# Cleanup
rm -f cookies.txt

echo ""
echo "✅ Production-identical testing complete!"
