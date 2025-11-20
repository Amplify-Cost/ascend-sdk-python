# OW-AI Frontend Architecture Summary

## Project Overview
- **Framework**: React 19.1.0 + Vite
- **Styling**: TailwindCSS 3.4.3 (primary styling method)
- **Routing**: React Router DOM 7.9.4
- **State Management**: React Hooks (useState, useEffect, useContext)
- **API Communication**: Native fetch API + custom `fetchWithAuth` wrapper
- **Charts**: Recharts 2.15.3 + Chart.js 4.4.9
- **Icons**: Emoji icons (SafeIcon component pattern)
- **Authentication**: Cookie-based (with CSRF protection)

## 1. Main Dashboard Structure

### Primary Dashboard Component
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/Dashboard.jsx`

**Architecture Pattern**:
```jsx
// Reusable metric card component
const MetricCard = ({ title, value, change, changeType, icon, color, trend }) => {
  const { isDarkMode } = useTheme();
  return (
    <div className={`p-6 rounded-xl border transition-all duration-300 hover:scale-105 hover:shadow-lg ${
      isDarkMode 
        ? 'bg-slate-700 border-slate-600 hover:border-slate-500' 
        : 'bg-white border-gray-300 hover:border-gray-400 shadow-sm'
    }`}>
      {/* Content */}
    </div>
  );
};
```

### Tab-Based Architecture
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/App.jsx` (lines 308-429)

The app uses a switch-case routing pattern in `renderAppContent()`:
```javascript
switch (activeTab) {
  case "dashboard":
    return contentWithTransition(<Dashboard getAuthHeaders={getAuthHeaders} />);
  case "analytics":
    return contentWithTransition(<SecurityInsights getAuthHeaders={getAuthHeaders} />);
  case "realtime-analytics":
    return contentWithTransition(<RealTimeAnalyticsDashboard getAuthHeaders={getAuthHeaders} user={user} />);
  case "auth":
    return user?.role === "admin" ? 
      contentWithTransition(<AgentAuthorizationDashboard getAuthHeaders={getAuthHeaders} user={user} />) 
      : adminRequiredMessage;
  // ... more cases
}
```

### Layout Components
- **Sidebar**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/Sidebar.jsx`
- **Breadcrumb Navigation**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/Breadcrumb.jsx`
- **Global Search**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/GlobalSearch.jsx`

---

## 2. API Integration Patterns

### Primary Fetch Method: `fetchWithAuth`
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/utils/fetchWithAuth.js`

Features:
- Cookie-based authentication (automatic via `credentials: "include"`)
- CSRF double-submit cookie protection (X-CSRF-Token header)
- Automatic 401 redirect to login
- 403 CSRF validation error handling
- Enterprise error logging

```javascript
const fetchWithAuth = async (url, options = {}) => {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  const method = (options.method || "GET").toUpperCase();

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add CSRF token for mutating methods
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }
  }

  const config = {
    ...options,
    headers,
    credentials: "include", // Critical: sends cookies
  };

  const response = await fetch(fullUrl, config);
  // Error handling...
  return await response.json();
};
```

### Authentication Headers
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/App.jsx` (lines 259-306)

```javascript
const getAuthHeaders = () => {
  const headers = {
    "Content-Type": "application/json"
  };

  // Add Bearer token if available
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add CSRF token for cookie auth
  const csrfToken = getCsrfToken();
  if (csrfToken && !token) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  return headers;
};
```

### API Endpoints Configuration
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/config/api.js`

```javascript
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  auth: {
    login: "/auth/login",
    logout: "/auth/logout",
    refresh: "/auth/refresh",
    csrf: "/auth/csrf",
    updateProfile: "/auth/update-profile"
  },
  agentActions: {
    list: "/agent-actions",
    submit: "/agent-action",
    approve: (id) => `/agent-action/${id}/approve`,
    reject: (id) => `/agent-action/${id}/reject`
  }
};
```

### API Service Layer
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/services/apiService.js`

Provides singleton service with methods for common operations:
```javascript
class ApiService {
  async request(endpoint, options = {}) { /* ... */ }
  async login(email, password) { /* ... */ }
  async getPolicies() { /* ... */ }
  async createPolicy(policyData) { /* ... */ }
  // ... more methods
}
export default new ApiService();
```

### Custom Hook Pattern
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/hooks/useEnterpriseApi.js`

```javascript
export function useAuthorizationData() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const result = await EnterpriseApiService.getAuthorizationData();
      setData(result.data || result || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
```

