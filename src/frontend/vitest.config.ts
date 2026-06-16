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
    testTimeout: 30000,
    hookTimeout: 30000,
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
        functions: 80,
        lines: 80,
        // Branch coverage is pinned below the 80% line/statement bar as a
        // ratchet, not an aspiration. The gh-plumbing coverage job (#189) only
        // went live recently and its real gate is line coverage; the strict
        // branch gate first bit on a frontend that already carried branch debt
        // in long-standing, untested components (ProfileEditDialog,
        // SpeciesWorkflowsSection, ProfilesSection, …). This pin reflects the
        // level reached after covering the species/cultivar detail pages; raise
        // it as the pre-existing debt is paid down, never lower it.
        branches: 75,
      },
    },
  },
});
