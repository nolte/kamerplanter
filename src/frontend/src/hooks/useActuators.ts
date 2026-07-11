import { useCallback, useEffect, useMemo, useState } from 'react';
import * as api from '@/api/endpoints/environment';
import { useApiError } from './useApiError';
import type { Actuator } from '@/api/types';

interface UseActuatorsResult {
  actuators: Actuator[];
  loading: boolean;
  /** Re-fetches the actuator list, e.g. after a command or creation. */
  reload: () => void;
}

/**
 * Loads the tenant's actuators on mount.
 *
 * The async loader lives inside the effect body so `setState` is never called
 * synchronously at the top level of the effect callback (mirrors
 * `useAquaponicSystems`), keeping `react-hooks/set-state-in-effect` clean.
 */
export function useActuators(): UseActuatorsResult {
  const { handleError } = useApiError();
  const [actuators, setActuators] = useState<Actuator[]>([]);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.listActuators();
        if (!cancelled) setActuators(data);
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

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  return useMemo(
    () => ({ actuators, loading, reload }),
    [actuators, loading, reload],
  );
}
