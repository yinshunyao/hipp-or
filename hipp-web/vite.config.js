import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  // 生产子路径用 VITE_BASE_PATH=/or/；兼容误传的 VITE_BASE
  base: process.env.VITE_BASE_PATH || process.env.VITE_BASE || '/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:46000',
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/media': {
        target: 'http://127.0.0.1:46000',
        changeOrigin: true
      }
    }
  }
})
