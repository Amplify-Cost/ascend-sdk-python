#!/bin/bash

echo "🧪 TESTING AUTH ENDPOINTS"
echo "========================="

echo "1. Testing /auth/token with email/password..."
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=shug12@gmail.com&password=yourpassword" \
  -v

echo ""
echo "2. Testing /auth/login with email/password..."
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"shug12@gmail.com","password":"yourpassword"}' \
  -v

echo ""
echo "3. Checking available auth routes..."
curl -s "http://localhost:8000/docs" | grep -i auth || echo "Docs endpoint not available"
