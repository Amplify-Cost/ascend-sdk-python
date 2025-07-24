import React from "react";
import {
  Home,
  Activity,
  AlertCircle,
  LogOut,
  BarChart,
  FileText,
  ClipboardList,
  LifeBuoy,
  User,
  Settings,
  Zap,
  ShieldCheck,
} from "lucide-react";

const Sidebar = ({ user, onLogout, onSupport, onNavigate, activeTab }) => {
  // Base navigation items that everyone can see
  const baseNavItems = [
    { label: "Dashboard", icon: <Home size={18} />, tab: "dashboard" },
    { label: "Agent Actions", icon: <ClipboardList size={18} />, tab: "actions" },
    { label: "Activity Feed", icon: <Activity size={18} />, tab: "activity" },
    { label: "Security Insights", icon: <BarChart size={18} />, tab: "analytics" },
    { label: "Submit Action", icon: <LifeBuoy size={18} />, tab: "support" },
    { label: "Profile", icon: <User size={18} />, tab: "profile" },
  ];

  // Admin-only navigation items - UPDATED TO INCLUDE AUTHORIZATION CENTER
  const adminNavItems = [
    { label: "Alerts", icon: <AlertCircle size={18} />, tab: "alerts" },
    { label: "Rules", icon: <FileText size={18} />, tab: "rules" },
    { label: "Smart Rule Gen", icon: <Zap size={18} />, tab: "smartRules" },
    { 
      label: "Authorization Center", 
      icon: <ShieldCheck size={18} />, 
      tab: "authorization",
      badge: "New"
    },
  ];

  // Combine nav items based on user role
  const navItems = user?.role === "admin" 
    ? [...baseNavItems.slice(0, 4), ...adminNavItems, ...baseNavItems.slice(4)]
    : baseNavItems;

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="text-2xl font-bold px-6 py-4 border-b border-gray-700">
        OW-AI
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
              <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
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
          <LogOut size={16} className="inline mr-2" /> Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;