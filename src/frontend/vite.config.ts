import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';
import { fileURLToPath, URL } from 'node:url';

/**
 * Group the genuinely eager, always-loaded core libraries into stable,
 * separately-cacheable vendor chunks (UI-NFR-003 R-013/R-016). Splitting these
 * long-lived vendors from the frequently-changing app code keeps a routine app
 * deploy from invalidating the whole vendor cache.
 *
 * Only route-independent core libs are grouped. Heavy, route-scoped libraries
 * (`recharts`, `@mui/x-date-pickers`, `@mui/x-tree-view`, `react-grid-layout`)
 * are intentionally left to Rolldown's automatic per-module splitting so they
 * stay lazy and never get dragged into the initial payload — the exact pitfall
 * an over-broad `@mui`/`charts` group would reintroduce (R-013/R-028).
 */
function manualChunks(id: string): string | undefined {
  if (!id.includes('node_modules')) return undefined;
  // Route-scoped heavy libs must remain their own on-demand chunks.
  if (
    /[\\/]node_modules[\\/](react-grid-layout|react-resizable|recharts|d3-[^\\/]+|victory-[^\\/]+|@mui[\\/]x-)/.test(
      id,
    )
  ) {
    return undefined;
  }
  if (
    /[\\/]node_modules[\\/](react|react-dom|scheduler|react-router|react-router-dom)[\\/]/.test(
      id,
    )
  ) {
    return 'vendor-react';
  }
  if (
    /[\\/]node_modules[\\/](@mui[\\/](material|system|base|utils|private-theming|styled-engine|core-downloads-tracker)|@emotion)[\\/]/.test(
      id,
    )
  ) {
    return 'vendor-mui';
  }
  if (
    /[\\/]node_modules[\\/](@reduxjs[\\/]toolkit|react-redux|redux|redux-thunk|immer|reselect)[\\/]/.test(
      id,
    )
  ) {
    return 'vendor-redux';
  }
  if (
    /[\\/]node_modules[\\/](i18next|react-i18next|i18next-browser-languagedetector)[\\/]/.test(
      id,
    )
  ) {
    return 'vendor-i18n';
  }
  return undefined;
}

export default defineConfig({
  plugins: [
    react(),
    // Emits a treemap of the bundle to bundle-stats/stats.html for the CI
    // artifact (UI-NFR-003 DoD §4). Gzip sizes make the report comparable to
    // the budget. Deliberately written OUTSIDE dist/ so the Lighthouse CI job
    // (which serves dist/ as a static site and auto-crawls every .html) does
    // not accidentally audit the analyzer report instead of the app.
    visualizer({
      filename: 'bundle-stats/stats.html',
      gzipSize: true,
      brotliSize: false,
      template: 'treemap',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    // Emit dist/.vite/manifest.json so the bundle-budget gate can resolve the
    // route-specific (/dashboard) chunk for its dedicated budget (R-028).
    manifest: true,
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
