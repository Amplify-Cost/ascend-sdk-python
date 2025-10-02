#!/bin/bash
set -e

echo "=== Build Verification Script ==="
echo "Commit SHA: $1"
echo "Image Tag: $2"

# Pull the built image
docker pull "$2"

# Extract bundle files
BUNDLE_FILES=$(docker run --rm "$2" ls -1 /usr/share/nginx/html/assets/ | grep "^index-" | grep ".js$" | grep -v ".map")
echo "Bundle files in image: $BUNDLE_FILES"

# Check source code for the critical fix
HAS_FIX=$(git show "$1:src/components/AgentAuthorizationDashboard.jsx" | grep -c "workflow_execution_id: workflow.workflow_execution_id" || echo "0")

if [ "$HAS_FIX" -eq "0" ]; then
    echo "ERROR: Source code missing workflow_execution_id fix"
    exit 1
fi

echo "Source code has fix: OK"

# Verify bundle contains the fix
docker run --rm "$2" cat /usr/share/nginx/html/assets/index-*.js | grep -q "workflow_execution_id:ye.workflow_execution_id"
if [ $? -ne 0 ]; then
    echo "ERROR: Built bundle missing workflow_execution_id mapping"
    exit 1
fi

echo "Bundle contains fix: OK"
echo "=== Verification PASSED ==="
