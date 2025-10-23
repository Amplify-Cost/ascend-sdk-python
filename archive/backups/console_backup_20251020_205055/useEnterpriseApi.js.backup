/**
 * Enterprise API Hook - Replaces direct fetch calls with service layer
 * Maintains existing component interfaces while using correct endpoints
 */

import { useState, useEffect, useCallback } from 'react';
import EnterpriseApiService from '../services/EnterpriseApiService';

export function useAuthorizationData() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await EnterpriseApiService.getAuthorizationData();
      setData(result.data || result || []);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch authorization data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const approveAction = useCallback(async (actionId, approvalData) => {
    try {
      const result = await EnterpriseApiService.approveAction(actionId, approvalData);
      // Refresh data after approval
      await fetchData();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchData]);

  const createTestActions = useCallback(async (count = 5) => {
    try {
      const result = await EnterpriseApiService.createTestActions(count);
      // Refresh data after creating test actions
      await fetchData();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    approveAction,
    createTestActions,
  };
}

export function useDashboardData() {
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        setLoading(true);
        setError(null);
        
        const [metricsData, healthData] = await Promise.all([
          EnterpriseApiService.getDashboardMetrics(),
          EnterpriseApiService.getSystemHealth(),
        ]);
        
        setMetrics(metricsData);
        setHealth(healthData);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  return { metrics, health, loading, error };
}

export function useChatApi() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async (message, context = {}) => {
    try {
      setLoading(true);
      const response = await EnterpriseApiService.sendChatMessage(message, context);
      
      setMessages(prev => [...prev, 
        { role: 'user', content: message },
        { role: 'assistant', content: response.message || response.content }
      ]);
      
      return response;
    } catch (err) {
      console.error('Failed to send message:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { messages, sendMessage, loading };
}
