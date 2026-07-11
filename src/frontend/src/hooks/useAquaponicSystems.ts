import { useCallback, useEffect, useMemo, useState } from 'react';
import * as api from '@/api/endpoints/aquaponik';
import { useApiError } from './useApiError';
import type {
  AquaponicSystem,
  CyclingProgress,
  FishStock,
  WaterQualityEvaluation,
} from '@/api/types';

export interface AquaponicSystemDetail {
  cycling: CyclingProgress | null;
  waterQuality: WaterQualityEvaluation[];
  stocks: FishStock[];
}

interface UseAquaponicSystemsResult {
  systems: AquaponicSystem[];
  loading: boolean;
  selectedKey: string | null;
  selectSystem: (key: string) => void;
  detail: AquaponicSystemDetail | null;
  detailLoading: boolean;
  /** Re-fetches the system list, e.g. after a system was created. */
  reloadSystems: () => void;
  /** Re-fetches the selected system's detail, e.g. after a water test was recorded. */
  reloadDetail: () => void;
}

/**
 * Loads the tenant's aquaponic systems on mount and the selected system's
 * detail (cycling progress, water quality, fish stock) whenever the
 * selection changes.
 *
 * The async loaders are declared *inside* each effect body (mirroring the
 * pattern established by `useSiteWeatherForecast`), so `setState` is never
 * called synchronously at the top level of the effect callback — this keeps
 * `react-hooks/set-state-in-effect` clean without adding an eslint-disable.
 */
export function useAquaponicSystems(): UseAquaponicSystemsResult {
  const { handleError } = useApiError();

  const [systems, setSystems] = useState<AquaponicSystem[]>([]);
  const [loading, setLoading] = useState(true);
  const [systemsReloadToken, setSystemsReloadToken] = useState(0);

  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [detail, setDetail] = useState<AquaponicSystemDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailReloadToken, setDetailReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.listSystems();
        if (cancelled) return;
        setSystems(data);
        if (data.length > 0) {
          setSelectedKey((prev) => prev ?? data[0].key);
        }
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
  }, [handleError, systemsReloadToken]);

  useEffect(() => {
    if (!selectedKey) return;
    let cancelled = false;
    const load = async () => {
      setDetailLoading(true);
      try {
        const [cycling, waterQuality, stocks] = await Promise.all([
          api.getCyclingProgress(selectedKey),
          api.getWaterQualityStatus(selectedKey),
          api.listStocks(selectedKey),
        ]);
        if (cancelled) return;
        setDetail({ cycling, waterQuality, stocks });
      } catch (error) {
        if (!cancelled) handleError(error);
      } finally {
        if (!cancelled) setDetailLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [selectedKey, handleError, detailReloadToken]);

  const selectSystem = useCallback((key: string) => setSelectedKey(key), []);
  const reloadSystems = useCallback(() => setSystemsReloadToken((t) => t + 1), []);
  const reloadDetail = useCallback(() => setDetailReloadToken((t) => t + 1), []);

  return useMemo(
    () => ({
      systems,
      loading,
      selectedKey,
      selectSystem,
      detail,
      detailLoading,
      reloadSystems,
      reloadDetail,
    }),
    [systems, loading, selectedKey, selectSystem, detail, detailLoading, reloadSystems, reloadDetail],
  );
}
