import { useEffect, useMemo, useState } from 'react';
import * as plantApi from '@/api/endpoints/plantInstances';
import { getPlantLabel } from '@/utils/plantDisplay';

/** Above this many keys the caller shows a count; one request per plant would not scale (a bed has up to 200). */
export const PLANT_LABEL_LIMIT = 5;

export interface PlantLabels {
  /** `plant key → label`; a key whose plant could not be loaded maps to the key itself. */
  labels: ReadonlyMap<string, string>;
  /** `true` while the names are being fetched. */
  loading: boolean;
  /** `true` when there are more keys than {@link PLANT_LABEL_LIMIT}: nothing is fetched, show a count. */
  tooMany: boolean;
}

/**
 * The display names of a few plants, best effort: each plant is loaded on its own, and a plant that cannot be
 * loaded (removed, no access) keeps its key as the label instead of failing the page.
 */
export function usePlantLabels(keys: readonly string[]): PlantLabels {
  // One stable dependency for the effect, whatever array identity the caller passes.
  const signature = keys.join('\u0000');
  const tooMany = keys.length > PLANT_LABEL_LIMIT;
  const [resolved, setResolved] = useState<{ signature: string; labels: Map<string, string> } | null>(null);

  useEffect(() => {
    const wanted = signature === '' ? [] : signature.split('\u0000');
    if (wanted.length === 0 || wanted.length > PLANT_LABEL_LIMIT) return;
    let cancelled = false;
    Promise.allSettled(wanted.map((key) => plantApi.getPlantInstance(key))).then((results) => {
      if (cancelled) return;
      const labels = new Map<string, string>();
      results.forEach((result, index) => {
        const key = wanted[index];
        labels.set(key, result.status === 'fulfilled' ? getPlantLabel(result.value) : key);
      });
      setResolved({ signature, labels });
    });
    return () => {
      cancelled = true;
    };
  }, [signature]);

  return useMemo(() => {
    const wanted = signature === '' ? [] : signature.split('\u0000');
    const current = resolved?.signature === signature ? resolved.labels : null;
    const labels = current ?? new Map(wanted.map((key) => [key, key] as const));
    const loading = !tooMany && wanted.length > 0 && current === null;
    return { labels, loading, tooMany };
  }, [resolved, signature, tooMany]);
}
