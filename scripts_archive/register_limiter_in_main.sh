#!/bin/bash

echo "🔧 Phase 3: Registering Rate Limiter in Main App..."
echo ""

cd ow-ai-backend || exit 1

# Step 1: Create backup
BACKUP_FILE="main.py.backup-$(date +%Y%m%d_%H%M%S)"
cp main.py "$BACKUP_FILE"
echo "✅ Created backup: $BACKUP_FILE"
echo ""

# Step 2: Add imports at the top
echo "📝 Adding rate limiter imports to main.py..."

# Find where other imports are
IMPORT_LINE=$(grep -n "^from routes.auth import" main.py | head -1 | cut -d: -f1)

# Add the imports right after the auth router import
{
  head -n "$IMPORT_LINE" main.py
  echo "from security.rate_limiter import limiter, rate_limit_exceeded_handler"
  echo "from slowapi.errors import RateLimitExceeded"
  tail -n +$((IMPORT_LINE + 1)) main.py
} > main.py.tmp

mv main.py.tmp main.py
echo "✅ Added rate limiter imports"
echo ""

# Step 3: Add limiter state to FastAPI app
echo "📝 Adding limiter to FastAPI app state..."

# Find the line where FastAPI app is created
APP_LINE=$(grep -n "^app = FastAPI" main.py | head -1 | cut -d: -f1)

# Add limiter state right after app creation
{
  head -n "$APP_LINE" main.py
  echo ""
  echo "# Register rate limiter"
  echo "app.state.limiter = limiter"
  echo "app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)"
  echo ""
  tail -n +$((APP_LINE + 1)) main.py
} > main.py.tmp

mv main.py.tmp main.py
echo "✅ Added limiter to app state and exception handler"
echo ""

# Step 4: Verify changes
echo "📊 Changes made to main.py:"
echo ""
echo "Imports added:"
grep -A 1 "from security.rate_limiter" main.py
echo ""
echo "Limiter registration:"
grep -A 2 "Register rate limiter" main.py
echo ""

# Step 5: Validate syntax
echo "🔍 Validating Python syntax..."
python3 -m py_compile main.py && echo "✅ Syntax valid!" || {
  echo "❌ Syntax error - restoring backup"
  cp "$BACKUP_FILE" main.py
  exit 1
}

echo ""
echo "✅ Phase 3 complete! Rate limiter registered in main app."
echo ""
echo "📋 Summary:"
echo "   - Backup created: $BACKUP_FILE"
echo "   - Rate limiter imports added"
echo "   - Limiter registered with app"
echo "   - Exception handler configured"
echo "   - Syntax validated"

