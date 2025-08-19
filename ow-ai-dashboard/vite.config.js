import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev proxy so requests from http://localhost:5175 to /auth, /api, etc.
// are forwarded to http://localhost:8000 (backend). This lets cookies work.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    host: true,
    proxy: {
      '^/(auth|api|smart-rules|smart-alerts|secrets|enterprise|health)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
