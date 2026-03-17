// Runtime config (injected by docker-entrypoint.sh) takes precedence over
// Vite build-time env var.  This allows switching modes without rebuilding.
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: { KAMERPLANTER_MODE?: string };
  }
}

export const KAMERPLANTER_MODE: 'light' | 'full' =
  (window.__RUNTIME_CONFIG__?.KAMERPLANTER_MODE as 'light' | 'full') ||
  (import.meta.env.VITE_KAMERPLANTER_MODE as string as 'light' | 'full') ||
  'full';

export const isLightMode = KAMERPLANTER_MODE === 'light';
export const isFullMode = KAMERPLANTER_MODE === 'full';
