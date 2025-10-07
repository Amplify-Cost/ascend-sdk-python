#!/bin/bash
set -e

echo "=== Build Verification Script ==="
echo "Commit SHA: $1"
echo "Image Tag: $2"

docker pull "$2"

BUNDLE_FILES=$(docker run --rm "$2" ls -1 /usr/share/nginx/html/assets/ | grep "^index-" | grep ".js$" | grep -v ".map")
echo "Bundle files in image: $BUNDLE_FILES"

# Check source code has the governance endpoint
HAS_FIX=$(git show "$1:src/components/AgentAuthorizationDashboard.jsx" | grep -c "/api/governance/dashboard/pending-approvals" || echo "0")

if [ "$HAS_FIX" -eq "0" ]; then
    echo "ERROR: Source code missing governance endpoint"
    exit 1
fi

echo "Source code has fix: OK"

# Get actual bundle filename
BUNDLE_FILE=$(echo "$BUNDLE_FILES" | grep "^index-" | head -1)

# Check bundle contains the governance endpoint URL (this survives minification)
docker run --rm "$2" cat "/usr/share/nginx/html/assets/$BUNDLE_FILE" > /tmp/bundle.js

if grep -q "/api/governance/dashboard/pending-approvals" /tmp/bundle.js; then
    echo "Bundle contains governance endpoint: OK"
    echo "=== Verification PASSED ==="
else
    echo "ERROR: Bundle is missing governance endpoint URL"
    echo "Checking what's in the bundle..."
    grep -o "/api/[a-z/]*" /tmp/bundle.js | sort -u | head -10
    exit 1
fi
