#!/usr/bin/env bash
# tools/fix_enterprise_user_mgmt.sh
# Purpose: Make EnterpriseUserManagement.jsx cookie-auth safe and env-agnostic.
set -euo pipefail

FILE="ow-ai-dashboard/src/components/EnterpriseUserManagement.jsx"

if [ ! -f "$FILE" ]; then
  echo "❌ Error: $FILE not found" >&2
  exit 1
fi

# Backup (timestamped)
cp "$FILE" "$FILE.bak.$(date +%Y%m%d%H%M%S)"

############################################
# 1) Insert fetchWithAuth import if missing
############################################
if ! grep -q "import { fetchWithAuth } from '../utils/fetchWithAuth';" "$FILE"; then
  awk 'BEGIN{added=0}
       {
         if(!added && $0 !~ /^import[[:space:]]/){
           print "import { fetchWithAuth } from '\''../utils/fetchWithAuth'\'';";
           added=1
         }
         print
       }
       END{
         if(!added){
           print "import { fetchWithAuth } from '\''../utils/fetchWithAuth'\'';"
         }
       }' "$FILE" > "$FILE.tmp" && mv "$FILE.tmp" "$FILE"
fi

############################################
# 2) Remove getAuthHeaders from props/usages
############################################
# Remove tokens in destructuring or lists
sed -E -i '' 's/, *getAuthHeaders//g' "$FILE"
sed -E -i '' 's/getAuthHeaders, *//g' "$FILE"
sed -E -i '' 's/\{ *getAuthHeaders *\}/\{\}/g' "$FILE"
# If the component ended up like `({})`, convert to `()`
sed -E -i '' 's/\(\{[[:space:]]*\}\)/\(\)/g' "$FILE"
# Tidy destructuring commas/spaces that might have been left behind
sed -E -i '' 's/\{[[:space:]]*,[[:space:]]*/\{/g' "$FILE"
sed -E -i '' 's/[[:space:]]*,[[:space:]]*\}/\}/g' "$FILE"

############################################
# 3) Remove const BASE_URL = "https://…"
############################################
sed -E -i '' '/^[[:space:]]*const[[:space:]]+BASE_URL[[:space:]]*=.*/d' "$FILE"

#########################################################################
# 4) Replace fetch(`${BASE_URL}/api/...`) → fetchWithAuth('/api/...')   #
#    Preserve options and keep template literals if the path uses ${...}#
#########################################################################

# With options object (comma present) — template string WITH ${...}
sed -E -i '' $'s/fetch\\(`\\$\\{BASE_URL\\}([^`]*\\$\\{[^`]+)`[[:space:]]*,/fetchWithAuth(`\\1`,/g' "$FILE"
# No options object (closing paren) — template string WITH ${...}
sed -E -i '' $'s/fetch\\(`\\$\\{BASE_URL\\}([^`]*\\$\\{[^`]+)`[[:space:]]*\\)/fetchWithAuth(`\\1`)/g' "$FILE"

# With options object (comma present) — NO interpolation
sed -E -i '' $'s/fetch\\(`\\$\\{BASE_URL\\}([^`$]+)`[[:space:]]*,/fetchWithAuth(\'\\1\',/g' "$FILE"
# No options object (closing paren) — NO interpolation
sed -E -i '' $'s/fetch\\(`\\$\\{BASE_URL\\}([^`$]+)`[[:space:]]*\\)/fetchWithAuth(\'\\1\')/g' "$FILE"

###############################################################
# 5) Done — print helpful notes
###############################################################
echo "✅ Updated $FILE"
echo "   - Added fetchWithAuth import (if missing)"
echo "   - Removed getAuthHeaders from props/usages"
echo "   - Deleted const BASE_URL"
echo "   - Rewrote fetch(\`\${BASE_URL}…\`) → fetchWithAuth('/api/…')"
echo "   - Left existing 'Content-Type': 'application/json' headers intact"
