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
    port: 3000,
    open: true,
    host: true,
    allowedHosts: ['eac.dvvcloud.work', 'localhost', '192.168.5.209'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Only proxy API auth endpoints, not the frontend auth pages
      '/auth/magic-link/request': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/magic-link/verify': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/register': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/login': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/refresh': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/logout': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/password': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/me': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/claims': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/customers': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/flights': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/eligibility': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/account': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-utils': ['date-fns', 'lucide-react', 'sonner', 'clsx', 'tailwind-merge'],
          'vendor-charts': ['recharts'],
          'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
        },
      },
    },
  },
})
