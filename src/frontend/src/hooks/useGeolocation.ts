import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from './useNotification';

/** A one-off browser geolocation fix, reduced to plain coordinates. */
export interface GeolocationFix {
  latitude: number;
  longitude: number;
}

/**
 * Stabilized return of {@link useGeolocation} (object return ⇒ `useMemo`,
 * FRONTEND.md custom-hook rule).
 */
export interface UseGeolocation {
  /** Browser exposes a usable Geolocation API (feature detect). */
  supported: boolean;
  /** Feature available for use: supported AND running in a secure context. */
  available: boolean;
  /** Localised reason the feature cannot be used (for a tooltip), else null. */
  unavailableReason: string | null;
  /** True while a position fix is in progress. */
  detecting: boolean;
  /**
   * Requests a single best-effort position fix (opt-in, permission-gated). On
   * success `onFix` is invoked with the coordinates; on failure a localised
   * error toast is shown and `onFix` is never called (existing input is kept).
   */
  detect: (onFix: (fix: GeolocationFix) => void) => void;
}

// GeolocationPositionError codes (compared numerically so the mapping does not
// depend on the error instance carrying the named constants).
const GEO_PERMISSION_DENIED = 1;
const GEO_TIMEOUT = 3;

const GEO_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 10_000,
};

/**
 * Encapsulates the opt-in browser geolocation flow shared by the site create
 * and edit forms (REQ-002): feature/secure-context detection, a permission-gated
 * one-off position fix, and graceful degradation with localised error toasts.
 * Never performs server-side location lookup.
 */
export function useGeolocation(): UseGeolocation {
  const { t } = useTranslation();
  const notification = useNotification();
  const [detecting, setDetecting] = useState(false);

  const supported =
    typeof navigator !== 'undefined' &&
    'geolocation' in navigator &&
    typeof navigator.geolocation?.getCurrentPosition === 'function';
  const secureContext = typeof window !== 'undefined' && window.isSecureContext;
  const available = supported && secureContext;

  const unavailableReason = useMemo(() => {
    if (!supported) return t('pages.sites.gpsDetectUnsupported');
    if (!secureContext) return t('pages.sites.gpsDetectInsecure');
    return null;
  }, [supported, secureContext, t]);

  const detect = useCallback(
    (onFix: (fix: GeolocationFix) => void) => {
      if (!available) return;
      setDetecting(true);
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setDetecting(false);
          onFix({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        (error) => {
          setDetecting(false);
          const messageKey =
            error.code === GEO_PERMISSION_DENIED
              ? 'pages.sites.gpsDetectDenied'
              : error.code === GEO_TIMEOUT
                ? 'pages.sites.gpsDetectTimeout'
                : 'pages.sites.gpsDetectUnavailable';
          notification.error(t(messageKey));
        },
        GEO_OPTIONS,
      );
    },
    [available, notification, t],
  );

  return useMemo(
    () => ({ supported, available, unavailableReason, detecting, detect }),
    [supported, available, unavailableReason, detecting, detect],
  );
}