---

## 3. UI Component Library & Styling

### Primary Styling Method: TailwindCSS
- **Setup**: `tailwindcss: ^3.4.3` in package.json
- **Import**: `src/index.css` contains Tailwind directives
- **Dark Mode**: Automatic via `isDarkMode` context + `dark:` prefix classes

### Theme Context
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/contexts/ThemeContext.jsx`

```javascript
export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('ow-ai-theme');
    return saved ? (saved === 'dark') : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Light & Dark theme color palettes
  const theme = {
    light: {
      primary: '#1e40af',
      background: '#f8fafc',
      cardBackground: '#ffffff',
      border: '#e2e8f0',
      text: '#1e293b',
      // ...
    },
    dark: {
      primary: '#60a5fa',
      background: '#1e293b',
      cardBackground: '#334155',
      border: '#475569',
      text: '#ffffff',
      // ...
    }
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme, theme: currentTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
```

### Common Component Patterns

#### Metric Card (Re-usable Pattern)
```jsx
<div className={`p-6 rounded-xl border transition-all duration-300 hover:scale-105 hover:shadow-lg ${
  isDarkMode 
    ? 'bg-slate-700 border-slate-600 hover:border-slate-500' 
    : 'bg-white border-gray-300 hover:border-gray-400 shadow-sm'
}`}>
  {/* Content */}
</div>
```

#### Activity/List Item
```jsx
<div className={`flex items-start space-x-3 p-3 rounded-lg transition-colors duration-300 ${
  isDarkMode ? 'bg-slate-600/50' : 'bg-gray-100 border border-gray-200'
}`}>
  {/* Icon circle */}
  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
    activity.type === 'alert' 
      ? 'bg-red-100 text-red-600' 
      : activity.type === 'approval'
      ? 'bg-green-100 text-green-600'
      : 'bg-blue-100 text-blue-600'
  }`}>
    {activityIcon}
  </div>
  {/* Content */}
</div>
```

#### Modal Pattern
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/SupportModal.jsx`

```jsx
<div className="fixed inset-0 bg-black bg-opacity-40 z-50 flex items-center justify-center">
  <div className="bg-white p-6 rounded-lg w-full max-w-md shadow-xl">
    <h3 className="text-lg font-semibold mb-4">Modal Title</h3>
    {/* Content */}
    <div className="flex justify-end space-x-2">
      <button className="px-4 py-2 text-sm bg-gray-200 rounded hover:bg-gray-300">
        Cancel
      </button>
      <button className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
        Submit
      </button>
    </div>
  </div>
</div>
```

#### Table Pattern
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/AuditTrailModal.jsx`

```jsx
<table className="w-full text-sm table-auto">
  <thead>
    <tr className="bg-gray-100">
      <th className="px-3 py-2 text-left">Column 1</th>
      <th className="px-3 py-2 text-left">Column 2</th>
    </tr>
  </thead>
  <tbody>
    {items.map((item) => (
      <tr key={item.id} className="border-t">
        <td className="px-3 py-1">{item.field1}</td>
        <td className="px-3 py-1">{item.field2}</td>
      </tr>
    ))}
  </tbody>
</table>
```

