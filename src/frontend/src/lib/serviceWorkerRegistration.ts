/**
 * The ONE service worker registration module (UI-NFR-012 §3.2, REQ-053 WP 9.1, #2741).
 *
 * The worker is built by `vite-plugin-pwa` (`injectManifest`, R-011) from `src/sw.ts` and served as
 * `/sw.js`; in `vite dev` the plugin serves it as a module worker at `/dev-sw.js?dev-sw`, so Web
 * Push also works on Skaffold's dev target. {@link registerServiceWorker} is the only entry point —
 * the bare `navigator.serviceWorker.register` call is not exported, so no caller can register while
 * skipping the kill switch or the namespace hand-over:
 *
 * - Kill switch (G-W9 e): `PWA_CACHING_ENABLED=false` in `runtime-config.js` (written at container
 *   start, never cached) unregisters every worker and deletes every cache and IndexedDB database
 *   instead of registering. The worker reads the same flag itself, so the switch also reaches a tab
 *   whose app code is an older build.
 * - A worker that takes control gets this tab's namespace again.
 * - Updates (R-014): a new version waits until the user confirms it in the update banner. Once a
 *   tab has seen a waiting update, it reloads when the new worker takes control — whichever tab
 *   confirmed it.
 *
 * The waiting registration is kept in a tiny external store ({@link subscribeToUpdate},
 * {@link getWaitingRegistration}) so the banner can read it with `useSyncExternalStore`.
 */
import { runtimeConfig } from '@/config/runtimeConfig';
import { SW_MESSAGE_SKIP_WAITING, isPwaCachingEnabled } from '@/pwa/cachePolicy';
import { clearAllOfflineStorage, repostNamespace } from '@/pwa/offlineData';

let waitingRegistration: ServiceWorkerRegistration | null = null;
const updateListeners = new Set<() => void>();
let reloadArmed = false;

function serviceWorkerSupported(): boolean {
  return typeof navigator !== 'undefined' && 'serviceWorker' in navigator && Boolean(navigator.serviceWorker);
}

/** Subscribe to "a new version is waiting" (for `useSyncExternalStore`). */
export function subscribeToUpdate(listener: () => void): () => void {
  updateListeners.add(listener);
  return () => {
    updateListeners.delete(listener);
  };
}

/** The registration whose new worker waits for the user's confirmation, if any. */
export function getWaitingRegistration(): ServiceWorkerRegistration | null {
  return waitingRegistration;
}

/** Reload this tab as soon as a new worker controls it (armed once per page). */
function armReloadOnControllerChange(): void {
  if (reloadArmed || !serviceWorkerSupported()) return;
  reloadArmed = true;
  navigator.serviceWorker.addEventListener(
    'controllerchange',
    () => {
      markUpdateAvailable(null);
      window.location.reload();
    },
    { once: true },
  );
}

/**
 * Record a waiting update (or its dismissal with `null`) and notify the banner. A tab that has seen
 * an update reloads when it activates — also when ANOTHER tab confirmed it (review finding 7).
 */
export function markUpdateAvailable(registration: ServiceWorkerRegistration | null): void {
  waitingRegistration = registration;
  if (registration) armReloadOnControllerChange();
  updateListeners.forEach((listener) => listener());
}

/** Whether this deployment allows the service worker to cache (default: yes). */
export function pwaCachingEnabled(): boolean {
  return isPwaCachingEnabled(runtimeConfig().PWA_CACHING_ENABLED);
}

/** The worker's URL and type: the built classic worker, or the dev server's module worker. */
function workerScript(): { url: string; type: WorkerType } {
  return import.meta.env.DEV ? { url: '/dev-sw.js?dev-sw', type: 'module' } : { url: '/sw.js', type: 'classic' };
}

function watchForUpdates(registration: ServiceWorkerRegistration): void {
  if (registration.waiting && navigator.serviceWorker.controller) markUpdateAvailable(registration);
  registration.addEventListener('updatefound', () => {
    const installing = registration.installing;
    if (!installing) return;
    installing.addEventListener('statechange', () => {
      // A first install has no controller and activates on its own; only a replacement waits.
      if (installing.state === 'installed' && navigator.serviceWorker.controller) {
        markUpdateAvailable(registration);
      }
    });
  });
}

/**
 * Register the worker, or — with the kill switch off — remove it and everything it stored.
 * Guarded: without service-worker support nothing happens, and a failure never breaks startup —
 * but it is reported, because a missing worker silently disables Web Push.
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!serviceWorkerSupported()) return null;
  try {
    if (!pwaCachingEnabled()) {
      await unregisterAll();
      await clearAllOfflineStorage();
      return null;
    }
    const { url, type } = workerScript();
    const registration = await navigator.serviceWorker.register(url, {
      scope: '/',
      type,
      updateViaCache: 'none',
    });
    watchForUpdates(registration);
    // A worker that just took control (first install, confirmed update) has no namespace for this
    // tab yet: hand it the current one.
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      void repostNamespace();
    });
    return registration;
  } catch (error) {
    console.warn('[pwa] service worker registration failed; push and offline reading are unavailable', error);
    return null;
  }
}

/**
 * Activate the waiting worker — the "Jetzt aktualisieren" button of the update banner (R-014). The
 * page reloads once the new worker controls it. When another tab already activated it (nothing
 * waits any more), the banner closes and this tab reloads onto the new build at once.
 */
export function activateWaitingWorker(registration: ServiceWorkerRegistration): void {
  if (!registration.waiting) {
    markUpdateAvailable(null);
    window.location.reload();
    return;
  }
  armReloadOnControllerChange();
  registration.waiting.postMessage({ type: SW_MESSAGE_SKIP_WAITING });
}

/** Unregister all service workers (kill switch). */
export async function unregisterAll(): Promise<void> {
  if (!serviceWorkerSupported()) return;
  const registrations = await navigator.serviceWorker.getRegistrations();
  await Promise.all(registrations.map((r) => r.unregister()));
}
