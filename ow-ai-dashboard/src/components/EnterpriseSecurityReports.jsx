import React, { useState } from "react";
import { useTheme } from "../contexts/ThemeContext";

const EnterpriseSecurityReports = ({ getAuthHeaders, user }) => {
  const { isDarkMode } = useTheme();
  const [generatingReport, setGeneratingReport] = useState(false);

  const handleGenerateReport = async (reportType) => {
    setGeneratingReport(true);
    setTimeout(() => setGeneratingReport(false), 2000);
  };

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

      {/* Enterprise Report Templates */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          {
            name: "SOX Compliance Report",
            icon: "📋",
            desc: "Sarbanes-Oxley compliance assessment",
            classification: "Confidential"
          },
          {
            name: "Risk Assessment Dashboard", 
            icon: "⚠️",
            desc: "Enterprise risk analysis and scoring",
            classification: "Internal"
          },
          {
            name: "HIPAA Security Assessment",
            icon: "🏥",
            desc: "Healthcare data protection compliance",
            classification: "Confidential"
          },
          {
            name: "PCI DSS Compliance Report",
            icon: "💳",
            desc: "Payment card industry security standards",
            classification: "Confidential"
          },
          {
            name: "Threat Intelligence Brief",
            icon: "🕵️",
            desc: "Current threat landscape analysis",
            classification: "Internal"
          },
          {
            name: "Executive Security Summary",
            icon: "👔",
            desc: "C-level security posture overview",
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
                <span className={isDarkMode ? 'text-slate-300' : 'text-gray-600'}>Classification:</span>
                <span className={`px-2 py-1 text-xs rounded-full border ${
                  template.classification === 'Confidential' 
                    ? 'bg-orange-100 text-orange-800 border-orange-200'
                    : 'bg-blue-100 text-blue-800 border-blue-200'
                }`}>
                  {template.classification}
                </span>
              </div>
            </div>

            <button
              onClick={() => handleGenerateReport(template.name)}
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
                47
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
                12
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
                8
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
                23
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnterpriseSecurityReports;