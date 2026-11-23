import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getWeatherFetchStatus, triggerWeatherFetch } from '@/api/endpoints/adminWeatherProviders';
import { isApiError } from '@/api/errors';
import type { WeatherFetchRun, WeatherFetchStatusResponse } from '@/api/types';
import { captureHandledError } from '@/observability/errorTracking';

/** How often the status is read while a fetch runs. */
export const WEATHER_FETCH_POLL_INTERVAL_MS = 3000;
/**
 * The most status reads one fetch is followed for (5 minutes at 3 s). A run
 * that takes longer is still running server-side; the card then says the result
 * will appear in the status instead of polling forever.
 */
export const WEATHER_FETCH_MAX_POLLS = 100;

/**
 * Where a manual fetch stands.
 *
 * - `idle` — nothing started from this card (or the last result was dismissed).
 * - `starting` — the POST is in flight.
 * - `running` — accepted (202) or already running (409), the status is polled.
 * - `finished` — a run newer than the one before the trigger has ended; `result` holds it.
 * - `timedOut` — the poll budget ran out before the run ended.
 */
export type WeatherFetchPhase = 'idle' | 'starting' | 'running' | 'finished' | 'timedOut';

/** Why a manual fetch was refused or could not be started. */
export type WeatherFetchRefusal =
  /** 429 — `availableAt` is the epoch-ms the cooldown ends, `null` when unknown. */
  | { kind: 'cooldown'; availableAt: number | null }
  /** 409 `WEATHER_FETCH_DISABLED` — `WEATHER_ENABLED=false` on this installation. */
  | { kind: 'disabled' }
  /** 503 — lock store or task broker unreachable. */
  | { kind: 'unavailable' }
  /** Anything else (network, 403, 5xx). */
  | { kind: 'error' };

export interface UseWeatherFetchResult {
  status: WeatherFetchStatusResponse | null;
  statusLoading: boolean;
  statusError: boolean;
  reloadStatus: () => Promise<void>;
  phase: WeatherFetchPhase;
  /** The run that ended after this card's trigger (phase `finished`). */
  result: WeatherFetchRun | null;
  refusal: WeatherFetchRefusal | null;
  /** Epoch-ms when the cooldown after the previous manual fetch ends; `null` when none runs. */
  cooldownUntil: number | null;
  /** Whether "fetch now" may be pressed right now. */
  canTrigger: boolean;
  trigger: () => Promise<void>;
}

/** The identity of a run: two runs never share a start instant. */
function runId(run: WeatherFetchRun | null | undefined): string | null {
  return run?.started_at ?? null;
}

/**
 * REQ-046 §3.6a (#2934, F-14) — the weather fetch status and the manual "fetch
 * now" of the installation's weather card.
 *
 * Reads `GET /admin/weather-providers/fetch-status` on mount and whenever
 * `statusVersion` changes. `trigger()` posts
 * the manual fetch and, once it is accepted, follows the status with a bounded
 * recursive timeout until a run newer than the one before the trigger has ended.
 * Every timer is cleared on unmount, so a card left mid-fetch stops polling.
 */
