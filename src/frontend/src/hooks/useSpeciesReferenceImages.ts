import { useCallback, useEffect, useMemo, useState } from 'react';
import { getSpeciesReferenceImages } from '@/api/endpoints/species';
import type { ReferenceImage } from '@/api/types';

/** Stable return shape of {@link useSpeciesReferenceImages}. */
export interface UseSpeciesReferenceImagesResult {
  images: ReferenceImage[];
  loading: boolean;
}

/**
 * Lazily loads the active external CC-BY/CC0 reference images of a species
 * (`GET /species/{key}/reference-images`).
 *
 * Only fetches when a `speciesKey` is provided — instances without an assigned
 * species never trigger a request. A failed lookup or unreachable
 * inference-service is treated as "no images" (empty list), never an error:
 * the reference section is simply hidden by the caller in that case.
 *
 * The return value is stabilised with `useMemo` per the project hook convention
 * (objects/arrays must not change identity on every render).
 */
export function useSpeciesReferenceImages(
  speciesKey: string | null | undefined,
): UseSpeciesReferenceImagesResult {
  const [images, setImages] = useState<ReferenceImage[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!speciesKey) {
      setImages([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await getSpeciesReferenceImages(speciesKey);
      setImages(data.images ?? []);
    } catch {
      // A missing index / unreachable service is treated as "no images".
      setImages([]);
    } finally {
      setLoading(false);
    }
  }, [speciesKey]);

  useEffect(() => {
    void load();
  }, [load]);

  return useMemo(() => ({ images, loading }), [images, loading]);
}
