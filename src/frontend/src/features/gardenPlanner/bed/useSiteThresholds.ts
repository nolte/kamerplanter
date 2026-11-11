/**
 * The garden-planning thresholds of a site (REQ-053 GP-FR-164/166, WP 8.24): the sun-class bounds the sun tiles
 * name and the reach thresholds of the `bed.reach_too_wide` hint. Read from `GET /sites/{key}` once per site key;
 * until the answer arrives, and when the request fails, the defaults apply, so the help texts and the hint never
 * wait for or break on the site.
 *
 * `useSiteFacts` hands out the site's type from the same read (WP 10.8): the bed view hides weather, frost and wind
 * for an indoor site (GP-FR-182). Until the site is read the type is `null` - a garden, as before. The latitude
 * (`gps_coordinates[0]`) feeds the window suggestion (GP-FR-181, WP 10.7): `null` while unknown, which assumes the
 * northern hemisphere and says so.
 */
import { useEffect, useMemo, useState } from 'react';
import { getSite } from '@/api/endpoints/sites';
import type { Site, SiteType } from '@/api/types';
import { siteThresholds, type SiteThresholds } from '../model/siteThresholds';

type SiteFields = Pick<Site, 'sun_class_thresholds' | 'reach_thresholds' | 'window_thresholds' | 'type' | 'gps_coordinates'>;

export interface SiteFacts {
  thresholds: SiteThresholds;
  /** `null` while the site is read or when it cannot be read. */
  siteType: SiteType | null;
  /** The site's latitude, `null` while the site is read, when it cannot be read or has no coordinates. */
  latitude: number | null;
}

export function useSiteFacts(siteKey: string | null | undefined): SiteFacts {
  const [loaded, setLoaded] = useState<{ key: string; site: SiteFields } | null>(null);
  useEffect(() => {
    if (!siteKey) return undefined;
    let cancelled = false;
    getSite(siteKey)
      .then((site) => {
        if (!cancelled) {
          setLoaded({
            key: siteKey,
            site: {
              sun_class_thresholds: site.sun_class_thresholds,
              reach_thresholds: site.reach_thresholds,
              window_thresholds: site.window_thresholds,
              type: site.type,
              gps_coordinates: site.gps_coordinates ?? null,
            },
          });
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [siteKey]);
  // A site loaded for another key (the user moved on) does not count.
  const site = loaded !== null && loaded.key === siteKey ? loaded.site : null;
  return useMemo(
    () => ({
      thresholds: siteThresholds(site),
      siteType: site?.type ?? null,
      latitude: site?.gps_coordinates?.[0] ?? null,
    }),
    [site],
  );
}
