import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/dietaryai/',
  server: {
    port: 5173,
    proxy: {
      '/ocr': 'http://localhost:8000',
      '/recognise': 'http://localhost:8000',
      '/advise': 'http://localhost:8000',
      '/markers': 'http://localhost:8000',
      '/profiles': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
