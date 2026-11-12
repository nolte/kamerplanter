/**
 * The device position for "My position" in field mode (REQ-053 GP-UX-026), following the REQ-002 opt-in pattern
 * of `useGeolocation`: nothing is asked of the browser until the user switches it on, the browser's own permission
 * prompt decides, an unsupported browser hides the feature, an insecure context disables it with the reason, and a
 * refusal, a missing fix or a timeout is said in words. Unlike the one-off site fix this follows the device
 * (`watchPosition`) while `enabled` is true and the page is visible; it stops on switch-off, on unmount (leaving the
 * map or field mode) and while the browser tab is hidden.
 *
 * The fix lives in this hook's state and nowhere else: no Redux, no storage, no request, no log (SR-019). The
 * opt-in itself is not remembered either - every visit starts with the switch off.
 */
import { useEffect, useMemo, useState } from 'react';

/** A device fix, reduced to what the plan needs. Never leaves the device. */
export interface DeviceFix {
  latitude: number;
  longitude: number;
  /** The device's 95 % radius in metres, as the browser reports it. */
  accuracyM: number;
}

export type OwnPositionStatus =
  | 'off'
  | 'unsupported'
  | 'insecure'
  | 'locating'
  | 'denied'
  | 'unavailable'
  | 'timeout'
  | 'located';

export interface UseOwnPosition {
  /** The browser has a Geolocation API with `watchPosition` (feature detect, REQ-002). */
  supported: boolean;
  /** Supported and in a secure context (HTTPS or localhost). */
  available: boolean;
  status: OwnPositionStatus;
  /** The latest fix while `status === 'located'`, else `null`. */
  fix: DeviceFix | null;
}

// GeolocationPositionError codes, compared numerically (as in `useGeolocation`).
const GEO_PERMISSION_DENIED = 1;
const GEO_TIMEOUT = 3;

const WATCH_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  // A fix a few seconds old is good enough to walk with and saves the battery.
  maximumAge: 5_000,
  timeout: 20_000,
};

function pageVisible(): boolean {
  return typeof document === 'undefined' || document.visibilityState !== 'hidden';
}

type Watch = { status: 'locating' | 'denied' | 'unavailable' | 'timeout' | 'located'; fix: DeviceFix | null };

export function useOwnPosition(enabled: boolean): UseOwnPosition {
  const supported =
    typeof navigator !== 'undefined' &&
    'geolocation' in navigator &&
    typeof navigator.geolocation?.watchPosition === 'function';
  const secureContext = typeof window !== 'undefined' && window.isSecureContext;
  const available = supported && secureContext;

  const [visible, setVisible] = useState(pageVisible);
  useEffect(() => {
    if (!enabled) return undefined;
    const onChange = () => setVisible(pageVisible());
    document.addEventListener('visibilitychange', onChange);
    return () => document.removeEventListener('visibilitychange', onChange);
  }, [enabled]);

  const watching = enabled && available && visible;
  const [watch, setWatch] = useState<Watch | null>(null);
  useEffect(() => {
    if (!watching) return undefined;
    let active = true;
    const id = navigator.geolocation.watchPosition(
      (position) => {
        if (!active) return;
        setWatch({
          status: 'located',
          fix: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracyM: position.coords.accuracy,
          },
        });
      },
      (error) => {
        if (!active) return;
        if (error.code === GEO_PERMISSION_DENIED) {
          setWatch({ status: 'denied', fix: null });
          return;
        }
        // A timeout or a lost fix keeps watching; an old fix is not shown as current.
        setWatch({ status: error.code === GEO_TIMEOUT ? 'timeout' : 'unavailable', fix: null });
      },
      WATCH_OPTIONS,
    );
    return () => {
      active = false;
      navigator.geolocation.clearWatch(id);
      // Nothing of the last fix survives the watch.
      setWatch(null);
    };
  }, [watching]);

  let status: OwnPositionStatus;
  if (!enabled) status = 'off';
  else if (!supported) status = 'unsupported';
  else if (!secureContext) status = 'insecure';
  else status = watch?.status ?? 'locating';
  const fix = status === 'located' ? (watch?.fix ?? null) : null;

  return useMemo(() => ({ supported, available, status, fix }), [supported, available, status, fix]);
}
