import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // The heavy MUI form pages (SpeciesDetailPage and friends) render and drive
    // userEvent interactions that comfortably finish in isolation (~3s) but blow
    // past the 5s default under full-suite parallelism — especially with v8
    // coverage instrumentation, which roughly doubles wall-clock. Give every
    // test and hook enough headroom that load, not correctness, decides the run.
    testTimeout: 20000,
    hookTimeout: 20000,
    server: {
      deps: {
        // @mui/material's Transition.mjs (MUI 9.1.1+) does an extensionless
        // directory import of react-transition-group, which ships no
        // "exports" map. Vitest's Node ESM resolver rejects that, while the
        // Vite build resolves it fine. Inlining the @mui packages and
        // react-transition-group routes them through Vitest's transform
        // pipeline, which resolves the import the same way the build does.
        inline: [/@mui\//, 'react-transition-group'],
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'json-summary'],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
});
