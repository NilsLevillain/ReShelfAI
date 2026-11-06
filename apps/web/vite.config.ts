import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

const ds = fileURLToPath(new URL('../../design_system/dist', import.meta.url));
const data = fileURLToPath(new URL('../../data', import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    resolve: { alias: { '@ds': ds, '@data': data } },
    server: {
      port: 5173,
      fs: { allow: ['../..'] },
      proxy: { '/api': { target: env.VITE_API_URL || 'http://localhost:8000', rewrite: (p) => p.replace(/^\/api/, '') } },
    },
  };
});
