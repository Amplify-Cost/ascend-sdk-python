import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useFocusTrap, useScreenReaderAnnounce, useKeyboardNavigation } from '../contexts/AccessibilityContext';

// Move searchData outside component to prevent recreation on every render
const searchData = [
    { 
      type: 'page', 
      title: 'Security Dashboard', 
      path: 'dashboard', 
      icon: '🏠', 
      description: 'Main security overview and real-time metrics',
      keywords: 'home overview metrics kpi dashboard main'
    },
    { 
      type: 'page', 
      title: 'AI Alert Management', 
      path: 'ai-alerts', 
      icon: '🚨', 
      description: 'Manage and analyze security alerts with AI',
      keywords: 'alerts notifications warnings threats ai artificial intelligence'
    },
    { 
      type: 'page', 
      title: 'AI Rule Engine', 
      path: 'smartRules', 
      icon: '⚡', 
      description: 'Create and manage security rules with AI assistance',
      keywords: 'rules engine smart ai automation logic conditions actions'
    },
    { 
      type: 'page', 
      title: 'Authorization Center', 
      path: 'auth', 
      icon: '🛡️', 
      description: 'Agent approval and authorization system',
      keywords: 'authorization approval permissions access control agents'
    },
    { 
      type: 'page', 
      title: 'User Management', 
      path: 'users', 
      icon: '👥', 
      description: 'Manage platform users and roles',
      keywords: 'users accounts rbac roles permissions management admin'
    },
    { 
      type: 'page', 
      title: 'Analytics', 
      path: 'analytics', 
      icon: '📊', 
      description: 'Security analytics and insights dashboard',
      keywords: 'analytics insights reports charts graphs data visualization'
    },
    { 
      type: 'page', 
      title: 'Settings', 
      path: 'settings', 
      icon: '⚙️', 
      description: 'Platform configuration and preferences',
      keywords: 'settings configuration preferences options admin setup'
    },
    { 
      type: 'agent', 
      title: 'security-scanner-01', 
      path: 'activity', 
      icon: '🤖', 
      description: 'Vulnerability scanning and security assessment agent',
      keywords: 'agent bot scanner vulnerability security assessment scan'
    },
    { 
      type: 'agent', 
      title: 'threat-detector', 
      path: 'activity', 
      icon: '🤖', 
      description: 'Advanced threat detection and analysis agent',
      keywords: 'agent bot threat detection malware analysis security'
    },
    { 
      type: 'agent', 
      title: 'compliance-monitor', 
      path: 'activity', 
      icon: '🤖', 
      description: 'Compliance monitoring and audit agent',
      keywords: 'agent bot compliance audit monitoring regulations standards'
    },
    { 
      type: 'action', 
      title: 'Create Security Rule', 
      path: 'smartRules', 
      icon: '➕', 
      description: 'Generate new security rule with AI assistance',
      keywords: 'create new rule security add generate make'
    },
    { 
      type: 'action', 
      title: 'Submit Agent Action', 
      path: 'auth', 
      icon: '📤', 
      description: 'Submit agent action for approval',
      keywords: 'submit send action approval authorization request'
    },
    { 
      type: 'action', 
      title: 'View Reports', 
      path: 'reports', 
      icon: '📋', 
      description: 'Access security reports and documentation',
      keywords: 'view reports documents analysis summaries export'
    }
  ];

