// Create this file: src/components/ToastNotification.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ToastContext = createContext();

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

// Individual Toast Component
const Toast = ({ toast, onRemove }) => {
  const { isDarkMode } = useTheme();

  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id);
    }, toast.duration || 4000);

    return () => clearTimeout(timer);
  }, [toast, onRemove]);

  const getToastStyles = () => {
    const baseStyles = `p-4 rounded-lg border shadow-lg transition-all duration-300 transform hover:scale-105`;
    
    switch (toast.type) {
      case 'success':
        return `${baseStyles} ${
          isDarkMode 
            ? 'bg-green-900/90 border-green-500 text-green-100' 
            : 'bg-green-50 border-green-200 text-green-800'
        }`;
      case 'error':
        return `${baseStyles} ${
          isDarkMode 
            ? 'bg-red-900/90 border-red-500 text-red-100' 
            : 'bg-red-50 border-red-200 text-red-800'
        }`;
      case 'warning':
        return `${baseStyles} ${
          isDarkMode 
            ? 'bg-yellow-900/90 border-yellow-500 text-yellow-100' 
            : 'bg-yellow-50 border-yellow-200 text-yellow-800'
        }`;
      case 'info':
      default:
        return `${baseStyles} ${
          isDarkMode 
            ? 'bg-blue-900/90 border-blue-500 text-blue-100' 
            : 'bg-blue-50 border-blue-200 text-blue-800'
        }`;
    }
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': 
      default: return 'ℹ️';
    }
  };

  return (
    <div className={getToastStyles()}>
      <div className="flex items-start space-x-3">
        <span className="text-xl">{getIcon()}</span>
        <div className="flex-1">
          {toast.title && (
            <h4 className="font-medium text-sm mb-1">{toast.title}</h4>
          )}
          <p className="text-sm">{toast.message}</p>
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className={`text-lg hover:scale-110 transition-transform ${
            isDarkMode ? 'text-slate-400 hover:text-slate-200' : 'text-gray-400 hover:text-gray-600'
          }`}
        >
          ×
        </button>
      </div>
    </div>
  );
};

// Toast Container
const ToastContainer = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {toasts.map(toast => (
        <Toast key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
};

// Toast Provider
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = (toast) => {
    const id = Date.now() + Math.random();
    const newToast = { ...toast, id };
    setToasts(prev => [...prev, newToast]);
    return id;
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const toast = {
    success: (message, title = null, duration = 4000) => 
      addToast({ type: 'success', message, title, duration }),
    error: (message, title = null, duration = 5000) => 
      addToast({ type: 'error', message, title, duration }),
    warning: (message, title = null, duration = 4000) => 
      addToast({ type: 'warning', message, title, duration }),
    info: (message, title = null, duration = 4000) => 
      addToast({ type: 'info', message, title, duration }),
  };

  return (
    <ToastContext.Provider value={{ toast, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};