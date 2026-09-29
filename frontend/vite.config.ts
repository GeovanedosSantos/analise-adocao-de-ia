import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] }),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // alias para apontar para o /src 
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    }
  },
  server: {
    // Em desenvolvimento, a API do Django roda em outra porta
    proxy: { '/api': 'http://localhost:8000' },
  },
})
