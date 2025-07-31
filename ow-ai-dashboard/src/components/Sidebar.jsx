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
    LifeBuoy: "🛟",
    User: "👤",
    Zap: "⚡",
    ShieldCheck: "🛡️",
    LogOut: "🚪",
    Brain: "🧠",  // New icon for AI Alert Management
    Target: "🎯"
  };

  const icon = iconMap[iconName] || "📎";
  
  return (
    <span 
      className={`inline-block ${className}`}
      style={{ fontSize: `${size}px`, lineHeight: 1 }}
    >
      {icon}
    </span>
  );
};

const Sidebar = ({ user, onLogout, onSupport, onNavigate, activeTab }) => {
  console.log("🔧 Sidebar rendering with user:", user?.role);
  
  // Base navigation items that everyone can see
  const baseNavItems = [
    { label: "Dashboard", icon: <SafeIcon iconName="Home" size={18} />, tab: "dashboard" },
    { label: "Agent Actions", icon: <SafeIcon iconName="ClipboardList" size={18} />, tab: "actions" },
    { label: "Activity Feed", icon: <SafeIcon iconName="Activity" size={18} />, tab: "activity" },
    { label: "Security Insights", icon: <SafeIcon iconName="BarChart" size={18} />, tab: "analytics" },
    { label: "Submit Action", icon: <SafeIcon iconName="LifeBuoy" size={18} />, tab: "support" },
    { label: "Profile", icon: <SafeIcon iconName="User" size={18} />, tab: "profile" },
  ];

  // Admin-only navigation items
  const adminNavItems = [
    { label: "Alerts", icon: <SafeIcon iconName="AlertCircle" size={18} />, tab: "alerts" },
    { 
      label: "AI Alert Management", 
      icon: <SafeIcon iconName="Brain" size={18} />, 
      tab: "ai-alerts",
      badge: "AI"
    },
    { label: "Rules", icon: <SafeIcon iconName="FileText" size={18} />, tab: "rules" },
    { label: "Smart Rule Gen", icon: <SafeIcon iconName="Zap" size={18} />, tab: "smartRules" },
    {
      label: "Authorization Center",
      icon: <SafeIcon iconName="ShieldCheck" size={18} />,
      tab: "authorization"
    },
  ];

  // Combine nav items based on user role
  const navItems = user?.role === "admin"
    ? [...baseNavItems.slice(0, 4), ...adminNavItems, ...baseNavItems.slice(4)]
    : baseNavItems;

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="text-2xl font-bold px-6 py-4 border-b border-gray-700">
        🛡️ OW-AI
      </div>
      <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <button
            key={item.tab}
            className={`flex items-center justify-between w-full px-3 py-2 rounded-md text-sm font-medium transition ${
              activeTab === item.tab
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            }`}
            onClick={() => onNavigate(item.tab)}
          >
            <div className="flex items-center">
              {item.icon}
              <span className="ml-3">{item.label}</span>
            </div>
            {item.badge && (
              <span className={`text-white text-xs px-2 py-0.5 rounded-full ${
                item.badge === "AI" ? "bg-purple-500" : "bg-red-500"
              }`}>
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>
      <div className="border-t border-gray-700 p-4">
        <p className="text-sm text-gray-400 mb-2">Logged in as:</p>
        <p className="text-sm font-medium">{user?.email}</p>
        {user?.role === "admin" && (
          <span className="inline-block mt-1 text-xs text-blue-400 bg-gray-800 px-2 py-1 rounded-full">
            🛡️ Admin
          </span>
        )}
        <button
          onClick={onLogout}
          className="mt-3 w-full bg-red-600 hover:bg-red-700 text-white text-sm px-3 py-2 rounded-md transition"
        >
          <SafeIcon iconName="LogOut" size={16} className="inline mr-2" /> Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;