#!/bin/bash
# tools/quick_fix_quotes.sh
# Quick fix for the missing quotes in fetchWithAuth calls

set -e

TARGET_FILE="ow-ai-dashboard/src/components/EnterpriseUserManagement.jsx"
BACKUP_FILE="$TARGET_FILE.quotes_backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Quick fix for missing quotes in fetchWithAuth calls"

if [[ ! -f "$TARGET_FILE" ]]; then
    echo "❌ Error: $TARGET_FILE not found"
    exit 1
fi

# Create backup
cp "$TARGET_FILE" "$BACKUP_FILE"
echo "📋 Created backup: $BACKUP_FILE"

echo ""
echo "🔍 Current problematic lines:"
grep -n "fetchWithAuth(/api" "$TARGET_FILE" || echo "No unquoted paths found"

echo ""
echo "🔧 Fixing unquoted paths..."

# Fix the specific unquoted paths found in your output
sed -i '' 's/fetchWithAuth(\/api\/enterprise-users\/users\/${editingUser\.id}/fetchWithAuth(`\/api\/enterprise-users\/users\/${editingUser.id}`/g' "$TARGET_FILE"
sed -i '' 's/fetchWithAuth(\/api\/enterprise-users\/users\/${userId}/fetchWithAuth(`\/api\/enterprise-users\/users\/${userId}`/g' "$TARGET_FILE"

# Fix any other unquoted paths
sed -i '' 's/fetchWithAuth(\/api\/\([^,}]*\),/fetchWithAuth("\/api\/\1",/g' "$TARGET_FILE"

echo ""
echo "🔍 Verification after fix:"
if grep -q "fetchWithAuth(/api" "$TARGET_FILE"; then
    echo "⚠️  Still found unquoted paths:"
    grep -n "fetchWithAuth(/api" "$TARGET_FILE"
    
    echo ""
    read -p "⚠️  Manual review needed. Open file for inspection? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📝 Please manually check lines with fetchWithAuth(/api patterns"
        echo "They should be either:"
        echo '  fetchWithAuth("/api/path", {...})  # for static paths'
        echo '  fetchWithAuth(`/api/path/${var}`, {...})  # for dynamic paths'
    fi
else
    echo "✅ All fetchWithAuth calls properly quoted"
fi

echo ""
echo "📋 Backup saved at: $BACKUP_FILE"
echo "🎉 Quick fix completed!"

# Show current state
echo ""
echo "🔍 Current fetchWithAuth usage:"
grep -n "fetchWithAuth" "$TARGET_FILE" | head -5