/**
 * Service worker boot (UI-NFR-012 basis, REQ-053 WP 9.1, #2741).
 *
 * One worker at `/sw.js` (built from `src/sw.ts`) carries Web Push, the app-shell precache and the
 * tenant-bound API cache. Registration is guarded and non-fatal: without service-worker support, or
 * if registration fails, app startup continues unaffected.
 *
 * Kill switch (G-W9 e): `PWA_CACHING_ENABLED=false` in `runtime-config.js` (written at container
 * start, never cached) unregisters every worker and deletes every cache and IndexedDB database
 * instead of registering. The worker reads the same flag on its own and removes itself as well, so
 * the switch also reaches a tab whose app code is an older build.
 */
import { runtimeConfig } from '@/config/runtimeConfig';
import { isPwaCachingEnabled } from '@/pwa/cachePolicy';
import { clearAllOfflineStorage, repostNamespace } from '@/pwa/offlineData';
import {
  markUpdateAvailable,
  registerServiceWorker as registerWorker,
  unregisterAll,
} from '@/lib/serviceWorkerRegistration';

/** Whether this deployment allows the service worker to cache (default: yes). */
export function pwaCachingEnabled(): boolean {
  return isPwaCachingEnabled(runtimeConfig().PWA_CACHING_ENABLED);
}

/** Register the worker, or — with the kill switch off — remove it and everything it stored. */
export async function registerServiceWorker(): Promise<void> {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }
  try {
    if (!pwaCachingEnabled()) {
      await unregisterAll();
      await clearAllOfflineStorage();
      return;
    }
    const registration = await registerWorker({ onUpdateAvailable: markUpdateAvailable });
    if (!registration) return;
    // A worker that just took control has no namespace yet (first install, or a confirmed update
    // whose reload is still pending): hand it the current one.
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      void repostNamespace();
    });
  } catch {
    // Non-fatal: push notifications and offline reading simply stay unavailable on this device.
  }
}
