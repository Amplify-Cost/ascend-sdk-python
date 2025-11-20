import React, { useState, useEffect, useRef } from 'react';
import { Bell, AlertTriangle, CheckCircle, Clock, Shield, TrendingUp, Users, Activity, X, Eye, EyeOff } from 'lucide-react';
import logger from '../utils/logger.js';

const SmartAlertManagement = ({ getAuthHeaders, user }) => {
  const [activeTab, setActiveTab] = useState("active");
  const [alerts, setAlerts] = useState([]);
  const [alertHistory, setAlertHistory] = useState([]);
  const [alertStats, setAlertStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const websocketRef = useRef(null);
  const audioRef = useRef(null);

  // Initialize audio for alert notifications
  useEffect(() => {
    // Create a simple beep sound using Web Audio API
    const createBeepSound = () => {
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0, audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
      } catch (error) {
        logger.debug('Audio not supported:', error);
      }
    };
    
    audioRef.current = { play: createBeepSound };
  }, []);

  // Connect to WebSocket for real-time alerts
  useEffect(() => {
    if (!user || !getAuthHeaders) return;

    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/alerts/stream`;
        websocketRef.current = new WebSocket(wsUrl);

        websocketRef.current.onopen = () => {
          logger.debug('Alert WebSocket connected');
        };

        websocketRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'alerts' || data.type === 'initial_alerts') {
            setAlerts(prevAlerts => {
              const newAlerts = [...prevAlerts, ...data.data];
              
              // Play notification sound for new alerts (not initial load)
              if (data.type === 'alerts' && soundEnabled && audioRef.current) {
                data.data.forEach(alert => {
                  if (alert.severity === 'critical' || alert.severity === 'high') {
                    audioRef.current.play();
                  }
                });
              }
              
              return newAlerts;
            });
          }
        };

        websocketRef.current.onclose = () => {
          logger.debug('Alert WebSocket disconnected, attempting to reconnect...');
          setTimeout(connectWebSocket, 5000);
        };

        websocketRef.current.onerror = (error) => {
          logger.error('Alert WebSocket error:', error);
        };

      } catch (error) {
        logger.error('Failed to connect to alert WebSocket:', error);
        setTimeout(connectWebSocket, 5000);
      }
    };

    connectWebSocket();

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [user, getAuthHeaders, soundEnabled]);

  // Fetch active alerts
  const fetchActiveAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch('/alerts/active', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
        setAlertStats(data.statistics || {});
      } else {
        throw new Error(`Failed to fetch alerts: ${response.status}`);
      }
    } catch (error) {
      logger.error('Error fetching active alerts:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch alert history
  const fetchAlertHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('/alerts/history?days=30', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setAlertHistory(data.history || []);
      } else {
        throw new Error(`Failed to fetch alert history: ${response.status}`);
      }
    } catch (error) {
      logger.error('Error fetching alert history:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Acknowledge alert
  const acknowledgeAlert = async (alertId) => {
    try {
      const response = await fetch(`/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        setAlerts(prev => 
          prev.map(alert => 
            alert.id === alertId 
              ? { ...alert, status: 'acknowledged', acknowledged_by: user.email }
              : alert
          )
        );
      } else {
        throw new Error('Failed to acknowledge alert');
      }
    } catch (error) {
      logger.error('Error acknowledging alert:', error);
    }
  };

  // Resolve alert
  const resolveAlert = async (alertId) => {
    try {
      const response = await fetch(`/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        setAlerts(prev => prev.filter(alert => alert.id !== alertId));
      } else {
        throw new Error('Failed to resolve alert');
      }
    } catch (error) {
      logger.error('Error resolving alert:', error);
    }
  };

  // Initial data fetch
  useEffect(() => {
    if (activeTab === 'active') {
      fetchActiveAlerts();
    } else if (activeTab === 'history') {
      fetchAlertHistory();
    }
  }, [activeTab, user]);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'high': return <AlertTriangle className="w-5 h-5 text-orange-600" />;
      case 'medium': return <Bell className="w-5 h-5 text-yellow-600" />;
      case 'low': return <Bell className="w-5 h-5 text-blue-600" />;
      default: return <Bell className="w-5 h-5 text-gray-600" />;
    }
  };

  if (loading && alerts.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading alerts...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Shield className="w-8 h-8 text-blue-600 mr-3" />
            Smart Alert Management
          </h1>
          <p className="text-gray-600 mt-1">Real-time monitoring and intelligent alerting system</p>
        </div>
        
        <div className="flex items-center gap-3 mt-4 sm:mt-0">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={`flex items-center px-3 py-2 rounded-lg border ${
              soundEnabled 
                ? 'bg-blue-50 border-blue-200 text-blue-700' 
                : 'bg-gray-50 border-gray-200 text-gray-500'
            }`}
          >
            {soundEnabled ? <Bell className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
            Sound {soundEnabled ? 'On' : 'Off'}
          </button>
        </div>
      </div>

      {/* Alert Statistics */}
      {alertStats.total_active > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-600 text-sm font-medium">Critical</p>
                <p className="text-2xl font-bold text-red-700">{alertStats.by_severity?.critical || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </div>
          
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-600 text-sm font-medium">High</p>
                <p className="text-2xl font-bold text-orange-700">{alertStats.by_severity?.high || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-600" />
            </div>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-600 text-sm font-medium">Medium</p>
                <p className="text-2xl font-bold text-yellow-700">{alertStats.by_severity?.medium || 0}</p>
              </div>
              <Bell className="w-8 h-8 text-yellow-600" />
            </div>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 text-sm font-medium">Low</p>
                <p className="text-2xl font-bold text-blue-700">{alertStats.by_severity?.low || 0}</p>
              </div>
              <Bell className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('active')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'active'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Activity className="w-4 h-4 inline mr-2" />
            Active Alerts ({alerts.length})
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Clock className="w-4 h-4 inline mr-2" />
            Alert History
          </button>
        </nav>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Active Alerts Tab */}
      {activeTab === 'active' && (
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">All Clear!</h3>
              <p className="text-gray-600">No active alerts at this time. Your systems are running smoothly.</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)} ${
                  selectedAlert?.id === alert.id ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getSeverityIcon(alert.severity)}
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{alert.rule_name}</h3>
                      <p className="text-sm text-gray-700 mt-1">{alert.message}</p>
                      <div className="flex items-center text-xs text-gray-500 mt-2 space-x-4">
                        <span>Triggered: {new Date(alert.triggered_at).toLocaleString()}</span>
                        <span className={`px-2 py-1 rounded-full font-medium ${
                          alert.status === 'acknowledged' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {alert.status === 'acknowledged' ? 'Acknowledged' : 'Active'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {alert.status !== 'acknowledged' && (
                      <button
                        onClick={() => acknowledgeAlert(alert.id)}
                        className="px-3 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200 transition-colors"
                      >
                        Acknowledge
                      </button>
                    )}
                    <button
                      onClick={() => resolveAlert(alert.id)}
                      className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded-lg hover:bg-green-200 transition-colors"
                    >
                      Resolve
                    </button>
                    <button
                      onClick={() => setSelectedAlert(selectedAlert?.id === alert.id ? null : alert)}
                      className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors"
                    >
                      {selectedAlert?.id === alert.id ? 'Hide' : 'Details'}
                    </button>
                  </div>
                </div>
                
                {/* Alert Details */}
                {selectedAlert?.id === alert.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="font-medium text-gray-900 mb-2">Alert Details</h4>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                        {JSON.stringify(alert.metrics_snapshot, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Alert History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {alertHistory.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Alert History</h3>
              <p className="text-gray-600">No alerts have been triggered in the past 30 days.</p>
            </div>
          ) : (
            alertHistory.map((alert) => (
              <div
                key={alert.id}
                className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)} opacity-75`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getSeverityIcon(alert.severity)}
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{alert.rule_name}</h3>
                      <div className="flex items-center text-xs text-gray-500 mt-2 space-x-4">
                        <span>Triggered: {new Date(alert.triggered_at).toLocaleString()}</span>
                        <span>Resolved: {new Date(alert.resolved_at).toLocaleString()}</span>
                        <span className="px-2 py-1 rounded-full font-medium bg-green-100 text-green-800">
                          Resolved
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default SmartAlertManagement;