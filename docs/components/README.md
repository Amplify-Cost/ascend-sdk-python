# Component Library

Complete documentation for all React components in the OW-AI Enterprise Frontend.

## Table of Contents

- [Dashboard Components](#dashboard-components)
- [Authorization Components](#authorization-components)
- [Alert Components](#alert-components)
- [Smart Rules Components](#smart-rules-components)
- [User Management Components](#user-management-components)
- [Shared Components](#shared-components)

## Dashboard Components

### Dashboard.jsx
Main dashboard component displaying KPIs and system overview.

**Location:** `src/components/Dashboard.jsx`

**Props:**
- None (uses context for data)

**Features:**
- Real-time metrics display
- Quick action buttons
- System health indicators
- Recent activity feed

**Usage:**
```jsx
import Dashboard from './components/Dashboard';

<Dashboard />
```

## Authorization Components

### AgentAuthorizationDashboard.jsx
Comprehensive authorization management dashboard.

**Location:** `src/components/AgentAuthorizationDashboard.jsx`

**Features:**
- Multi-tab interface (Dashboard, Pending Actions, History, Policies)
- Real-time approval workflows
- Risk-based action routing
- Compliance mapping (SOX, PCI-DSS, HIPAA, GDPR)
- Audit trail visualization

**State Management:**
```javascript
const [activeTab, setActiveTab] = useState('dashboard');
const [pendingActions, setPendingActions] = useState([]);
const [dashboardData, setDashboardData] = useState(null);
```

**API Endpoints Used:**
- `GET /api/authorization/dashboard`
- `GET /api/authorization/pending-actions`
- `POST /api/authorization/authorize/{action_id}`
- `GET /api/authorization/execution-history`

### AgentActionsPanel.jsx
Display and manage agent actions requiring approval.

**Props:**
```typescript
{
  actions: Array<Action>,
  onApprove: (actionId: number) => Promise<void>,
  onReject: (actionId: number) => Promise<void>
}
```

### AgentActionSubmitPanel.jsx
Submit new agent actions for approval.

**Features:**
- Action type selection
- Risk level calculation
- Compliance validation
- Form validation

## Alert Components

### AIAlertManagementSystem.jsx
AI-powered alert management system with real-time monitoring.

**Location:** `src/components/AIAlertManagementSystem.jsx`

**Features:**
- Real-time alert feed
- AI insights and threat intelligence
- Performance metrics dashboard
- Alert correlation and grouping
- Automated response capabilities

**Tabs:**
1. **Alerts** - Active and historical alerts
2. **AI Insights** - ML-powered threat analysis
3. **Threat Intelligence** - Real-time threat data
4. **Performance** - System performance metrics

**API Endpoints Used:**
- `GET /api/alerts`
- `GET /api/alerts/ai-insights`
- `GET /api/alerts/threat-intelligence`
- `GET /api/alerts/performance-metrics`
- `PATCH /api/alerts/{alert_id}`

**Usage:**
```jsx
import AIAlertManagementSystem from './components/AIAlertManagementSystem';

<AIAlertManagementSystem />
```

### AlertPanel.jsx
Simplified alert display panel.

**Props:**
```typescript
{
  alerts: Array<Alert>,
  onAcknowledge?: (alertId: number) => void,
  maxDisplay?: number
}
```

### Alerts.jsx
Basic alert list component.

**Features:**
- Alert filtering by severity
- Status updates
- Quick actions

## Smart Rules Components

### SmartRulesPanel.jsx
Smart rules management interface.

**Features:**
- Natural language rule creation
- Rule performance analytics
- AI-powered rule suggestions
- Rule optimization

**API Endpoints:**
- `GET /api/smart-rules`
- `POST /api/smart-rules/generate-from-nl`
- `POST /api/smart-rules/optimize/{rule_id}`
- `GET /api/smart-rules/suggestions`

### RuleEditor.jsx
Visual rule editor with syntax highlighting.

**Props:**
```typescript
{
  rule: Rule | null,
  onSave: (rule: Rule) => Promise<void>,
  onCancel: () => void
}
```

## User Management Components

### EnterpriseUserManagement.jsx
Enterprise user management dashboard.

**Features:**
- User CRUD operations
- Role assignment
- Permission management
- Activity monitoring

**API Endpoints:**
- `GET /api/enterprise-users/users`
- `POST /api/enterprise-users/users`
- `PUT /api/enterprise-users/users/{user_id}`
- `DELETE /api/enterprise-users/users/{user_id}`

## Shared Components

### BannerAlert.jsx
System-wide alert banner for important notifications.

**Props:**
```typescript
{
  message: string,
  type: 'info' | 'warning' | 'error' | 'success',
  dismissible?: boolean,
  onDismiss?: () => void
}
```

**Usage:**
```jsx
<BannerAlert
  message="System maintenance scheduled"
  type="warning"
  dismissible
/>
```

### Breadcrumb.jsx
Navigation breadcrumb component.

**Props:**
```typescript
{
  items: Array<{ label: string, href?: string }>,
  separator?: ReactNode
}
```

### LoadingSpinner.jsx
Reusable loading indicator.

**Props:**
```typescript
{
  size?: 'small' | 'medium' | 'large',
  color?: string,
  text?: string
}
```

### ErrorBoundary.jsx
React error boundary for graceful error handling.

**Usage:**
```jsx
<ErrorBoundary fallback={<ErrorMessage />}>
  <YourComponent />
</ErrorBoundary>
```

## Component Patterns

### 1. Data Fetching Pattern

```javascript
function MyComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await apiService.getData();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return <DataDisplay data={data} />;
}
```

### 2. Form Handling Pattern

```javascript
function FormComponent() {
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const validate = (data) => {
    // Validation logic
    return {};
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate(formData);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSubmitting(true);
    try {
      await apiService.submit(formData);
      // Success handling
    } catch (error) {
      setErrors({ submit: error.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
}
```

### 3. Context Usage Pattern

```javascript
import { useAuth } from '../contexts/AuthContext';

function ProtectedComponent() {
  const { user, token, logout } = useAuth();

  if (!user) {
    return <Redirect to="/login" />;
  }

  return (
    <div>
      <h1>Welcome, {user.email}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

## Styling Guidelines

### Tailwind CSS Classes

Use Tailwind utility classes for styling:

```jsx
<div className="bg-white rounded-lg shadow-md p-6 mb-4">
  <h2 className="text-2xl font-bold text-gray-900 mb-4">
    Title
  </h2>
  <p className="text-gray-600">
    Content
  </p>
</div>
```

### Common Class Patterns

**Cards:**
```
bg-white rounded-lg shadow-md p-6
```

**Buttons:**
```
px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition
```

**Input Fields:**
```
w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500
```

## Testing Components

### Unit Test Example

```javascript
// src/components/__tests__/Dashboard.test.jsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../Dashboard';

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('displays metrics when data is loaded', async () => {
    render(<Dashboard />);
    const metrics = await screen.findByText(/Total Pending/i);
    expect(metrics).toBeInTheDocument();
  });
});
```

## Component Lifecycle

1. **Mount** - Component is created and inserted into the DOM
2. **Update** - Props or state changes trigger re-render
3. **Unmount** - Component is removed from the DOM

### Cleanup in useEffect

```javascript
useEffect(() => {
  const subscription = apiService.subscribe();

  return () => {
    // Cleanup function
    subscription.unsubscribe();
  };
}, []);
```

## Performance Optimization

### 1. React.memo for Expensive Components

```javascript
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* Expensive render logic */}</div>;
});
```

### 2. useMemo for Expensive Calculations

```javascript
const filteredData = useMemo(() => {
  return data.filter(item => item.active);
}, [data]);
```

### 3. useCallback for Event Handlers

```javascript
const handleClick = useCallback(() => {
  console.log('Clicked');
}, []);
```

## Accessibility

All components follow WCAG 2.1 AA standards:

- Semantic HTML elements
- ARIA labels where necessary
- Keyboard navigation support
- Screen reader compatible
- Sufficient color contrast

```jsx
<button
  aria-label="Close dialog"
  onClick={handleClose}
  className="focus:outline-none focus:ring-2 focus:ring-blue-500"
>
  <CloseIcon />
</button>
```

## See Also

- [Frontend Architecture](../architecture/FRONTEND-ARCHITECTURE.md)
- [API Integration Guide](../api/INTEGRATION.md)
- [Testing Guide](../guides/TESTING.md)