export function useWeatherFetch(statusVersion = 0): UseWeatherFetchResult {
  const [status, setStatus] = useState<WeatherFetchStatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState(false);
  const [phase, setPhase] = useState<WeatherFetchPhase>('idle');
  const [result, setResult] = useState<WeatherFetchRun | null>(null);
  const [refusal, setRefusal] = useState<WeatherFetchRefusal | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(null);

  const mountedRef = useRef(true);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const statusRef = useRef<WeatherFetchStatusResponse | null>(null);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      stopPolling();
    };
  }, [stopPolling]);

  const applyStatus = useCallback((next: WeatherFetchStatusResponse) => {
    statusRef.current = next;
    setStatus(next);
    const wait = next.manual_fetch_available_in_s;
    setCooldownUntil(wait && wait > 0 ? Date.now() + wait * 1000 : null);
  }, []);

  /** Read the status; every state update happens in the promise callbacks, never synchronously. */
  const readStatus = useCallback(
    () =>
      getWeatherFetchStatus().then(
        (next) => {
          if (!mountedRef.current) return;
          applyStatus(next);
          setStatusError(false);
          setStatusLoading(false);
        },
        (err: unknown) => {
          if (!mountedRef.current) return;
          captureHandledError(err, { source: 'useWeatherFetch.status' });
          setStatusError(true);
          setStatusLoading(false);
        },
      ),
    [applyStatus],
  );

  const reloadStatus = useCallback(async () => {
    setStatusLoading(true);
    await readStatus();
  }, [readStatus]);

  // On mount, and again whenever the caller bumps `statusVersion` (e.g. after a saved
  // interval moved the next scheduled fetch).
  useEffect(() => {
    void readStatus();
  }, [readStatus, statusVersion]);

  // The cooldown ends on its own: re-enable the button at that instant.
  useEffect(() => {
    if (cooldownUntil === null) return undefined;
    const timer = setTimeout(() => {
      setCooldownUntil(null);
      setRefusal((prev) => (prev?.kind === 'cooldown' ? null : prev));
    }, Math.max(0, cooldownUntil - Date.now()));
    return () => clearTimeout(timer);
  }, [cooldownUntil]);

  /** Follow the status until a run newer than `baseline` has ended, or the budget is spent. */
  const pollUntilFinished = useCallback(
    (baseline: string | null) => {
      stopPolling();
      let polls = 0;
      const tick = async () => {
        pollTimerRef.current = null;
        polls += 1;
        try {
          const next = await getWeatherFetchStatus();
          if (!mountedRef.current) return;
          applyStatus(next);
          setStatusError(false);
          const latest = next.last_run ?? null;
          if (next.running !== true && latest && runId(latest) !== baseline) {
            setResult(latest);
            setPhase('finished');
            return;
          }
        } catch (err) {
          if (!mountedRef.current) return;
          // A failed read costs one poll of the budget; the next tick tries again.
          captureHandledError(err, { source: 'useWeatherFetch.poll' });
        }
        if (polls >= WEATHER_FETCH_MAX_POLLS) {
          setPhase('timedOut');
          return;
        }
        pollTimerRef.current = setTimeout(() => void tick(), WEATHER_FETCH_POLL_INTERVAL_MS);
      };
      pollTimerRef.current = setTimeout(() => void tick(), WEATHER_FETCH_POLL_INTERVAL_MS);
    },
    [applyStatus, stopPolling],
  );

  const trigger = useCallback(async () => {
    const baseline = runId(statusRef.current?.last_run);
    stopPolling();
    setPhase('starting');
    setResult(null);
    setRefusal(null);
    try {
      await triggerWeatherFetch();
      if (!mountedRef.current) return;
      setPhase('running');
      pollUntilFinished(baseline);
    } catch (err) {
      if (!mountedRef.current) return;
      if (isApiError(err) && err.errorCode === 'WEATHER_FETCH_RUNNING') {
        // Another run (scheduled or someone else's) holds the lock: follow that one.
        setPhase('running');
        pollUntilFinished(baseline);
        return;
      }
      setPhase('idle');
      if (isApiError(err) && err.errorCode === 'WEATHER_FETCH_DISABLED') {
        setRefusal({ kind: 'disabled' });
      } else if (isApiError(err) && err.statusCode === 429) {
        let waitSeconds = err.retryAfterSeconds;
        if (waitSeconds === null) {
          // No readable Retry-After (a proxy may drop it): the status knows the same wait.
          try {
            const next = await getWeatherFetchStatus();
            if (!mountedRef.current) return;
            applyStatus(next);
            waitSeconds = next.manual_fetch_available_in_s ?? null;
          } catch (statusErr) {
            // Swallowed on purpose: the refusal is still shown, only without the instant
            // (`cooldownUnknown` says to wait 10 minutes). Logged so it stays visible.
            captureHandledError(statusErr, { source: 'useWeatherFetch.cooldownStatus' });
          }
        }
        const availableAt = waitSeconds !== null && waitSeconds > 0 ? Date.now() + waitSeconds * 1000 : null;
        if (availableAt !== null) setCooldownUntil(availableAt);
        setRefusal({ kind: 'cooldown', availableAt });
      } else if (isApiError(err) && err.statusCode === 503) {
        setRefusal({ kind: 'unavailable' });
      } else {
        captureHandledError(err, { source: 'useWeatherFetch.trigger' });
        setRefusal({ kind: 'error' });
      }
    }
  }, [applyStatus, pollUntilFinished, stopPolling]);

  const weatherDisabled = status !== null && !status.next_scheduled_at;
  const canTrigger =
    status !== null &&
    !weatherDisabled &&
    status.running === false &&
    cooldownUntil === null &&
    phase !== 'starting' &&
    phase !== 'running';

  return useMemo(
    () => ({
      status,
      statusLoading,
      statusError,
      reloadStatus,
      phase,
      result,
      refusal,
      cooldownUntil,
      canTrigger,
      trigger,
    }),
    [status, statusLoading, statusError, reloadStatus, phase, result, refusal, cooldownUntil, canTrigger, trigger],
  );
}
