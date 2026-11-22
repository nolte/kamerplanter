import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { PlantInstance } from '@/api/types';
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
  const { i18n } = useTranslation();
  const language = i18n.language;
  // The loaded plants (null = could not be loaded), labelled in the render so a
  // language switch relabels the species name without refetching (#2902).
  const [resolved, setResolved] = useState<{
    signature: string;
    plants: Map<string, PlantInstance | null>;
  } | null>(null);

  useEffect(() => {
    const wanted = signature === '' ? [] : signature.split('\u0000');
    if (wanted.length === 0 || wanted.length > PLANT_LABEL_LIMIT) return;
    let cancelled = false;
    Promise.allSettled(wanted.map((key) => plantApi.getPlantInstance(key))).then((results) => {
      if (cancelled) return;
      const plants = new Map<string, PlantInstance | null>();
      results.forEach((result, index) => {
        plants.set(wanted[index], result.status === 'fulfilled' ? result.value : null);
      });
      setResolved({ signature, plants });
    });
    return () => {
      cancelled = true;
    };
  }, [signature]);

  return useMemo(() => {
    const wanted = signature === '' ? [] : signature.split('\u0000');
    const current = resolved?.signature === signature ? resolved.plants : null;
    const labels = new Map(
      wanted.map((key) => {
        const plant = current?.get(key);
        return [key, plant ? getPlantLabel(plant, language) : key] as const;
      }),
    );
    const loading = !tooMany && wanted.length > 0 && current === null;
    return { labels, loading, tooMany };
  }, [resolved, signature, tooMany, language]);
}
