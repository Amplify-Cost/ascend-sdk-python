# Frontend Implementation Plan: Enterprise Policy Features 1-3

**Date:** 2025-11-04
**Status:** READY FOR IMPLEMENTATION
**Backend:** ✅ COMPLETE (All APIs deployed and tested)
**Frontend:** ⏳ PENDING

---

## Executive Summary

The **backend APIs for Features 1-3 are fully functional and tested**. Now we need to add UI components to make these features accessible to users.

**Current State:**
- ✅ Backend APIs working (11/11 tests passed)
- ✅ Existing policy management UI exists (`EnhancedPolicyTab.jsx`)
- ⏳ Need to add 3 new feature sections to UI

**Implementation Effort:** ~4-6 hours for all 3 features

---

## Required Frontend Changes

### Overview

We need to enhance the existing **Policy Management** section in the Authorization Center with 3 new tabs/sections:

1. **Conflict Detection** - Show policy conflicts with resolution suggestions
2. **Import/Export** - Download/upload policies in multiple formats
3. **Bulk Operations** - Mass enable/disable, delete, priority updates

---

## Feature 1: Conflict Detection UI

### What to Add

**Location:** Add new tab in `EnhancedPolicyTab.jsx` or create `PolicyConflictDetector.jsx`

**UI Components Needed:**

1. **Conflict Analysis Dashboard**
   - Show total conflicts by severity (critical/high/medium/low)
   - Visual breakdown (donut chart or bar chart)
   - "Analyze All Policies" button

2. **Conflict List View**
   - Table showing all detected conflicts
   - Columns: Policy 1, Policy 2, Type, Severity, Actions
   - Color coding: Red (critical), Orange (high), Yellow (medium)

3. **Conflict Detail Card**
   - Show conflict description
   - List resolution suggestions
   - Option to "Ignore" or "Fix Now"

### API Endpoints to Call

```javascript
// Get all conflicts
GET /api/governance/policies/conflicts/analyze

Response:
{
  success: true,
  total_conflicts: 5,
  critical: 1,
  high: 2,
  medium: 2,
  conflicts: [
    {
      conflict_type: "effect_contradiction",
      severity: "critical",
      policy1: {id: 1, name: "Policy A"},
      policy2: {id: 2, name: "Policy B"},
      description: "...",
      resolution_suggestions: ["...", "..."]
    }
  ]
}

// Check single policy for conflicts
POST /api/governance/policies/{policy_id}/check-conflicts
Body: { policy_name, effect, actions, resources, conditions, priority }

Response:
{
  has_conflicts: true,
  conflict_summary: { total: 2, critical: 1 },
  conflicts: [...],
  recommendation: "BLOCK" | "WARN" | "PROCEED"
}
```

### UI Mockup (Text Description)

```
┌─────────────────────────────────────────────────────┐
│ Policy Conflict Detection                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Analyze All Policies]  Last Scan: 2 mins ago    │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Conflict Summary                            │  │
│  │  Critical: 1    High: 2                     │  │
│  │  Medium: 2      Low: 0                      │  │
│  │  Total: 5 conflicts                         │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  Conflicts Detected:                               │
│                                                     │
│  🔴 CRITICAL: Effect Contradiction                 │
│  Policy A (Deny) vs Policy B (Allow)              │
│  Resource: database:*                              │
│  [View Details] [Resolve]                         │
│                                                     │
│  🟠 HIGH: Priority Conflict                        │
│  Policy C and Policy D both priority 100          │
│  [View Details] [Resolve]                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### When to Show Conflict Warnings

**Automatically check for conflicts when:**
1. Creating a new policy (before save)
2. Editing an existing policy (before save)
3. User clicks "Analyze All Policies"

**Warning Flow:**
```javascript
// When user saves a policy
const checkConflicts = async (policyData) => {
  const response = await fetch(
    `/api/governance/policies/${policyId}/check-conflicts`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(policyData)
    }
  );

  const result = await response.json();

  if (result.has_conflicts) {
    if (result.recommendation === "BLOCK") {
      // Show error modal - prevent save
      alert("CRITICAL conflicts detected. Cannot deploy this policy.");
    } else if (result.recommendation === "WARN") {
      // Show warning modal - allow save with confirmation
      if (confirm("Conflicts detected. Deploy anyway?")) {
        // Proceed with save
      }
    }
  }
};
```

---

## Feature 2: Import/Export UI

### What to Add

**Location:** Add "Import/Export" section to Policy Management

**UI Components Needed:**

1. **Export Panel**
   - Format selector dropdown: JSON | YAML | Cedar
   - Filter options: All policies | Active only | Inactive only
   - "Download" button
   - Shows preview before download

2. **Import Panel**
   - File upload dropzone
   - Format auto-detection
   - "Dry Run" checkbox
   - Conflict resolution strategy: Skip | Overwrite | Merge
   - Progress indicator
   - Result summary after import

3. **Backup Manager**
   - "Create Backup Now" button
   - List of recent backups
   - Download/restore options

### API Endpoints to Call

```javascript
// Export policies
GET /api/governance/policies/export?format=json&status=active

Response: JSON/YAML/Cedar formatted file

// Import policies
POST /api/governance/policies/import
Body: {
  import_data: "<json_or_yaml_string>",
  format: "json",
  dry_run: true,
  conflict_resolution: "skip"
}

Response:
{
  success: true,
  dry_run: true,
  imported: 5,
  skipped: 2,
  errors: 0,
  conflicts: [...]
}

// Get import template
GET /api/governance/policies/import/template?format=json

Response: Template with example policies

// Create backup
POST /api/governance/policies/backup
Body: { backup_name: "pre_deploy_backup" }

Response:
{
  success: true,
  backup_name: "...",
  total_policies: 10,
  backup_data: "..."
}
```

### UI Mockup

```
┌─────────────────────────────────────────────────────┐
│ Import / Export Policies                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│ [Export] [Import] [Backups]  <-- Tabs             │
│                                                     │
│ ┌─ EXPORT ────────────────────────────────────┐   │
│ │                                              │   │
│ │ Format:  [JSON ▼]                           │   │
│ │ Filter:  [All Policies ▼]                   │   │
│ │                                              │   │
│ │ Preview:                                     │   │
│ │ {                                            │   │
│ │   "version": "1.0",                         │   │
│ │   "total_policies": 15,                     │   │
│ │   ...                                        │   │
│ │ }                                            │   │
│ │                                              │   │
│ │          [Download Export File]              │   │
│ │                                              │   │
│ └──────────────────────────────────────────────┘   │
│                                                     │
│ ┌─ IMPORT ────────────────────────────────────┐   │
│ │                                              │   │
│ │  Drag & drop file here or click to browse   │   │
│ │                                              │   │
│ │  ☑ Dry Run (test without saving)           │   │
│ │  Conflict Resolution: [Skip ▼]              │   │
│ │                                              │   │
│ │          [Import Policies]                   │   │
│ │                                              │   │
│ └──────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Example React Component

```jsx
const PolicyImportExport = ({ API_BASE_URL, getAuthHeaders }) => {
  const [format, setFormat] = useState('json');
  const [exportData, setExportData] = useState(null);

  const handleExport = async () => {
    const response = await fetch(
      `${API_BASE_URL}/api/governance/policies/export?format=${format}`,
      { headers: getAuthHeaders() }
    );

    const data = await response.text(); // Get raw text (could be JSON/YAML/Cedar)

    // Trigger download
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `policies_export_${Date.now()}.${format}`;
    a.click();
  };

  const handleImport = async (file) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const importData = e.target.result;

      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/import`,
        {
          method: 'POST',
          headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({
            import_data: importData,
            format: 'json',
            dry_run: true,
            conflict_resolution: 'skip'
          })
        }
      );

      const result = await response.json();
      alert(`Import preview: ${result.imported} would be imported, ${result.skipped} skipped`);
    };
    reader.readAsText(file);
  };

  return (
    // UI components here
  );
};
```

---

## Feature 3: Bulk Operations UI

### What to Add

**Location:** Add "Bulk Actions" toolbar to policy list view

**UI Components Needed:**

1. **Bulk Selection Controls**
   - Checkbox column in policy table
   - "Select All" / "Deselect All" buttons
   - Selected count indicator

2. **Bulk Action Toolbar**
   - Appears when policies are selected
   - Buttons: Enable | Disable | Delete | Update Priority
   - Shows count of selected policies

3. **Bulk Update Modal**
   - Priority slider (for bulk priority update)
   - Reason text field (for audit trail)
   - Confirmation checkbox for destructive actions
   - Preview of changes

4. **Result Summary**
   - Show success/failure counts
   - List any errors
   - Option to download results

### API Endpoints to Call

```javascript
// Bulk update status
POST /api/governance/policies/bulk-update-status
Body: {
  policy_ids: [1, 2, 3],
  new_status: "inactive",
  reason: "Temporary maintenance"
}

Response:
{
  success: true,
  updated_count: 3,
  error_count: 0,
  updated_policies: [
    {policy_id: 1, policy_name: "...", old_status: "active", new_status: "inactive"}
  ],
  errors: []
}

// Bulk delete
POST /api/governance/policies/bulk-delete
Body: {
  policy_ids: [5, 6],
  confirmation: "DELETE",
  create_backup: true
}

Response:
{
  success: true,
  deleted_count: 2,
  backup: { backup_name: "...", timestamp: "..." }
}

// Bulk update priority
POST /api/governance/policies/bulk-update-priority
Body: {
  updates: [
    {policy_id: 1, priority: 100},
    {policy_id: 2, priority: 90}
  ]
}

Response:
{
  success: true,
  updated_count: 2,
  updated_policies: [...]
}
```

### UI Mockup

```
┌─────────────────────────────────────────────────────┐
│ Policy Management                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ☑ 3 policies selected                             │
│ [Enable] [Disable] [Update Priority] [Delete]     │
│                                                     │
│ ┌──────────────────────────────────────────────┐  │
│ │ ☑ │ Policy Name        │ Status  │ Priority │  │
│ ├───┼────────────────────┼─────────┼──────────┤  │
│ │ ☑ │ Allow Database     │ Active  │ 100      │  │
│ │ ☐ │ Deny Production    │ Active  │ 90       │  │
│ │ ☑ │ Require Approval   │ Active  │ 95       │  │
│ │ ☑ │ Block Deletes      │ Inactive│ 85       │  │
│ └──────────────────────────────────────────────┘  │
│                                                     │
│ [Bulk Action Confirmation Modal]                  │
│ ┌──────────────────────────────────────────────┐  │
│ │ Disable 3 Policies?                          │  │
│ │                                              │  │
│ │ Reason (required):                           │  │
│ │ [Temporary maintenance window____________]   │  │
│ │                                              │  │
│ │ Policies to be disabled:                     │  │
│ │ • Allow Database Read                        │  │
│ │ • Require Approval for Schema Changes        │  │
│ │ • Block Deletes                              │  │
│ │                                              │  │
│ │      [Cancel]  [Confirm Disable]            │  │
│ └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Example React Component

```jsx
const BulkPolicyActions = ({ selectedPolicies, onComplete }) => {
  const [reason, setReason] = useState('');

  const handleBulkDisable = async () => {
    const policyIds = selectedPolicies.map(p => p.id);

    const response = await fetch(
      `${API_BASE_URL}/api/governance/policies/bulk-update-status`,
      {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          policy_ids: policyIds,
          new_status: 'inactive',
          reason: reason
        })
      }
    );

    const result = await response.json();

    if (result.success) {
      alert(`Successfully disabled ${result.updated_count} policies`);
      onComplete(); // Refresh policy list
    } else {
      alert(`Error: ${result.error}`);
    }
  };

  return (
    // Modal UI here
  );
};
```

---

## Implementation Priority

### Phase 1: Essential UI (High Priority)

**Goal:** Make features usable immediately

1. **Feature 2: Import/Export** ⭐ PRIORITY 1
   - Simple export button with format dropdown
   - Download as JSON/YAML/Cedar
   - Estimated: 2 hours

2. **Feature 3: Bulk Operations** ⭐ PRIORITY 2
   - Add checkboxes to policy table
   - Bulk enable/disable buttons
   - Simple confirmation modal
   - Estimated: 2 hours

