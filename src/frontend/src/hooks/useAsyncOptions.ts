import { useState, useEffect, useCallback, useMemo } from 'react';

export interface AsyncOptionsResult<T> {
  options: T[];
  loading: boolean;
  /** True when the load failed — render an error hint instead of an empty list. */
  error: boolean;
  /** Re-run the loader (e.g. from a "retry" affordance). */
  reload: () => void;
}

interface UseAsyncOptionsConfig {
  /** When false the loader is not called (e.g. dialog not yet open). */
  enabled?: boolean;
}

/**
 * Loads select/autocomplete options with explicit loading/error state.
 *
 * Replaces the silent `.catch(() => {})` pattern (Code-Review FE-L3): a failed
 * load previously produced an empty list indistinguishable from "no data". With
 * this hook the caller can render a visible hint when `error` is true.
 *
 * The `loader` MUST be referentially stable across renders (wrap it in
 * `useCallback` in the caller); otherwise the effect re-runs on every render.
 * ESLint's `react-hooks/exhaustive-deps` enforces this.
 */
export function useAsyncOptions<T>(
  loader: () => Promise<T[]>,
  { enabled = true }: UseAsyncOptionsConfig = {},
): AsyncOptionsResult<T> {
  const [options, setOptions] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    setLoading(true);
    setError(false);
    loader()
      .then((items) => {
        if (!cancelled) setOptions(items);
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
  }, [loader, enabled, nonce]);

  // FRONTEND.md §6.1: object return MUST be useMemo-stabilised.
  return useMemo(
    () => ({ options, loading, error, reload }),
    [options, loading, error, reload],
  );
}
