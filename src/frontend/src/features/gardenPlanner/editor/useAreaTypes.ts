/**
 * The types the user can pick for a new area (REQ-053 §9.5, GP-UX-071, #2913): the location types that are neither a
 * bed nor carry a slot layout and make sense as a surface of this plan.
 *
 * - Garden plan: the seeded garden, terrace, balcony and greenhouse, plus every type a platform admin added that is
 *   not indoor. Zone, home, building, room and container are structure, not something one draws in a garden.
 * - Indoor plan (WP 10.8): the seeded room, plus every added indoor type. Tent and shelf stay planting spots
 *   (`supports_layout`, the bed tool offers them).
 *
 * Loaded on demand, like {@link useBedTypes}: only while an area is about to be created. A failed request leaves the
 * list empty; the draw tool then uses the editor's fallback type.
 */
import { useEffect, useMemo, useState } from 'react';
import * as sitesApi from '@/api/endpoints/sites';
import type { LocationType } from '@/api/types';

/** The seeded area types a garden plan offers, in this order. */
const GARDEN_AREA_TYPES: readonly string[] = ['garden', 'terrace', 'balcony', 'greenhouse'];
/** The seeded area types an indoor plan offers. */
const INDOOR_AREA_TYPES: readonly string[] = ['room'];

/** Whether `type` is offered as an area type of a garden plan (`indoor` false) or an indoor plan. Pure. */
export function isOfferedAreaType(type: LocationType, indoor: boolean): boolean {
  if (type.is_bed || type.supports_layout) return false;
  if (type.is_system) return (indoor ? INDOOR_AREA_TYPES : GARDEN_AREA_TYPES).includes(type.key);
  return type.is_indoor === indoor;
}

/** The offered area types of `all`: the seeded ones in their fixed order, then the added ones by `sort_order`. */
export function offeredAreaTypes(all: readonly LocationType[], indoor: boolean): LocationType[] {
  const seeded = indoor ? INDOOR_AREA_TYPES : GARDEN_AREA_TYPES;
  const rank = (type: LocationType) => {
    const index = seeded.indexOf(type.key);
    return index === -1 ? seeded.length : index;
  };
  return all
    .filter((type) => isOfferedAreaType(type, indoor))
    .sort((a, b) => rank(a) - rank(b) || a.sort_order - b.sort_order || a.name.localeCompare(b.name));
}

export function useAreaTypes(enabled: boolean, indoor: boolean): LocationType[] {
  const [all, setAll] = useState<LocationType[] | null>(null);
  useEffect(() => {
    if (!enabled || all !== null) return undefined;
    let cancelled = false;
    sitesApi
      .listLocationTypes()
      .then((types) => {
        if (!cancelled) setAll(types);
      })
      .catch(() => {
        if (!cancelled) setAll([]);
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, all]);
  // Derived per plan kind; the array keeps its identity while neither changes (FRONTEND.md: useMemo for arrays).
  return useMemo(() => (all ? offeredAreaTypes(all, indoor) : NO_TYPES), [all, indoor]);
}

const NO_TYPES: LocationType[] = [];
