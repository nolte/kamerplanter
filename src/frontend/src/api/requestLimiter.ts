/**
 * Bounded concurrency for client-side fan-out reads (#3032).
 *
 * **The defect this closes.** A list page that resolves display names one key at
 * a time (`Promise.all(keys.map(getSlot))`) fires every request at once. Over
 * plain HTTP the browser holds at most six connections per host and queues the
 * rest — including the lazily imported chunk of the page the user navigates to
 * next. React Router renders that navigation in a transition, so while the chunk
 * waits behind hundreds of enrichment reads the old page stays on screen with
 * the new URL already in the address bar. Measured on the plant list of the
 * shared CI tenant (nightly 44706366400): ~13 700 `GET /slots/{key}` in one run,
 * backend latency up to 35 s, and no detail chunk served for the last eight
 * minutes of the run.
 *
 * A limiter keeps the fan-out to a few concurrent reads, so the connections left
 * over serve the navigation, and an `AbortSignal` drops every read still queued
 * once its caller is gone (unmount, superseded effect run).
 */

/**
 * Concurrent enrichment reads one page may hold. Below the browser's six
 * connections per host on purpose: the remainder is what a navigation away from
 * the page (route chunk, the destination's first fetch) and the app chrome's own
 * polling get while the page is still enriching.
 */
export const ENRICHMENT_CONCURRENCY = 3;

/** Rejection reason of a task dropped from the queue because its signal aborted. */
export class RequestDroppedError extends Error {
  constructor() {
    super('Request dropped before it started: its caller aborted.');
    this.name = 'RequestDroppedError';
  }
}

export interface RequestLimiter {
  /**
   * Runs *task* as soon as fewer than the limit are in flight. A task whose
   * *signal* aborts while it is still queued never starts and rejects with
   * {@link RequestDroppedError}; a task already started runs to completion.
   */
  run<T>(task: () => Promise<T>, signal?: AbortSignal): Promise<T>;
}

type QueuedTask = () => void;

/** Creates a limiter that lets at most *limit* tasks run at once (FIFO). */
export function createRequestLimiter(limit: number): RequestLimiter {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new RangeError(`limit must be a positive integer, got ${limit}`);
  }
  let inFlight = 0;
  const queue: QueuedTask[] = [];

  const pump = () => {
    while (inFlight < limit && queue.length > 0) {
      inFlight += 1;
      queue.shift()!();
    }
  };

  return {
    run<T>(task: () => Promise<T>, signal?: AbortSignal): Promise<T> {
      return new Promise<T>((resolve, reject) => {
        if (signal?.aborted) {
          reject(new RequestDroppedError());
          return;
        }
        // Leaves the queue at once on abort, so a dropped read neither waits for a free
        // slot to be rejected nor holds one.
        const onAbort = () => {
          const index = queue.indexOf(start);
          if (index !== -1) queue.splice(index, 1);
          reject(new RequestDroppedError());
        };
        const start: QueuedTask = () => {
          signal?.removeEventListener('abort', onAbort);
          let pending: Promise<T>;
          try {
            pending = task();
          } catch (err) {
            pending = Promise.reject(err);
          }
          pending.then(resolve, reject).finally(() => {
            inFlight -= 1;
            pump();
          });
        };
        signal?.addEventListener('abort', onAbort, { once: true });
        queue.push(start);
        pump();
      });
    },
  };
}
