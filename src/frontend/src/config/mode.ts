import { runtimeConfig } from './runtimeConfig';

// Runtime config (injected by docker-entrypoint.sh) takes precedence over the
// Vite build-time env var. This allows switching modes without rebuilding. The
// `Window.__RUNTIME_CONFIG__` shape itself is declared once in `runtimeConfig`,
// so mode and error tracking cannot disagree about what the container injects.
export const KAMERPLANTER_MODE: 'light' | 'full' =
  (runtimeConfig().KAMERPLANTER_MODE as 'light' | 'full') ||
  (import.meta.env.VITE_KAMERPLANTER_MODE as string as 'light' | 'full') ||
  'full';

export const isLightMode = KAMERPLANTER_MODE === 'light';
export const isFullMode = KAMERPLANTER_MODE === 'full';
