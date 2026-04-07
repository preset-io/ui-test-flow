import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8019,
    proxy: {
      '/api': {
        target: 'http://localhost:8018',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8018',
        ws: true,
      },
    },
  },
})
