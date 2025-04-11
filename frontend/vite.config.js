// frontend/src/vite.config.js

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Critical for Docker: Ensure proper CORS and HMR
    cors: true,
    hmr: {
      clientPort: 5173,
      host: 'localhost'
    }
  },
  base: '/app/'
});