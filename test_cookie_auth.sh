#!/bin/bash
# Cookie Authentication Diagnostic Test

echo "======================================"
echo "Cookie Authentication Diagnostic Test"
echo "======================================"
echo ""

# Test 1: Login and capture cookies
echo "Test 1: Login with Browser User-Agent"
echo "---------------------------------------"
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "X-Auth-Mode: cookie" \
  -d '{"email": "admin@owkai.com", "password": "admin123"}' \
  -c /tmp/test-cookies.txt \
  -i 2>&1 | grep -E "(HTTP/|Set-Cookie:|token_type)" | head -20

echo ""
echo "Test 2: Check Cookie File"
echo "-------------------------"
cat /tmp/test-cookies.txt

echo ""
echo "Test 3: Test /api/auth/me with Cookies"
echo "--------------------------------------"
curl -X GET http://localhost:8000/api/auth/me \
  -b /tmp/test-cookies.txt \
  -i 2>&1 | grep -E "(HTTP/|email|role)"

echo ""
echo "Test 4: Test Approve Action with Cookies"
echo "----------------------------------------"
curl -X POST http://localhost:8000/api/authorization/authorize/4 \
  -H "Content-Type: application/json" \
  -b /tmp/test-cookies.txt \
  -d '{"action": "approve"}' \
  -i 2>&1 | head -20

echo ""
echo "======================================"
echo "Test Complete"
echo "======================================"
