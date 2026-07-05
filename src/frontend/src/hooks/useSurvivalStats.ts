import { useCallback, useEffect, useMemo, useState } from 'react';
import { getSurvivalStats } from '@/api/endpoints/plantInstances';
import type { SurvivalStats } from '@/api/types';

interface UseSurvivalStatsResult {
  stats: SurvivalStats | null;
  loading: boolean;
  error: boolean;
  reload: () => void;
}

/**
 * Loads the tenant's survival / failure-cause analytics (REQ-003 G1).
 *
 * ``refreshKey`` lets a caller re-fetch after a plant is removed/terminated
 * (bump the value). The returned object is ``useMemo``-stabilised per the
 * custom-hook convention so consumers can safely put it in dependency arrays.
 */
export function useSurvivalStats(refreshKey: number = 0): UseSurvivalStatsResult {
  const [stats, setStats] = useState<SurvivalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    getSurvivalStats()
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => load(), [load, refreshKey]);

  return useMemo(
    () => ({ stats, loading, error, reload: load }),
    [stats, loading, error, load],
  );
}
