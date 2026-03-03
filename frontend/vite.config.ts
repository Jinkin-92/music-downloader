import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      // 代理所有API请求到后端（简单可靠）
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        ws: true,
        configure: (proxy, options) => {
          proxy.on('proxyRes', (proxyRes) => {
            proxyRes.headers['cache-control'] = 'no-cache';
            proxyRes.headers['connection'] = 'keep-alive';
          });
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // 优化包大小
    rollupOptions: {
      output: {
        manualChunks: {
          // React相关
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // UI组件
          'antd': ['antd', '@ant-design/icons'],
          // 工具库
          'utils': ['axios', 'dayjs', '@microsoft/fetch-event-source'],
        },
      },
    },
  },
});
