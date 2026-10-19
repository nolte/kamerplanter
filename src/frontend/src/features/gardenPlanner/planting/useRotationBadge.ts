/**
 * The badge a bed carries while a planting that was started despite a crop-rotation hint is under way
 * (REQ-053 GP-FR-132, GP-ACC-047): the runs of the bed that are not finished and carry a
 * `rotation_override_reason`. A failed request shows no badge - the badge is a hint, not a gate.
 */
import { useEffect, useState } from 'react';
import { listBedRuns } from './plantingApi';

export interface RotationBadge {
  /** The reasons grown-ups gave when they planted anyway, newest run first. */
  reasons: string[];
}

const FINISHED = new Set(['completed', 'cancelled']);

export function useRotationBadge(bedKey: string, refreshKey: number = 0): RotationBadge | null {
  const [badge, setBadge] = useState<{ bedKey: string; value: RotationBadge | null } | null>(null);
  useEffect(() => {
    let cancelled = false;
    listBedRuns(bedKey)
      .then((runs) => {
        if (cancelled) return;
        const reasons = runs
          .filter((run) => !FINISHED.has(run.status) && run.rotation_override_reason)
          .map((run) => run.rotation_override_reason as string);
        setBadge({ bedKey, value: reasons.length > 0 ? { reasons } : null });
      })
      .catch(() => {
        if (!cancelled) setBadge({ bedKey, value: null });
      });
    return () => {
      cancelled = true;
    };
  }, [bedKey, refreshKey]);
  return badge && badge.bedKey === bedKey ? badge.value : null;
}
