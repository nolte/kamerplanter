import { useCallback, useEffect, useMemo, useState } from 'react';
import { getSoilAnalyses } from './bedApi';
import type { SoilAnalysesResponse } from './soilAnalysisTypes';

export interface SoilAnalysesState {
  data: SoilAnalysesResponse | null;
  /** No answer yet (first read). */
  loading: boolean;
  failed: boolean;
  reload: () => void;
}

/**
 * The soil analyses of a bed (GP-FR-122). `version` is anything that changes when the profile behind it changed
 * (the summary reloaded) - the liming hint is derived from the current profile, so the answer is read again.
 */
export function useSoilAnalyses(bedKey: string, version: unknown): SoilAnalysesState {
  const [data, setData] = useState<SoilAnalysesResponse | null>(null);
  const [failed, setFailed] = useState(false);
  const [round, setRound] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getSoilAnalyses(bedKey, controller.signal)
      .then((answer) => {
        setData(answer);
        setFailed(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [bedKey, version, round]);

  const reload = useCallback(() => setRound((value) => value + 1), []);
  // Loading until the first answer or failure; a later reload keeps the last answer on screen.
  const loading = data === null && !failed;
  return useMemo(() => ({ data, loading, failed, reload }), [data, loading, failed, reload]);
}
