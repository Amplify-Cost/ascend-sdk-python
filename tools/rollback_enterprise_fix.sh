#!/bin/bash
# tools/rollback_enterprise_fix.sh
# Safely rollback the enterprise user management changes

set -e

TARGET_FILE="ow-ai-dashboard/src/components/EnterpriseUserManagement.jsx"

echo "🔙 Rolling back changes to $TARGET_FILE..."

# Find the most recent backup
BACKUP_FILE=$(ls -t "$TARGET_FILE".bak.* 2>/dev/null | head -1)

if [[ -z "$BACKUP_FILE" ]]; then
    echo "❌ No backup file found! Looking for .backup files..."
    BACKUP_FILE=$(ls -t "$TARGET_FILE".backup 2>/dev/null | head -1)
fi

if [[ -z "$BACKUP_FILE" ]]; then
    echo "❌ No backup files found. Cannot rollback safely."
    echo "Available files:"
    ls -la "$TARGET_FILE"* 2>/dev/null || echo "No related files found"
    exit 1
fi

echo "📋 Found backup: $BACKUP_FILE"
echo "📋 Current file size: $(wc -l < "$TARGET_FILE") lines"
echo "📋 Backup file size: $(wc -l < "$BACKUP_FILE") lines"

# Show diff for confirmation
echo ""
echo "🔍 Changes that will be reverted:"
diff "$BACKUP_FILE" "$TARGET_FILE" || true

echo ""
read -p "⚠️  Proceed with rollback? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Rollback cancelled"
    exit 1
fi

# Perform rollback
cp "$BACKUP_FILE" "$TARGET_FILE"
echo "✅ Rollback completed"
echo "📋 Restored from: $BACKUP_FILE"

# Verify rollback
echo ""
echo "🔍 Verification after rollback:"
grep -n "BASE_URL" "$TARGET_FILE" | head -3 || echo "No BASE_URL found"
grep -n "getAuthHeaders" "$TARGET_FILE" | head -1 || echo "No getAuthHeaders found"