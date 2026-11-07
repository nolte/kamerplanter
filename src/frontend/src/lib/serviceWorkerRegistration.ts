/**
 * UI-NFR-012 §3.2 service worker registration helper (REQ-053 WP 9.1, #2741).
 *
 * The worker is built by `vite-plugin-pwa` (`injectManifest`, R-011) from `src/sw.ts` and served as
 * `/sw.js`. This module wraps the registration and the update lifecycle: a new version waits until
 * the user confirms it in the update banner (R-014), which calls {@link activateWaitingWorker}; the
 * page reloads once the new worker has taken control.
 *
 * The waiting registration is kept in a tiny external store ({@link subscribeToUpdate},
 * {@link getWaitingRegistration}) so the banner can read it with `useSyncExternalStore` without the
 * boot code depending on React.
 */
import { SW_MESSAGE_SKIP_WAITING } from '@/pwa/cachePolicy';

export interface ServiceWorkerRegistrationOptions {
  /**
   * Called when a new service worker version is available. UI layers
   * use this to render the "Neue Version verfügbar" banner (R-014).
   */
  onUpdateAvailable?: (registration: ServiceWorkerRegistration) => void;
  /** Called once the service worker has activated for the first time. */
  onActivated?: (registration: ServiceWorkerRegistration) => void;
  /** Suppress registration entirely (test seam / opt-out). */
  disabled?: boolean;
}

let waitingRegistration: ServiceWorkerRegistration | null = null;
const updateListeners = new Set<() => void>();
let reloadArmed = false;

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

/** Record a waiting update (or its dismissal with `null`) and notify the banner. */
export function markUpdateAvailable(registration: ServiceWorkerRegistration | null): void {
  waitingRegistration = registration;
  updateListeners.forEach((listener) => listener());
}

/**
 * Register the service worker if the runtime supports it.
 *
 * Returns `null` on environments without service worker support
 * (`navigator.serviceWorker` undefined, e.g. SSR, very old browsers,
 * insecure http), when registration is explicitly disabled, or when the
 * browser refuses it. On success returns the `ServiceWorkerRegistration`.
 */
export async function registerServiceWorker(
  options: ServiceWorkerRegistrationOptions = {},
): Promise<ServiceWorkerRegistration | null> {
  if (options.disabled) return null;
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
      updateViaCache: 'none',
    });

    if (registration.waiting && options.onUpdateAvailable) {
      options.onUpdateAvailable(registration);
    }

    registration.addEventListener('updatefound', () => {
      const installing = registration.installing;
      if (!installing) return;
      installing.addEventListener('statechange', () => {
        if (installing.state === 'installed') {
          if (navigator.serviceWorker.controller && options.onUpdateAvailable) {
            options.onUpdateAvailable(registration);
          } else if (!navigator.serviceWorker.controller && options.onActivated) {
            options.onActivated(registration);
          }
        }
      });
    });

    return registration;
  } catch {
    // The environment refuses the worker (e.g. the dev server serves none). Don't break the app.
    return null;
  }
}

/**
 * Activate the waiting worker — the "Jetzt aktualisieren" button of the update banner (R-014). The
 * page reloads once the new worker controls it, so the new build's assets are the ones in use.
 */
export function activateWaitingWorker(registration: ServiceWorkerRegistration): void {
  if (!registration.waiting) return;
  if (!reloadArmed && typeof navigator !== 'undefined' && navigator.serviceWorker) {
    reloadArmed = true;
    navigator.serviceWorker.addEventListener('controllerchange', () => window.location.reload(), {
      once: true,
    });
  }
  registration.waiting.postMessage({ type: SW_MESSAGE_SKIP_WAITING });
}

/**
 * Unregister all service workers. Used by the kill switch (`PWA_CACHING_ENABLED=false`).
 */
export async function unregisterAll(): Promise<void> {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }
  const registrations = await navigator.serviceWorker.getRegistrations();
  await Promise.all(registrations.map((r) => r.unregister()));
}
