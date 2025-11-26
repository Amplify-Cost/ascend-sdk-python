#!/usr/bin/env python3
"""
Script to add org_id parameter and filtering to remaining endpoints.
This script generates the edit commands needed for manual application.
"""

import re

# Remaining endpoints that need updates
remaining_endpoints = [
    # Policy conflict and analysis
    ("check_policy_conflicts", 1488, "POST", "/policies/{policy_id}/check-conflicts"),
    ("analyze_all_policy_conflicts", 1545, "GET", "/policies/conflicts/analyze"),

    # Policy import/export
    ("export_policies", 1582, "GET", "/policies/export"),
    ("import_policies", 1634, "POST", "/policies/import"),
    ("get_import_template", 1703, "GET", "/policies/import/template"),

    # Policy management operations
    ("create_policy_backup", 1740, "POST", "/policies/backup"),
    ("bulk_update_policy_status", 1785, "POST", "/policies/bulk-update-status"),
    ("bulk_delete_policies", 1821, "POST", "/policies/bulk-delete"),
    ("bulk_update_policy_priority", 1857, "POST", "/policies/bulk-update-priority"),

    # Policy evaluation
    ("evaluate_policy_realtime", 1892, "POST", "/policies/evaluate-realtime"),
    ("get_policy_engine_metrics", 1978, "GET", "/policies/engine-metrics"),
    ("deploy_policy", 2063, "POST", "/policies/{policy_id}/deploy"),
    ("evaluate_action_with_policies", 2123, "POST", "/authorization/policies/evaluate-realtime"),
    ("get_authorization_policy_metrics", 2285, "GET", "/authorization/policies/engine-metrics"),

    # Cedar policy operations
    ("compile_policy", 2373, "POST", "/policies/compile"),
    ("enforce_policy", 2434, "POST", "/policies/enforce"),
    ("get_enforcement_stats", 2558, "GET", "/policies/enforcement-stats"),

    # Pre-execution check
    ("pre_execute_check", 2575, "POST", "/agent/actions/pre-execute-check"),

    # Policy templates
    ("get_policy_templates", 2630, "GET", "/policies/templates"),
    ("get_policy_template_detail", 2648, "GET", "/policies/templates/{template_id}"),
    ("create_policy_from_template", 2672, "POST", "/policies/from-template"),
    ("build_custom_policy", 2729, "POST", "/policies/custom/build"),

    # Resource/Action types (likely static, but add for consistency)
    ("get_resource_types", 2838, "GET", "/policies/resources/types"),
    ("get_action_types", 2848, "GET", "/policies/actions/types"),
]

print("="*80)
print("ENTERPRISE MULTI-TENANT ISOLATION - REMAINING ENDPOINTS")
print("="*80)
print(f"\nTotal endpoints requiring updates: {len(remaining_endpoints)}\n")

print("STEP 1: Add org_id parameter to function signature")
print("-" * 80)
for func_name, line_num, method, path in remaining_endpoints:
    print(f"\nEndpoint: {method} {path}")
    print(f"Function: {func_name} (line ~{line_num})")
    print(f"Add parameter: org_id: int = Depends(get_organization_filter)")

print("\n" + "="*80)
print("STEP 2: Add org_id filtering to database queries")
print("-" * 80)
print("""
For GET/POST/PUT/DELETE operations that query the database:

1. After creating a query object:
   query = db.query(Model).filter(...)

2. Add multi-tenant isolation:
   # 🏢 ENTERPRISE: Multi-tenant isolation
   if org_id is not None:
       query = query.filter(Model.organization_id == org_id)

3. For POST/PUT operations that create/update records:
   model.organization_id = org_id
   # or in constructor
   Model(..., organization_id=org_id)

4. Add logging with org_id:
   logger.info(f"Operation by user {email} [org_id={org_id}]")
""")

print("\n" + "="*80)
print("ENDPOINTS BY CATEGORY")
print("="*80)