const GlobalSearch = ({ onNavigate }) => {
  const { isDarkMode } = useTheme();
  const { announce } = useScreenReaderAnnounce();
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredResults, setFilteredResults] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const searchRef = useRef(null);
  const resultsRef = useRef([]);

  // Enable focus trap when modal is open
  useFocusTrap(isOpen);

  // Create stable announce function to prevent infinite loops
  const stableAnnounce = useCallback((message, priority) => {
    announce(message, priority);
  }, [announce]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+K or Cmd+K to open search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
        stableAnnounce('Search opened', 'assertive');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []); // Remove announce dependency to prevent infinite loops

  // Handle keyboard navigation within search
  useKeyboardNavigation(
    () => {
      // Escape handler
      if (isOpen) {
        setIsOpen(false);
        setSearchQuery('');
        setSelectedIndex(-1);
        stableAnnounce('Search closed', 'polite');
      }
    },
    (e) => {
      // Enter handler
      if (isOpen && selectedIndex >= 0 && filteredResults[selectedIndex]) {
        handleSelect(filteredResults[selectedIndex]);
      }
    }
  );

  // Handle arrow key navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => {
            const next = Math.min(prev + 1, filteredResults.length - 1);
            if (next !== prev && filteredResults[next]) {
              stableAnnounce(`${filteredResults[next].title}, ${filteredResults[next].type}`, 'polite');
            }
            return next;
          });
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => {
            const next = Math.max(prev - 1, -1);
            if (next !== prev) {
              if (next === -1) {
                stableAnnounce('Search input', 'polite');
              } else if (filteredResults[next]) {
                stableAnnounce(`${filteredResults[next].title}, ${filteredResults[next].type}`, 'polite');
              }
            }
            return next;
          });
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredResults, stableAnnounce]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setSelectedIndex(-1);
    }
  }, [isOpen]);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchQuery('');
        setSelectedIndex(-1);
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
      setSelectedIndex(-1);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = searchData.filter(item =>
      item.title.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query) ||
      item.keywords.toLowerCase().includes(query)
    );

    setFilteredResults(filtered.slice(0, 8)); // Limit to 8 results
    setSelectedIndex(-1);
    
    if (filtered.length > 0) {
      stableAnnounce(`${filtered.length} search result${filtered.length === 1 ? '' : 's'} found`, 'polite');
    } else {
      stableAnnounce('No search results found', 'polite');
    }
  }, [searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && resultsRef.current[selectedIndex]) {
      resultsRef.current[selectedIndex].scrollIntoView({
        block: 'nearest',
        behavior: 'smooth'
      });
    }
  }, [selectedIndex]);

  const handleSelect = useCallback((item) => {
    onNavigate(item.path);
    setIsOpen(false);
    setSearchQuery('');
    setSelectedIndex(-1);
    stableAnnounce(`Navigating to ${item.title}`, 'assertive');
  }, [onNavigate, stableAnnounce]);

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

  const getTypeLabel = (type) => {
    switch (type) {
      case 'page': return 'Page';
      case 'agent': return 'Agent';
      case 'action': return 'Action';
      default: return 'Item';
    }
  };

  return (
    <>
      {/* Search Trigger Button */}
      <button
        onClick={() => {
          setIsOpen(true);
          stableAnnounce('Search opened', 'assertive');
        }}
        className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600' 
            : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
        }`}
        aria-label="Open search dialog. Keyboard shortcut: Control or Command K"
      >
        <span className="text-lg" aria-hidden="true">🔍</span>
        <span className="text-sm">Search...</span>
        <kbd className={`px-2 py-1 text-xs rounded ${
          isDarkMode ? 'bg-slate-600 text-slate-300' : 'bg-gray-200 text-gray-600'
        }`}>
          ⌘K
        </kbd>
      </button>

      {/* Search Modal */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="search-title"
          aria-describedby="search-description"
        >
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/20 backdrop-blur-sm" aria-hidden="true"></div>
          
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
              <span className="text-2xl mr-3" aria-hidden="true">🔍</span>
              <label htmlFor="search-input" className="sr-only">
                Search pages, agents, and actions
              </label>
              <input
                id="search-input"
                ref={inputRef}
                type="text"
                placeholder="Search pages, agents, actions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`flex-1 bg-transparent outline-none text-lg ${
                  isDarkMode ? 'text-white placeholder-slate-400' : 'text-gray-900 placeholder-gray-500'
                }`}
                aria-describedby="search-description"
                aria-autocomplete="list"
                aria-expanded={filteredResults.length > 0}
                aria-controls="search-results"
                role="combobox"
              />
              <kbd className={`px-2 py-1 text-xs rounded ${
                isDarkMode ? 'bg-slate-700 text-slate-300' : 'bg-gray-100 text-gray-600'
              }`}>
                ESC
              </kbd>
            </div>

            {/* Hidden description for screen readers */}
            <div id="search-description" className="sr-only">
              Search through pages, agents, and actions. Use arrow keys to navigate results, Enter to select, Escape to close.
            </div>

            {/* Search Results */}
            <div 
              className="max-h-96 overflow-y-auto"
              id="search-results"
              role="listbox"
              aria-label="Search results"
            >
              {searchQuery.trim() === '' ? (
                <div className={`p-8 text-center ${
                  isDarkMode ? 'text-slate-400' : 'text-gray-500'
                }`}>
                  <div className="text-4xl mb-4" aria-hidden="true">🔍</div>
                  <h2 id="search-title" className="text-lg font-medium mb-2">Search Ascend Platform</h2>
                  <p className="text-sm mb-4">Find pages, agents, actions, and more...</p>
                  <div className="text-xs space-y-1">
                    <div>
                      <kbd className={`px-2 py-1 rounded mr-2 ${
                        isDarkMode ? 'bg-slate-700' : 'bg-gray-100'
                      }`}>⌘K</kbd>
                      to open search
                    </div>
                    <div>
                      <kbd className={`px-2 py-1 rounded mr-2 ${
                        isDarkMode ? 'bg-slate-700' : 'bg-gray-100'
                      }`}>↑↓</kbd>
                      to navigate
                    </div>
                    <div>
                      <kbd className={`px-2 py-1 rounded mr-2 ${
                        isDarkMode ? 'bg-slate-700' : 'bg-gray-100'
                      }`}>↵</kbd>
                      to select
                    </div>
                  </div>
                </div>
              ) : filteredResults.length === 0 ? (
                <div className={`p-8 text-center ${
                  isDarkMode ? 'text-slate-400' : 'text-gray-500'
                }`} role="status">
                  <div className="text-4xl mb-4" aria-hidden="true">🤷‍♂️</div>
                  <p className="text-lg font-medium mb-2">No results found</p>
                  <p className="text-sm">Try searching for something else</p>
                </div>
              ) : (
                <div className="p-2">
                  {filteredResults.map((item, index) => (
                    <button
                      key={index}
                      ref={el => resultsRef.current[index] = el}
                      onClick={() => handleSelect(item)}
                      className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        selectedIndex === index
                          ? isDarkMode
                            ? 'bg-slate-600 text-white ring-2 ring-blue-400'
                            : 'bg-blue-50 text-gray-900 ring-2 ring-blue-500'
                          : isDarkMode 
                            ? 'hover:bg-slate-700 text-slate-200' 
                            : 'hover:bg-gray-100 text-gray-800'
                      }`}
                      role="option"
                      aria-selected={selectedIndex === index}
                      aria-describedby={`result-${index}-description`}
                    >
                      <span className="text-2xl" aria-hidden="true">{item.icon}</span>
                      <div className="flex-1 text-left">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{item.title}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${getTypeColor(item.type)}`}>
                            {getTypeLabel(item.type)}
                          </span>
                        </div>
                        <p 
                          id={`result-${index}-description`}
                          className={`text-sm mt-1 ${
                            isDarkMode ? 'text-slate-400' : 'text-gray-600'
                          }`}
                        >
                          {item.description}
                        </p>
                      </div>
                      <span className={`text-xs ${
                        isDarkMode ? 'text-slate-500' : 'text-gray-400'
                      }`} aria-hidden="true">
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
              <div className="flex items-center space-x-4" role="status">
                <span>↑↓ Navigate</span>
                <span>↵ Select</span>
                <span>ESC Close</span>
              </div>
              <div>
                Powered by Ascend
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default GlobalSearch;