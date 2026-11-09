import path from 'path';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  // Served from the root locally (the charts prototype is a standalone page).
  base: '/',
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
    },
  },
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    // The charts chunk is large on purpose (about 160 kB with gzip).
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // Recharts is by far the largest dependency and changes rarely: a chunk
        // of its own stays cached when the application code changes.
        manualChunks(id) {
          if (/node_modules\/(recharts|d3-|victory-vendor)/.test(id)) return 'charts';
          return undefined;
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
  },
});
