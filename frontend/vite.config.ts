import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// El visor habla con el servidor de lectura (frontend/server) a través de /api.
// En desarrollo, Vite hace de intermediario para que no haga falta configurar nada.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5170',
        changeOrigin: false,
      },
    },
  },
})
