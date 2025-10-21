/**
 * Example: How to update your existing authorization components
 * Replace your old fetch calls with this pattern
 */

import React from 'react';
import { useAuthorizationData } from '../hooks/useEnterpriseApi';
import logger from '../utils/logger.js';

export function AuthorizationExample() {
  const { 
    data, 
    loading, 
    error, 
    approveAction, 
    createTestActions 
  } = useAuthorizationData();

  const handleApproval = async (actionId) => {
    try {
      await approveAction(actionId, { approved: true, timestamp: new Date().toISOString() });
      logger.debug('✅ Action approved successfully!');
    } catch (error) {
      logger.error('❌ Approval failed:', error);
    }
  };

  const handleCreateTest = async () => {
    try {
      await createTestActions(5);
      logger.debug('✅ Test actions created!');
    } catch (error) {
      logger.error('❌ Failed to create test actions:', error);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Authorization Dashboard</h2>
      <button onClick={handleCreateTest}>
        Create Test Actions
      </button>
      
      {data.map((action) => (
        <div key={action.id} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
          <h3>{action.type}</h3>
          <p>{action.description}</p>
          <button onClick={() => handleApproval(action.id)}>
            Approve Action
          </button>
        </div>
      ))}
    </div>
  );
}
