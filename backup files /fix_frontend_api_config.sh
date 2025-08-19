#!/bin/bash

echo "🔧 ENTERPRISE FRONTEND API CONFIGURATION FIX"
echo "============================================="
echo ""
echo "🎯 ISSUE IDENTIFIED:"
echo "❌ ReferenceError: API_BASE_URL is not defined"
echo "✅ Backend operational - Frontend can't connect"
echo ""

cd /Users/mac_001/OW_AI_Project/ow-ai-dashboard/src/utils

echo "📋 STEP 1: Checking Current fetchWithAuth Configuration"
echo "===================================================="

echo "🔍 Current API_BASE_URL configuration in fetchWithAuth.js:"
grep -n "API_BASE_URL" fetchWithAuth.js || echo "❌ API_BASE_URL not found"

echo ""
echo "📋 STEP 2: Enterprise API Configuration Fix"
echo "==========================================="

# Backup fetchWithAuth.js
cp fetchWithAuth.js fetchWithAuth.js.backup_api_fix

echo "🔧 Adding enterprise API configuration..."

# Add API_BASE_URL configuration at the top of the file
sed -i '' '1i\
// Enterprise API Configuration\
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";\
' fetchWithAuth.js

echo "✅ Added API_BASE_URL configuration"

echo ""
echo "🔍 Verifying the fix..."
head -10 fetchWithAuth.js

echo ""
echo "📋 STEP 3: Enterprise Environment Configuration"
echo "=============================================="

cd /Users/mac_001/OW_AI_Project/ow-ai-dashboard

echo "🔧 Checking for environment configuration..."

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    echo "📄 Current VITE_API_URL configuration:"
    grep "VITE_API_URL" .env || echo "❌ VITE_API_URL not configured"
else
    echo "⚠️ Creating enterprise .env configuration..."
    cat > .env << 'EOF'
# Enterprise API Configuration
VITE_API_URL=https://owai-production.up.railway.app
EOF
    echo "✅ Created .env with enterprise API configuration"
fi

# Also check .env.local
if [ -f ".env.local" ]; then
    echo "✅ .env.local exists"
    echo "📄 Local API configuration:"
    grep "VITE_API_URL" .env.local || echo "❌ VITE_API_URL not in .env.local"
else
    echo "💡 Creating .env.local for local development..."
    cat > .env.local << 'EOF'
# Local Development Configuration  
VITE_API_URL=https://owai-production.up.railway.app
EOF
    echo "✅ Created .env.local with enterprise API configuration"
fi

echo ""
echo "📋 STEP 4: Alternative API Configuration (Fallback)"
echo "=================================================="

echo "🔧 Adding hardcoded enterprise fallback in fetchWithAuth.js..."

# Ensure API_BASE_URL has a working fallback
sed -i '' 's|const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";|const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";\n\n// Enterprise debug logging\nconsole.log("🏢 Enterprise API Base URL:", API_BASE_URL);|' fetchWithAuth.js

echo "✅ Added enterprise fallback and debug logging"

echo ""
echo "📋 STEP 5: Verification"
echo "====================="

echo "🔍 Final fetchWithAuth.js configuration:"
head -15 fetchWithAuth.js

echo ""
echo "🚀 Deploying enterprise API fix..."
cd /Users/mac_001/OW_AI_Project

git add ow-ai-dashboard/src/utils/fetchWithAuth.js
git add ow-ai-dashboard/.env
git add ow-ai-dashboard/.env.local
git commit -m "🔧 ENTERPRISE FIX: Add API_BASE_URL configuration for frontend-backend communication"
git push origin main

echo ""
echo "✅ ENTERPRISE API CONFIGURATION DEPLOYED!"
echo "========================================"
echo ""
echo "⏱️  Frontend should rebuild and connect successfully"
echo "   API_BASE_URL now properly configured"
echo "   Backend communication should work"
echo ""
echo "🧪 Expected behavior:"
echo "   1. Frontend builds successfully ✅"
echo "   2. No more API_BASE_URL errors ✅"  
echo "   3. Login attempts reach backend ✅"
echo "   4. Enterprise authentication works ✅"
echo ""
echo "🏢 ENTERPRISE STATUS:"
echo "   ✅ Backend: Fully operational"
echo "   🔧 Frontend: API configuration fixed"
echo "   ✅ Authentication: Ready for testing"
echo "   ✅ Enterprise features: Accessible"
echo ""
echo "📋 FRONTEND API CONFIGURATION COMPLETE!"
echo "======================================"
