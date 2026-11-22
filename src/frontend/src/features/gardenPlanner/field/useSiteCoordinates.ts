/**
 * `Site.gps_coordinates` for "My position" in field mode (REQ-053 GP-UX-026). The plan response does not carry
 * the coordinate, so the site is read once the user switches the position on - not before, so field mode costs no
 * extra request for those who never use it. The request names the site only; the device position is never part
 * of it (SR-019).
 */
import { useEffect, useMemo, useState } from 'react';
import { getSite } from '@/api/endpoints/sites';
import type { GeoPoint } from '../model/ownPosition';

export type SiteCoordinates =
  | { status: 'idle' | 'loading' | 'error' | 'missing'; coordinates: null }
  | { status: 'ready'; coordinates: GeoPoint };

type Loaded = { key: string; coordinates: GeoPoint | null } | { key: string; failed: true };

export function useSiteCoordinates(siteKey: string, enabled: boolean): SiteCoordinates {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const current = loaded !== null && loaded.key === siteKey ? loaded : null;
  // A failed read is tried again when the user switches the position off and on (or comes back online and does).
  const known = current !== null && !('failed' in current);
  useEffect(() => {
    if (!enabled || known) return undefined;
    let cancelled = false;
    getSite(siteKey)
      .then((site) => {
        if (cancelled) return;
        const gps = site.gps_coordinates ?? null;
        setLoaded({ key: siteKey, coordinates: gps ? { latitude: gps[0], longitude: gps[1] } : null });
      })
      .catch(() => {
        if (!cancelled) setLoaded({ key: siteKey, failed: true });
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, known, siteKey]);

  return useMemo((): SiteCoordinates => {
    if (!enabled) return { status: 'idle', coordinates: null };
    if (current === null) return { status: 'loading', coordinates: null };
    if ('failed' in current) return { status: 'error', coordinates: null };
    return current.coordinates
      ? { status: 'ready', coordinates: current.coordinates }
      : { status: 'missing', coordinates: null };
  }, [enabled, current]);
}
