import { useCallback, useEffect, useRef } from 'react';

/**
 * One load run handed out by {@link useAbortableLoad}.
 *
 * `isCurrent()` turns false as soon as a newer run starts or the component
 * unmounts; `signal` is aborted at the same moment, so a request that accepts
 * an `AbortSignal` can be cancelled instead of merely ignored.
 */
export interface LoadTicket {
  readonly signal: AbortSignal;
  isCurrent: () => boolean;
}

/**
 * Latest-wins guard for detail-page loads (#3014).
 *
 * A detail page re-runs its load when the route key changes or after a save.
 * Without a guard, the response of the superseded run can arrive last and
 * overwrite the entity that is now selected. Call the returned `begin()` at the
 * start of every load run and check `ticket.isCurrent()` after each `await`
 * before writing state:
 *
 * ```ts
 * const beginLoad = useAbortableLoad();
 * const load = useCallback(async () => {
 *   const ticket = beginLoad();
 *   const entity = await api.get(key);
 *   if (!ticket.isCurrent()) return;
 *   setEntity(entity);
 * }, [beginLoad, key]);
 * ```
 *
 * The returned function is referentially stable, so it is safe in effect and
 * callback dependency lists. It deliberately carries no data/error state: a
 * loading/error/data contract can be layered on top of the ticket without
 * changing how pages discard stale runs.
 */
export function useAbortableLoad(): () => LoadTicket {
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      controllerRef.current?.abort();
      controllerRef.current = null;
    },
    [],
  );

  return useCallback(() => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    return {
      signal: controller.signal,
      isCurrent: () => controllerRef.current === controller && !controller.signal.aborted,
    };
  }, []);
}
