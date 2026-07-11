import { useCallback, useEffect, useMemo, useState } from 'react';
import * as api from '@/api/endpoints/inventree';
import { useApiError } from './useApiError';
import type { Equipment, InvenTreeConnection } from '@/api/types';

interface UseEquipmentResult {
  equipment: Equipment[];
  connections: InvenTreeConnection[];
  loading: boolean;
  /** Re-fetches the equipment list and connection summary. */
  reload: () => void;
}

/**
 * Loads the tenant's equipment inventory and the InvenTree connection summary
 * on mount (REQ-016). Connections are optional — a failed connection fetch
 * (feature disabled) never blocks the equipment list, so the page degrades
 * gracefully to a pure equipment view.
 *
 * The async loader is declared inside the effect body so `setState` is never
 * called synchronously at the effect's top level (react-hooks lint clean).
 */
export function useEquipment(): UseEquipmentResult {
  const { handleError } = useApiError();

  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [connections, setConnections] = useState<InvenTreeConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const items = await api.listEquipment();
        if (cancelled) return;
        setEquipment(items);
      } catch (error) {
        if (!cancelled) handleError(error);
      } finally {
        if (!cancelled) setLoading(false);
      }
      // Connections are optional (admin-only, feature-gated) — a failure here
      // must not surface an error toast on the equipment view.
      try {
        const conns = await api.listConnections();
        if (!cancelled) setConnections(conns);
      } catch {
        if (!cancelled) setConnections([]);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [handleError, reloadToken]);

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  return useMemo(
    () => ({ equipment, connections, loading, reload }),
    [equipment, connections, loading, reload],
  );
}
