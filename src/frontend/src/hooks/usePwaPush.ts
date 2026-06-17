import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  getPwaVapidPublicKey,
  subscribePwa,
  unsubscribePwa,
} from '@/api/endpoints/notifications';

export type PwaPushState =
  | 'unsupported'
  | 'checking'
  | 'denied'
  | 'inactive'
  | 'active';

interface UsePwaPushResult {
  /** Current high-level state of the push subscription on this device. */
  state: PwaPushState;
  /** Whether an enable/disable operation is currently in flight. */
  busy: boolean;
  /** Whether the browser supports the Web Push APIs needed here. */
  supported: boolean;
  /**
   * Request permission + subscribe + register with the backend.
   * Returns the resulting state so the caller can react synchronously
   * without waiting for the React state update to flush.
   */
  enable: () => Promise<PwaPushState>;
  /** Unsubscribe locally and tell the backend to drop the subscription. */
  disable: () => Promise<void>;
}

/**
 * Decode a URL-safe base64 VAPID public key into the Uint8Array that
 * `PushManager.subscribe({ applicationServerKey })` expects.
 */
export function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i += 1) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function isPushSupported(): boolean {
  return (
    typeof navigator !== 'undefined' &&
    'serviceWorker' in navigator &&
    typeof window !== 'undefined' &&
    'PushManager' in window &&
    'Notification' in window
  );
}

/**
 * Manages the browser's Web Push subscription for the current device:
 * permission, the `PushManager` subscription and backend registration.
 *
 * Per project convention the returned object is wrapped in {@link useMemo} so
 * its reference stays stable between renders.
 */
export function usePwaPush(): UsePwaPushResult {
  const supported = useMemo(() => isPushSupported(), []);
  const [state, setState] = useState<PwaPushState>(
    supported ? 'checking' : 'unsupported',
  );
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!supported) {
      setState('unsupported');
      return;
    }
    if (Notification.permission === 'denied') {
      setState('denied');
      return;
    }
    try {
      const registration = await navigator.serviceWorker.ready;
      const existing = await registration.pushManager.getSubscription();
      setState(existing ? 'active' : 'inactive');
    } catch {
      setState('inactive');
    }
  }, [supported]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const enable = useCallback(async (): Promise<PwaPushState> => {
    if (!supported) {
      setState('unsupported');
      return 'unsupported';
    }
    setBusy(true);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        const next: PwaPushState = permission === 'denied' ? 'denied' : 'inactive';
        setState(next);
        return next;
      }
      const registration = await navigator.serviceWorker.ready;
      const { vapid_public_key } = await getPwaVapidPublicKey();
      const applicationServerKey = urlBase64ToUint8Array(vapid_public_key);
      const subscription =
        (await registration.pushManager.getSubscription()) ??
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          // applicationServerKey expects a BufferSource; the underlying
          // ArrayBuffer satisfies it across TS lib.dom variations.
          applicationServerKey: applicationServerKey.buffer as ArrayBuffer,
        }));
      await subscribePwa(subscription.toJSON());
      setState('active');
      return 'active';
    } finally {
      setBusy(false);
    }
  }, [supported]);

  const disable = useCallback(async () => {
    if (!supported) {
      return;
    }
    setBusy(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        const endpoint = subscription.endpoint;
        await subscription.unsubscribe();
        await unsubscribePwa(endpoint);
      }
      setState('inactive');
    } finally {
      setBusy(false);
    }
  }, [supported]);

  return useMemo(
    () => ({ state, busy, supported, enable, disable }),
    [state, busy, supported, enable, disable],
  );
}
