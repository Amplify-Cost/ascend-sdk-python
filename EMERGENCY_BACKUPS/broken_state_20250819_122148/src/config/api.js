// Centralized API configuration with fallbacks
const getApiBaseUrl = () => {
  // Try different environment variable approaches
  const viteUrl = import.meta.env.VITE_API_URL;
  const processUrl = typeof process !== 'undefined' && process.env?.VITE_API_URL;
  
  // Fallback chain
  return viteUrl || processUrl || 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

// Debug logging (remove in production)
console.log('🔧 API Configuration:', {
  'import.meta.env.VITE_API_URL': import.meta.env.VITE_API_URL,
  'Final API_BASE_URL': API_BASE_URL
});

export default API_BASE_URL;
