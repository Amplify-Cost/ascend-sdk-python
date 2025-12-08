// Create this file: src/components/Breadcrumb.jsx
import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const Breadcrumb = ({ activeTab, user }) => {
  const { isDarkMode } = useTheme();

  // Define breadcrumb paths for each tab
  const getBreadcrumbPath = (tab) => {
    const paths = {
      dashboard: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Security Command Center', path: '/dashboard' }
      ],
      analytics: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Analytics & Insights', path: '/analytics' }
      ],
      activity: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Agent Activity', path: '/activity' }
      ],
      reports: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Security Reports', path: '/reports' }
      ],
      support: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Support Center', path: '/support' }
      ],
      auth: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Admin', path: '/admin' },
        { label: 'Authorization Center', path: '/auth' }
      ],
      'ai-alerts': [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Admin', path: '/admin' },
        { label: 'AI Alert Management', path: '/ai-alerts' }
      ],
      smartRules: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Admin', path: '/admin' },
        { label: 'AI Rule Engine', path: '/smart-rules' }
      ],
      users: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Admin', path: '/admin' },
        { label: 'User Management', path: '/users' }
      ],
      settings: [
        { label: 'Ascend Platform', path: '/' },
        { label: 'Admin', path: '/admin' },
        { label: 'Enterprise Settings', path: '/settings' }
      ]
    };

    return paths[tab] || [
      { label: 'Ascend Platform', path: '/' },
      { label: 'Unknown', path: '/' }
    ];
  };

  const breadcrumbPath = getBreadcrumbPath(activeTab);

  return (
    <nav className={`flex items-center space-x-2 text-sm mb-4 transition-colors duration-300 ${
      isDarkMode ? 'text-slate-300' : 'text-gray-600'
    }`}>
      {breadcrumbPath.map((item, index) => (
        <div key={index} className="flex items-center space-x-2">
          {index > 0 && (
            <span className={`transition-colors duration-300 ${
              isDarkMode ? 'text-slate-500' : 'text-gray-400'
            }`}>
              /
            </span>
          )}
          <span className={`transition-colors duration-300 ${
            index === breadcrumbPath.length - 1
              ? isDarkMode ? 'text-white font-medium' : 'text-gray-900 font-medium'
              : isDarkMode ? 'text-slate-400 hover:text-slate-200' : 'text-gray-500 hover:text-gray-700'
          } ${index < breadcrumbPath.length - 1 ? 'cursor-pointer' : ''}`}>
            {item.label}
          </span>
        </div>
      ))}
      
      {/* Admin Badge */}
      {["admin", "super_admin"].includes(user?.role) && ['auth', 'ai-alerts', 'smartRules', 'users', 'settings'].includes(activeTab) && (
        <div className={`ml-3 px-2 py-1 rounded-full text-xs font-medium transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-blue-900/30 text-blue-300 border border-blue-500/30' 
            : 'bg-blue-100 text-blue-800 border border-blue-200'
        }`}>
          Admin Access
        </div>
      )}
    </nav>
  );
};

export default Breadcrumb;