3. **Feature 1: Conflict Detection** ⭐ PRIORITY 3
   - "Check for Conflicts" button
   - Show conflict list
   - Display resolution suggestions
   - Estimated: 2 hours

### Phase 2: Enhanced UI (Medium Priority)

**Goal:** Better UX and visual polish

1. Charts/graphs for conflict analysis
2. Drag-drop file upload for import
3. Backup management UI
4. Real-time conflict detection on policy edit

**Estimated:** 4-6 hours

---

## Files to Modify

### Primary File
- `owkai-pilot-frontend/src/components/EnhancedPolicyTab.jsx` - Main policy UI

### Option 1: Add to Existing Component
Enhance `EnhancedPolicyTab.jsx` with 3 new views:
- Add "Conflicts" tab
- Add "Import/Export" tab
- Add bulk action toolbar to "list" view

### Option 2: Create New Components
Create separate component files:
- `PolicyConflictDetector.jsx` - Feature 1
- `PolicyImportExport.jsx` - Feature 2
- `PolicyBulkActions.jsx` - Feature 3

Then import into `EnhancedPolicyTab.jsx`

**Recommendation:** Use **Option 2** for cleaner code organization.

---

## Testing Checklist

### Feature 1: Conflict Detection
- [ ] "Analyze All Policies" button works
- [ ] Conflicts display with correct severity colors
- [ ] Resolution suggestions show correctly
- [ ] Warning appears when creating conflicting policy

### Feature 2: Import/Export
- [ ] Export to JSON downloads correctly
- [ ] Export to YAML downloads correctly
- [ ] Export to Cedar downloads correctly
- [ ] Import template downloads
- [ ] File upload accepts JSON/YAML
- [ ] Dry run shows preview
- [ ] Actual import creates policies

### Feature 3: Bulk Operations
- [ ] Policy checkboxes work
- [ ] Select all/deselect all works
- [ ] Bulk disable updates all selected policies
- [ ] Bulk enable updates all selected policies
- [ ] Bulk priority update works
- [ ] Bulk delete requires confirmation
- [ ] Audit trail records reason

---

## Minimal Implementation (Quick Start)

If you want to **start simple** and add features incrementally:

### Step 1: Export Only (15 minutes)
```jsx
const SimpleExport = () => {
  const downloadPolicies = async () => {
    const response = await fetch('/api/governance/policies/export?format=json');
    const data = await response.text();
    const blob = new Blob([data], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'policies.json';
    a.click();
  };

  return <button onClick={downloadPolicies}>Export Policies (JSON)</button>;
};
```

### Step 2: Conflict Detection (30 minutes)
```jsx
const SimpleConflictChecker = () => {
  const [conflicts, setConflicts] = useState([]);

  const checkConflicts = async () => {
    const response = await fetch('/api/governance/policies/conflicts/analyze');
    const data = await response.json();
    setConflicts(data.conflicts);
  };

  return (
    <div>
      <button onClick={checkConflicts}>Check for Conflicts</button>
      {conflicts.map(c => (
        <div key={c.detected_at} className="border p-2 my-2">
          <strong>{c.severity}:</strong> {c.description}
        </div>
      ))}
    </div>
  );
};
```

### Step 3: Bulk Disable (30 minutes)
```jsx
const SimpleBulkDisable = ({ selectedIds }) => {
  const bulkDisable = async () => {
    await fetch('/api/governance/policies/bulk-update-status', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        policy_ids: selectedIds,
        new_status: 'inactive',
        reason: 'Bulk disable'
      })
    });
    alert('Policies disabled!');
  };

  return <button onClick={bulkDisable}>Disable Selected</button>;
};
```

---

## Summary

**Backend:** ✅ 100% Complete
**Frontend:** ⏳ Not Started

**Minimum Viable UI:** ~2 hours (export + basic bulk actions)
**Full Featured UI:** ~6-8 hours (all 3 features with polish)

**Next Steps:**
1. Decide on implementation approach (minimal vs full-featured)
2. Choose file organization (single file vs multiple components)
3. Start with Feature 2 (Import/Export) - easiest and most useful
4. Then Feature 3 (Bulk Operations) - high user value
5. Finally Feature 1 (Conflict Detection) - more complex UI

**Want me to implement the frontend now?** I can create the React components for you.