### Icon Component Pattern (SafeIcon)
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/Sidebar.jsx`

Uses emoji icons to avoid import issues:
```jsx
const SafeIcon = ({ iconName, size = 18, className = "", ariaLabel }) => {
  const iconMap = {
    Home: "🏠",
    Activity: "📊",
    AlertCircle: "⚠️",
    BarChart: "📈",
    // ... more icons
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
```

### Common TailwindCSS Classes Used
- **Spacing**: `p-6`, `space-y-4`, `space-x-3`
- **Typography**: `text-lg`, `font-semibold`, `font-bold`, `text-sm`
- **Colors**: `text-gray-700`, `bg-white`, `border-gray-300`, `text-blue-600`
- **Dark Mode**: `dark:bg-slate-700`, `dark:text-white`, `dark:border-slate-600`
- **Layout**: `flex`, `items-center`, `justify-between`, `rounded-lg`, `rounded-xl`
- **Effects**: `transition-all`, `duration-300`, `hover:scale-105`, `hover:shadow-lg`
- **Responsive**: `lg:flex-row`, `flex-col`

---

## 4. State Management

### React Hooks Pattern
Primary state management uses React Hooks:

```javascript
const [dashboardData, setDashboardData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
const [activeTab, setActiveTab] = useState("pending");

useEffect(() => {
  fetchData();
  const interval = setInterval(fetchData, 300000); // 5 min polling
  return () => clearInterval(interval);
}, [activeTab]);
```

### Context API
**Files**:
- `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/contexts/ThemeContext.jsx`
- `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/contexts/AccessibilityContext.jsx`

Usage pattern:
```javascript
const { isDarkMode, toggleTheme } = useTheme();
const { announce } = useScreenReaderAnnounce();
```

### Data Fetching Patterns

**Fetch with Polling**:
```javascript
useEffect(() => {
  fetchPendingActions().then(() => {
    fetchDashboardData();
    fetchApprovalMetrics();
  });

  const interval = setInterval(() => {
    // Refetch data
  }, 300000); // 5 minutes

  return () => clearInterval(interval);
}, [activeTab]);
```

**Parallel Data Loading**:
```javascript
const [metricsResult, predictiveResult, performanceResult] = await Promise.allSettled([
  fetchWithAuth('/api/analytics/realtime/metrics'),
  fetchWithAuth('/api/analytics/predictive/trends'),
  fetchWithAuth('/api/analytics/performance/system')
]);
```

---

## 5. Routing Architecture

### Tab-Based Routing
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/App.jsx` (lines 76-81, 308-429)

```javascript
const [activeTab, setActiveTab] = useState("dashboard");

const handleTabChange = (tab) => {
  setPageTransition(true);
  setTimeout(() => {
    setActiveTab(tab);
    setPageTransition(false);
  }, 150);
};
```

### Sidebar Menu Structure
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/Sidebar.jsx`

```javascript
const menuItems = [
  { 
    label: "Dashboard", 
    icon: <SafeIcon iconName="Home" />, 
    tab: "dashboard",
    description: "Main security overview and metrics"
  },
  { 
    label: "Analytics", 
    icon: <SafeIcon iconName="BarChart" />, 
    tab: "analytics",
    description: "Security analytics and insights"
  },
  // ... more items
];
```

### Role-Based Access Control
```javascript
case "auth":
  return user?.role === "admin" ? 
    contentWithTransition(<AgentAuthorizationDashboard />) 
    : adminRequiredMessage;
```

---

## 6. Component Directory Structure

```
src/
├── components/
│   ├── Dashboard.jsx                          # Main dashboard
│   ├── AgentAuthorizationDashboard.jsx        # Authorization system
│   ├── RealTimeAnalyticsDashboard.jsx         # Real-time monitoring
│   ├── Sidebar.jsx                            # Navigation
│   ├── Breadcrumb.jsx                         # Breadcrumb navigation
│   ├── GlobalSearch.jsx                       # Global search
│   ├── modals/
│   │   ├── SupportModal.jsx                   # Modal template
│   │   ├── AuditTrailModal.jsx                # Table inside modal
│   │   ├── AgentHistoryModal.jsx
│   │   └── PolicyBlockedModal.jsx
│   ├── forms/
│   │   ├── SubmitActionForm.jsx               # Form pattern
│   │   └── AgentActionSubmitPanel.jsx
│   ├── enterprise/
│   │   ├── EnterpriseCard.jsx                 # Reusable card
│   │   ├── SkeletonCard.jsx                   # Loading state
│   │   ├── ErrorCard.jsx                      # Error state
│   │   └── EmptyCard.jsx                      # Empty state
│   └── shared/
│       └── PolicyFusionDisplay.jsx
├── contexts/
│   ├── ThemeContext.jsx                       # Dark/light mode
│   └── AccessibilityContext.jsx               # a11y features
├── hooks/
│   ├── useEnterpriseApi.js                    # Custom API hooks
│   └── usePolicyCheck.js
├── services/
│   ├── apiService.js                          # API service layer
│   └── ApprovalService.js
├── utils/
│   ├── fetchWithAuth.js                       # Fetch wrapper
│   ├── logger.js                              # Logging utility
│   └── pdfGenerator.js
└── config/
    └── api.js                                 # API configuration
```

---

## 7. Key Integration Patterns for Risk Scoring Dashboard

### Example: How AgentAuthorizationDashboard Uses These Patterns
**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx`

```jsx
import React, { useState, useEffect } from "react";
import { fetchWithAuth } from '../utils/fetchWithAuth';

const AgentAuthorizationDashboard = ({ getAuthHeaders, user }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("pending");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 300000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetchWithAuth(`${API_BASE_URL}/api/authorization/dashboard`);
      setDashboardData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Tab rendering logic
  const renderContent = () => {
    switch (activeTab) {
      case "pending":
        return <div>{/* pending tab content */}</div>;
      case "workflows":
        return <div>{/* workflows tab content */}</div>;
      default:
        return <div>Not found</div>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab buttons */}
      <div className="flex space-x-2 border-b">
        {["pending", "workflows"].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 ${activeTab === tab ? 'border-b-2 border-blue-600' : ''}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? <div>Loading...</div> : renderContent()}
    </div>
  );
};

export default AgentAuthorizationDashboard;
```

---

## 8. Building a Risk Scoring Configuration Dashboard

### Where to Add It
1. Create: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/RiskScoringConfiguration.jsx`
2. Import in `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/App.jsx`
3. Add tab case in `renderAppContent()` 
4. Add menu item in Sidebar

### Basic Template Following Patterns

```jsx
import React, { useState, useEffect } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { fetchWithAuth } from '../utils/fetchWithAuth';

const RiskScoringConfiguration = ({ getAuthHeaders, user }) => {
  const { isDarkMode } = useTheme();
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("thresholds");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchRiskConfig();
  }, []);

  const fetchRiskConfig = async () => {
    try {
      setLoading(true);
      const data = await fetchWithAuth(`${API_BASE_URL}/api/risk-scoring/config`);
      setConfig(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`p-6 space-y-6 transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-800 text-white' : 'bg-gray-100 text-gray-900'
    }`}>
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Risk Scoring Configuration</h1>
      </div>

      {/* Tabs */}
      <div className={`flex space-x-2 border-b transition-colors duration-300 ${
        isDarkMode ? 'border-slate-600' : 'border-gray-300'
      }`}>
        {["thresholds", "weights", "rules"].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium transition-colors duration-300 ${
              activeTab === tab
                ? isDarkMode ? 'border-b-2 border-blue-400 text-blue-400' : 'border-b-2 border-blue-600 text-blue-600'
                : isDarkMode ? 'text-slate-400' : 'text-gray-600'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : error ? (
        <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-red-900/30' : 'bg-red-100'}`}>
          Error: {error}
        </div>
      ) : (
        <div className={`p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600' 
            : 'bg-white border-gray-300'
        }`}>
          {activeTab === "thresholds" && <ThresholdsTab config={config} />}
          {activeTab === "weights" && <WeightsTab config={config} />}
          {activeTab === "rules" && <RulesTab config={config} />}
        </div>
      )}
    </div>
  );
};

export default RiskScoringConfiguration;
```

### Integration Checklist
- [x] Use `useTheme()` for dark mode support
- [x] Use `fetchWithAuth()` for API calls with CSRF protection
- [x] Pass `getAuthHeaders` from App.jsx (already available in props)
- [x] Use TailwindCSS classes with dark mode variants
- [x] Tab-based UI with state management
- [x] Loading/Error/Empty states
- [x] Modal pattern for forms if needed
- [x] Permission checks with `user?.role === "admin"`
- [x] Follow metric card pattern for displays
- [x] Use page transition effect (wrap in contentWithTransition)

---

## Quick Reference: Common API Patterns

### Fetching Data
```javascript
const data = await fetchWithAuth('/api/endpoint');
```

### Creating Data
```javascript
await fetchWithAuth('/api/endpoint', {
  method: 'POST',
  body: JSON.stringify({ /* data */ })
});
```

### Updating Data
```javascript
await fetchWithAuth('/api/endpoint/123', {
  method: 'PUT',
  body: JSON.stringify({ /* updated data */ })
});
```

### Deleting Data
```javascript
await fetchWithAuth('/api/endpoint/123', {
  method: 'DELETE'
});
```

### Using Dark Mode
```javascript
const { isDarkMode } = useTheme();

<div className={isDarkMode ? 'bg-slate-700 text-white' : 'bg-white text-gray-900'}>
```

---

## Summary
The frontend uses:
- **Fetch**: Native fetch + custom `fetchWithAuth` wrapper
- **State**: React Hooks (useState, useEffect, useContext)
- **Styling**: TailwindCSS with theme context
- **Auth**: Cookie-based with CSRF protection
- **Structure**: Tab-based routing with sidebar navigation
- **Patterns**: Reusable metric cards, modals, tables, forms
- **Charts**: Recharts library
- **Icons**: Emoji-based SafeIcon component

All components follow a consistent pattern with dark mode support, proper loading states, error handling, and accessibility considerations.
