import React from "react";
import { useTheme } from "../contexts/ThemeContext";
import { useAccessibility, useScreenReaderAnnounce } from "../contexts/AccessibilityContext";

// ✅ SAFE: Using emoji icons to avoid import issues
const SafeIcon = ({ iconName, size = 18, className = "", ariaLabel }) => {
  const iconMap = {
    Home: "🏠",
    Activity: "📊",
    AlertCircle: "⚠️",
    BarChart: "📈",
    FileText: "📄",
    ClipboardList: "📋",
    LifeBuoy: "🆘",
    Settings: "⚙️",
    LogOut: "🚪",
    Shield: "🛡️",
    Users: "👥",
    Brain: "🧠",
    Zap: "⚡",
    Lock: "🔒",
    Sun: "☀️",
    Moon: "🌙",
    // 🚀 NEW: Real-Time Analytics icon
    Radar: "📡",
    // SEC-024: Agent Registry icon
    Robot: "🤖",
    // SEC-022: Admin Console icon
    Building: "🏛️",
    // DOC-003: Documentation icon
    Book: "📚",
  };

  return (
    <span
      className={`inline-flex items-center justify-center ${className}`}
      style={{ fontSize: `${size}px` }}
      aria-label={ariaLabel || iconName}
      role="img"
    >
      {iconMap[iconName] || "📄"}
    </span>
  );
};

