// frontend/src/vite.config.js

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/app/',  // This must match the Nginx location block
  server: {
    host: '0.0.0.0',
    port: 5173,
  }
})