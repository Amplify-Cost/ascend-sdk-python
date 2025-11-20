# OW-AI Frontend Quick Reference Guide

## Project Tech Stack
- **React** 19.1.0 + Vite
- **Styling** TailwindCSS 3.4.3 (with dark mode)
- **Routing** Tab-based (switch case in App.jsx)
- **State** React Hooks + Context API
- **Charts** Recharts 2.15.3 + Chart.js
- **Auth** Cookie-based with CSRF protection
- **Icons** Emoji-based SafeIcon component

---

## 1. API Integration Quick Start

### Fetch with Authentication
```javascript
import { fetchWithAuth } from '../utils/fetchWithAuth';

// GET request
const data = await fetchWithAuth('/api/endpoint');

// POST request with CSRF protection (automatic)
const result = await fetchWithAuth('/api/endpoint', {
  method: 'POST',
  body: JSON.stringify({ key: 'value' })
});

// PUT/PATCH/DELETE (CSRF token added automatically)
await fetchWithAuth('/api/endpoint/123', {
  method: 'PUT',
  body: JSON.stringify({ updated: 'data' })
});
```

### Key Features
- Cookie-based authentication (automatic)
- CSRF double-submit cookie protection
- Auto 401 redirect to login
- 403 CSRF error handling
- Enterprise error logging

---

## 2. Component Structure Template

Every admin-only component follows this pattern:

```jsx
import React, { useState, useEffect } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { fetchWithAuth } from '../utils/fetchWithAuth';

const MyNewComponent = ({ getAuthHeaders, user }) => {
  const { isDarkMode } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("tab1");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const result = await fetchWithAuth(`${API_BASE_URL}/api/my-endpoint`);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`p-6 space-y-6 ${isDarkMode ? 'bg-slate-800 text-white' : 'bg-gray-100'}`}>
      {/* Header */}
      <h1 className="text-3xl font-bold">Component Title</h1>

      {/* Tabs */}
      <div className="flex space-x-2 border-b">
        {["tab1", "tab2"].map(tab => (
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
      {loading ? <div>Loading...</div> : 
       error ? <div className="text-red-600">{error}</div> :
       <div>{/* Tab content */}</div>}
    </div>
  );
};

export default MyNewComponent;
```

---

## 3. Styling Patterns

### Dark Mode Pattern
```jsx
const { isDarkMode } = useTheme();

<div className={isDarkMode ? 'bg-slate-700 text-white' : 'bg-white text-gray-900'}>
```

### Card Pattern
```jsx
<div className={`p-6 rounded-xl border transition-all duration-300 hover:scale-105 hover:shadow-lg ${
  isDarkMode 
    ? 'bg-slate-700 border-slate-600' 
    : 'bg-white border-gray-300 shadow-sm'
}`}>
```

### Button Patterns
```jsx
{/* Primary Button */}
<button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  Submit
</button>

{/* Secondary Button */}
<button className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">
  Cancel
</button>

{/* Danger Button */}
<button className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
  Delete
</button>
```

### Table Pattern
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

### Modal Pattern
```jsx
<div className="fixed inset-0 bg-black bg-opacity-40 z-50 flex items-center justify-center">
  <div className="bg-white p-6 rounded-lg w-full max-w-md shadow-xl">
    <h3 className="text-lg font-semibold mb-4">Modal Title</h3>
    {/* Content */}
    <div className="flex justify-end space-x-2">
      <button onClick={onClose} className="px-4 py-2 bg-gray-200 rounded">Cancel</button>
      <button onClick={onSubmit} className="px-4 py-2 bg-blue-600 text-white rounded">Submit</button>
    </div>
  </div>
</div>
```

---

## 4. State Management Patterns

### Simple Data Fetching
```javascript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  const fetch = async () => {
    try {
      setLoading(true);
      const result = await fetchWithAuth('/api/endpoint');
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  fetch();
}, []);
```

### Data Polling
```javascript
useEffect(() => {
  const fetch = async () => {
    try {
      const result = await fetchWithAuth('/api/endpoint');
      setData(result);
    } catch (err) {
      setError(err.message);
    }
  };

  fetch();
  const interval = setInterval(fetch, 300000); // Poll every 5 minutes
  
  return () => clearInterval(interval);
}, [activeTab]); // Re-fetch when tab changes
```

### Parallel Data Loading
```javascript
useEffect(() => {
  const fetchMultiple = async () => {
    try {
      setLoading(true);
      const [results1, results2, results3] = await Promise.all([
        fetchWithAuth('/api/endpoint1'),
        fetchWithAuth('/api/endpoint2'),
        fetchWithAuth('/api/endpoint3')
      ]);
      setData1(results1);
      setData2(results2);
      setData3(results3);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  fetchMultiple();
}, []);
```

---

## 5. Common Components & Patterns

