import React from "react";

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
      { label: "User Management", icon: <SafeIcon iconName="Users" size={18} />, tab: "users" },
      { label: "Settings", icon: <SafeIcon iconName="Settings" size={18} />, tab: "settings" }
    );
  }

  return (
    <div className="w-64 bg-gradient-to-b from-blue-900 to-blue-800 text-white h-screen flex flex-col shadow-xl">
      {/* Header */}
      <div className="p-6 border-b border-blue-700">
        <h2 className="text-xl font-bold bg-gradient-to-r from-blue-200 to-white bg-clip-text text-transparent">
          OW AI Platform
        </h2>
        <p className="text-blue-200 text-sm mt-1">Enterprise Security</p>
      </div>

      {/* User Info */}
      <div className="p-4 border-b border-blue-700 bg-blue-800/50">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user?.email || "User"}
            </p>
            <p className="text-xs text-blue-200 capitalize">
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
                    ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg transform scale-[1.02]"
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
                  <span className="px-2 py-1 text-xs bg-gradient-to-r from-green-400 to-blue-500 text-white rounded-full font-semibold shadow-sm">
                    {item.badge}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-blue-700">
        <button
          onClick={handleLogout}
          className="w-full flex items-center space-x-3 px-4 py-3 text-blue-100 hover:bg-red-600/20 hover:text-white rounded-lg transition-all duration-200 group"
        >
          <SafeIcon iconName="LogOut" size={18} className="group-hover:scale-105 transition-transform" />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;