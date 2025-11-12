# Enterprise Frontend Implementation Plan - Policy Management Features 1-3

**Date:** 2025-11-04
**Status:** READY FOR IMPLEMENTATION
**Backend Status:** ✅ COMPLETE (11/11 tests passed)
**Frontend Analysis:** ✅ COMPLETE (Architecture fully understood)
**Author:** OW-KAI Engineering Team

---

## Executive Summary

Based on comprehensive frontend architecture analysis, this document provides an **enterprise-level implementation plan** for adding 3 policy management features to the OW AI Enterprise Platform.

### Implementation Approach

**NOT doing:** Quick fixes, shortcuts, or pattern violations
**DOING:** Enterprise-grade components following exact application patterns

### Key Architectural Decisions

1. **Component Organization:** Create 3 separate component files for maintainability
2. **Integration Point:** Add new tabs to `EnhancedPolicyTabComplete.jsx`
3. **API Pattern:** Use standard `fetch()` with `credentials: "include"` + `getAuthHeaders()`
4. **Styling:** Follow existing Tailwind + `isDarkMode` theme pattern
5. **State Management:** Local component state with `useState` hooks
6. **Error Handling:** Toast notifications for user feedback
7. **Accessibility:** Full screen reader and keyboard navigation support

---

## Architecture Analysis Summary

### Your Application Patterns (MUST FOLLOW)

✅ **Routing:** State-based view switching (NO React Router)
✅ **State Management:** React Context (global) + useState (local)
✅ **Authentication:** Cookie-based with CSRF protection
✅ **API Calls:** `credentials: "include"` + `getAuthHeaders()`
✅ **Styling:** Tailwind CSS with dark mode via `isDarkMode`
✅ **Icons:** lucide-react library
✅ **Notifications:** Toast provider for user feedback
✅ **Loading States:** Component-level loading indicators
✅ **Error Handling:** Try-catch with toast.error()

### Integration Point

**File:** `owkai-pilot-frontend/src/components/EnhancedPolicyTabComplete.jsx`

**Current Tabs:**
- List (policies list)
- Analytics (policy metrics)
- Test (policy testing)
- Compliance (compliance dashboard)
- Create (visual policy builder)

**Adding 3 New Tabs:**
- **Conflicts** (Feature 1: Conflict Detection)
- **Import/Export** (Feature 2: Import/Export)
- **Bulk Actions** (Feature 3: Bulk Operations - integrated into List view)

---

## Feature 1: Policy Conflict Detection

### Component Design

**File:** `owkai-pilot-frontend/src/components/PolicyConflictDetector.jsx`

**Purpose:** Detect and display policy conflicts with actionable resolution suggestions

### Component Structure

```javascript
import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Shield, RefreshCw, XCircle } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from './ToastNotification';

export const PolicyConflictDetector = ({ API_BASE_URL, getAuthHeaders }) => {
  // State management
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastScan, setLastScan] = useState(null);
  const [selectedConflict, setSelectedConflict] = useState(null);

  const { isDarkMode } = useTheme();
  const { toast } = useToast();

  // Auto-scan on mount
  useEffect(() => {
    analyzeConflicts();
  }, []);

  // Main Features:
  // 1. System-wide conflict analysis
  // 2. Conflict severity visualization
  // 3. Detailed conflict cards
  // 4. Resolution suggestions
  // 5. Manual re-scan capability
};
```

### UI Sections

#### 1. Header with Scan Button
```jsx
<div className="flex justify-between items-center mb-6">
  <div>
    <h2 className="text-2xl font-bold">Policy Conflict Detection</h2>
    <p className="text-sm text-gray-500">
      Last scan: {lastScan ? formatTime(lastScan) : 'Never'}
    </p>
  </div>
  <button
    onClick={analyzeConflicts}
    disabled={loading}
    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
  >
    <RefreshCw className={`inline h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
    {loading ? 'Scanning...' : 'Analyze All Policies'}
  </button>
