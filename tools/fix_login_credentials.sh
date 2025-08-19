#!/bin/bash

echo "🔐 FIXING LOGIN CREDENTIALS FORMAT"
echo "=================================="

cd ow-ai-dashboard

echo "🛠️ Backend expects 'email' and 'password', not 'username' and 'password'"
echo "From logs: {'detail':'Email and password required'}"

# Fix the App.jsx login function to send correct field names
cp src/App.jsx src/App.jsx.backup.$(date +%Y%m%d_%H%M%S)

# Update just the login function to send email/password instead of username/password
sed -i.bak '/body: new URLSearchParams({/,/}),/c\
        body: new URLSearchParams({\
          email: loginData.email,\
          password: loginData.password,\
        }),
' src/App.jsx

echo "✅ Updated login form to send 'email' instead of 'username'"

# Also, let's add a debug endpoint check
echo ""
echo "🔍 Let's check what auth endpoints your backend actually has..."
echo "Run this to see available endpoints:"
echo "curl http://localhost:8000/docs"
echo ""
echo "Or check these endpoints manually:"
echo "GET  http://localhost:8000/auth/me"
echo "POST http://localhost:8000/auth/login" 
echo "POST http://localhost:8000/auth/token"
echo ""

# Create a test script to verify the endpoint
cat > test_auth.sh << 'EOF'
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
EOF

chmod +x test_auth.sh

echo "✅ Created test_auth.sh - you can run this to test endpoints manually"

echo ""
echo "🎯 LIKELY ISSUE:"
echo "Backend logs show 400 Bad Request with 'Email and password required'"
echo "This means the endpoint exists but expects different field names."
echo ""
echo "🔧 FIX APPLIED:"
echo "✅ Changed 'username' → 'email' in login form"
echo ""
echo "🚀 TEST NOW:"
echo "1. npm run dev"
echo "2. Try login with your credentials"
echo "3. Should now send correct field names to backend"
echo ""
echo "If it still fails, run ./test_auth.sh to debug endpoints manually"