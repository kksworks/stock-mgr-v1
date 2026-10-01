import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('chart.js') || id.includes('chartjs-')) return 'chartjs'
          if (id.includes('bootstrap')) return 'bootstrap'
        },
      },
    },
  },
  server: {
    // 리버스 프록시 등 모든 Host 허용 (Blocked request 방지)
    allowedHosts: true,
    // Docker/nginx proxy_pass :8080 과 맞추려면 PORT=8080 (예: docker-compose)
    port: Number(process.env.PORT) || 5173,
    host: true,  // 0.0.0.0 - LAN IP(예: 192.168.x.x)로 접속 가능
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET || 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
