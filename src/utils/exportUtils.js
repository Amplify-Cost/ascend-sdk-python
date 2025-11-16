/**
 * Enterprise Export Utilities for Agent Activity Feed
 *
 * Supports CSV, JSON, and PDF export formats
 * Includes compliance report templates (SOX, PCI-DSS, HIPAA, GDPR)
 */

/**
 * Export activities to CSV format
 * @param {Array} activities - Array of activity objects
 * @param {Array} columns - Column configuration (optional)
 * @returns {void} Downloads CSV file
 */
export const exportToCSV = (activities, columns = null) => {
  if (!activities || activities.length === 0) {
    alert('No data to export');
    return;
  }

  // Default columns if not specified
  const defaultColumns = [
    { key: 'id', label: 'ID' },
    { key: 'timestamp', label: 'Timestamp', format: (val) => new Date(val * 1000).toISOString() },
    { key: 'agent_id', label: 'Agent ID' },
    { key: 'user_id', label: 'User ID' },
    { key: 'action_type', label: 'Action Type' },
    { key: 'tool_name', label: 'Tool' },
    { key: 'description', label: 'Description' },
    { key: 'risk_level', label: 'Risk Level' },
    { key: 'cvss_score', label: 'CVSS Score' },
    { key: 'cvss_severity', label: 'CVSS Severity' },
    { key: 'risk_score', label: 'Risk Score (0-100)' },
    { key: 'mitre_tactic', label: 'MITRE Tactic' },
    { key: 'mitre_technique', label: 'MITRE Technique' },
    { key: 'nist_control', label: 'NIST Control' },
    { key: 'status', label: 'Status' },
    { key: 'approved', label: 'Approved' },
    { key: 'approved_by', label: 'Approved By' },
    { key: 'reviewed_by', label: 'Reviewed By' },
    { key: 'current_approval_level', label: 'Current Approval Level' },
    { key: 'required_approval_level', label: 'Required Approval Level' },
    { key: 'target_system', label: 'Target System' },
    { key: 'target_resource', label: 'Target Resource' },
    { key: 'recommendation', label: 'Recommendation' },
    { key: 'summary', label: 'AI Summary' },
  ];

  const selectedColumns = columns || defaultColumns;

  // Build CSV header
  const headers = selectedColumns.map(col => escapeCSV(col.label)).join(',');

  // Build CSV rows
  const rows = activities.map(activity => {
    return selectedColumns.map(col => {
      let value = activity[col.key];

      // Apply formatter if provided
      if (col.format && value !== null && value !== undefined) {
        value = col.format(value);
      }

      // Handle null/undefined
      if (value === null || value === undefined) {
        return '';
      }

      return escapeCSV(String(value));
    }).join(',');
  });

  const csv = [headers, ...rows].join('\n');

  // Download file
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `agent_activity_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Escape CSV special characters
 */
const escapeCSV = (str) => {
  if (typeof str !== 'string') return str;

  // If contains comma, quote, or newline, wrap in quotes and escape quotes
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }

  return str;
};

/**
 * Export activities to JSON format
 * @param {Array} activities - Array of activity objects
 * @param {boolean} pretty - Pretty print JSON (default: true)
 * @returns {void} Downloads JSON file
 */
export const exportToJSON = (activities, pretty = true) => {
  if (!activities || activities.length === 0) {
    alert('No data to export');
    return;
  }

  const json = pretty
    ? JSON.stringify(activities, null, 2)
    : JSON.stringify(activities);

  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `agent_activity_${new Date().toISOString().split('T')[0]}.json`);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Export activities to PDF format
 * Note: Requires jsPDF and jspdf-autotable libraries
 * Run: npm install jspdf jspdf-autotable
 *
 * @param {Array} activities - Array of activity objects
 * @param {Object} options - Export options
 * @returns {void} Downloads PDF file
 */
export const exportToPDF = async (activities, options = {}) => {
  if (!activities || activities.length === 0) {
    alert('No data to export');
    return;
  }

  // Dynamic import to avoid bundle bloat if not used
  try {
    const jsPDF = (await import('jspdf')).default;
    const autoTable = (await import('jspdf-autotable')).default;

    const doc = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: 'a4'
    });

    // Add header
    doc.setFontSize(16);
    doc.text('Agent Activity Report', 14, 15);

    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 22);
    doc.text(`Total Activities: ${activities.length}`, 14, 27);

    if (options.title) {
      doc.setFontSize(12);
      doc.text(options.title, 14, 35);
    }

    // Prepare table data
    const tableData = activities.map(activity => [
      activity.id || '—',
      new Date((activity.timestamp || 0) * 1000).toLocaleDateString(),
      activity.agent_id || '—',
      activity.action_type || '—',
      activity.cvss_score !== null ? activity.cvss_score.toFixed(1) : '—',
      activity.risk_level || '—',
      activity.mitre_tactic || '—',
      activity.nist_control || '—',
      activity.status || '—',
      activity.approved ? 'Yes' : activity.approved === false ? 'No' : '—'
    ]);

    // Add table
    autoTable(doc, {
      head: [['ID', 'Date', 'Agent', 'Action', 'CVSS', 'Risk', 'MITRE', 'NIST', 'Status', 'Approved']],
      body: tableData,
      startY: options.title ? 40 : 32,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [37, 99, 235], textColor: 255 },
      alternateRowStyles: { fillColor: [245, 247, 250] },
      margin: { top: 10 }
    });

    // Add footer with page numbers
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.text(
        `Page ${i} of ${pageCount}`,
        doc.internal.pageSize.getWidth() / 2,
        doc.internal.pageSize.getHeight() - 10,
        { align: 'center' }
      );
    }

    // Save PDF
    doc.save(`agent_activity_${new Date().toISOString().split('T')[0]}.pdf`);
  } catch (error) {
    console.error('PDF export failed:', error);
    alert(`PDF export failed: ${error.message}. Please ensure jsPDF and jspdf-autotable are installed.`);
  }
};

/**
 * Generate compliance report (SOX, PCI-DSS, HIPAA, GDPR)
 * @param {Array} activities - Array of activity objects
 * @param {string} framework - Compliance framework (sox, pci-dss, hipaa, gdpr)
 * @returns {void} Downloads compliance report PDF
 */
export const generateComplianceReport = async (activities, framework = 'sox') => {
  if (!activities || activities.length === 0) {
    alert('No data to export');
    return;
  }

  // Filter activities relevant to compliance framework
  const complianceActivities = filterByCompliance(activities, framework);

  if (complianceActivities.length === 0) {
    alert(`No activities found for ${framework.toUpperCase()} compliance`);
    return;
  }

  // Framework-specific configuration
  const frameworkConfig = {
    sox: {
      title: 'SOX Compliance Report - IT General Controls',
      controls: ['AU-2', 'AU-3', 'AU-6', 'AU-12', 'AC-2', 'AC-6'],
      description: 'Sarbanes-Oxley Act audit trail for agent actions affecting financial systems'
    },
    'pci-dss': {
      title: 'PCI-DSS Compliance Report - Requirement 10',
      controls: ['AU-2', 'AU-3', 'AU-6', 'AC-2', 'AC-3', 'SC-8'],
      description: 'Payment Card Industry Data Security Standard - Track and monitor all access to network resources'
    },
    hipaa: {
      title: 'HIPAA Compliance Report - Security Rule',
      controls: ['AU-2', 'AU-3', 'AU-6', 'AC-2', 'AC-3', 'AC-4'],
      description: 'Health Insurance Portability and Accountability Act - PHI access audit trail'
    },
    gdpr: {
      title: 'GDPR Compliance Report - Article 32',
      controls: ['AU-2', 'AU-3', 'AU-6', 'AC-2', 'AC-3', 'AC-5'],
      description: 'General Data Protection Regulation - Personal data processing security measures'
    }
  };

  const config = frameworkConfig[framework] || frameworkConfig.sox;

  await exportToPDF(complianceActivities, {
    title: config.title
  });
};

/**
 * Filter activities by compliance framework
 */
const filterByCompliance = (activities, framework) => {
  const frameworkControls = {
    sox: ['AU-', 'AC-2', 'AC-6'],  // Audit and access controls
    'pci-dss': ['AU-', 'AC-', 'SC-'],  // Audit, access, system communications
    hipaa: ['AU-', 'AC-', 'PE-'],  // Audit, access, physical/environmental
    gdpr: ['AU-', 'AC-', 'SC-', 'SI-']  // Audit, access, communications, integrity
  };

  const controls = frameworkControls[framework] || frameworkControls.sox;

  return activities.filter(activity => {
    const nistControl = activity.nist_control || '';
    return controls.some(control => nistControl.startsWith(control));
  });
};

/**
 * Export utilities object
 */
const exportUtils = {
  exportToCSV,
  exportToJSON,
  exportToPDF,
  generateComplianceReport
};

export default exportUtils;
