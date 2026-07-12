import { useEffect, useMemo, useState } from 'react';
import { listPlantInstances } from '@/api/endpoints/plantInstances';
import type { PlantInstance } from '@/api/types';

export interface PlantInstanceOptionsState {
  instances: PlantInstance[];
  loading: boolean;
}

/**
 * Loads the tenant's plant instances once for use as autocomplete options
 * (e.g. in {@link PlantInstanceAutocompleteField}). The backing list API
 * (`listPlantInstances`) has no name-search parameter, so a single capped page
 * is fetched and filtering happens client-side inside the picker — this mirrors
 * how `SpeciesAutocompleteField` consumes a pre-fetched `species` list.
 *
 * The async loader is declared *inside* the effect body so `setState` is never
 * called synchronously at the top level of the effect callback, keeping
 * `react-hooks/set-state-in-effect` clean without an eslint-disable.
 *
 * @param enabled - When false, no fetch happens (e.g. a closed dialog).
 */
export function usePlantInstanceOptions(enabled = true): PlantInstanceOptionsState {
  const [instances, setInstances] = useState<PlantInstance[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const result = await listPlantInstances(0, 200);
        if (!cancelled) setInstances(result);
      } catch {
        if (!cancelled) setInstances([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return useMemo(() => ({ instances, loading }), [instances, loading]);
}
