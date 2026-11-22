import { useEffect, useState } from 'react';
import { listCultivars } from '@/api/endpoints/species';
import type { Cultivar } from '@/api/types';

/** The cultivars of a species (empty while loading or when the request fails: the cultivar is optional). */
export function useCultivars(speciesKey: string | null): Cultivar[] {
  const [loaded, setLoaded] = useState<{ speciesKey: string; items: Cultivar[] } | null>(null);
  useEffect(() => {
    if (!speciesKey) return undefined;
    let cancelled = false;
    listCultivars(speciesKey)
      .then((items) => {
        if (!cancelled) setLoaded({ speciesKey, items });
      })
      .catch(() => {
        if (!cancelled) setLoaded({ speciesKey, items: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [speciesKey]);
  return loaded && loaded.speciesKey === speciesKey ? loaded.items : EMPTY;
}

const EMPTY: Cultivar[] = [];
