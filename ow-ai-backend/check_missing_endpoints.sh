#!/bin/bash

echo "Checking backend endpoints..."
echo ""

endpoints=(
    "GET /api/governance/policies/engine-metrics"
    "POST /api/governance/policies/enforce"
    "GET /api/governance/policies/templates"
    "POST /api/governance/policies/from-template"
    "POST /api/governance/policies/compile"
    "GET /api/governance/policies/{id}/versions"
    "POST /api/governance/policies/{id}/rollback"
    "POST /api/governance/policies/{id}/impact-analysis"
)

for endpoint in "${endpoints[@]}"; do
    if grep -q "${endpoint##* }" routes/unified_governance_routes.py; then
        echo "✅ $endpoint"
    else
        echo "❌ MISSING: $endpoint"
    fi
done
