#!/bin/bash
set -e

echo "=== Build Verification Script ==="
echo "Commit SHA: $1"
echo "Image Tag: $2"

docker pull "$2"

BUNDLE_FILES=$(docker run --rm "$2" ls -1 /usr/share/nginx/html/assets/ | grep "^index-" | grep ".js$" | grep -v ".map")
echo "Bundle files in image: $BUNDLE_FILES"

HAS_FIX=$(git show "$1:src/components/AgentAuthorizationDashboard.jsx" | grep -c "workflow_execution_id: workflow.workflow_execution_id" || echo "0")

if [ "$HAS_FIX" -eq "0" ]; then
    echo "ERROR: Source code missing workflow_execution_id fix"
    exit 1
fi

echo "Source code has fix: OK"

# Get actual bundle filename
BUNDLE_FILE=$(echo "$BUNDLE_FILES" | grep "^index-" | head -1)

# Check bundle contents
docker run --rm "$2" cat "/usr/share/nginx/html/assets/$BUNDLE_FILE" > /tmp/bundle.js

if grep -q "workflow_execution_id:.*\.workflow_execution_id" /tmp/bundle.js; then
    echo "Bundle contains fix: OK"
    echo "=== Verification PASSED ==="
else
    echo "ERROR: Bundle is missing the workflow_execution_id mapping"
    echo "This means Vite built old code despite new source"
    exit 1
fi
