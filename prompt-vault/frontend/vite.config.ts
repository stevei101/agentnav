import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5176,  // Changed to avoid conflict with cursor-ide (5173)
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})

