/**
 * The garden-planning thresholds of a site (REQ-053 GP-FR-164/166, WP 8.24): the sun-class bounds the sun tiles
 * name and the reach thresholds of the `bed.reach_too_wide` hint. Read from `GET /sites/{key}` once per site key;
 * until the answer arrives, and when the request fails, the defaults apply, so the help texts and the hint never
 * wait for or break on the site.
 */
import { useEffect, useMemo, useState } from 'react';
import { getSite } from '@/api/endpoints/sites';
import type { Site } from '@/api/types';
import { siteThresholds, type SiteThresholds } from '../model/siteThresholds';

type ThresholdFields = Pick<Site, 'sun_class_thresholds' | 'reach_thresholds'>;

export function useSiteThresholds(siteKey: string | null | undefined): SiteThresholds {
  const [loaded, setLoaded] = useState<{ key: string; site: ThresholdFields } | null>(null);
  useEffect(() => {
    if (!siteKey) return undefined;
    let cancelled = false;
    getSite(siteKey)
      .then((site) => {
        if (!cancelled) {
          setLoaded({
            key: siteKey,
            site: { sun_class_thresholds: site.sun_class_thresholds, reach_thresholds: site.reach_thresholds },
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
  return useMemo(() => siteThresholds(site), [site]);
}
