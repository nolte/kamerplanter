/**
 * The trellises standing in a bed, for the planting dialog's support hint (REQ-053 W-005, Anhang A 62, WP 10.10):
 * the site's garden objects of class `trellis` whose outline lies in the bed or touches it - edge distance 0 by the
 * plan's own measure (`rawEdgeDistanceM`, GP-FR-167), so a trellis along the bed edge counts, one a step away does
 * not. Scenery beyond the boundary (`off_site`) never stands in a bed.
 *
 * Read only while `needed` (a chosen species has `support_required`) and the site is known; the hint is information,
 * so a failed read is shown as "could not check", never as "no trellis".
 */
import { useEffect, useMemo, useState } from 'react';
import { rawEdgeDistanceM } from '../model/geometryDistance';
import type { GardenObject, Geometry } from '../model/types';
import { listSiteGardenObjects } from './plantingApi';

/** A trellis in the bed: its key, its label (may be empty) and its height in m when recorded. */
export interface BedTrellis {
  key: string;
  label: string;
  heightM: number | null;
}

export type BedTrellisState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; trellises: BedTrellis[] }
  | { status: 'error' };

type Answer = { siteKey: string; objects: GardenObject[] } | { siteKey: string; failed: true };

const IDLE: BedTrellisState = { status: 'idle' };
const LOADING: BedTrellisState = { status: 'loading' };
const ERROR: BedTrellisState = { status: 'error' };

/** The trellises among `objects` that lie in `bed` or touch it (same plan frame). */
export function trellisesInBed(objects: readonly GardenObject[], bed: Geometry): BedTrellis[] {
  return objects.flatMap((object) => {
    if (object.object_type !== 'trellis' || object.off_site) return [];
    if (rawEdgeDistanceM(bed, object.geometry) > 0) return [];
    const heightM = object.props.object_type === 'trellis' ? object.props.height_m : null;
    return [{ key: object.key, label: object.label, heightM }];
  });
}

export function useBedTrellises(siteKey: string | undefined, bed: Geometry, needed: boolean): BedTrellisState {
  const [answer, setAnswer] = useState<Answer | null>(null);
  const active = needed && Boolean(siteKey);

  useEffect(() => {
    if (!active || !siteKey) return undefined;
    let cancelled = false;
    listSiteGardenObjects(siteKey)
      .then((objects) => {
        if (!cancelled) setAnswer({ siteKey, objects });
      })
      .catch(() => {
        if (!cancelled) setAnswer({ siteKey, failed: true });
      });
    return () => {
      cancelled = true;
    };
  }, [active, siteKey]);

  return useMemo<BedTrellisState>(() => {
    if (!active) return IDLE;
    if (answer === null || answer.siteKey !== siteKey) return LOADING;
    if ('failed' in answer) return ERROR;
    return { status: 'ready', trellises: trellisesInBed(answer.objects, bed) };
  }, [active, answer, siteKey, bed]);
}
