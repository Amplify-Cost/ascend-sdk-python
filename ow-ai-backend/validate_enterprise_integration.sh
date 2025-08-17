#!/bin/bash

# Enterprise Integration Validation Script
# ========================================

echo "🧪 Validating Enterprise Cookie Auth Integration..."
echo "=================================================="

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend: Running on port 8000"
    
    # Test health endpoint
    HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "📊 Health Status: $HEALTH"
    
    # Test auth endpoints
    echo "🔐 Testing auth endpoints..."
    
    # Test /auth/token endpoint
    if curl -s -X POST http://localhost:8000/auth/token -H "Content-Type: application/json" -d '{}' | grep -q "detail"; then
        echo "✅ Auth endpoint: Responding"
    else
        echo "❌ Auth endpoint: Not responding properly"
    fi
    
else
    echo "❌ Backend: Not running on port 8000"
fi

# Check if frontend is accessible
if curl -s http://localhost:5174 > /dev/null; then
    echo "✅ Frontend: Running on port 5174"
else
    echo "❌ Frontend: Not running on port 5174"
fi

# Check configuration files
if [ -f ".env" ]; then
    echo "✅ Configuration: .env file exists"
    if grep -q "ALGORITHM=RS256" .env; then
        echo "✅ Security: RS256 algorithm configured"
    fi
    if grep -q "COOKIE_SECURE" .env; then
        echo "✅ Cookies: Enterprise cookie settings configured"
    fi
else
    echo "❌ Configuration: .env file missing"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Start backend: cd ow-ai-backend && python3 main.py"
echo "2. Start frontend: cd ow-ai-dashboard && npm run dev"
echo "3. Test login at: http://localhost:5174"
echo ""
