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
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('recharts') || id.includes('/d3-') || id.includes('d3-format')) {
            return 'vendor-charts'
          }
          if (id.includes('framer-motion') || id.includes('@headlessui')) return 'vendor-motion'
          if (id.includes('@tanstack/react-query') || id.includes('axios')) return 'vendor-data'
          if (id.includes('react-router-dom')) return 'vendor-router'
          if (id.includes('lucide-react') || id.includes('@heroicons')) return 'vendor-icons'
          if (id.includes('/react/') || id.includes('react-dom')) return 'vendor-react'
          return 'vendor-misc'
        },
      },
    },
  },
})
