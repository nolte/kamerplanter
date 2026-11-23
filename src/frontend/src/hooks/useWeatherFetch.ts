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
 * How much earlier than the click a run may have started and still count as the
 * one this click caused: the server's and the browser's clock can differ. A
 * fetch takes the lock only after the POST was admitted, so its run cannot start
 * long before the click.
 */
export const WEATHER_FETCH_CLOCK_TOLERANCE_MS = 120_000;

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

/**
 * Whose run `result` is.
 *
 * - `own` — the manual fetch this click queued.
 * - `scheduledInstead` — the click was accepted, but a scheduled run took the lock
 *   first; the manual task then skips (`already_running`) and records no run of
 *   its own, so the scheduled run's result is all there is.
 * - `alreadyRunning` — the click was refused with 409 `WEATHER_FETCH_RUNNING`; the
 *   card followed the run that held the lock.
 */
export type WeatherFetchResultOrigin = 'own' | 'scheduledInstead' | 'alreadyRunning';

export interface UseWeatherFetchResult {
  status: WeatherFetchStatusResponse | null;
  statusLoading: boolean;
  statusError: boolean;
  reloadStatus: () => Promise<void>;
  phase: WeatherFetchPhase;
  /** The run that ended after this card's trigger (phase `finished`). */
  result: WeatherFetchRun | null;
  /** Whose run `result` is; `null` while there is none. */
  resultOrigin: WeatherFetchResultOrigin | null;
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
  const [resultOrigin, setResultOrigin] = useState<WeatherFetchResultOrigin | null>(null);
  const [refusal, setRefusal] = useState<WeatherFetchRefusal | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(null);

  // One controller per mount: unmounting aborts every status read still in flight,
  // so a card that is gone neither sets state nor leaves an admin read behind.
  const controllerRef = useRef<AbortController | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const statusRef = useRef<WeatherFetchStatusResponse | null>(null);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    controllerRef.current = controller;
    return () => {
      controller.abort();
      stopPolling();
    };
  }, [stopPolling]);

  /** The signal of the current mount; an aborted one before the first effect has run. */
  const currentSignal = useCallback((): AbortSignal => {
    if (controllerRef.current) return controllerRef.current.signal;
    return AbortSignal.abort();
  }, []);

  const applyStatus = useCallback((next: WeatherFetchStatusResponse) => {
    statusRef.current = next;
    setStatus(next);
    const wait = next.manual_fetch_available_in_s;
    setCooldownUntil(wait && wait > 0 ? Date.now() + wait * 1000 : null);
  }, []);

  /** Read the status; every state update happens in the promise callbacks, never synchronously. */
  const readStatus = useCallback(() => {
    const signal = currentSignal();
    return getWeatherFetchStatus(signal).then(
      (next) => {
        if (signal.aborted) return;
        applyStatus(next);
        setStatusError(false);
        setStatusLoading(false);
      },
      (err: unknown) => {
        // An aborted read belongs to a card that is gone: nothing to show or report.
        if (signal.aborted) return;
        captureHandledError(err, { source: 'useWeatherFetch.status' });
        setStatusError(true);
        setStatusLoading(false);
      },
    );
  }, [applyStatus, currentSignal]);

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

  /**
   * Follow the status until a run newer than `baseline` has ended, or the budget is spent.
   *
   * `notBefore` (epoch-ms) additionally drops runs that started before it — a run
   * that ended between the page load and the click is not this click's result,
   * even when the fresh pre-click read failed and `baseline` is stale. `null` for
   * the 409 path, where the followed run may have started well before the click.
   */
  const pollUntilFinished = useCallback(
    (baseline: string | null, notBefore: number | null, accepted: boolean) => {
      stopPolling();
      let polls = 0;
      const tick = async () => {
        pollTimerRef.current = null;
        polls += 1;
        const signal = currentSignal();
        try {
          const next = await getWeatherFetchStatus(signal);
          if (signal.aborted) return;
          applyStatus(next);
          setStatusError(false);
          const latest = next.last_run ?? null;
          const isNewRun =
            latest !== null &&
            runId(latest) !== baseline &&
            (notBefore === null || Date.parse(latest.started_at) >= notBefore);
          if (next.running !== true && latest && isNewRun) {
            setResult(latest);
            if (!accepted) setResultOrigin('alreadyRunning');
            else setResultOrigin(latest.trigger === 'manual' ? 'own' : 'scheduledInstead');
            setPhase('finished');
            return;
          }
        } catch (err) {
          if (signal.aborted) return;
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
    [applyStatus, currentSignal, stopPolling],
  );

  const trigger = useCallback(async () => {
    const clickedAt = Date.now();
    const signal = currentSignal();
    stopPolling();
    setPhase('starting');
    setResult(null);
    setResultOrigin(null);
    setRefusal(null);
    // The baseline is the newest run *right now*, not the one the page loaded: a
    // scheduled run that ran while the page was open must not pass for this click's.
    let baseline = runId(statusRef.current?.last_run);
    try {
      const fresh = await getWeatherFetchStatus(signal);
      if (signal.aborted) return;
      applyStatus(fresh);
      baseline = runId(fresh.last_run);
    } catch (err) {
      if (signal.aborted) return;
      // Not fatal: the click-time bound in the poll still keeps an older run out.
      captureHandledError(err, { source: 'useWeatherFetch.baseline' });
    }
    try {
      // The POST itself is not aborted: a click that reached the server stays a click.
      await triggerWeatherFetch();
      if (signal.aborted) return;
      setPhase('running');
      pollUntilFinished(baseline, clickedAt - WEATHER_FETCH_CLOCK_TOLERANCE_MS, true);
    } catch (err) {
      if (signal.aborted) return;
      if (isApiError(err) && err.errorCode === 'WEATHER_FETCH_RUNNING') {
        // Another run (scheduled or someone else's) holds the lock: follow that one.
        setPhase('running');
        pollUntilFinished(baseline, null, false);
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
            const next = await getWeatherFetchStatus(signal);
            if (signal.aborted) return;
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
  }, [applyStatus, currentSignal, pollUntilFinished, stopPolling]);

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
      resultOrigin,
      refusal,
      cooldownUntil,
      canTrigger,
      trigger,
    }),
    [
      status,
      statusLoading,
      statusError,
      reloadStatus,
      phase,
      result,
      resultOrigin,
      refusal,
      cooldownUntil,
      canTrigger,
      trigger,
    ],
  );
}
