/**
 * Enterprise API Provider - Context provider for API service
 */

import React, { createContext, useContext } from 'react';
import EnterpriseApiService from '../services/EnterpriseApiService';

const EnterpriseApiContext = createContext(null);

export function EnterpriseApiProvider({ children }) {
  return (
    <EnterpriseApiContext.Provider value={EnterpriseApiService}>
      {children}
    </EnterpriseApiContext.Provider>
  );
}

export function useEnterpriseApi() {
  const context = useContext(EnterpriseApiContext);
  if (!context) {
    throw new Error('useEnterpriseApi must be used within an EnterpriseApiProvider');
  }
  return context;
}
