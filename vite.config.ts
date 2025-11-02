import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  server: {
    port: 5173, // Vite default port (mapped to 3000 on host in docker-compose)
    host: '0.0.0.0',
  },
  plugins: [react()],
  // SECURITY: Removed GEMINI_API_KEY exposure - frontend should call backend API
  // API keys should NEVER be exposed to browser/client-side code
  // Frontend should use backend API endpoints for secure API key handling
  define: {
    // Only include safe, public configuration
    // API_KEY removed for security - use backend API instead
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
});
