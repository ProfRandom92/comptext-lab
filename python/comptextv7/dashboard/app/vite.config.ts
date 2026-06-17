import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  publicDir: '../../docs/reports',
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8765',
      '/export.json': 'http://127.0.0.1:8765',
      '/export.csv': 'http://127.0.0.1:8765',
      '/dashboard-health-summary.json': 'http://127.0.0.1:8765',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