categories = {
    "Policy Conflict & Analysis": [
        ("check_policy_conflicts", "POST /policies/{policy_id}/check-conflicts"),
        ("analyze_all_policy_conflicts", "GET /policies/conflicts/analyze"),
    ],
    "Policy Import/Export": [
        ("export_policies", "GET /policies/export"),
        ("import_policies", "POST /policies/import"),
        ("get_import_template", "GET /policies/import/template"),
    ],
    "Policy Bulk Operations": [
        ("create_policy_backup", "POST /policies/backup"),
        ("bulk_update_policy_status", "POST /policies/bulk-update-status"),
        ("bulk_delete_policies", "POST /policies/bulk-delete"),
        ("bulk_update_policy_priority", "POST /policies/bulk-update-priority"),
    ],
    "Policy Evaluation & Metrics": [
        ("evaluate_policy_realtime", "POST /policies/evaluate-realtime"),
        ("get_policy_engine_metrics", "GET /policies/engine-metrics"),
        ("deploy_policy", "POST /policies/{policy_id}/deploy"),
        ("evaluate_action_with_policies", "POST /authorization/policies/evaluate-realtime"),
        ("get_authorization_policy_metrics", "GET /authorization/policies/engine-metrics"),
    ],
    "Cedar Policy Operations": [
        ("compile_policy", "POST /policies/compile"),
        ("enforce_policy", "POST /policies/enforce"),
        ("get_enforcement_stats", "GET /policies/enforcement-stats"),
    ],
    "Action Pre-Execution": [
        ("pre_execute_check", "POST /agent/actions/pre-execute-check"),
    ],
    "Policy Templates": [
        ("get_policy_templates", "GET /policies/templates"),
        ("get_policy_template_detail", "GET /policies/templates/{template_id}"),
        ("create_policy_from_template", "POST /policies/from-template"),
        ("build_custom_policy", "POST /policies/custom/build"),
    ],
    "Static Resources (Low Priority)": [
        ("get_resource_types", "GET /policies/resources/types"),
        ("get_action_types", "GET /policies/actions/types"),
    ],
}

for category, endpoints in categories.items():
    print(f"\n{category}:")
    for func, path in endpoints:
        print(f"  - {path}")

print("\n" + "="*80)
print("COMPLETED ENDPOINTS (Already Updated)")
print("="*80)
completed = [
    "POST /unified/action - create_unified_action",
    "GET /unified-stats - get_unified_governance_stats",
    "GET /unified-actions - get_unified_pending_actions",
    "GET /unified/actions - get_unified_actions_alias",
    "POST /mcp-governance/evaluate-action - evaluate_mcp_action",
    "GET /health - governance_health_check",
    "GET /admin/unified-report - get_unified_admin_report",
    "POST /create-policy - create_governance_policy",
    "GET /policies - get_policies",
    "PUT /policies/{policy_id} - update_governance_policy",
    "DELETE /policies/{policy_id} - delete_governance_policy",
    "GET /dashboard/pending-approvals - get_pending_approvals",
    "POST /workflows/{workflow_execution_id}/approve - approve_workflow",
    "GET /pending-actions - get_unified_pending_actions (second instance)",
]
for endpoint in completed:
    print(f"  ✅ {endpoint}")

print("\n" + "="*80)
print("NOTES")
print("="*80)
print("""
1. Priority Order:
   - HIGH: Data modification endpoints (POST/PUT/DELETE)
   - MEDIUM: Data retrieval endpoints that return sensitive data
   - LOW: Static resource endpoints

2. Testing Required:
   - Verify org_id is properly passed through dependency injection
   - Test with org_id=None (backward compatibility)
   - Test with org_id set (isolation verification)
   - Ensure no cross-organization data leakage

3. Pattern to Follow:
   - All endpoints get org_id parameter: org_id: int = Depends(get_organization_filter)
   - All database queries get filtered: if org_id is not None: query = query.filter(...)
   - All creates/updates set organization_id
   - All logging includes [org_id={org_id}]
""")
