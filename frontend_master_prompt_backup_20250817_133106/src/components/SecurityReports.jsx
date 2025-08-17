import React, { useState, useEffect } from "react";
import { useTheme } from "../contexts/ThemeContext";

const EnterpriseSecurityReports = ({ getAuthHeaders, user }) => {
  const { isDarkMode } = useTheme();
  const [reports, setReports] = useState([]);
  const [scheduledReports, setScheduledReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [activeTab, setActiveTab] = useState("library");
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [sortBy, setSortBy] = useState("date");

  const BASE_URL = "https://owai-production.up.railway.app";

  // Enterprise-level mock data
  const enterpriseReports = [
    {
      id: 1,
      title: "SOX Compliance Quarterly Report - Q3 2025",
      type: "compliance",
      classification: "Confidential",
      date: "2025-08-07",
      status: "completed",
      format: "PDF",
      size: "12.7 MB",
      pages: 47,
      description: "Comprehensive Sarbanes-Oxley compliance assessment including IT general controls, access management, and financial reporting controls",
      author: "Chief Compliance Officer",
      department: "Compliance",
      approver: "Board of Directors",
      tags: ["SOX", "quarterly", "compliance", "financial-controls"],
      distribution: ["CEO", "CFO", "Board", "External Auditors"],
      retentionPeriod: "7 years",
      securityLevel: "Restricted",
      lastAccessed: "2025-08-07T10:30:00Z",
      downloadCount: 15,
      complianceFrameworks: ["SOX", "COSO", "PCAOB"]
    },
    {
      id: 2,
      title: "Enterprise Security Risk Assessment - Annual",
      type: "risk",
      classification: "Highly Confidential",
      date: "2025-08-05",
      status: "completed",
      format: "PDF",
      size: "23.4 MB",
      pages: 89,
      description: "Comprehensive enterprise-wide security risk assessment covering cyber threats, operational risks, and business continuity planning",
      author: "Chief Information Security Officer",
      department: "Information Security",
      approver: "Chief Risk Officer",
      tags: ["risk-assessment", "annual", "cyber-security", "business-continuity"],
      distribution: ["C-Suite", "Board", "Department Heads"],
      retentionPeriod: "10 years",
      securityLevel: "Restricted",
      lastAccessed: "2025-08-06T14:22:00Z",
      downloadCount: 8,
      complianceFrameworks: ["ISO 27001", "NIST CSF", "COBIT"]
    },
    {
      id: 3,
      title: "HIPAA Security Compliance Audit Report",
      type: "compliance",
      classification: "Confidential",
      date: "2025-08-03",
      status: "completed",
      format: "PDF",
      size: "8.9 MB",
      pages: 34,
      description: "Health Insurance Portability and Accountability Act security rule compliance audit with recommendations for healthcare data protection",
      author: "Privacy Officer",
      department: "Legal & Compliance",
      approver: "Chief Privacy Officer",
      tags: ["HIPAA", "healthcare", "privacy", "PHI"],
      distribution: ["Healthcare Division", "Legal", "IT Security"],
      retentionPeriod: "6 years",
      securityLevel: "Restricted",
      lastAccessed: "2025-08-04T09:15:00Z",
      downloadCount: 12,
      complianceFrameworks: ["HIPAA", "HITECH", "State Privacy Laws"]
    },
    {
      id: 4,
      title: "AI Agent Security Performance Analysis - Monthly",
      type: "technical",
      classification: "Internal",
      date: "2025-08-06",
      status: "completed",
      format: "Excel",
      size: "5.2 MB",
      pages: null,
      description: "Monthly performance metrics and security analysis of AI agent operations including threat detection accuracy, false positive rates, and response times",
      author: "AI Security Team Lead",
      department: "AI Operations",
      approver: "Chief Technology Officer",
      tags: ["AI-agents", "performance", "monthly", "security-metrics"],
      distribution: ["AI Team", "Security Operations", "CTO Office"],
      retentionPeriod: "3 years",
      securityLevel: "Internal",
      lastAccessed: "2025-08-07T08:45:00Z",
      downloadCount: 25,
      complianceFrameworks: ["Internal Standards", "AI Ethics Framework"]
    },
    {
      id: 5,
      title: "PCI DSS Compliance Assessment Report",
      type: "compliance",
      classification: "Confidential", 
      date: "2025-08-01",
      status: "generating",
      format: "PDF",
      size: "—",
      pages: null,
      description: "Payment Card Industry Data Security Standard compliance assessment for payment processing systems and cardholder data environment",
      author: "Payment Security Team",
      department: "Financial Systems",
      approver: "Chief Financial Officer",
      tags: ["PCI-DSS", "payments", "cardholder-data", "compliance"],
      distribution: ["Finance", "IT Security", "QSA"],
      retentionPeriod: "3 years",
      securityLevel: "Restricted",
      lastAccessed: null,
      downloadCount: 0,
      complianceFrameworks: ["PCI DSS", "Payment Brand Requirements"]
    },
    {
      id: 6,
      title: "Enterprise Threat Intelligence Brief - Weekly",
      type: "intelligence",
      classification: "For Official Use Only",
      date: "2025-08-07",
      status: "completed",
      format: "PDF",
      size: "3.1 MB",
      pages: 18,
      description: "Weekly threat intelligence briefing covering emerging cyber threats, threat actor activities, and recommended defensive measures",
      author: "Threat Intelligence Team",
      department: "Cyber Threat Intelligence",
      approver: "Director of Intelligence",
      tags: ["threat-intel", "weekly", "APT", "IOCs"],
      distribution: ["Security Team", "SOC", "CISO Office"],
      retentionPeriod: "1 year",
      securityLevel: "Internal",
      lastAccessed: "2025-08-07T11:00:00Z",
      downloadCount: 42,
      complianceFrameworks: ["STIX/TAXII", "MITRE ATT&CK"]
    }
  ];

  const scheduledReportsData = [
    {
      id: 1,
      name: "SOX Quarterly Compliance",
      frequency: "Quarterly",
      nextRun: "2025-11-01",
      recipients: ["board@company.com", "cfo@company.com"],
      template: "SOX Compliance Template",
      status: "Active",
      lastGenerated: "2025-08-01"
    },
    {
      id: 2,
      name: "Weekly Threat Intelligence",
      frequency: "Weekly",
      nextRun: "2025-08-14",
      recipients: ["security@company.com", "soc@company.com"],
      template: "Threat Intel Brief",
      status: "Active",
      lastGenerated: "2025-08-07"
    },
    {
      id: 3,
      name: "Monthly Risk Dashboard",
      frequency: "Monthly",
      nextRun: "2025-09-01",
      recipients: ["cro@company.com", "executives@company.com"],
      template: "Risk Assessment Summary",
      status: "Active",
      lastGenerated: "2025-08-01"
    }
  ];

  useEffect(() => {
    loadReportsData();
  }, []);

  const loadReportsData = async () => {
    setLoading(true);
    try {
      // In real implementation, these would be API calls
      setReports(enterpriseReports);
      setScheduledReports(scheduledReportsData);
    } catch (error) {
      console.error("❌ Error loading reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (reportType, template) => {
    setGeneratingReport(true);
    try {
      // Simulate enterprise report generation
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const newReport = {
        id: Date.now(),
        title: `${template} - ${new Date().toLocaleDateString()}`,
        type: reportType.toLowerCase(),
        classification: "Internal",
        date: new Date().toISOString().split('T')[0],
        status: "completed",
        format: "PDF",
        size: "4.2 MB",
        pages: Math.floor(Math.random() * 30) + 10,
        description: `Auto-generated ${template.toLowerCase()} report for enterprise security analysis`,
        author: user?.email || "System Generated",
        department: "Information Security",
        approver: "Pending Review",
        tags: ["auto-generated", reportType.toLowerCase(), "enterprise"],
        distribution: ["Security Team"],
        retentionPeriod: "1 year",
        securityLevel: "Internal",
        lastAccessed: new Date().toISOString(),
        downloadCount: 0,
        complianceFrameworks: ["Internal Standards"]
      };
      
      setReports(prev => [newReport, ...prev]);
    } catch (error) {
      console.error("❌ Error generating report:", error);
    } finally {
      setGeneratingReport(false);
    }
  };

  const getClassificationBadge = (classification) => {
    const badges = {
      "Highly Confidential": "bg-red-100 text-red-800 border-red-200",
      "Confidential": "bg-orange-100 text-orange-800 border-orange-200",
      "For Official Use Only": "bg-yellow-100 text-yellow-800 border-yellow-200",
      "Internal": "bg-blue-100 text-blue-800 border-blue-200",
      "Public": "bg-green-100 text-green-800 border-green-200"
    };
    return badges[classification] || badges["Internal"];
  };

  const getStatusBadge = (status) => {
    const badges = {
      completed: "bg-green-100 text-green-800 border-green-200",
      generating: "bg-yellow-100 text-yellow-800 border-yellow-200",
      pending: "bg-blue-100 text-blue-800 border-blue-200",
      failed: "bg-red-100 text-red-800 border-red-200"
    };
    return badges[status] || badges.completed;
  };

  const getTypeIcon = (type) => {
    const icons = {
      compliance: "📋",
      risk: "⚠️", 
      technical: "⚙️",
      intelligence: "🕵️",
      executive: "👔",
      financial: "💰",
      audit: "🔍"
    };
    return icons[type] || "📄";
  };

  const filteredReports = reports
    .filter(report => {
      const matchesSearch = report.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           report.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           report.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesType = filterType === "all" || report.type === filterType;
      return matchesSearch && matchesType;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "date":
          return new Date(b.date) - new Date(a.date);
        case "title":
          return a.title.localeCompare(b.title);
        case "size":
          return parseFloat(b.size) - parseFloat(a.size);
        default:
          return 0;
      }
    });

  const renderReportLibrary = () => (
    <div className="space-y-6">
      {/* Search and Filter Controls */}
      <div className={`p-6 rounded-xl border transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-slate-700 border-slate-600' 
          : 'bg-white border-gray-300 shadow-sm'
      }`}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={`px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600 text-white' 
                : 'bg-white border-gray-300 text-gray-900'
            }`}
          />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className={`px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600 text-white' 
                : 'bg-white border-gray-300 text-gray-900'
            }`}
          >
            <option value="all">All Types</option>
            <option value="compliance">Compliance</option>
            <option value="risk">Risk Assessment</option>
            <option value="technical">Technical</option>
            <option value="intelligence">Threat Intelligence</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className={`px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600 text-white' 
                : 'bg-white border-gray-300 text-gray-900'
            }`}
          >
            <option value="date">Sort by Date</option>
            <option value="title">Sort by Title</option>
            <option value="size">Sort by Size</option>
          </select>
          <div className="text-sm text-gray-500 flex items-center">
            📊 {filteredReports.length} reports found
          </div>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {filteredReports.map((report) => (
          <div 
            key={report.id}
            className={`p-6 rounded-xl border transition-all duration-300 hover:scale-[1.02] hover:shadow-xl cursor-pointer ${
              isDarkMode 
                ? 'bg-slate-700 border-slate-600 hover:border-slate-500' 
                : 'bg-white border-gray-300 hover:border-gray-400 shadow-sm'
            }`}
            onClick={() => setSelectedReport(report)}
          >
            {/* Report Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start space-x-3 flex-1">
                <span className="text-3xl mt-1">{getTypeIcon(report.type)}</span>
                <div className="flex-1">
                  <h3 className={`font-semibold text-lg mb-1 transition-colors duration-300 ${
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    {report.title}
                  </h3>
                  <div className="flex items-center space-x-3 mb-2">
                    <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getClassificationBadge(report.classification)}`}>
                      🔒 {report.classification}
                    </span>
                    <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusBadge(report.status)}`}>
                      {report.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Report Details */}
            <div className="space-y-4">
              <p className={`text-sm transition-colors duration-300 ${
                isDarkMode ? 'text-slate-300' : 'text-gray-700'
              }`}>
                {report.description}
              </p>

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className={`font-medium ${isDarkMode ? 'text-slate-200' : 'text-gray-600'}`}>Author:</span>
                  <br />
                  <span className={isDarkMode ? 'text-slate-300' : 'text-gray-800'}>{report.author}</span>
                </div>
                <div>
                  <span className={`font-medium ${isDarkMode ? 'text-slate-200' : 'text-gray-600'}`}>Department:</span>
                  <br />
                  <span className={isDarkMode ? 'text-slate-300' : 'text-gray-800'}>{report.department}</span>
                </div>
                <div>
                  <span className={`font-medium ${isDarkMode ? 'text-slate-200' : 'text-gray-600'}`}>Approver:</span>
                  <br />
                  <span className={isDarkMode ? 'text-slate-300' : 'text-gray-800'}>{report.approver}</span>
                </div>
                <div>
                  <span className={`font-medium ${isDarkMode ? 'text-slate-200' : 'text-gray-600'}`}>Date:</span>
                  <br />
                  <span className={isDarkMode ? 'text-slate-300' : 'text-gray-800'}>{report.date}</span>
                </div>
              </div>

              {/* File Details */}
              <div className="flex justify-between items-center text-sm border-t pt-3">
                <div className={`transition-colors duration-300 ${
                  isDarkMode ? 'text-slate-400' : 'text-gray-500'
                }`}>
                  📄 {report.format} • {report.size} {report.pages && `• ${report.pages} pages`}
                </div>
                <div className={`transition-colors duration-300 ${
                  isDarkMode ? 'text-slate-400' : 'text-gray-500'
                }`}>
                  📥 {report.downloadCount} downloads
                </div>
              </div>

              {/* Compliance Frameworks */}
              <div className="flex flex-wrap gap-2">
                {report.complianceFrameworks.slice(0, 3).map((framework, index) => (
                  <span 
                    key={index}
                    className={`px-2 py-1 text-xs rounded-full font-medium transition-colors duration-300 ${
                      isDarkMode 
                        ? 'bg-purple-900/30 text-purple-300 border border-purple-500/30' 
                        : 'bg-purple-100 text-purple-800 border border-purple-200'
                    }`}
                  >
                    {framework}
                  </span>
                ))}
              </div>

              {/* Actions */}
              <div className="flex space-x-2 pt-2">
                <button className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-300 ${
                  isDarkMode 
                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}>
                  📖 View Report
                </button>
                <button className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-300 ${
                  isDarkMode 
                    ? 'bg-slate-600 hover:bg-slate-500 text-slate-200' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}>
                  📥 Download
                </button>
                <button className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-300 ${
                  isDarkMode 
                    ? 'bg-slate-600 hover:bg-slate-500 text-slate-200' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}>
                  📧 Share
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderScheduledReports = () => (
    <div className="space-y-6">
      {/* Scheduled Reports Table */}
      <div className={`rounded-xl border overflow-hidden transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-slate-700 border-slate-600' 
          : 'bg-white border-gray-300 shadow-sm'
      }`}>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className={`text-lg font-semibold transition-colors duration-300 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            📅 Scheduled Reports
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className={`${isDarkMode ? 'bg-slate-600' : 'bg-gray-50'}`}>
              <tr>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                  isDarkMode ? 'text-slate-200' : 'text-gray-500'
                }`}>
                  Report Name
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                  isDarkMode ? 'text-slate-200' : 'text-gray-500'
                }`}>
                  Frequency
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                  isDarkMode ? 'text-slate-200' : 'text-gray-500'
                }`}>
                  Next Run
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                  isDarkMode ? 'text-slate-200' : 'text-gray-500'
                }`}>
                  Recipients
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                  isDarkMode ? 'text-slate-200' : 'text-gray-500'
                }`}>
                  Status
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                  isDarkMode ? 'text-slate-200' : 'text-gray-500'
                }`}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDarkMode ? 'divide-slate-600' : 'divide-gray-200'}`}>
              {scheduledReports.map((schedule) => (
                <tr key={schedule.id} className={`${isDarkMode ? 'hover:bg-slate-600' : 'hover:bg-gray-50'}`}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                      {schedule.name}
                    </div>
                    <div className={`text-sm ${isDarkMode ? 'text-slate-300' : 'text-gray-500'}`}>
                      {schedule.template}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      isDarkMode ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {schedule.frequency}
                    </span>
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-slate-200' : 'text-gray-900'}`}>
                    {schedule.nextRun}
                  </td>
                  <td className={`px-6 py-4 text-sm ${isDarkMode ? 'text-slate-200' : 'text-gray-900'}`}>
                    {schedule.recipients.length} recipients
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      schedule.status === 'Active' 
                        ? isDarkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800'
                        : isDarkMode ? 'bg-red-900/30 text-red-300' : 'bg-red-100 text-red-800'
                    }`}>
                      {schedule.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button className={`${isDarkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-900'}`}>
                        Edit
                      </button>
                      <button className={`${isDarkMode ? 'text-green-400 hover:text-green-300' : 'text-green-600 hover:text-green-900'}`}>
                        Run Now
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderTemplates = () => (
    <div className="space-y-6">
      {/* Enterprise Report Templates */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          {
            name: "SOX Compliance Report",
            icon: "📋",
            desc: "Sarbanes-Oxley compliance assessment",
            complexity: "High",
            estimatedTime: "45 minutes",
            requiredData: ["Financial Controls", "IT General Controls", "Access Reviews"],
            approvalRequired: true,
            classification: "Confidential"
          },
          {
            name: "Risk Assessment Dashboard", 
            icon: "⚠️",
            desc: "Enterprise risk analysis and scoring",
            complexity: "Medium",
            estimatedTime: "20 minutes",
            requiredData: ["Risk Registry", "Control Assessments", "Incident Data"],
            approvalRequired: true,
            classification: "Internal"
          },
          {
            name: "HIPAA Security Assessment",
            icon: "🏥",
            desc: "Healthcare data protection compliance",
            complexity: "High",
            estimatedTime: "60 minutes",
            requiredData: ["PHI Access Logs", "Security Controls", "Training Records"],
            approvalRequired: true,
            classification: "Confidential"
          },
          {
            name: "PCI DSS Compliance Report",
            icon: "💳",
            desc: "Payment card industry security standards",
            complexity: "High",
            estimatedTime: "90 minutes",
            requiredData: ["Cardholder Data Environment", "Network Segmentation", "Vulnerability Scans"],
            approvalRequired: true,
            classification: "Confidential"
          },
          {
            name: "Threat Intelligence Brief",
            icon: "🕵️",
            desc: "Current threat landscape analysis",
            complexity: "Medium",
            estimatedTime: "15 minutes",
            requiredData: ["Threat Feeds", "IOCs", "Attack Patterns"],
            approvalRequired: false,
            classification: "Internal"
          },
          {
            name: "Executive Security Summary",
            icon: "👔",
            desc: "C-level security posture overview",
            complexity: "Low",
            estimatedTime: "10 minutes",
            requiredData: ["Security Metrics", "Incident Summary", "Compliance Status"],
            approvalRequired: true,
            classification: "Confidential"
          }
        ].map((template, index) => (
          <div
            key={index}
            className={`p-6 rounded-xl border transition-all duration-300 hover:scale-105 hover:shadow-lg ${
              isDarkMode 
                ? 'bg-slate-700 border-slate-600 hover:border-slate-500' 
                : 'bg-white border-gray-300 hover:border-gray-400 shadow-sm'
            }`}
          >
            <div className="text-center mb-4">
              <div className="text-4xl mb-3">{template.icon}</div>
              <h4 className={`font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                {template.name}
              </h4>
              <p className={`text-sm ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}>
                {template.desc}
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className={isDarkMode ? 'text-slate-300' : 'text-gray-600'}>Complexity:</span>
                <span className={`font-medium ${
                  template.complexity === 'High' ? 'text-red-500' :
                  template.complexity === 'Medium' ? 'text-yellow-500' : 'text-green-500'
                }`}>
                  {template.complexity}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className={isDarkMode ? 'text-slate-300' : 'text-gray-600'}>Est. Time:</span>
                <span className={isDarkMode ? 'text-slate-200' : 'text-gray-800'}>{template.estimatedTime}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className={isDarkMode ? 'text-slate-300' : 'text-gray-600'}>Classification:</span>
                <span className={`px-2 py-1 text-xs rounded-full border ${getClassificationBadge(template.classification)}`}>
                  {template.classification}
                </span>
              </div>
            </div>

            <button
              onClick={() => handleGenerateReport(template.name.split(' ')[0], template.name)}
              disabled={generatingReport}
              className={`w-full mt-4 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                generatingReport
                  ? isDarkMode ? 'bg-slate-600 text-slate-400' : 'bg-gray-300 text-gray-500'
                  : isDarkMode 
                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {generatingReport ? "Generating..." : "Generate Report"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Enterprise Reports...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-6 space-y-6 transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold transition-colors duration-300 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            🏢 Enterprise Security Reports
          </h1>
          <p className={`text-lg mt-2 transition-colors duration-300 ${
            isDarkMode ? 'text-slate-300' : 'text-gray-700'
          }`}>
            Compliance reporting, risk assessments, and executive briefings
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            🔒 Secure Document Management
          </span>
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
            ✅ SOX Compliant
          </span>
        </div>
      </div>

      {/* Report Generation Status */}
      {generatingReport && (
        <div className={`p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-blue-900/30 border-blue-500 text-blue-300' 
            : 'bg-blue-50 border-blue-200 text-blue-700'
        }`}>
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <div>
              <p className="font-medium">Generating Enterprise Report...</p>
              <p className="text-sm opacity-75">Collecting data from secure sources and applying compliance templates</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "library", label: "📚 Report Library", count: reports.length },
            { id: "scheduled", label: "📅 Scheduled Reports", count: scheduledReports.length },
            { id: "templates", label: "📋 Templates & Generation" }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors duration-300 ${
                activeTab === tab.id
                  ? isDarkMode 
                    ? "border-blue-400 text-blue-400" 
                    : "border-blue-500 text-blue-600"
                  : isDarkMode
                    ? "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-300"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  isDarkMode ? 'bg-slate-600 text-slate-200' : 'bg-gray-100 text-gray-900'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === "library" && renderReportLibrary()}
        {activeTab === "scheduled" && renderScheduledReports()}
        {activeTab === "templates" && renderTemplates()}
      </div>

      {/* Enterprise Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className={`p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600' 
            : 'bg-white border-gray-300 shadow-sm'
        }`}>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <span className="text-2xl">📊</span>
            </div>
            <div className="ml-4">
              <p className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-slate-300' : 'text-gray-600'
              }`}>
                Total Reports
              </p>
              <p className={`text-2xl font-bold transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {reports.length}
              </p>
            </div>
          </div>
        </div>

        <div className={`p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600' 
            : 'bg-white border-gray-300 shadow-sm'
        }`}>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <span className="text-2xl">📋</span>
            </div>
            <div className="ml-4">
              <p className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-slate-300' : 'text-gray-600'
              }`}>
                Compliance Reports
              </p>
              <p className={`text-2xl font-bold transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {reports.filter(r => r.type === 'compliance').length}
              </p>
            </div>
          </div>
        </div>

        <div className={`p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600' 
            : 'bg-white border-gray-300 shadow-sm'
        }`}>
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <span className="text-2xl">📅</span>
            </div>
            <div className="ml-4">
              <p className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-slate-300' : 'text-gray-600'
              }`}>
                Scheduled Reports
              </p>
              <p className={`text-2xl font-bold transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {scheduledReports.length}
              </p>
            </div>
          </div>
        </div>

        <div className={`p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600' 
            : 'bg-white border-gray-300 shadow-sm'
        }`}>
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <span className="text-2xl">🔒</span>
            </div>
            <div className="ml-4">
              <p className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-slate-300' : 'text-gray-600'
              }`}>
                Confidential
              </p>
              <p className={`text-2xl font-bold transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {reports.filter(r => r.classification === 'Confidential').length}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnterpriseSecurityReports;