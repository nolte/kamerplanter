/**
 * The bed types the user can pick for a new bed (REQ-053 GP-FR-040: location types flagged
 * `is_bed`). Loaded on demand - only while a bed is about to be created - so the editor makes no
 * request of its own otherwise. A failed request leaves the list empty; the draw tool then keeps
 * the plan's most common bed type.
 */
import { useEffect, useState } from 'react';
import * as sitesApi from '@/api/endpoints/sites';
import type { LocationType } from '@/api/types';

export function useBedTypes(enabled: boolean): LocationType[] {
  const [types, setTypes] = useState<LocationType[] | null>(null);
  useEffect(() => {
    if (!enabled || types !== null) return undefined;
    let cancelled = false;
    sitesApi
      .listLocationTypes()
      .then((all) => {
        if (!cancelled) setTypes(all.filter((type) => type.is_bed));
      })
      .catch(() => {
        if (!cancelled) setTypes([]);
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, types]);
  return types ?? [];
}
