// Create this file: src/contexts/ThemeContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Check localStorage first, then system preference
    const saved = localStorage.getItem('ow-ai-theme');
    if (saved) {
      return saved === 'dark';
    }
    // Check system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    // Apply theme to document
    const root = document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    
    // Save preference
    localStorage.setItem('ow-ai-theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
  };

  // Enterprise theme variables
  const theme = {
    // Light theme colors
    light: {
      primary: '#1e40af',
      primaryHover: '#1d4ed8',
      secondary: '#64748b',
      background: '#f8fafc',
      cardBackground: '#ffffff',
      border: '#e2e8f0',
      text: '#1e293b',
      textSecondary: '#64748b',
      textMuted: '#94a3b8',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    },
    // Dark theme colors - Lighter for better readability
    dark: {
      primary: '#60a5fa',
      primaryHover: '#3b82f6',
      secondary: '#cbd5e1',
      background: '#1e293b',  // Lighter main background
      cardBackground: '#334155',  // Lighter card background
      border: '#475569',  // Lighter borders
      text: '#ffffff',  // Pure white for main text
      textSecondary: '#e2e8f0',  // Much lighter secondary text
      textMuted: '#cbd5e1',  // Lighter muted text
      success: '#34d399',
      warning: '#fbbf24',
      error: '#f87171',
      info: '#60a5fa',
    }
  };

  const currentTheme = isDarkMode ? theme.dark : theme.light;

  return (
    <ThemeContext.Provider value={{ 
      isDarkMode, 
      toggleTheme, 
      theme: currentTheme,
      colors: theme 
    }}>
      {children}
    </ThemeContext.Provider>
  );
};