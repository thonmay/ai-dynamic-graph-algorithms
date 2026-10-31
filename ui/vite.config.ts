// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The production build is written into the Python package so `evoalgo ui`
// serves it without Node. `npm run dev` proxies the API to a running
// `evoalgo ui` on port 8765.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: '../src/evoalgo/ui_dist', emptyOutDir: true },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8765', ws: true } },
  },
})
