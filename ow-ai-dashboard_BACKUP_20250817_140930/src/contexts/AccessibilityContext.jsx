// Create this file: src/contexts/AccessibilityContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useTheme } from './ThemeContext';

const AccessibilityContext = createContext();

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

// Skip Link Component
const SkipLink = () => {
  const { isDarkMode } = useTheme();
  
  return (
    <a
      href="#main-content"
      className={`sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
        isDarkMode 
          ? 'bg-blue-600 text-white focus:bg-blue-700' 
          : 'bg-blue-600 text-white focus:bg-blue-700'
      }`}
    >
      Skip to main content
    </a>
  );
};

// Focus Trap Hook
export const useFocusTrap = (isActive) => {
  useEffect(() => {
    if (!isActive) return;

    const focusableElements = document.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    document.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      document.removeEventListener('keydown', handleTabKey);
    };
  }, [isActive]);
};

// Announcer for screen readers
export const useScreenReaderAnnounce = () => {
  const announce = (message, priority = 'polite') => {
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    announcer.textContent = message;
    
    document.body.appendChild(announcer);
    
    setTimeout(() => {
      document.body.removeChild(announcer);
    }, 1000);
  };

  return { announce };
};

// Keyboard Navigation Hook
export const useKeyboardNavigation = (onEscape, onEnter) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'Escape':
          onEscape?.();
          break;
        case 'Enter':
          if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') {
            onEnter?.(e);
          }
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onEscape, onEnter]);
};

// Motion preferences
export const useReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
};

// High contrast mode detection
export const useHighContrast = () => {
  const [highContrast, setHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    setHighContrast(mediaQuery.matches);

    const handleChange = (e) => setHighContrast(e.matches);
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return highContrast;
};

// Loading Skeleton Component
export const LoadingSkeleton = ({ width = '100%', height = '1rem', className = '' }) => {
  const { isDarkMode } = useTheme();
  const prefersReducedMotion = useReducedMotion();
  
  return (
    <div
      className={`rounded ${
        prefersReducedMotion ? '' : 'animate-pulse'
      } ${
        isDarkMode ? 'bg-slate-600' : 'bg-gray-200'
      } ${className}`}
      style={{ width, height }}
      aria-label="Loading content"
      role="status"
    />
  );
};

// Enhanced Button Component with accessibility
export const AccessibleButton = ({ 
  children, 
  onClick, 
  disabled = false, 
  variant = 'primary',
  size = 'md',
  loading = false,
  ariaLabel,
  className = '',
  ...props 
}) => {
  const { isDarkMode } = useTheme();
  const { announce } = useScreenReaderAnnounce();
  
  const baseClasses = `
    inline-flex items-center justify-center font-medium rounded-lg 
    transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${!disabled && !loading ? 'hover:scale-105' : ''}
  `;
  
  const variantClasses = {
    primary: isDarkMode 
      ? 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-400' 
      : 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
    secondary: isDarkMode 
      ? 'bg-slate-600 hover:bg-slate-700 text-white focus:ring-slate-400' 
      : 'bg-gray-600 hover:bg-gray-700 text-white focus:ring-gray-500',
    outline: isDarkMode 
      ? 'border-2 border-slate-600 text-slate-200 hover:bg-slate-700 focus:ring-slate-400' 
      : 'border-2 border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const handleClick = (e) => {
    if (disabled || loading) return;
    onClick?.(e);
    if (ariaLabel) {
      announce(`${ariaLabel} activated`);
    }
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      onClick={handleClick}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
      )}
      {children}
    </button>
  );
};

// Accessible Form Input
export const AccessibleInput = ({
  label,
  error,
  required = false,
  helpText,
  id,
  className = '',
  ...props
}) => {
  const { isDarkMode } = useTheme();
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const helpId = helpText ? `${inputId}-help` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  
  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label 
          htmlFor={inputId}
          className={`block text-sm font-medium transition-colors duration-300 ${
            isDarkMode ? 'text-slate-200' : 'text-gray-700'
          }`}
        >
          {label}
          {required && <span className="text-red-500 ml-1" aria-label="required">*</span>}
        </label>
      )}
      
      <input
        id={inputId}
        className={`
          w-full px-3 py-2 border rounded-lg transition-all duration-300
          focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed
          ${error 
            ? isDarkMode 
              ? 'border-red-500 bg-red-900/20 text-red-200' 
              : 'border-red-500 bg-red-50 text-red-900'
            : isDarkMode 
              ? 'bg-slate-800 border-slate-600 text-white' 
              : 'bg-white border-gray-300 text-gray-900'
          }
        `}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={[helpId, errorId].filter(Boolean).join(' ') || undefined}
        required={required}
        {...props}
      />
      
      {helpText && (
        <p 
          id={helpId}
          className={`text-sm transition-colors duration-300 ${
            isDarkMode ? 'text-slate-400' : 'text-gray-600'
          }`}
        >
          {helpText}
        </p>
      )}
      
      {error && (
        <p 
          id={errorId}
          className={`text-sm font-medium transition-colors duration-300 ${
            isDarkMode ? 'text-red-400' : 'text-red-600'
          }`}
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
};

export const AccessibilityProvider = ({ children }) => {
  const [focusMode, setFocusMode] = useState(false);
  const [announcements, setAnnouncements] = useState([]);
  const prefersReducedMotion = useReducedMotion();
  const highContrast = useHighContrast();

  // Enable focus mode on tab key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Tab') {
        setFocusMode(true);
      }
    };

    const handleMouseDown = () => {
      setFocusMode(false);
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  // Apply focus mode class to body
  useEffect(() => {
    if (focusMode) {
      document.body.classList.add('focus-mode');
    } else {
      document.body.classList.remove('focus-mode');
    }
  }, [focusMode]);

  const value = {
    focusMode,
    prefersReducedMotion,
    highContrast,
    announcements,
    setAnnouncements,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      <SkipLink />
      {children}
    </AccessibilityContext.Provider>
  );
};