### Metric Card (from Dashboard.jsx)
```jsx
const MetricCard = ({ title, value, change, changeType, icon, color, trend }) => {
  const { isDarkMode } = useTheme();
  
  return (
    <div className={`p-6 rounded-xl border transition-all duration-300 hover:scale-105 ${
      isDarkMode ? 'bg-slate-700 border-slate-600' : 'bg-white border-gray-300'
    }`}>
      <div className="flex items-center justify-between">
        <div>
          <p className={`text-sm font-medium ${isDarkMode ? 'text-slate-300' : 'text-gray-700'}`}>
            {title}
          </p>
          <p className={`text-2xl font-bold mt-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {value}
          </p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );
};
```

### Activity Item Pattern
```jsx
<div className={`flex items-start space-x-3 p-3 rounded-lg ${
  isDarkMode ? 'bg-slate-600/50' : 'bg-gray-100'
}`}>
  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
    type === 'alert' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
  }`}>
    {icon}
  </div>
  <div className="flex-1">
    <p className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
      {title}
    </p>
    <p className={`text-xs mt-1 ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}>
      {time} • {agent}
    </p>
  </div>
</div>
```

### SafeIcon (Emoji Icons)
```jsx
import { SafeIcon } from "./Sidebar";

<SafeIcon iconName="Home" size={18} ariaLabel="Home icon" />
// Available icons: Home, Activity, BarChart, FileText, Settings, Shield, etc.
```

---

## 6. Integration into App.jsx

### Add Component Import
```javascript
import RiskScoringConfiguration from "./components/RiskScoringConfiguration";
```

### Add Tab Case in renderAppContent()
```javascript
case "risk-scoring":
  return user?.role === "admin" ? 
    contentWithTransition(<RiskScoringConfiguration getAuthHeaders={getAuthHeaders} user={user} />) 
    : adminRequiredMessage;
```

### Add Menu Item in Sidebar.jsx
```javascript
const menuItems = [
  // ... existing items ...
  {
    label: "Risk Scoring",
    icon: <SafeIcon iconName="Target" size={18} />,
    tab: "risk-scoring",
    description: "Configure risk scoring thresholds and weights",
    adminOnly: true
  }
];
```

---

## 7. File Locations Reference

### Core Files
- **App.jsx** - Main app component, routing logic, auth state
- **Sidebar.jsx** - Navigation menu with tab switching
- **Dashboard.jsx** - Example of metric cards and component patterns

### Utilities
- **fetchWithAuth.js** - API fetch wrapper with CSRF protection
- **logger.js** - Logging utility
- **api.js** - API endpoints configuration

### Contexts
- **ThemeContext.jsx** - Dark/light mode toggle and theme colors
- **AccessibilityContext.jsx** - Accessibility features

### Services
- **apiService.js** - API service layer (singleton)
- **ApprovalService.js** - Approval workflow service

### Hooks
- **useEnterpriseApi.js** - Custom hooks for API data fetching
- **usePolicyCheck.js** - Policy validation hook

---

## 8. Development Commands

```bash
# Start development server
npm run dev

# Start with local backend
npm run dev:local

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

---

## 9. Common Issues & Solutions

### Issue: CSRF Token Missing
**Solution**: Ensure login endpoint sets `owai_csrf` cookie. fetchWithAuth extracts it automatically.

### Issue: Dark Mode Not Working
**Solution**: Check that component uses `const { isDarkMode } = useTheme()` and applies conditional classes.

### Issue: 401 Unauthorized
**Solution**: Session expired. fetchWithAuth auto-redirects to login. Check cookie-based auth setup.

### Issue: Data Not Updating
**Solution**: Add dependency array to useEffect or call refetch function after POST/PUT/DELETE.

---

## 10. Best Practices

1. Always use `fetchWithAuth()` instead of raw `fetch()` for API calls
2. Include dark mode variants: `className={isDarkMode ? 'dark:classes' : 'light:classes'}`
3. Wrap admin-only features: `user?.role === "admin" ? <Component /> : <AdminRequired />`
4. Add loading/error states for all async operations
5. Use TailwindCSS classes instead of inline styles
6. Pass `getAuthHeaders` and `user` props from App.jsx
7. Poll data with cleanup: `return () => clearInterval(interval)`
8. Use SafeIcon for consistent iconography
9. Follow metric card pattern for consistent styling
10. Test in both light and dark modes

---

## 11. Example: Risk Scoring Configuration Dashboard

See `/Users/mac_001/OW_AI_Project/FRONTEND_ARCHITECTURE.md` (Section 8) for complete example code.

Key points:
- Use `/api/risk-scoring/config` endpoint
- Create tabs for: Thresholds, Weights, Rules
- Display current values in MetricCards
- Provide form inputs for updates
- Add Save button with POST request
- Show loading/error states
- Support dark mode

