import React, { useState, useRef } from 'react';
import {
  Download,
  Upload,
  FileText,
  Save,
  XCircle,
  CheckCircle,
  AlertCircle,
  FileJson,
  Code,
  Archive
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from './ToastNotification';

/**
 * Enterprise Policy Import/Export Manager
 *
 * Features:
 * - Multi-format export (JSON, YAML, Cedar)
 * - Policy import with validation
 * - Dry-run mode for safe testing
 * - Conflict resolution strategies
 * - Backup creation and management
 *
 * @param {Object} props
 * @param {string} props.API_BASE_URL - Base URL for API calls
 * @param {Function} props.getAuthHeaders - Authentication headers provider
 * @param {Function} props.onImportComplete - Callback after successful import
 */
export const PolicyImportExport = ({ API_BASE_URL, getAuthHeaders, onImportComplete }) => {
  // Tab management
  const [activeTab, setActiveTab] = useState('export');

  // Export state
  const [exportFormat, setExportFormat] = useState('json');
  const [exportFilter, setExportFilter] = useState('all');
  const [exportPreview, setExportPreview] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);

  // Import state
  const [importFile, setImportFile] = useState(null);
  const [dryRun, setDryRun] = useState(true);
  const [conflictResolution, setConflictResolution] = useState('skip');
  const [importResult, setImportResult] = useState(null);
  const [importLoading, setImportLoading] = useState(false);

  // Backup state
  const [backupName, setBackupName] = useState('');
  const [backupLoading, setBackupLoading] = useState(false);

  // Refs
  const fileInputRef = useRef(null);

  // Hooks
  const { isDarkMode } = useTheme();
  const { toast } = useToast();

  /**
   * Load export preview
   */
  const loadExportPreview = async () => {
    try {
      setExportLoading(true);
      const statusParam = exportFilter !== 'all' ? `&status=${exportFilter}` : '';
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/export?format=${exportFormat}${statusParam}`,
        {
          credentials: "include",
          headers: getAuthHeaders()
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Export preview failed`);
      }

      const data = await response.text();

      // Truncate for preview
      const preview = data.length > 1000
        ? data.substring(0, 1000) + '\n\n... (truncated for preview)'
        : data;

      setExportPreview(preview);
    } catch (error) {
      toast.error(error.message || 'Failed to load preview', 'Error');
      console.error('Export preview error:', error);
    } finally {
      setExportLoading(false);
    }
  };

  /**
   * Download export file
   */
  const handleExport = async () => {
    try {
      setExportLoading(true);
      const statusParam = exportFilter !== 'all' ? `&status=${exportFilter}` : '';
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/export?format=${exportFormat}${statusParam}`,
        {
          credentials: "include",
          headers: getAuthHeaders()
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Export failed`);
      }

      const data = await response.text();

      // Create download
      const mimeTypes = {
        json: 'application/json',
        yaml: 'text/yaml',
        cedar: 'text/plain'
      };

      const blob = new Blob([data], { type: mimeTypes[exportFormat] || 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `policies_${exportFormat}_${Date.now()}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success(
        `Exported policies in ${exportFormat.toUpperCase()} format`,
        'Export Successful'
      );
    } catch (error) {
      toast.error(error.message || 'Export failed', 'Error');
      console.error('Export error:', error);
    } finally {
      setExportLoading(false);
    }
  };

  /**
   * Handle file selection
   */
  const handleFileSelect = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const validExtensions = ['.json', '.yaml', '.yml'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

      if (!validExtensions.includes(fileExtension)) {
        toast.error('Please select a JSON or YAML file', 'Invalid File Type');
        return;
      }

      setImportFile(file);
      setImportResult(null);
      toast.info(`Selected file: ${file.name}`, 'File Ready');
    }
  };

  /**
   * Handle policy import
   */
  const handleImport = async () => {
    if (!importFile) {
      toast.error('Please select a file to import', 'No File Selected');
      return;
    }

    try {
      setImportLoading(true);

      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const importData = e.target.result;

          const response = await fetch(
            `${API_BASE_URL}/api/governance/policies/import`,
            {
              method: 'POST',
              credentials: "include",
              headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
              body: JSON.stringify({
                import_data: importData,
                format: 'json', // Auto-detect or use file extension
                dry_run: dryRun,
                conflict_resolution: conflictResolution
              })
            }
          );

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Import failed`);
          }

          const result = await response.json();

          if (!result.success) {
            throw new Error(result.error || 'Import failed');
          }

          setImportResult(result);

          if (dryRun) {
            toast.info(
              `Preview: ${result.imported} policies would be imported, ${result.skipped} skipped`,
              'Import Preview'
            );
          } else {
            toast.success(
              `Imported ${result.imported} policies successfully`,
              'Import Complete'
            );
            if (onImportComplete) {
              onImportComplete();
            }
          }
        } catch (error) {
          toast.error(error.message || 'Import failed', 'Error');
          console.error('Import error:', error);
        } finally {
          setImportLoading(false);
        }
      };

      reader.onerror = () => {
        toast.error('Failed to read file', 'Error');
        setImportLoading(false);
      };

      reader.readAsText(importFile);
    } catch (error) {
      toast.error(error.message || 'Import failed', 'Error');
      console.error('Import error:', error);
      setImportLoading(false);
    }
  };

  /**
   * Create backup
   */
  const createBackup = async () => {
    try {
      setBackupLoading(true);

      const finalBackupName = backupName.trim() || `manual_backup_${Date.now()}`;

      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/backup`,
        {
          method: 'POST',
          credentials: "include",
          headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ backup_name: finalBackupName })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Backup creation failed`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Backup creation failed');
      }

      // Download backup file
      const blob = new Blob([result.backup_data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${result.backup_name}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success(
        `Backup created: ${result.backup_name} (${result.total_policies} policies)`,
        'Backup Successful'
      );

      setBackupName('');
    } catch (error) {
      toast.error(error.message || 'Backup creation failed', 'Error');
      console.error('Backup error:', error);
    } finally {
      setBackupLoading(false);
    }
  };

  return (
    <div className={`space-y-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold mb-2">Policy Import / Export</h2>
        <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          Download policies in multiple formats or upload policy files for import
        </p>
      </div>

      {/* Tab Navigation */}
      <div className={`border-b ${isDarkMode ? 'border-gray-600' : 'border-gray-300'}`}>
        <nav className="flex gap-2">
          {[
            { id: 'export', label: 'Export', icon: Download },
            { id: 'import', label: 'Import', icon: Upload },
            { id: 'backup', label: 'Backup', icon: Archive }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : `border-transparent ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'}`
              }`}
              aria-label={`Switch to ${tab.label} tab`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Export Tab */}
      {activeTab === 'export' && (
        <div className={`rounded-lg border p-6 space-y-6 ${
          isDarkMode ? 'bg-slate-700 border-slate-600' : 'bg-white border-gray-300'
        }`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Format Selector */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Export Format
              </label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  isDarkMode
                    ? 'bg-slate-600 border-slate-500 text-white'
                    : 'bg-white border-gray-300'
                }`}
              >
                <option value="json">JSON - JavaScript Object Notation</option>
                <option value="yaml">YAML - Human-Readable Format</option>
                <option value="cedar">Cedar - Policy Language</option>
              </select>
            </div>

            {/* Filter Selector */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Filter Policies
              </label>
              <select
                value={exportFilter}
                onChange={(e) => setExportFilter(e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  isDarkMode
                    ? 'bg-slate-600 border-slate-500 text-white'
                    : 'bg-white border-gray-300'
                }`}
              >
                <option value="all">All Policies</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
              </select>
            </div>
          </div>

          {/* Preview Button */}
          <button
            onClick={loadExportPreview}
            disabled={exportLoading}
            className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <FileText className="h-4 w-4" />
            {exportLoading ? 'Loading Preview...' : 'Load Preview'}
          </button>

          {/* Preview Area */}
          {exportPreview && (
            <div className={`rounded-lg p-4 ${
              isDarkMode ? 'bg-slate-800' : 'bg-gray-50'
            }`}>
              <p className="text-sm font-medium mb-2 flex items-center gap-2">
                <FileJson className="h-4 w-4" />
                Preview:
              </p>
              <pre className={`text-xs overflow-auto max-h-64 p-3 rounded ${
                isDarkMode ? 'bg-slate-900' : 'bg-white'
              }`}>
                {exportPreview}
              </pre>
            </div>
          )}

          {/* Export Button */}
          <button
            onClick={handleExport}
            disabled={exportLoading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
          >
            <Download className="h-4 w-4" />
            {exportLoading ? 'Exporting...' : 'Download Export File'}
          </button>
        </div>
      )}

      {/* Import Tab */}
      {activeTab === 'import' && (
        <div className={`rounded-lg border p-6 space-y-6 ${
          isDarkMode ? 'bg-slate-700 border-slate-600' : 'bg-white border-gray-300'
        }`}>
          {/* File Upload Dropzone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDarkMode
                ? 'border-slate-500 hover:border-blue-500 bg-slate-800'
                : 'border-gray-300 hover:border-blue-500 bg-gray-50'
            }`}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                fileInputRef.current?.click();
              }
            }}
            aria-label="Click to upload file"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.yaml,.yml"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload className={`h-12 w-12 mx-auto mb-4 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-500'
            }`} />
            <p className="text-lg font-medium mb-2">Drop file here or click to browse</p>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Supports JSON and YAML formats
            </p>
          </div>

          {/* Selected File */}
          {importFile && (
            <div className={`flex items-center justify-between p-3 rounded-lg ${
              isDarkMode ? 'bg-blue-900' : 'bg-blue-50'
            }`}>
              <div className="flex items-center gap-3">
                <FileJson className="h-5 w-5 text-blue-500" />
                <div>
                  <p className="font-medium">{importFile.name}</p>
                  <p className="text-xs opacity-75">
                    {(importFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setImportFile(null);
                  setImportResult(null);
                }}
                className="p-1 rounded hover:bg-black hover:bg-opacity-10"
                aria-label="Remove file"
              >
                <XCircle className="h-5 w-5 text-red-500" />
              </button>
            </div>
          )}

          {importFile && (
            <>
              {/* Import Options */}
              <div className="space-y-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={(e) => setDryRun(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium">
                    Dry Run (preview without saving changes)
                  </span>
                </label>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Conflict Resolution Strategy
                  </label>
                  <select
                    value={conflictResolution}
                    onChange={(e) => setConflictResolution(e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      isDarkMode
                        ? 'bg-slate-600 border-slate-500 text-white'
                        : 'bg-white border-gray-300'
                    }`}
                  >
                    <option value="skip">Skip Existing Policies</option>
                    <option value="overwrite">Overwrite Existing Policies</option>
                    <option value="merge">Merge with Existing Policies</option>
                  </select>
                  <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    How to handle policies that already exist in the system
                  </p>
                </div>
              </div>

              {/* Import Button */}
              <button
                onClick={handleImport}
                disabled={importLoading}
                className={`w-full px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2 font-medium ${
                  dryRun
                    ? 'bg-orange-600 hover:bg-orange-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {importLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"></div>
                    {dryRun ? 'Previewing...' : 'Importing...'}
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    {dryRun ? 'Preview Import' : 'Import Policies'}
                  </>
                )}
              </button>
            </>
          )}

          {/* Import Results */}
          {importResult && (
            <div className={`rounded-lg border p-4 ${
              importResult.success
                ? isDarkMode ? 'bg-green-900 border-green-500' : 'bg-green-50 border-green-500'
                : isDarkMode ? 'bg-red-900 border-red-500' : 'bg-red-50 border-red-500'
            }`}>
              <div className="flex items-start gap-3">
                {importResult.success ? (
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="font-semibold mb-2">
                    {importResult.dry_run ? 'Import Preview' : 'Import Results'}
                  </p>
                  <div className="space-y-1 text-sm">
                    <p>✓ Processed: {importResult.total_processed} policies</p>
                    <p>✓ Imported: {importResult.imported} policies</p>
                    <p>⊘ Skipped: {importResult.skipped} policies</p>
                    <p>✗ Errors: {importResult.errors} policies</p>
                  </div>

                  {importResult.error_details && importResult.error_details.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-current border-opacity-20">
                      <p className="font-medium mb-2">Errors:</p>
                      <ul className="space-y-1 text-xs">
                        {importResult.error_details.map((err, idx) => (
                          <li key={idx} className="flex gap-2">
                            <span>•</span>
                            <span>{err.policy_name}: {err.errors?.join(', ')}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Backup Tab */}
      {activeTab === 'backup' && (
        <div className={`rounded-lg border p-6 space-y-6 ${
          isDarkMode ? 'bg-slate-700 border-slate-600' : 'bg-white border-gray-300'
        }`}>
          <div>
            <h3 className="text-lg font-bold mb-2">Create Policy Backup</h3>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Creates a full backup of all policies in JSON format
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Backup Name (optional)
            </label>
            <input
              type="text"
              value={backupName}
              onChange={(e) => setBackupName(e.target.value)}
              placeholder="e.g., pre_deployment_backup"
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                isDarkMode
                  ? 'bg-slate-600 border-slate-500 text-white placeholder-gray-400'
                  : 'bg-white border-gray-300 placeholder-gray-500'
              }`}
            />
            <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Leave empty to auto-generate a timestamped name
            </p>
          </div>

          <button
            onClick={createBackup}
            disabled={backupLoading}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
          >
            {backupLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"></div>
                Creating Backup...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Create Backup Now
              </>
            )}
          </button>

          <div className={`rounded-lg p-4 ${
            isDarkMode ? 'bg-blue-900 bg-opacity-20 border border-blue-500' : 'bg-blue-50 border border-blue-300'
          }`}>
            <p className="text-sm">
              <strong>Tip:</strong> Create regular backups before making bulk changes or deploying
              new policies to production. Backups can be restored using the import feature.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyImportExport;