const Sidebar = ({ activeTab, setActiveTab, user, handleLogout }) => {
  const { isDarkMode, toggleTheme } = useTheme();
  const { announce } = useScreenReaderAnnounce();
  const { focusMode, prefersReducedMotion } = useAccessibility();
  
  console.log("🔧 Sidebar rendering with user:", user?.role);

  // ✅ PRESERVED: All existing menu items unchanged
  const menuItems = [
    { 
      label: "Dashboard", 
      icon: <SafeIcon iconName="Home" size={18} ariaLabel="Dashboard home" />, 
      tab: "dashboard",
      description: "Main security overview and metrics"
    },
    { 
      label: "Analytics", 
      icon: <SafeIcon iconName="BarChart" size={18} ariaLabel="Analytics charts" />, 
      tab: "analytics",
      description: "Security analytics and insights"
    },
    // 🚀 NEW: Real-Time Analytics tab (enterprise feature)
    { 
      label: "Real-Time Analytics", 
      icon: <SafeIcon iconName="Radar" size={18} ariaLabel="Real-time radar monitoring" />, 
      tab: "realtime-analytics",
      badge: "Live",
      description: "Real-time monitoring, predictive analytics, and live system performance",
      adminOnly: false // Available to all enterprise users
    },
    { 
      label: "Activity", 
      icon: <SafeIcon iconName="Activity" size={18} ariaLabel="Activity monitor" />, 
      tab: "activity",
      description: "Agent activity monitoring"
    },
    { 
      label: "Reports", 
      icon: <SafeIcon iconName="FileText" size={18} ariaLabel="Reports document" />, 
      tab: "reports",
      description: "Security reports and documentation"
    },
    {
      label: "Support",
      icon: <SafeIcon iconName="LifeBuoy" size={18} ariaLabel="Life buoy support" />,
      tab: "support",
      description: "Help and support center"
    },
    // DOC-003: Enterprise Documentation - Available to all users
    {
      label: "Documentation",
      icon: <SafeIcon iconName="Book" size={18} ariaLabel="Documentation book" />,
      tab: "documentation",
      badge: "Docs",
      description: "Integration guides and API documentation"
    },
  ];

  // SEC-040: Consolidated admin features with single Admin Console entry point
  if (user?.role === "admin") {
    menuItems.push(
      {
        label: "Authorization Center",
        icon: <SafeIcon iconName="Shield" size={18} ariaLabel="Security shield" />,
        tab: "auth",
        description: "Agent authorization and approval system",
        adminOnly: true
      },
      {
        label: "🧠 AI Alert Management",
        icon: <SafeIcon iconName="AlertCircle" size={18} ariaLabel="Alert warning" />,
        tab: "ai-alerts",
        description: "AI-powered alert management system",
        adminOnly: true
      },
      {
        label: "🧠 AI Rule Engine",
        icon: <SafeIcon iconName="Zap" size={18} ariaLabel="Lightning bolt" />,
        tab: "smartRules",
        badge: "Enterprise",
        description: "AI-powered rule generation and management",
        adminOnly: true
      },
      {
        label: "Settings",
        icon: <SafeIcon iconName="Settings" size={18} ariaLabel="Settings gear" />,
        tab: "settings",
        description: "Enterprise platform configuration",
        adminOnly: true
      },
      // SEC-024: Enterprise Agent Registry - MCP Server & Agent Governance
      {
        label: "🤖 Agent Registry",
        icon: <SafeIcon iconName="Robot" size={18} ariaLabel="Agent robot" />,
        tab: "agent-registry",
        badge: "Enterprise",
        description: "Enterprise AI agent registration, MCP server governance, and SDK integration",
        adminOnly: true
      },
      // SEC-040: Unified Admin Console - Consolidated Organization & User Management
      // Replaces separate "User Management" tab - now single entry point for all admin functions
      {
        label: "🏛️ Admin Console",
        icon: <SafeIcon iconName="Building" size={18} ariaLabel="Admin building" />,
        tab: "admin-console",
        badge: "Admin",
        description: "Unified administration: users, RBAC, billing, compliance, and organization settings",
        adminOnly: true
      }
    );
  }

  // ✅ PRESERVED: All existing functions unchanged
  const handleTabChange = (tab, itemLabel) => {
    if (tab === activeTab) return;
    
    setActiveTab(tab);
    announce(`Navigated to ${itemLabel}`, 'polite');
  };

  const handleThemeToggle = () => {
    toggleTheme();
    announce(`Switched to ${isDarkMode ? 'light' : 'dark'} mode`, 'polite');
  };

  const handleLogoutClick = () => {
    announce('Logging out...', 'polite');
    handleLogout();
  };

  return (
    <aside 
      className={`w-64 h-screen flex flex-col shadow-xl transition-all duration-300 ${
        isDarkMode 
          ? 'bg-gradient-to-b from-slate-800 to-slate-700 text-white' 
          : 'bg-gradient-to-b from-blue-900 to-blue-800 text-white'
      }`}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* ✅ PRESERVED: Header unchanged */}
      <header className={`p-6 border-b transition-colors duration-300 ${
        isDarkMode ? 'border-slate-600' : 'border-blue-700'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-xl font-bold transition-all duration-300 ${
              isDarkMode
                ? 'bg-gradient-to-r from-white to-slate-200 bg-clip-text text-transparent'
                : 'bg-gradient-to-r from-blue-200 to-white bg-clip-text text-transparent'
            }`}>
              Ascend
            </h1>
            <p className={`text-sm mt-1 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-blue-200'
            }`}>
              Enterprise Security
            </p>
          </div>
          
          {/* Theme Toggle */}
          <button
            onClick={handleThemeToggle}
            className={`p-2 rounded-lg transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              focusMode ? 'focus:ring-yellow-400' : ''
            } ${
              !prefersReducedMotion ? 'hover:scale-110' : ''
            } ${
              isDarkMode 
                ? 'bg-slate-600 hover:bg-slate-500 text-yellow-300 focus:ring-yellow-400' 
                : 'bg-blue-700 hover:bg-blue-600 text-yellow-300 focus:ring-yellow-400'
            }`}
            aria-label={`Switch to ${isDarkMode ? 'light' : 'dark'} mode`}
            title={`Switch to ${isDarkMode ? 'light' : 'dark'} mode`}
          >
            <SafeIcon 
              iconName={isDarkMode ? "Sun" : "Moon"} 
              size={16} 
              ariaLabel={isDarkMode ? "Sun icon" : "Moon icon"}
            />
          </button>
        </div>
      </header>

      {/* ✅ PRESERVED: User Info unchanged */}
      <div className={`p-4 border-b transition-colors duration-300 ${
        isDarkMode 
          ? 'border-slate-600 bg-slate-700/50' 
          : 'border-blue-700 bg-blue-800/50'
      }`}>
        <div className="flex items-center space-x-3">
          <div 
            className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-sm transition-all duration-300 ${
              isDarkMode 
                ? 'bg-gradient-to-r from-slate-500 to-slate-400' 
                : 'bg-gradient-to-r from-blue-400 to-purple-500'
            }`}
            aria-hidden="true"
          >
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user?.email || "User"}
            </p>
            <p className={`text-xs capitalize transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-blue-200'
            }`}>
              {user?.role || "Member"}
            </p>
          </div>
        </div>
      </div>

      {/* ✅ ENHANCED: Navigation with Real-Time Analytics */}
      <nav className="flex-1 py-4 overflow-y-auto" role="navigation" aria-label="Platform sections">
        <ul className="space-y-1 px-3">
          {menuItems.map((item) => (
            <li key={item.tab}>
              <button
                onClick={() => handleTabChange(item.tab, item.label)}
                className={`w-full flex items-center justify-between px-4 py-3 text-left rounded-lg transition-all duration-200 group focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  focusMode ? 'focus:ring-yellow-400' : ''
                } ${
                  activeTab === item.tab
                    ? isDarkMode
                      ? "bg-gradient-to-r from-slate-500 to-slate-600 text-white shadow-lg transform scale-[1.02] ring-2 ring-slate-400/50"
                      : "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg transform scale-[1.02]"
                    : isDarkMode
                      ? "text-slate-200 hover:bg-slate-600/50 hover:text-white"
                      : "text-blue-100 hover:bg-blue-700/50 hover:text-white"
                }`}
                aria-current={activeTab === item.tab ? 'page' : undefined}
                aria-describedby={`${item.tab}-description`}
              >
                <div className="flex items-center space-x-3">
                  <span className={`transition-transform duration-200 ${
                    !prefersReducedMotion && (activeTab === item.tab ? "scale-110" : "group-hover:scale-105")
                  }`}>
                    {item.icon}
                  </span>
                  <span className="text-sm font-medium">
                    {item.label}
                  </span>
                </div>
                {item.badge && (
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full shadow-sm transition-all duration-300 ${
                    item.badge === "Enterprise" 
                      ? isDarkMode
                        ? "bg-gradient-to-r from-emerald-500 to-cyan-500 text-white"
                        : "bg-gradient-to-r from-green-400 to-blue-500 text-white"
                    : item.badge === "RBAC"
                      ? isDarkMode
                        ? "bg-gradient-to-r from-violet-500 to-purple-500 text-white"
                        : "bg-gradient-to-r from-purple-400 to-pink-500 text-white"
                    : item.badge === "Live" // 🚀 NEW: Live badge styling for Real-Time Analytics
                      ? isDarkMode
                        ? "bg-gradient-to-r from-red-500 to-pink-500 text-white animate-pulse"
                        : "bg-gradient-to-r from-red-400 to-pink-500 text-white animate-pulse"
                      : isDarkMode
                        ? "bg-gradient-to-r from-slate-500 to-slate-600 text-white"
                        : "bg-gradient-to-r from-blue-400 to-purple-500 text-white"
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
              
              {/* Hidden description for screen readers */}
              <span 
                id={`${item.tab}-description`} 
                className="sr-only"
              >
                {item.description}
                {item.adminOnly ? '. Administrator access required.' : ''}
              </span>
            </li>
          ))}
        </ul>
      </nav>

      {/* ✅ PRESERVED: Footer unchanged */}
      <footer className={`p-4 border-t transition-colors duration-300 ${
        isDarkMode ? 'border-slate-600' : 'border-blue-700'
      }`}>
        <button
          onClick={handleLogoutClick}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            focusMode ? 'focus:ring-red-400' : ''
          } ${
            isDarkMode 
              ? 'text-slate-200 hover:bg-red-600/20 hover:text-red-300 focus:ring-red-400' 
              : 'text-blue-100 hover:bg-red-600/20 hover:text-white focus:ring-red-400'
          }`}
          aria-label="Log out of Ascend"
        >
          <SafeIcon 
            iconName="LogOut" 
            size={18} 
            className={`transition-transform duration-200 ${
              !prefersReducedMotion ? 'group-hover:scale-105' : ''
            }`}
            ariaLabel="Logout door"
          />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </footer>
    </aside>
  );
};

export default Sidebar;