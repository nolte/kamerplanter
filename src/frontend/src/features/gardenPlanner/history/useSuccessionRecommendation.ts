/**
 * Loads the follow-up crop recommendation of a bed (`GET /locations/{key}/succession-recommendation`, REQ-053
 * GP-FR-133). It is a hint beside the timeline: a failed request leaves the timeline alone and shows its own retry.
 * `version` is bumped by the caller when the history changed (a year was filled in or taken back).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getSuccessionRecommendation } from './historyApi';
import type { SuccessionRecommendation } from './historyTypes';

export type SuccessionState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; recommendation: SuccessionRecommendation };

export function useSuccessionRecommendation(bedKey: string, version: number) {
  const [state, setState] = useState<SuccessionState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    getSuccessionRecommendation(bedKey)
      .then((recommendation) => {
        if (!cancelled) setState({ status: 'ready', recommendation });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [bedKey, version, attempt]);

  const retry = useCallback(() => {
    setState({ status: 'loading' });
    setAttempt((value) => value + 1);
  }, []);
  return useMemo(() => ({ state, retry }), [state, retry]);
}
