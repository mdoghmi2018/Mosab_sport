import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,  // Explicitly set to 3000 to match docker-compose
    watch: {
      usePolling: true
    }
  }
})

