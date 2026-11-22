/**
 * Display names of the location types by key, in the active language. A failed request leaves the
 * map empty; callers then show the raw key rather than nothing — a display enrichment, so the
 * failure is reported (#3013) but not rendered.
 */
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { listLocationTypes } from '@/api/endpoints/sites';
import { captureHandledError } from '@/observability/errorTracking';
import type { LocationType } from '@/api/types';

export function useLocationTypeNames(): ReadonlyMap<string, string> {
  const { i18n } = useTranslation();
  const [types, setTypes] = useState<LocationType[]>([]);
  useEffect(() => {
    let cancelled = false;
    listLocationTypes()
      .then((all) => {
        if (!cancelled) setTypes(all);
      })
      .catch((error: unknown) => {
        // Display enrichment only: the raw type key stands in for its name.
        captureHandledError(error, { source: 'useLocationTypeNames' });
      });
    return () => {
      cancelled = true;
    };
  }, []);
  const english = i18n.language.startsWith('en');
  return useMemo(
    () => new Map(types.map((type) => [type.key, (english && type.name_en) || type.name])),
    [types, english],
  );
}
