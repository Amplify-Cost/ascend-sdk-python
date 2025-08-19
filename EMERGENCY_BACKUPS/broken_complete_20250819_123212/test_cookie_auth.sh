#!/bin/bash

echo "🧪 Testing Cookie Authentication..."
echo "================================="

# Test 1: Health check
echo "Test 1: Health check"
curl -s http://localhost:8002/health
echo ""

# Test 2: Login and get cookie
echo "Test 2: Login (should set cookie)"
curl -X POST http://localhost:8002/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  -c cookies.txt \
  -s | python3 -m json.tool
echo ""

# Test 3: Check if cookie was set
echo "Test 3: Cookie file contents"
cat cookies.txt
echo ""

# Test 4: Use cookie to access protected endpoint
echo "Test 4: Access /auth/me with cookie"
curl -s http://localhost:8002/auth/me -b cookies.txt | python3 -m json.tool
echo ""

# Test 5: Logout (clear cookie)
echo "Test 5: Logout (clear cookie)"
curl -X POST http://localhost:8002/auth/logout -b cookies.txt -c cookies.txt -s | python3 -m json.tool
echo ""

echo "✅ Cookie authentication tests completed!"
