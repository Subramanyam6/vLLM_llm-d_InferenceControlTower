import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import process from 'node:process'

const apiHost = process.env.VITE_API_HOST || process.env.API_HOST || '127.0.0.1'
const apiPort = process.env.VITE_API_PORT || process.env.API_PORT || '8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': `http://${apiHost}:${apiPort}`,
    },
  },
})
