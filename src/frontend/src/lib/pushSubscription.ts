import { unsubscribePwa } from '@/api/endpoints/notifications';

/** How long the session end waits for the browser's service-worker registration. */
const REGISTRATION_TIMEOUT_MS = 2_000;
/** How long a logout waits for the backend to drop the subscription before it signs out anyway. */
const SERVER_UNSUBSCRIBE_TIMEOUT_MS = 3_000;

/** Whether the browser offers the Web Push APIs the PWA channel needs. */
export function isPushSupported(): boolean {
  return (
    typeof navigator !== 'undefined' &&
    'serviceWorker' in navigator &&
    typeof window !== 'undefined' &&
    'PushManager' in window &&
    'Notification' in window
  );
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T | undefined> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(undefined), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      () => {
        clearTimeout(timer);
        resolve(undefined);
      },
    );
  });
}

/**
 * Drop this device's Web-Push subscription at the end of a session (#2117).
 *
 * A push endpoint identifies the browser profile, not the person: left in place,
 * the next account to sign in on a shared device would receive the previous
 * account's notifications. With `notifyServer` the backend copy is removed first
 * — that needs the access token, so the logout calls this before its own request;
 * a forced sign-out (the session is already gone) only unsubscribes the browser,
 * and the push service then answers the backend's next send with "gone", which
 * prunes the stored copy.
 *
 * Best effort and bounded: never throws, waits at most
 * {@link REGISTRATION_TIMEOUT_MS} for a service worker that may never register
 * (development, an unsupported browser) and {@link SERVER_UNSUBSCRIBE_TIMEOUT_MS}
 * for the backend — a logout must not hang on either.
 */
export async function releasePushSubscription({ notifyServer }: { notifyServer: boolean }): Promise<void> {
  if (!isPushSupported()) return;
  try {
    const registration = await withTimeout(
      navigator.serviceWorker.getRegistration(),
      REGISTRATION_TIMEOUT_MS,
    );
    const subscription = await registration?.pushManager.getSubscription();
    if (!subscription) return;
    if (notifyServer) {
      // Bounded, and a failure is swallowed by `withTimeout`: the browser
      // unsubscribe below still ends delivery, and the server copy is pruned when
      // the push service reports the endpoint gone.
      await withTimeout(unsubscribePwa(subscription.endpoint), SERVER_UNSUBSCRIBE_TIMEOUT_MS);
    }
    await subscription.unsubscribe();
  } catch {
    // Nothing here may keep a session from ending.
  }
}
