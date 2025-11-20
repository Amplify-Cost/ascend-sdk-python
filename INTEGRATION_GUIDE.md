# Enterprise API Integration Guide

## Files Created:
- ✅ `src/services/EnterpriseApiService.js` - Main API service
- ✅ `src/hooks/useEnterpriseApi.js` - React hooks for API calls
- ✅ `src/components/EnterpriseApiProvider.jsx` - Context provider
- ✅ `src/components/AuthorizationExample.jsx` - Example component

## Next Steps:

### 1. Update your main App component:
```jsx
import { EnterpriseApiProvider } from './components/EnterpriseApiProvider';

function App() {
  return (
    <EnterpriseApiProvider>
      {/* Your existing app content */}
    </EnterpriseApiProvider>
  );
}
```

### 2. Update your authorization components:
Replace old fetch calls with:
```jsx
import { useAuthorizationData } from '../hooks/useEnterpriseApi';

// Use the hook in your component:
const { data, loading, error, approveAction, createTestActions } = useAuthorizationData();
```

### 3. Test the integration:
- Your API calls now use the correct backend endpoints
- Approval buttons will work with `/agent-control/authorize-with-audit/{id}`
- Test data generation works with `/agent-control/create-test-actions`

## API Endpoints Mapped:
- Authorization data: `/agent-control/pending-actions`
- Approve actions: `/agent-control/authorize-with-audit/{id}`
- Create test data: `/agent-control/create-test-actions`
- Dashboard metrics: `/dashboard/metrics`
- System health: `/system/health`

Your frontend is now connected to your working backend APIs! 🎉
