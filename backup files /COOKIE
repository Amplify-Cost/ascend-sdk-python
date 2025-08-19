#!/bin/bash

echo "🔍 COOKIE AUTHENTICATION DIAGNOSTIC"
echo "=================================="

# Test 1: Check if login endpoint works and sets cookies
echo "📋 Test 1: Login and Cookie Setting"
curl -X POST https://owai-production.up.railway.app/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"test","password":"test"}' \
  -c cookies.txt \
  -v \
  --silent \
  --show-error \
  2>&1

echo -e "\n📋 Test 2: Check if cookies were saved"
if [ -f cookies.txt ]; then
  echo "✅ Cookie file created:"
  cat cookies.txt
else
  echo "❌ No cookie file created"
fi

echo -e "\n📋 Test 3: Test /auth/me with cookies"
curl -X GET https://owai-production.up.railway.app/auth/me \
  -b cookies.txt \
  -v \
  --silent \
  --show-error \
  2>&1

echo -e "\n📋 Test 4: Check CORS headers"
curl -X OPTIONS https://owai-production.up.railway.app/auth/me \
  -H "Origin: https://your-frontend-domain.railway.app" \
  -v \
  --silent \
  --show-error \
  2>&1

echo -e "\n📋 Test 5: Check if CSRF endpoint works"
curl -X GET https://owai-production.up.railway.app/auth/csrf-token \
  -c csrf_cookies.txt \
  -v \
  --silent \
  --show-error \
  2>&1

echo -e "\n🔍 ANALYSIS COMPLETE"
echo "Run this script and share the output to identify the exact issue"
