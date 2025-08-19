#!/bin/bash
# tools/fix_fetchWithAuth_exports.sh
# Add missing getCurrentUser and logout functions to fetchWithAuth.js

set -e

FETCHAUTH_FILE="ow-ai-dashboard/src/utils/fetchWithAuth.js"

echo "🔧 FIXING FETCHAUTH.JS EXPORTS"
echo "=============================="

if [[ ! -f "$FETCHAUTH_FILE" ]]; then
    echo "❌ $FETCHAUTH_FILE not found"
    exit 1
fi

# Create backup
BACKUP_FILE="$FETCHAUTH_FILE.backup.$(date +%Y%m%d_%H%M%S)"
cp "$FETCHAUTH_FILE" "$BACKUP_FILE"
echo "📋 Created backup: $BACKUP_FILE"

echo ""
echo "🔍 Current file content:"
cat "$FETCHAUTH_FILE"

echo ""
echo "➕ Adding missing functions..."

# First, fix the broken export at the end
sed -i '' 's/const ct = resp\.headers\.get.*text;.*/const ct = resp.headers.get("content-type") || ""; return ct.includes("application\/json") ? resp.json() : resp.text();/g' "$FETCHAUTH_FILE"

# Add the missing functions
cat >> "$FETCHAUTH_FILE" << 'EOF'

// Get current user info using cookie auth
export async function getCurrentUser() {
  try {
    const response = await fetchWithAuth('/api/auth/me');
    return response;
  } catch (error) {
    console.error('Error fetching current user:', error);
    return null;
  }
}

// Logout function using cookie auth
export async function logout() {
  try {
    const response = await fetchWithAuth('/api/auth/logout', {
      method: 'POST'
    });
    return response;
  } catch (error) {
    console.error('Error during logout:', error);
    throw error;
  }
}
EOF

echo ""
echo "✅ Added missing functions to fetchWithAuth.js"
echo "📋 Backup saved at: $BACKUP_FILE"

echo ""
echo "🔍 Updated exports:"
grep -n "export" "$FETCHAUTH_FILE"

echo ""
echo "🎯 Functions now available:"
echo "  ✓ fetchWithAuth - Main API call function"
echo "  ✓ getCurrentUser - Get current user via /api/auth/me"
echo "  ✓ logout - Logout via /api/auth/logout"
echo "  ✓ All use cookie-based authentication"