</div>
```

#### 2. Summary Dashboard
```jsx
<div className="grid grid-cols-4 gap-4 mb-6">
  <MetricCard
    title="Total Conflicts"
    value={conflicts.length}
    color="bg-red-100 dark:bg-red-900"
  />
  <MetricCard
    title="Critical"
    value={conflicts.filter(c => c.severity === 'critical').length}
    color="bg-red-500"
  />
  <MetricCard
    title="High"
    value={conflicts.filter(c => c.severity === 'high').length}
    color="bg-orange-500"
  />
  <MetricCard
    title="Medium"
    value={conflicts.filter(c => c.severity === 'medium').length}
    color="bg-yellow-500"
  />
</div>
```

#### 3. Conflict List
```jsx
<div className="space-y-3">
  {conflicts.map((conflict, idx) => (
    <ConflictCard
      key={idx}
      conflict={conflict}
      onClick={() => setSelectedConflict(conflict)}
      isDarkMode={isDarkMode}
    />
  ))}
</div>
```

#### 4. Conflict Detail Modal
```jsx
{selectedConflict && (
  <ConflictDetailModal
    conflict={selectedConflict}
    onClose={() => setSelectedConflict(null)}
    isDarkMode={isDarkMode}
  />
)}
```

### API Integration

```javascript
const analyzeConflicts = async () => {
  try {
    setLoading(true);
    const response = await fetch(
      `${API_BASE_URL}/api/governance/policies/conflicts/analyze`,
      {
        credentials: "include",
        headers: getAuthHeaders()
      }
    );

    if (!response.ok) throw new Error('Failed to analyze conflicts');

    const data = await response.json();
    setConflicts(data.conflicts || []);
    setLastScan(new Date());

    if (data.total_conflicts > 0) {
      toast.warning(`Found ${data.total_conflicts} conflicts`, 'Conflicts Detected');
    } else {
      toast.success('No conflicts detected', 'All Clear');
    }
  } catch (error) {
    toast.error('Failed to analyze conflicts', 'Error');
    console.error('Conflict analysis error:', error);
  } finally {
    setLoading(false);
  }
};
```

### Severity Color Mapping

```javascript
const getSeverityColor = (severity) => {
  const colors = {
    critical: {
      light: 'bg-red-50 border-red-500 text-red-900',
      dark: 'bg-red-900 border-red-500 text-red-100',
      badge: 'bg-red-500 text-white'
    },
    high: {
      light: 'bg-orange-50 border-orange-500 text-orange-900',
      dark: 'bg-orange-900 border-orange-500 text-orange-100',
      badge: 'bg-orange-500 text-white'
    },
    medium: {
      light: 'bg-yellow-50 border-yellow-500 text-yellow-900',
      dark: 'bg-yellow-900 border-yellow-500 text-yellow-100',
      badge: 'bg-yellow-500 text-white'
    },
    low: {
      light: 'bg-blue-50 border-blue-500 text-blue-900',
      dark: 'bg-blue-900 border-blue-500 text-blue-100',
      badge: 'bg-blue-500 text-white'
    }
  };
  return colors[severity] || colors.medium;
};
```

### Accessibility Features

- ARIA labels for all interactive elements
- Keyboard navigation support
- Screen reader announcements for scan results
- Focus management in modals

---

## Feature 2: Policy Import/Export

### Component Design

**File:** `owkai-pilot-frontend/src/components/PolicyImportExport.jsx`

**Purpose:** Download policies in multiple formats and upload policy files

### Component Structure

```javascript
export const PolicyImportExport = ({ API_BASE_URL, getAuthHeaders }) => {
  // Tabs: Export, Import, Backups
  const [activeTab, setActiveTab] = useState('export');

  // Export state
  const [exportFormat, setExportFormat] = useState('json');
  const [exportFilter, setExportFilter] = useState('all');
  const [exportPreview, setExportPreview] = useState(null);

  // Import state
  const [importFile, setImportFile] = useState(null);
  const [dryRun, setDryRun] = useState(true);
  const [conflictResolution, setConflictResolution] = useState('skip');
  const [importResult, setImportResult] = useState(null);

  // Backup state
  const [backups, setBackups] = useState([]);

  const { isDarkMode } = useTheme();
  const { toast } = useToast();
};
```

### UI Sections

#### 1. Tab Navigation
```jsx
<div className="border-b mb-6">
  <nav className="flex gap-2">
    {['export', 'import', 'backups'].map(tab => (
      <button
        key={tab}
        onClick={() => setActiveTab(tab)}
        className={`px-4 py-3 border-b-2 capitalize ${
          activeTab === tab
            ? 'border-blue-600 text-blue-600 font-semibold'
            : 'border-transparent text-gray-600'
        }`}
      >
        {tab}
      </button>
    ))}
  </nav>
