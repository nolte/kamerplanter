/**
 * Display names of the location types by key, in the active language. A failed request leaves the
 * map empty; callers then show the raw key rather than nothing.
 */
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { listLocationTypes } from '@/api/endpoints/sites';
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
      .catch(() => undefined);
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
