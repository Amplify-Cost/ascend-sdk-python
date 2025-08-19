#!/bin/bash
# tools/safe_fix_enterprise_user_mgmt.sh
# Safely fix EnterpriseUserManagement.jsx with validation and testing

set -e

TARGET_FILE="ow-ai-dashboard/src/components/EnterpriseUserManagement.jsx"
TEST_FILE="$TARGET_FILE.test"
BACKUP_FILE="$TARGET_FILE.backup.$(date +%Y%m%d_%H%M%S)"

echo "🛡️  SAFE Enterprise User Management Fixer"
echo "Target: $TARGET_FILE"

# Safety checks
if [[ ! -f "$TARGET_FILE" ]]; then
    echo "❌ Error: $TARGET_FILE not found"
    exit 1
fi

# Create timestamped backup
cp "$TARGET_FILE" "$BACKUP_FILE"
echo "📋 Created backup: $BACKUP_FILE"

# Create test copy for validation
cp "$TARGET_FILE" "$TEST_FILE"
echo "📋 Created test copy: $TEST_FILE"

echo ""
echo "🔍 Current state analysis:"
echo "Lines with BASE_URL: $(grep -c "BASE_URL" "$TARGET_FILE" || echo "0")"
echo "Lines with getAuthHeaders: $(grep -c "getAuthHeaders" "$TARGET_FILE" || echo "0")"
echo "Lines with fetch calls: $(grep -c "fetch(" "$TARGET_FILE" || echo "0")"

# Apply fixes to test file first
echo ""
echo "🧪 Testing fixes on copy..."

# 1. Add fetchWithAuth import if missing
if ! grep -q "import { fetchWithAuth }" "$TEST_FILE"; then
    echo "➕ Adding fetchWithAuth import..."
    sed -i '' '1a\
import { fetchWithAuth } from '\''../utils/fetchWithAuth'\'';
' "$TEST_FILE"
fi

# 2. Remove getAuthHeaders from component props
echo "🧹 Removing getAuthHeaders from props..."
sed -i '' 's/{ getAuthHeaders, user }/{ user }/g' "$TEST_FILE"
sed -i '' 's/{ getAuthHeaders }/{ }/g' "$TEST_FILE"
sed -i '' 's/({ getAuthHeaders, /({ /g' "$TEST_FILE"
sed -i '' 's/, getAuthHeaders }/}/g' "$TEST_FILE"

# 3. Remove BASE_URL constant
echo "🗑️  Removing BASE_URL constant..."
sed -i '' '/const BASE_URL = /d' "$TEST_FILE"

# 4. Fix fetch calls (more precise patterns)
echo "🔄 Converting fetch calls to fetchWithAuth..."

# Simple paths without variables
sed -i '' 's/fetch(`${BASE_URL}\/api\/enterprise-users\/users`, {/fetchWithAuth("\/api\/enterprise-users\/users", {/g' "$TEST_FILE"
sed -i '' 's/fetch(`${BASE_URL}\/api\/enterprise-users\/roles`, {/fetchWithAuth("\/api\/enterprise-users\/roles", {/g' "$TEST_FILE"
sed -i '' 's/fetch(`${BASE_URL}\/api\/enterprise-users\/audit-logs?limit=50`, {/fetchWithAuth("\/api\/enterprise-users\/audit-logs?limit=50", {/g' "$TEST_FILE"
sed -i '' 's/fetch(`${BASE_URL}\/api\/enterprise-users\/analytics`, {/fetchWithAuth("\/api\/enterprise-users\/analytics", {/g' "$TEST_FILE"

# Paths with variables (keep as template literals)
sed -i '' 's/fetch(`${BASE_URL}\/api\/enterprise-users\/users\/${editingUser\.id}`, {/fetchWithAuth(`\/api\/enterprise-users\/users\/${editingUser.id}`, {/g' "$TEST_FILE"
sed -i '' 's/fetch(`${BASE_URL}\/api\/enterprise-users\/users\/${userId}`, {/fetchWithAuth(`\/api\/enterprise-users\/users\/${userId}`, {/g' "$TEST_FILE"

# Clean up any remaining BASE_URL references
sed -i '' 's/fetch(`${BASE_URL}/fetchWithAuth(`/g' "$TEST_FILE"

echo ""
echo "🔍 Test results:"
echo "BASE_URL remaining: $(grep -c "BASE_URL" "$TEST_FILE" || echo "0")"
echo "getAuthHeaders remaining: $(grep -c "getAuthHeaders" "$TEST_FILE" || echo "0")"
echo "fetchWithAuth calls: $(grep -c "fetchWithAuth" "$TEST_FILE" || echo "0")"

# Validate the test file
echo ""
echo "🧪 Validating test file syntax..."

# Check for syntax issues
if grep -q "fetchWithAuth(/api" "$TEST_FILE"; then
    echo "⚠️  Found unquoted paths in fetchWithAuth calls"
    echo "Fixing unquoted paths..."
    sed -i '' 's/fetchWithAuth(\/api/fetchWithAuth("\/api/g' "$TEST_FILE"
    sed -i '' 's/fetchWithAuth("\/api\/\([^"]*\)", {/fetchWithAuth("\/api\/\1", {/g' "$TEST_FILE"
fi

# Final validation
echo ""
echo "🔍 Final validation:"
ERRORS=0

if grep -q "BASE_URL" "$TEST_FILE"; then
    echo "❌ BASE_URL still found"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "getAuthHeaders" "$TEST_FILE"; then
    echo "❌ getAuthHeaders still found"
    ERRORS=$((ERRORS + 1))
fi

if ! grep -q "import { fetchWithAuth }" "$TEST_FILE"; then
    echo "❌ fetchWithAuth import missing"
    ERRORS=$((ERRORS + 1))
fi

# Check for syntax issues
if grep -q "fetchWithAuth(/api" "$TEST_FILE"; then
    echo "❌ Unquoted paths found"
    ERRORS=$((ERRORS + 1))
fi

if [[ $ERRORS -gt 0 ]]; then
    echo ""
    echo "❌ Validation failed with $ERRORS errors"
    echo "Test file preserved at: $TEST_FILE"
    echo "Original backup at: $BACKUP_FILE"
    exit 1
fi

echo "✅ All validations passed!"

# Show the user what will change
echo ""
echo "🔍 Preview of changes:"
diff "$TARGET_FILE" "$TEST_FILE" | head -20 || true

echo ""
read -p "📝 Apply these changes to the actual file? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cp "$TEST_FILE" "$TARGET_FILE"
    echo "✅ Changes applied successfully!"
    
    # Clean up test file
    rm "$TEST_FILE"
    
    echo ""
    echo "🎉 Enterprise User Management component is now cookie-auth compliant!"
    echo "📋 Backup available at: $BACKUP_FILE"
    
    # Final verification
    echo ""
    echo "🔍 Final verification:"
    grep -n "import { fetchWithAuth }" "$TARGET_FILE"
    echo "fetchWithAuth calls: $(grep -c "fetchWithAuth" "$TARGET_FILE")"
    grep -n "BASE_URL" "$TARGET_FILE" || echo "✅ No BASE_URL found"
    grep -n "getAuthHeaders" "$TARGET_FILE" || echo "✅ No getAuthHeaders found"
    
else
    echo "❌ Changes not applied"
    echo "📋 Test file preserved at: $TEST_FILE"
    echo "📋 Backup available at: $BACKUP_FILE"
fi