</div>
```

#### 2. Export Tab
```jsx
{activeTab === 'export' && (
  <div className="space-y-6">
    {/* Format Selector */}
    <div>
      <label className="block text-sm font-medium mb-2">Export Format</label>
      <select
        value={exportFormat}
        onChange={(e) => setExportFormat(e.target.value)}
        className="w-full px-3 py-2 border rounded-md"
      >
        <option value="json">JSON</option>
        <option value="yaml">YAML</option>
        <option value="cedar">Cedar Policy Language</option>
      </select>
    </div>

    {/* Filter Selector */}
    <div>
      <label className="block text-sm font-medium mb-2">Filter</label>
      <select
        value={exportFilter}
        onChange={(e) => setExportFilter(e.target.value)}
        className="w-full px-3 py-2 border rounded-md"
      >
        <option value="all">All Policies</option>
        <option value="active">Active Only</option>
        <option value="inactive">Inactive Only</option>
      </select>
    </div>

    {/* Preview */}
    {exportPreview && (
      <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
        <p className="text-sm font-medium mb-2">Preview:</p>
        <pre className="text-xs overflow-auto max-h-64">
          {exportPreview}
        </pre>
      </div>
    )}

    {/* Export Button */}
    <button
      onClick={handleExport}
      className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      Download Export File
    </button>
  </div>
)}
```

#### 3. Import Tab
```jsx
{activeTab === 'import' && (
  <div className="space-y-6">
    {/* File Upload Dropzone */}
    <div
      className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-blue-500"
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,.yaml,.yml"
        onChange={handleFileSelect}
        className="hidden"
      />
      <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
      <p className="text-lg font-medium">Drop file here or click to browse</p>
      <p className="text-sm text-gray-500">Supports JSON and YAML formats</p>
    </div>

    {importFile && (
      <>
        <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900 rounded-lg">
          <span className="text-sm font-medium">{importFile.name}</span>
          <button onClick={() => setImportFile(null)}>
            <XCircle className="h-5 w-5 text-red-500" />
          </button>
        </div>

        {/* Import Options */}
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="mr-2"
            />
            Dry Run (test without saving)
          </label>

          <div>
            <label className="block text-sm font-medium mb-2">Conflict Resolution</label>
            <select
              value={conflictResolution}
              onChange={(e) => setConflictResolution(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="skip">Skip Existing</option>
              <option value="overwrite">Overwrite Existing</option>
              <option value="merge">Merge Changes</option>
            </select>
          </div>
        </div>

        {/* Import Button */}
        <button
          onClick={handleImport}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          {dryRun ? 'Preview Import' : 'Import Policies'}
        </button>
      </>
    )}

    {/* Import Results */}
    {importResult && (
      <ImportResultsCard result={importResult} isDarkMode={isDarkMode} />
    )}
  </div>
)}
```

#### 4. Backups Tab
```jsx
{activeTab === 'backups' && (
  <div className="space-y-4">
    <button
      onClick={createBackup}
      className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
    >
      Create Backup Now
    </button>

    <div className="space-y-2">
      {backups.map((backup, idx) => (
        <BackupCard key={idx} backup={backup} onRestore={handleRestore} />
      ))}
    </div>
  </div>
)}
```

### API Integration

```javascript
// Export
const handleExport = async () => {
  try {
    const statusParam = exportFilter !== 'all' ? `&status=${exportFilter}` : '';
    const response = await fetch(
      `${API_BASE_URL}/api/governance/policies/export?format=${exportFormat}${statusParam}`,
      {
        credentials: "include",
        headers: getAuthHeaders()
      }
    );

    const data = await response.text();

    // Trigger download
    const blob = new Blob([data], {
      type: exportFormat === 'json' ? 'application/json' : 'text/plain'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `policies_${exportFormat}_${Date.now()}.${exportFormat}`;
    a.click();
    URL.revokeObjectURL(url);

    toast.success(`Exported policies in ${exportFormat.toUpperCase()} format`);
  } catch (error) {
    toast.error('Export failed');
    console.error('Export error:', error);
  }
};

// Import
const handleImport = async () => {
  try {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const importData = e.target.result;

      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/import`,
        {
          method: 'POST',
          credentials: "include",
          headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({
            import_data: importData,
            format: 'json',
            dry_run: dryRun,
            conflict_resolution: conflictResolution
          })
        }
      );

      const result = await response.json();
      setImportResult(result);

      if (result.success) {
        toast.success(`${dryRun ? 'Preview' : 'Imported'}: ${result.imported} policies`);
      }
    };
    reader.readAsText(importFile);
  } catch (error) {
    toast.error('Import failed');
    console.error('Import error:', error);
  }
};

// Backup
const createBackup = async () => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/governance/policies/backup`,
      {
        method: 'POST',
        credentials: "include",
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          backup_name: `manual_backup_${Date.now()}`
        })
      }
    );

    const result = await response.json();

    if (result.success) {
      toast.success('Backup created successfully');
      // Download backup file
      const blob = new Blob([result.backup_data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${result.backup_name}.json`;
      a.click();
    }
  } catch (error) {
    toast.error('Backup creation failed');
  }
};
```

---

## Feature 3: Bulk Policy Operations

### Component Design

**File:** `owkai-pilot-frontend/src/components/PolicyBulkActions.jsx`

**Purpose:** Select multiple policies and perform bulk operations

### Integration Approach

**Location:** Enhance existing policy list view in `EnhancedPolicyTabComplete.jsx`

**NOT creating:** Separate tab
**DOING:** Adding bulk selection and action toolbar to existing "list" view

### Component Structure

```javascript
export const PolicyBulkActions = ({
  selectedPolicies,
  onBulkComplete,
  API_BASE_URL,
  getAuthHeaders
}) => {
  const [action, setAction] = useState(null);
  const [reason, setReason] = useState('');
  const [newPriority, setNewPriority] = useState(100);
  const [showModal, setShowModal] = useState(false);

  const { toast } = useToast();

  // Actions: enable, disable, delete, update-priority
};
```

### UI Sections

#### 1. Selection Toolbar (appears when policies selected)
```jsx
{selectedPolicies.length > 0 && (
  <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white dark:bg-slate-800 shadow-2xl rounded-lg p-4 flex items-center gap-4 z-50">
    <span className="font-semibold">
      {selectedPolicies.length} selected
    </span>

    <div className="h-6 w-px bg-gray-300"></div>

    <button
      onClick={() => openBulkAction('enable')}
      className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700"
    >
      <CheckCircle className="inline h-4 w-4 mr-1" />
      Enable
    </button>

    <button
      onClick={() => openBulkAction('disable')}
      className="px-3 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
    >
      <XCircle className="inline h-4 w-4 mr-1" />
      Disable
    </button>

    <button
      onClick={() => openBulkAction('priority')}
      className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
    >
      <ArrowUpDown className="inline h-4 w-4 mr-1" />
      Update Priority
    </button>

    <button
      onClick={() => openBulkAction('delete')}
      className="px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700"
    >
      <Trash2 className="inline h-4 w-4 mr-1" />
      Delete
    </button>

    <button
      onClick={() => onClearSelection()}
      className="ml-auto text-gray-500 hover:text-gray-700"
    >
      Cancel
    </button>
  </div>
)}
```

#### 2. Confirmation Modal
```jsx
{showModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
    <div className={`max-w-md w-full mx-4 rounded-lg p-6 ${
      isDarkMode ? 'bg-slate-800' : 'bg-white'
    }`}>
      <h3 className="text-xl font-bold mb-4">
        {getBulkActionTitle(action)}
      </h3>

      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-3">
          This will affect {selectedPolicies.length} policies:
        </p>
        <ul className="max-h-32 overflow-auto text-sm space-y-1">
          {selectedPolicies.map(p => (
            <li key={p.id} className="flex items-center">
              <Shield className="h-3 w-3 mr-2 text-blue-500" />
              {p.policy_name}
            </li>
          ))}
        </ul>
      </div>

      {/* Action-specific inputs */}
      {action === 'priority' && (
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">New Priority</label>
          <input
            type="number"
            value={newPriority}
            onChange={(e) => setNewPriority(parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-md"
            min="1"
            max="1000"
          />
        </div>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Reason {action !== 'priority' && <span className="text-red-500">*</span>}
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="w-full px-3 py-2 border rounded-md"
          rows="3"
          placeholder="Enter reason for this bulk operation..."
        />
      </div>

      {action === 'delete' && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">
            ⚠️ This will soft-delete the selected policies. A backup will be created automatically.
          </p>
        </div>
      )}

      <div className="flex justify-end gap-2">
        <button
          onClick={() => setShowModal(false)}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={executeBulkAction}
          disabled={!reason && action !== 'priority'}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Confirm {getBulkActionLabel(action)}
        </button>
      </div>
    </div>
  </div>
)}
```

### API Integration

```javascript
const executeBulkAction = async () => {
  try {
    const policyIds = selectedPolicies.map(p => p.id);
    let endpoint, body;

    switch (action) {
      case 'enable':
      case 'disable':
        endpoint = '/api/governance/policies/bulk-update-status';
        body = {
          policy_ids: policyIds,
          new_status: action === 'enable' ? 'active' : 'inactive',
          reason: reason
        };
        break;

      case 'priority':
        endpoint = '/api/governance/policies/bulk-update-priority';
        body = {
          updates: policyIds.map(id => ({
            policy_id: id,
            priority: newPriority
          }))
        };
        break;

      case 'delete':
        endpoint = '/api/governance/policies/bulk-delete';
        body = {
          policy_ids: policyIds,
          confirmation: 'DELETE',
          create_backup: true
        };
        break;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      credentials: "include",
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const result = await response.json();

    if (result.success) {
      toast.success(
        `Successfully ${getActionVerb(action)} ${result.updated_count || result.deleted_count} policies`,
        'Bulk Operation Complete'
      );
      setShowModal(false);
      onBulkComplete(); // Refresh policy list
    } else {
      toast.error(result.error || 'Bulk operation failed');
    }
  } catch (error) {
    toast.error('Failed to execute bulk operation');
    console.error('Bulk operation error:', error);
  }
};
```

### Integration into Policy List

**Modify:** `EnhancedPolicyTabComplete.jsx` list view

```javascript
// Add selection state
const [selectedPolicies, setSelectedPolicies] = useState([]);

// Add selection handlers
const togglePolicySelection = (policy) => {
  setSelectedPolicies(prev =>
    prev.find(p => p.id === policy.id)
      ? prev.filter(p => p.id !== policy.id)
      : [...prev, policy]
  );
};

const toggleSelectAll = () => {
  setSelectedPolicies(
    selectedPolicies.length === policies.length ? [] : [...policies]
  );
};

// Modify policy table to include checkboxes
<table>
  <thead>
    <tr>
      <th>
        <input
          type="checkbox"
          checked={selectedPolicies.length === policies.length}
          onChange={toggleSelectAll}
        />
      </th>
      <th>Policy Name</th>
      <th>Status</th>
      <th>Priority</th>
    </tr>
  </thead>
  <tbody>
    {policies.map(policy => (
      <tr key={policy.id}>
        <td>
          <input
            type="checkbox"
            checked={selectedPolicies.some(p => p.id === policy.id)}
            onChange={() => togglePolicySelection(policy)}
          />
        </td>
        <td>{policy.policy_name}</td>
        <td>{policy.status}</td>
        <td>{policy.priority}</td>
      </tr>
    ))}
  </tbody>
</table>

// Add bulk actions toolbar
<PolicyBulkActions
  selectedPolicies={selectedPolicies}
  onBulkComplete={() => {
    setSelectedPolicies([]);
    onRefreshPolicies();
  }}
  API_BASE_URL={API_BASE_URL}
  getAuthHeaders={getAuthHeaders}
/>
```

---

## Implementation Plan

### Phase 1: Component Creation (3-4 hours)

**Step 1:** Create PolicyConflictDetector.jsx
**Step 2:** Create PolicyImportExport.jsx
**Step 3:** Create PolicyBulkActions.jsx

Each component includes:
- ✅ Full TypeScript-style JSDoc comments
- ✅ Comprehensive error handling
- ✅ Dark mode support
- ✅ Loading states
- ✅ Accessibility features
- ✅ Toast notifications

### Phase 2: Integration (1-2 hours)

**Step 4:** Integrate into EnhancedPolicyTabComplete.jsx
- Add new tabs for Conflicts and Import/Export
- Integrate bulk actions into list view
- Update tab navigation
- Add routing logic

### Phase 3: Testing (2-3 hours)

**Step 5:** Test all features
- ✅ Light mode testing
- ✅ Dark mode testing
- ✅ Mobile responsiveness
- ✅ Keyboard navigation
- ✅ Screen reader compatibility
- ✅ Error scenarios
- ✅ Edge cases (no data, API failures, etc.)

### Phase 4: Documentation & Deployment (1 hour)

**Step 6:** Create documentation
**Step 7:** Deploy to production
**Step 8:** User acceptance testing

---

## Quality Checklist

### Code Quality
- [ ] Follows exact application patterns
- [ ] Uses existing utilities (fetchWithAuth, getAuthHeaders)
- [ ] Consistent with theme system
- [ ] Proper error handling
- [ ] JSDoc comments for all functions
- [ ] No console.log in production code

### UI/UX Quality
- [ ] Dark mode support verified
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Loading states for all async operations
- [ ] Clear error messages
- [ ] Toast notifications for user feedback
- [ ] Confirmation modals for destructive actions

### Accessibility
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation works
- [ ] Focus management in modals
- [ ] Screen reader announcements
- [ ] Color contrast meets WCAG AA

### Integration
- [ ] Props match parent component interface
- [ ] API endpoints correct
- [ ] Authentication headers included
- [ ] CSRF protection in place
- [ ] No breaking changes to existing code

---

## Files to Create/Modify

### New Files (3)
1. `owkai-pilot-frontend/src/components/PolicyConflictDetector.jsx`
2. `owkai-pilot-frontend/src/components/PolicyImportExport.jsx`
3. `owkai-pilot-frontend/src/components/PolicyBulkActions.jsx`

### Modified Files (1)
1. `owkai-pilot-frontend/src/components/EnhancedPolicyTabComplete.jsx`
   - Add imports for new components
   - Add new tabs to tab array
   - Add routing in renderView()
   - Integrate bulk actions into list view

---

## Risk Mitigation

### Potential Issues & Solutions

**Issue:** Breaking existing policy management
**Mitigation:** All changes are additive, no modifications to existing features

**Issue:** Theme inconsistencies
**Mitigation:** Use existing theme hooks and color patterns

**Issue:** API authentication failures
**Mitigation:** Follow exact cookie + header pattern from existing components

**Issue:** Performance with large policy lists
**Mitigation:** Use pagination if > 100 policies, optimize conflict detection

---

## Success Criteria

✅ **Feature 1 (Conflicts):** Users can see all policy conflicts with severity levels and resolution suggestions
✅ **Feature 2 (Import/Export):** Users can download policies in 3 formats and upload policy files
✅ **Feature 3 (Bulk Actions):** Users can select multiple policies and perform bulk operations

✅ **Quality:** All features work in light and dark mode
✅ **Accessibility:** Full keyboard navigation and screen reader support
✅ **Integration:** Seamless integration with existing policy management UI
✅ **Testing:** 100% feature coverage with manual testing

---

## Next Steps

Ready to implement? I will:

1. Create 3 component files with full enterprise-grade code
2. Integrate into EnhancedPolicyTabComplete
3. Test all features locally
4. Provide testing checklist
5. Deploy to production

**Time Estimate:** 6-8 hours total for enterprise-level implementation

**Proceed with implementation?**

