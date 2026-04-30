// AIMETA P=Vite配置_构建和开发服务器配置|R=构建配置_代理配置|NR=不含业务逻辑|E=-|X=internal|A=Vite配置|D=vite|S=fs|RD=./README.ai
import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

const frontendHost = process.env.FRONTEND_HOST || '0.0.0.0'
const frontendPort = Number(process.env.FRONTEND_PORT || '5173')
const frontendHmrHost = process.env.FRONTEND_HMR_HOST || 'localhost'
const backendProxyHost = process.env.BACKEND_PROXY_HOST || '127.0.0.1'
const backendPort = Number(process.env.BACKEND_PORT || '8000')

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: frontendHost,
    port: frontendPort,
    strictPort: true,
    hmr: {
      protocol: 'ws',
      host: frontendHmrHost,
      port: frontendPort,
      clientPort: frontendPort,
    },
    proxy: {
      '/api': {
        target: `http://${backendProxyHost}:${backendPort}`,
        changeOrigin: true,
      }
    }
  }
})
