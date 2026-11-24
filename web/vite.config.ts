import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// HOST env selects the bind address for the S2-c / S6 checks.
export default defineConfig({
  plugins: [react()],
  server: {
    host: process.env.VHOST || 'localhost',
    port: 5173,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } },
  },
})
