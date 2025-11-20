# Frontend Architecture Exploration - Master Guide

This guide documents the complete frontend architecture for the OW-AI pilot platform and provides a blueprint for building seamlessly integrated components like the Risk Scoring Configuration Dashboard.

## Documentation Files

### 1. FRONTEND_ARCHITECTURE.md (Primary Reference)
**Comprehensive guide with 8 major sections:**
- Main Dashboard Structure (tab routing, layouts)
- API Integration Patterns (fetchWithAuth, service layer, hooks)
- UI Component Library (TailwindCSS, themes, patterns)
- State Management (hooks, context, polling)
- Routing Architecture (tab-based, role-based access)
- Component Directory Structure
- Key Integration Patterns (template with examples)
- Building Risk Scoring Configuration Dashboard

**Best for:** Understanding the complete architecture and building complex components

### 2. FRONTEND_QUICK_REFERENCE.md (Practical Guide)
**Quick lookup guide with copy-paste templates:**
- API Integration Quick Start
- Component Structure Template
- Styling Patterns (cards, buttons, tables, modals)
- State Management Patterns
- Common Components & Patterns
- Integration into App.jsx
- File Location Reference
- Development Commands
- Common Issues & Solutions
- Best Practices

**Best for:** Quick lookups, copy-paste templates, troubleshooting

## Quick Overview

### Technology Stack
```
React 19.1.0 | Vite | TailwindCSS 3.4.3 | Recharts | React Hooks
Cookie-based Auth (CSRF protected) | No Redux
```

### Core Architecture
```
App.jsx (main routing via activeTab state)
├── Sidebar (navigation with menu items)
├── Main Content (switch case rendering)
└── Theme/Accessibility Providers

API Layer:
fetchWithAuth() → Service Layer → Components

State Management:
React Hooks (useState, useEffect) + Context API
```

### Key Patterns
1. **Tab-Based Routing**: Switch case on activeTab state (not React Router)
2. **API Integration**: fetchWithAuth() wrapper with CSRF protection
3. **Styling**: TailwindCSS with dark mode via ThemeContext
4. **Components**: MetricCard, Modal, Table, ActivityFeed patterns
5. **State**: Loading/Error/Data pattern for async operations

## Building the Risk Scoring Configuration Dashboard

### Step-by-Step

#### 1. Create Component File
```javascript
// /src/components/RiskScoringConfiguration.jsx
import React, { useState, useEffect } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { fetchWithAuth } from '../utils/fetchWithAuth';

const RiskScoringConfiguration = ({ getAuthHeaders, user }) => {
  // Template from FRONTEND_ARCHITECTURE.md Section 8
  // ... component code ...
};

export default RiskScoringConfiguration;
```

#### 2. Add to App.jsx
```javascript
// Import
import RiskScoringConfiguration from "./components/RiskScoringConfiguration";

// Add case in renderAppContent()
case "risk-scoring":
  return user?.role === "admin" ? 
    contentWithTransition(<RiskScoringConfiguration getAuthHeaders={getAuthHeaders} user={user} />) 
    : adminRequiredMessage;
```

#### 3. Add to Sidebar.jsx
```javascript
// Add to menuItems array
{
  label: "Risk Scoring",
  icon: <SafeIcon iconName="Target" size={18} />,
  tab: "risk-scoring",
  description: "Configure risk scoring thresholds and weights",
  adminOnly: true
}
```

#### 4. Implement Component Features
- **Tabs**: Thresholds, Weights, Rules
- **Display**: MetricCard pattern for current values
- **Input**: Form inputs for configuration changes
- **Actions**: Save button with POST request
- **States**: Loading, error, success
- **Styling**: Dark mode support with isDarkMode context

#### 5. API Integration
```javascript
// Fetch config
const config = await fetchWithAuth('/api/risk-scoring/config');

// Update config
await fetchWithAuth('/api/risk-scoring/config', {
  method: 'POST',
  body: JSON.stringify(updatedConfig)
});
```

## File Structure Reference

