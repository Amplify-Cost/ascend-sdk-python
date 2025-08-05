import React from "react";
import { useTheme } from "../contexts/ThemeContext";

// ✅ SAFE: Using emoji icons to avoid import issues
const SafeIcon = ({ iconName, size = 18, className = "" }) => {
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
  };

  return (
    <span
      className={`inline-flex items-center justify-center ${className}`}
      style={{ fontSize: `${size}px` }}
    >
      {iconMap[iconName] || "📄"}
    </span>
  );
};

const Sidebar = ({ activeTab, setActiveTab, user, handleLogout }) => {
  const { isDarkMode, toggleTheme } = useTheme();
  console.log("🔧 Sidebar rendering with user:", user?.role);

  const menuItems = [
    { label: "Dashboard", icon: <SafeIcon iconName="Home" size={18} />, tab: "dashboard" },
    { label: "Analytics", icon: <SafeIcon iconName="BarChart" size={18} />, tab: "analytics" },
    { label: "Activity", icon: <SafeIcon iconName="Activity" size={18} />, tab: "activity" },
    { label: "Reports", icon: <SafeIcon iconName="FileText" size={18} />, tab: "reports" },
    { label: "Support", icon: <SafeIcon iconName="LifeBuoy" size={18} />, tab: "support" },
  ];

  // Add admin-only features
  if (user?.role === "admin") {
    menuItems.push(
      { label: "Authorization Center", icon: <SafeIcon iconName="Shield" size={18} />, tab: "auth" },
      { label: "🧠 AI Alert Management", icon: <SafeIcon iconName="AlertCircle" size={18} />, tab: "ai-alerts" },
      { 
        label: "🧠 AI Rule Engine", 
        icon: <SafeIcon iconName="Zap" size={18} />, 
        tab: "smartRules",
        badge: "Enterprise"
      },
      { 
        label: "👥 User Management", 
        icon: <SafeIcon iconName="Users" size={18} />, 
        tab: "users",
        badge: "RBAC"
      },
      { label: "Settings", icon: <SafeIcon iconName="Settings" size={18} />, tab: "settings" }
    );
  }

  return (
    <div className={`w-64 h-screen flex flex-col shadow-xl transition-all duration-300 ${
      isDarkMode 
        ? 'bg-gradient-to-b from-slate-900 to-slate-800 text-slate-100' 
        : 'bg-gradient-to-b from-blue-900 to-blue-800 text-white'
    }`}>
      {/* Header */}
      <div className={`p-6 border-b transition-colors duration-300 ${
        isDarkMode ? 'border-slate-700' : 'border-blue-700'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className={`text-xl font-bold transition-all duration-300 ${
              isDarkMode 
                ? 'bg-gradient-to-r from-slate-200 to-white bg-clip-text text-transparent'
                : 'bg-gradient-to-r from-blue-200 to-white bg-clip-text text-transparent'
            }`}>
              OW AI Platform
            </h2>
            <p className={`text-sm mt-1 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-300' : 'text-blue-200'
            }`}>
              Enterprise Security
            </p>
          </div>
          
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg transition-all duration-300 hover:scale-110 ${
              isDarkMode 
                ? 'bg-slate-700 hover:bg-slate-600 text-yellow-400' 
                : 'bg-blue-700 hover:bg-blue-600 text-yellow-300'
            }`}
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            <SafeIcon iconName={isDarkMode ? "Sun" : "Moon"} size={16} />
          </button>
        </div>
      </div>

      {/* User Info */}
      <div className={`p-4 border-b transition-colors duration-300 ${
        isDarkMode 
          ? 'border-slate-700 bg-slate-800/50' 
          : 'border-blue-700 bg-blue-800/50'
      }`}>
        <div className="flex items-center space-x-3">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-sm transition-all duration-300 ${
            isDarkMode 
              ? 'bg-gradient-to-r from-slate-400 to-slate-500' 
              : 'bg-gradient-to-r from-blue-400 to-purple-500'
          }`}>
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium truncate transition-colors duration-300 ${
              isDarkMode ? 'text-slate-100' : 'text-white'
            }`}>
              {user?.email || "User"}
            </p>
            <p className={`text-xs capitalize transition-colors duration-300 ${
              isDarkMode ? 'text-slate-300' : 'text-blue-200'
            }`}>
              {user?.role || "Member"}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-3">
          {menuItems.map((item) => (
            <li key={item.tab}>
              <button
                onClick={() => setActiveTab(item.tab)}
                className={`w-full flex items-center justify-between px-4 py-3 text-left rounded-lg transition-all duration-200 group ${
                  activeTab === item.tab
                    ? isDarkMode
                      ? "bg-gradient-to-r from-slate-600 to-slate-700 text-slate-100 shadow-lg transform scale-[1.02] ring-2 ring-slate-500/50"
                      : "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg transform scale-[1.02]"
                    : isDarkMode
                      ? "text-slate-300 hover:bg-slate-700/50 hover:text-slate-100"
                      : "text-blue-100 hover:bg-blue-700/50 hover:text-white"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className={`transition-transform duration-200 ${
                    activeTab === item.tab ? "scale-110" : "group-hover:scale-105"
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
                      : isDarkMode
                        ? "bg-gradient-to-r from-slate-500 to-slate-600 text-white"
                        : "bg-gradient-to-r from-blue-400 to-purple-500 text-white"
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className={`p-4 border-t transition-colors duration-300 ${
        isDarkMode ? 'border-slate-700' : 'border-blue-700'
      }`}>
        <button
          onClick={handleLogout}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
            isDarkMode 
              ? 'text-slate-300 hover:bg-red-600/20 hover:text-red-400' 
              : 'text-blue-100 hover:bg-red-600/20 hover:text-white'
          }`}
        >
          <SafeIcon iconName="LogOut" size={18} className="group-hover:scale-105 transition-transform" />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;