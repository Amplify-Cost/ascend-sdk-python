#!/bin/bash

# Add getCurrentUser Function to Enterprise fetchWithAuth.js
# ========================================================
# Adds the missing getCurrentUser export to your existing enterprise cookie authentication

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="${1:-$(pwd)}"
FRONTEND_DIR="${PROJECT_ROOT}/ow-ai-dashboard"
FETCH_AUTH_FILE="${FRONTEND_DIR}/src/utils/fetchWithAuth.js"

echo -e "${BLUE}🏢 Adding getCurrentUser to Enterprise Authentication${NC}"
echo -e "${BLUE}=================================================${NC}"
echo "📁 Project root: ${PROJECT_ROOT}"
echo "📄 Target file: ${FETCH_AUTH_FILE}"
echo ""

# Validate file exists
if [ ! -f "$FETCH_AUTH_FILE" ]; then
    echo -e "${RED}❌ Error: fetchWithAuth.js not found at: ${FETCH_AUTH_FILE}${NC}"
    echo "Please run this script from your project root directory."
    exit 1
fi

echo -e "${YELLOW}📦 Creating backup...${NC}"

# Create backup with timestamp
BACKUP_FILE="${FETCH_AUTH_FILE}.backup_$(date +%Y%m%d_%H%M%S)"
cp "$FETCH_AUTH_FILE" "$BACKUP_FILE"
echo "✅ Backup created: $(basename "$BACKUP_FILE")"

echo -e "${YELLOW}🔍 Checking current exports...${NC}"

# Check if getCurrentUser already exists
if grep -q "getCurrentUser" "$FETCH_AUTH_FILE"; then
    echo -e "${YELLOW}⚠️  getCurrentUser function already exists in the file${NC}"
    echo "Current exports found:"
    grep -n "export.*getCurrentUser" "$FETCH_AUTH_FILE" || echo "  (function exists but may not be exported)"
    echo ""
    echo -e "${BLUE}Do you want to replace/update it? (y/N):${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted - no changes made"
        exit 0
    fi
    
    # Remove existing getCurrentUser function
    echo "🔄 Removing existing getCurrentUser function..."
    # Create temp file without getCurrentUser function
    awk '
    /export async function getCurrentUser\(\)/ { skip=1 }
    /^export function/ && skip { skip=0 }
    /^export async function/ && skip && !/getCurrentUser/ { skip=0 }
    /^\/\*\*/ && skip { skip=0 }
    !skip { print }
    ' "$FETCH_AUTH_FILE" > "${FETCH_AUTH_FILE}.tmp"
    mv "${FETCH_AUTH_FILE}.tmp" "$FETCH_AUTH_FILE"
fi

echo -e "${YELLOW}🔧 Adding getCurrentUser function...${NC}"

# Add the getCurrentUser function to the end of the file
cat >> "$FETCH_AUTH_FILE" << 'EOF'

/**
 * Get current user information using enterprise cookie authentication
 * Integrates with your existing CSRF and cookie architecture
 */
export async function getCurrentUser() {
  try {
    console.log('🔍 Getting current user via enterprise cookie auth...');
    
    const response = await fetchWithAuth('/auth/me', {
      method: 'GET'
      // credentials: 'include' is already handled by fetchWithAuth
    });

    if (response.ok) {
      const userData = await response.json();
      console.log('✅ User data retrieved via cookies:', userData.email || userData.user_id);
      
      return {
        ...userData,
        enterprise_validated: true,
        auth_source: 'cookie'
      };
    } else if (response.status === 401) {
      console.log('ℹ️ No valid authentication - user not logged in');
      // No valid authentication - fetchWithAuth already handled redirect
      return null;
    } else {
      throw new Error(`Failed to get user: ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Error getting current user:', error);
    return null;
  }
}
EOF

echo -e "${GREEN}✅ Successfully added getCurrentUser function!${NC}"

echo -e "${YELLOW}🔍 Validating the update...${NC}"

# Validate the function was added correctly
if grep -q "export async function getCurrentUser" "$FETCH_AUTH_FILE"; then
    echo "✅ getCurrentUser function found and exported"
else
    echo -e "${RED}❌ Error: Function may not have been added correctly${NC}"
    exit 1
fi

# Show current exports
echo ""
echo -e "${BLUE}📋 Current exports in fetchWithAuth.js:${NC}"
grep -n "^export" "$FETCH_AUTH_FILE" | sed 's/^/  /'

echo ""
echo -e "${GREEN}🎉 Enterprise Authentication Update Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"

echo ""
echo -e "${BLUE}📋 What was added:${NC}"
echo "✅ getCurrentUser() function with enterprise cookie support"
echo "✅ Integrates with your existing CSRF protection"
echo "✅ Uses your existing fetchWithAuth architecture"
echo "✅ Proper error handling and logging"
echo "✅ Returns enterprise_validated flag for security"

echo ""
echo -e "${BLUE}📁 Files:${NC}"
echo "• Original: fetchWithAuth.js"
echo "• Backup: $(basename "$BACKUP_FILE")"

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "1. Restart your frontend:"
echo "   cd ow-ai-dashboard && npm run dev"
echo ""
echo "2. Test the login at: http://localhost:5174"
echo ""
echo "3. Check browser console for:"
echo "   ✅ '🔍 Getting current user via enterprise cookie auth...'"
echo "   ✅ '✅ User data retrieved via cookies: [email]'"

echo ""
echo -e "${BLUE}🔧 If issues occur:${NC}"
echo "Restore backup: cp $(basename "$BACKUP_FILE") fetchWithAuth.js"

echo ""
echo -e "${GREEN}✅ Ready to test enterprise cookie authentication!${NC}"