### Required Files (Located in Frontend)
```
/src/
├── App.jsx                                    # Main routing
├── components/
│   ├── Dashboard.jsx                          # Example patterns
│   ├── AgentAuthorizationDashboard.jsx        # Complex example
│   ├── RealTimeAnalyticsDashboard.jsx         # Advanced example
│   ├── Sidebar.jsx                            # Navigation
│   └── RiskScoringConfiguration.jsx           # YOUR COMPONENT
├── contexts/
│   ├── ThemeContext.jsx                       # Dark/light mode
│   └── AccessibilityContext.jsx
├── utils/
│   ├── fetchWithAuth.js                       # API wrapper
│   ├── logger.js                              # Logging
│   └── pdfGenerator.js
├── services/
│   ├── apiService.js                          # Service layer
│   └── ApprovalService.js
├── hooks/
│   ├── useEnterpriseApi.js                    # Data hooks
│   └── usePolicyCheck.js
└── config/
    └── api.js                                 # Endpoints
```

## Common Code Snippets

### Fetch Data with Loading State
```javascript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  const fetchData = async () => {
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
  fetchData();
}, []);
```

### Dark Mode Styling
```javascript
const { isDarkMode } = useTheme();

<div className={`p-6 rounded-xl border ${
  isDarkMode 
    ? 'bg-slate-700 border-slate-600 text-white' 
    : 'bg-white border-gray-300 text-gray-900'
}`}>
```

### Tab Navigation
```javascript
const [activeTab, setActiveTab] = useState("tab1");

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

{activeTab === "tab1" && <Tab1Content />}
{activeTab === "tab2" && <Tab2Content />}
```

### Admin-Only Access Control
```javascript
{user?.role === "admin" ? (
  <RiskScoringConfiguration getAuthHeaders={getAuthHeaders} user={user} />
) : (
  <div className="p-6 text-center text-red-600">
    Admin access required
  </div>
)}
```

## Testing Checklist

- [ ] Component renders with loading state
- [ ] Data fetches correctly via fetchWithAuth
- [ ] Dark mode toggle works
- [ ] Admin-only access control works
- [ ] CSRF token present in POST requests
- [ ] Error messages display correctly
- [ ] Form submission updates data
- [ ] Tab switching works smoothly
- [ ] Mobile responsive (if needed)
- [ ] Accessibility features work (aria labels, keyboard nav)

## Debugging Tips

1. **Check CSRF Token**: Open DevTools Network tab, look for X-CSRF-Token header
2. **Check Auth**: Verify cookies are being sent (credentials: "include")
3. **Check Dark Mode**: Toggle theme to ensure all classes have dark: prefix
4. **Check Routing**: Verify activeTab value in React DevTools
5. **Check Console**: Use logger utility for debugging (logger.debug, logger.error)

## Additional Resources

- **FRONTEND_ARCHITECTURE.md**: Complete architecture guide with examples
- **FRONTEND_QUICK_REFERENCE.md**: Quick lookup guide with templates
- **Example Components**:
  - `/src/components/Dashboard.jsx` - Basic patterns
  - `/src/components/AgentAuthorizationDashboard.jsx` - Complex component
  - `/src/components/RealTimeAnalyticsDashboard.jsx` - Advanced patterns

## Key Takeaways

1. Use **fetchWithAuth()** for all API calls (CSRF handled automatically)
2. Use **useTheme()** for dark mode support
3. Use **tab-based routing** with switch case (not React Router)
4. Use **MetricCard pattern** for displaying metrics
5. Use **loading/error states** for async operations
6. Use **TailwindCSS** with dark: prefix for styling
7. Use **permission checks** for admin-only features
8. Use **SafeIcon** for consistent iconography
9. Always pass **getAuthHeaders** and **user** props from App.jsx
10. Test in both **light and dark modes**

## Questions?

Refer to the appropriate documentation:
- **How do I...?** → FRONTEND_QUICK_REFERENCE.md
- **What is the architecture of...?** → FRONTEND_ARCHITECTURE.md
- **Can you show me an example of...?** → Both documents have examples
- **How do I integrate a new component?** → FRONTEND_ARCHITECTURE.md Section 7

---

**Created:** November 14, 2025
**Status:** Complete and Ready for Integration
**Target:** Risk Scoring Configuration Dashboard
