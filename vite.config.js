import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  // Enterprise fix for CommonJS libraries like pdfmake
  // pdfmake uses pre-built UMD bundles that need special handling
  optimizeDeps: {
    include: [
      'pdfmake/build/pdfmake',
      'pdfmake/build/vfs_fonts'
    ],
    esbuildOptions: {
      // Handle CommonJS modules properly
      format: 'esm'
    }
  },

  server: {
    port: 5173,
    host: true, // Allow external connections
    cors: true,
    // Proxy API calls to backend for development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },

  // Environment variable validation
  define: {
    __API_URL__: JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8000'),
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    // Optimize for production with proper chunking
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['lucide-react'],
          // Separate chunk for PDF generation library
          pdf: ['pdfmake']
        }
      }
    },
    // Increase chunk size warning limit for pdfmake (large library)
    chunkSizeWarningLimit: 1000
  }
});
// Force rebuild Tue Oct  7 11:48:35 EDT 2025
