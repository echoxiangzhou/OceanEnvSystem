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
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'shadcn-ui': [
            './src/components/ui/button.tsx',
            './src/components/ui/card.tsx',
            './src/components/ui/input.tsx',
            './src/components/ui/tabs.tsx',
          ],
        },
      },
    },
  },
})
