// Create this file: src/components/GlobalSearch.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const GlobalSearch = ({ onNavigate }) => {
  const { isDarkMode } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredResults, setFilteredResults] = useState([]);
  const inputRef = useRef(null);
  const searchRef = useRef(null);

  // Mock search data - in real app, this would come from your API
  const searchData = [
    { type: 'page', title: 'Security Dashboard', path: 'dashboard', icon: '🏠', description: 'Main security overview' },
    { type: 'page', title: 'AI Alert Management', path: 'ai-alerts', icon: '🚨', description: 'Manage security alerts' },
    { type: 'page', title: 'AI Rule Engine', path: 'smartRules', icon: '⚡', description: 'Create and manage rules' },
    { type: 'page', title: 'Authorization Center', path: 'auth', icon: '🛡️', description: 'Agent approval system' },
    { type: 'page', title: 'User Management', path: 'users', icon: '👥', description: 'Manage platform users' },
    { type: 'page', title: 'Analytics', path: 'analytics', icon: '📊', description: 'Security analytics and insights' },
    { type: 'page', title: 'Settings', path: 'settings', icon: '⚙️', description: 'Platform configuration' },
    { type: 'agent', title: 'security-scanner-01', path: 'activity', icon: '🤖', description: 'Vulnerability scanning agent' },
    { type: 'agent', title: 'threat-detector', path: 'activity', icon: '🤖', description: 'Threat detection agent' },
    { type: 'agent', title: 'compliance-monitor', path: 'activity', icon: '🤖', description: 'Compliance monitoring agent' },
    { type: 'action', title: 'Create Security Rule', path: 'smartRules', icon: '➕', description: 'Generate new security rule' },
    { type: 'action', title: 'Submit Agent Action', path: 'auth', icon: '📤', description: 'Submit action for approval' },
    { type: 'action', title: 'View Reports', path: 'reports', icon: '📋', description: 'Access security reports' }
  ];

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+K or Cmd+K to open search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      // Escape to close
      if (e.key === 'Escape') {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Filter search results
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredResults([]);
      return;
    }

    const filtered = searchData.filter(item =>
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
    );

    setFilteredResults(filtered.slice(0, 8)); // Limit to 8 results
  }, [searchQuery]);

  const handleSelect = (item) => {
    onNavigate(item.path);
    setIsOpen(false);
    setSearchQuery('');
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'page':
        return isDarkMode ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-100 text-blue-800';
      case 'agent':
        return isDarkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800';
      case 'action':
        return isDarkMode ? 'bg-purple-900/30 text-purple-300' : 'bg-purple-100 text-purple-800';
      default:
        return isDarkMode ? 'bg-gray-900/30 text-gray-300' : 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <>
      {/* Search Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-all duration-200 hover:scale-105 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600' 
            : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
        }`}
      >
        <span className="text-lg">🔍</span>
        <span className="text-sm">Search...</span>
        <kbd className={`px-2 py-1 text-xs rounded ${
          isDarkMode ? 'bg-slate-600 text-slate-300' : 'bg-gray-200 text-gray-600'
        }`}>
          ⌘K
        </kbd>
      </button>

      {/* Search Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/20 backdrop-blur-sm"></div>
          
          {/* Search Panel */}
          <div 
            ref={searchRef}
            className={`relative w-full max-w-2xl rounded-xl border shadow-2xl transition-all duration-300 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600' 
                : 'bg-white border-gray-300'
            }`}
          >
            {/* Search Input */}
            <div className="flex items-center p-4 border-b border-gray-200 dark:border-slate-600">
              <span className="text-2xl mr-3">🔍</span>
              <input
                ref={inputRef}
                type="text"
                placeholder="Search pages, agents, actions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`flex-1 bg-transparent outline-none text-lg ${
                  isDarkMode ? 'text-white placeholder-slate-400' : 'text-gray-900 placeholder-gray-500'
                }`}
              />
              <kbd className={`px-2 py-1 text-xs rounded ${
                isDarkMode ? 'bg-slate-700 text-slate-300' : 'bg-gray-100 text-gray-600'
              }`}>
                ESC
              </kbd>
            </div>

            {/* Search Results */}
            <div className="max-h-96 overflow-y-auto">
              {searchQuery.trim() === '' ? (
                <div className={`p-8 text-center ${
                  isDarkMode ? 'text-slate-400' : 'text-gray-500'
                }`}>
                  <div className="text-4xl mb-4">🔍</div>
                  <p className="text-lg font-medium mb-2">Search OW-AI Platform</p>
                  <p className="text-sm">Find pages, agents, actions, and more...</p>
                  <div className="mt-4 text-xs">
                    <span className={`px-2 py-1 rounded mr-2 ${
                      isDarkMode ? 'bg-slate-700' : 'bg-gray-100'
                    }`}>⌘K</span>
                    to open search
                  </div>
                </div>
              ) : filteredResults.length === 0 ? (
                <div className={`p-8 text-center ${
                  isDarkMode ? 'text-slate-400' : 'text-gray-500'
                }`}>
                  <div className="text-4xl mb-4">🤷‍♂️</div>
                  <p className="text-lg font-medium mb-2">No results found</p>
                  <p className="text-sm">Try searching for something else</p>
                </div>
              ) : (
                <div className="p-2">
                  {filteredResults.map((item, index) => (
                    <button
                      key={index}
                      onClick={() => handleSelect(item)}
                      className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 hover:scale-[1.02] ${
                        isDarkMode 
                          ? 'hover:bg-slate-700 text-slate-200' 
                          : 'hover:bg-gray-100 text-gray-800'
                      }`}
                    >
                      <span className="text-2xl">{item.icon}</span>
                      <div className="flex-1 text-left">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{item.title}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${getTypeColor(item.type)}`}>
                            {item.type}
                          </span>
                        </div>
                        <p className={`text-sm mt-1 ${
                          isDarkMode ? 'text-slate-400' : 'text-gray-600'
                        }`}>
                          {item.description}
                        </p>
                      </div>
                      <span className={`text-xs ${
                        isDarkMode ? 'text-slate-500' : 'text-gray-400'
                      }`}>
                        ↵
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className={`flex items-center justify-between p-3 border-t text-xs ${
              isDarkMode 
                ? 'border-slate-600 text-slate-400' 
                : 'border-gray-200 text-gray-500'
            }`}>
              <div className="flex items-center space-x-4">
                <span>↑↓ Navigate</span>
                <span>↵ Select</span>
                <span>ESC Close</span>
              </div>
              <div>
                Powered by OW-AI
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default GlobalSearch;