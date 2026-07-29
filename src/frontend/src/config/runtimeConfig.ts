/**
 * Values injected into the served bundle at container start, not at build time.
 *
 * `docker-entrypoint.d/10-runtime-config.sh` (and the Helm init container that
 * mirrors it) writes `runtime-config.js` into the web root before nginx starts;
 * `index.html` loads it before the app bundle. That is what lets one image serve
 * every stage: mode, error-tracking DSN and release are deployment facts, not
 * build facts.
 *
 * Everything is optional by construction — a plain `vite dev` run has no
 * `runtime-config.js` at all, so every consumer must carry its own fallback.
 */
export interface RuntimeConfig {
  /** REQ-027 operating mode: `light` (anonymous) or `full`. */
  KAMERPLANTER_MODE?: string;
  /** #777 — error-tracking DSN. Empty or absent keeps the SDK unloaded. */
  SENTRY_DSN?: string;
  /** Stage name from the closed vocabulary in `observability/errorTracking.ts`. */
  SENTRY_ENVIRONMENT?: string;
  /** Release identifier, normally the image tag or commit SHA. */
  SENTRY_RELEASE?: string;
  /** Event sample rate as a string, because it arrives from a shell heredoc. */
  SENTRY_SAMPLE_RATE?: string;
}

declare global {
  interface Window {
    __RUNTIME_CONFIG__?: RuntimeConfig;
  }
}

/** The injected runtime config, or an empty object when none was served. */
export function runtimeConfig(): RuntimeConfig {
  return window.__RUNTIME_CONFIG__ ?? {};
}
