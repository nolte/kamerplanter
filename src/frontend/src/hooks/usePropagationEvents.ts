import { useCallback, useEffect, useMemo, useState } from 'react';
import * as api from '@/api/endpoints/propagation';
import { useApiError } from './useApiError';
import type { PropagationEvent } from '@/api/types';

interface UsePropagationEventsResult {
  events: PropagationEvent[];
  loading: boolean;
  /** Re-fetches the event list, e.g. after a new event was recorded. */
  reload: () => void;
}

/**
 * Loads the tenant's propagation events (REQ-017). The async loader is declared
 * inside the effect body (mirroring `useAquaponicSystems`) so `setState` is
 * never called synchronously at the top level of the effect callback. The
 * returned object is `useMemo`-stabilized per the custom-hook convention.
 */
export function usePropagationEvents(): UsePropagationEventsResult {
  const { handleError } = useApiError();
  const [events, setEvents] = useState<PropagationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.listPropagationEvents({ limit: 200 });
        if (!cancelled) setEvents(data);
      } catch (error) {
        if (!cancelled) handleError(error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [handleError, reloadToken]);

  const reload = useCallback(() => setReloadToken((n) => n + 1), []);

  return useMemo(() => ({ events, loading, reload }), [events, loading, reload]);
}
