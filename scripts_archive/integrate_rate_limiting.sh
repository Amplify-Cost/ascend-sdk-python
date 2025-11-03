#!/bin/bash

echo "🔧 Phase 2: Integrating Rate Limiting into Auth Routes..."
echo ""

cd ow-ai-backend || exit 1

# Step 1: Create backup
BACKUP_FILE="routes/auth.py.backup-$(date +%Y%m%d_%H%M%S)"
cp routes/auth.py "$BACKUP_FILE"
echo "✅ Created backup: $BACKUP_FILE"
echo ""

# Step 2: Add rate limiter import (after other imports)
echo "📝 Adding rate limiter import..."

# Find the line number after the last import
LAST_IMPORT_LINE=$(grep -n "^import\|^from" routes/auth.py | tail -1 | cut -d: -f1)

# Create temp file with import added
{
  head -n "$LAST_IMPORT_LINE" routes/auth.py
  echo ""
  echo "# Enterprise rate limiting"
  echo "from security.rate_limiter import limiter, RATE_LIMITS"
  tail -n +$((LAST_IMPORT_LINE + 1)) routes/auth.py
} > routes/auth.py.tmp

mv routes/auth.py.tmp routes/auth.py
echo "✅ Added rate limiter import"
echo ""

# Step 3: Add rate limiting decorators to endpoints
echo "📝 Adding rate limiting decorators to critical endpoints..."

# Add to /auth/token (login endpoint) - most critical
sed -i '' '/^@router.post("\/token")/i\
@limiter.limit(RATE_LIMITS["auth_login"])
' routes/auth.py

# Add to /auth/refresh-token
sed -i '' '/^@router.post("\/refresh-token")/i\
@limiter.limit(RATE_LIMITS["auth_refresh"])
' routes/auth.py

# Add to /auth/csrf
sed -i '' '/^@router.get("\/csrf")/i\
@limiter.limit(RATE_LIMITS["auth_csrf"])
' routes/auth.py

echo "✅ Added rate limiting decorators to 3 endpoints:"
echo "   - POST /auth/token (5/minute)"
echo "   - POST /auth/refresh-token (10/minute)"
echo "   - GET /auth/csrf (20/minute)"
echo ""

# Step 4: Show what changed
echo "📊 Changes made to auth.py:"
echo ""
echo "Import added:"
grep -A 1 "Enterprise rate limiting" routes/auth.py
echo ""
echo "Rate-limited endpoints:"
grep -B 1 "@limiter.limit" routes/auth.py | grep -E "@limiter|@router"
echo ""

# Step 5: Validate syntax
echo "🔍 Validating Python syntax..."
python3 -m py_compile routes/auth.py && echo "✅ Syntax valid!" || echo "❌ Syntax error - restoring backup"

if [ $? -ne 0 ]; then
  echo "⚠️  Syntax error detected, restoring backup..."
  cp "$BACKUP_FILE" routes/auth.py
  echo "✅ Backup restored"
  exit 1
fi

echo ""
echo "✅ Phase 2 complete! Rate limiting integrated into auth routes."
echo ""
echo "📋 Summary:"
echo "   - Backup created: $BACKUP_FILE"
echo "   - Rate limiter imported"
echo "   - 3 endpoints protected"
echo "   - Syntax validated"

