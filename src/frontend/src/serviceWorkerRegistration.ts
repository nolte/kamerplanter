/**
 * Service worker registration for Web Push (PWA notifications).
 *
 * The worker itself lives at `public/sw.js` and is served from the site root as
 * `/sw.js`. Registration is intentionally guarded and non-fatal: on browsers
 * without service-worker support, or if registration fails, app startup must
 * continue unaffected.
 */
export function registerServiceWorker(): void {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }
  // Register after load to avoid competing with critical startup work.
  navigator.serviceWorker.register('/sw.js').catch(() => {
    // Non-fatal: push notifications simply stay unavailable on this device.
  });
}
