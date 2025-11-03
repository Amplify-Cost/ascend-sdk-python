#!/bin/bash

echo "🔍 VERIFYING YOUR ACTUAL APPLICATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Check Backend Structure
echo "1️⃣ Backend Analysis:"
echo "Routes found:"
ls -1 ow-ai-backend/routes/*.py 2>/dev/null | sed 's|.*/||' | sed 's|\.py||'

echo ""
echo "Services found:"
ls -1 ow-ai-backend/services/*.py 2>/dev/null | grep -v __init__ | sed 's|.*/||' | sed 's|\.py||'

echo ""
echo "Schemas found:"
ls -1 ow-ai-backend/schemas/*.py 2>/dev/null | grep -v __init__ | sed 's|.*/||' | sed 's|\.py||'

# 2. Check Authentication
echo ""
echo "2️⃣ Authentication Check:"
if grep -q "request.cookies.get" ow-ai-backend/dependencies.py 2>/dev/null; then
    echo "✅ Uses cookie-based authentication"
else
    echo "❌ Cookie auth not found"
fi

if grep -q "Authorization" ow-ai-backend/dependencies.py 2>/dev/null; then
    echo "✅ Also supports Bearer token (header)"
else
    echo "❌ Bearer token not found"
fi

# 3. Check Database Tables
echo ""
echo "3️⃣ Database Tables:"
grep "__tablename__" ow-ai-backend/models.py 2>/dev/null | sed 's/.*= *["\x27]//' | sed 's/["\x27].*//' | while read table; do
    echo "✅ $table"
done

# 4. Check Deployment
echo ""
echo "4️⃣ Deployment Configuration:"
if [ -f "ow-ai-backend/Dockerfile" ]; then
    echo "✅ Backend Dockerfile exists"
fi

if [ -f "owkai-pilot-frontend/Dockerfile" ]; then
    echo "✅ Frontend Dockerfile exists"
fi

if [ -d "ow-ai-backend/alembic" ]; then
    echo "✅ Uses Alembic migrations"
fi

# 5. Count API Endpoints
echo ""
echo "5️⃣ API Endpoints Count:"
for route_file in ow-ai-backend/routes/*.py; do
    filename=$(basename "$route_file" .py)
    count=$(grep -c "@router\." "$route_file" 2>/dev/null || echo 0)
    if [ "$count" -gt 0 ]; then
        echo "✅ $filename: $count endpoints"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Verification Complete!"
echo ""

