import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';
import { VitePWA } from 'vite-plugin-pwa';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';
import { appShellFiles, isAppShellEntry } from './src/pwa/appShell';

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
    // UI-NFR-012 basis (REQ-053 WP 9.1, #2741, R-011): one Workbox service worker, built from
    // src/sw.ts and emitted as dist/sw.js — the URL of the former push-only worker, so existing
    // registrations update in place. `injectManifest` because the worker also owns Web Push, the
    // tenant-bound API cache and the kill switch; a generated worker could hold none of them.
    // Registration lives in src/lib/serviceWorkerRegistration.ts (`injectRegister: false`), and the
    // manifest is the hand-written public/manifest.json (`manifest: false`).
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      injectRegister: false,
      manifest: false,
      injectManifest: {
        // Candidates: built JS/CSS, index.html, icons, manifest. runtime-config.js is deployment
        // state rewritten at container start and the kill switch's carrier: never precached.
        globPatterns: ['**/*.{js,css,html}', 'icons/*.png', 'manifest.json'],
        globIgnores: ['runtime-config.js', 'sw.js', '**/node_modules/**'],
        maximumFileSizeToCacheInBytes: 3 * 1024 * 1024,
        // ...narrowed to the app shell (src/pwa/appShell.ts): index.html and what it loads
        // eagerly. Lazy route chunks are cached on first use by the worker's /assets/ route.
        manifestTransforms: [
          (entries) => {
            // `vite dev` has no dist/index.html (and its worker skips the precache anyway).
            const indexPath = fileURLToPath(new URL('./dist/index.html', import.meta.url));
            const indexHtml = existsSync(indexPath) ? readFileSync(indexPath, 'utf8') : '';
            const shell = appShellFiles(indexHtml);
            return { manifest: entries.filter((entry) => isAppShellEntry(entry.url, shell)), warnings: [] };
          },
        ],
      },
      // Skaffold's dev target runs `vite dev`: serve the worker there too (as a module worker at
      // /dev-sw.js?dev-sw, without the precache), so Web Push keeps working in development.
      devOptions: {
        enabled: true,
        type: 'module',
      },
    }),
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
