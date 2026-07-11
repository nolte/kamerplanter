import { useCallback, useEffect, useMemo, useState } from 'react';
import { getSiteClimateNormals } from '@/api/endpoints/weatherSources';
import type { ClimateNormal } from '@/api/types';

interface FetchState {
  loading: boolean;
  /** True when the climate-normals request itself failed (endpoint/network). */
  error: boolean;
  normals: ClimateNormal[];
}

interface State extends FetchState {
  /** Re-runs the fetch (surfaced so the section can offer a retry). */
  refetch: () => void;
}

const INITIAL: FetchState = { loading: true, error: false, normals: [] };

/**
 * REQ-041 — loads a site's long-term climate normals (NASA POWER) for the
 * "Klima am Standort" section. Graceful by contract: an unpopulated site returns
 * an empty `normals` list (not an error), so the section renders its empty state.
 *
 * Returns an object, `useMemo`-stabilised per the custom-hook convention so
 * consumers don't re-render on referentially-new snapshots.
 */
export function useSiteClimateNormals(siteKey: string | undefined): State {
  const [state, setState] = useState<FetchState>(INITIAL);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!siteKey) {
      setState({ loading: false, error: false, normals: [] });
      return;
    }
    let cancelled = false;
    const load = async () => {
      setState((prev) => ({ ...prev, loading: true, error: false }));
      try {
        const resp = await getSiteClimateNormals(siteKey);
        if (cancelled) return;
        setState({ loading: false, error: false, normals: resp.normals });
      } catch {
        if (!cancelled) setState({ loading: false, error: true, normals: [] });
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [siteKey, reloadToken]);

  const refetch = useCallback(() => setReloadToken((n) => n + 1), []);

  return useMemo(
    () => ({ loading: state.loading, error: state.error, normals: state.normals, refetch }),
    [state.loading, state.error, state.normals, refetch],
  );
}
