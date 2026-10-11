import type { Middleware, UnknownAction } from '@reduxjs/toolkit';
import { isSessionEnd } from './rootReducer';

/** The part of an async-thunk lifecycle action this middleware reads. */
interface ThunkLifecycleMeta {
  requestId?: unknown;
  requestStatus?: unknown;
}

function lifecycleOf(action: unknown): { requestId: string; status: unknown } | null {
  if (typeof action !== 'object' || action === null) return null;
  const meta = (action as { meta?: ThunkLifecycleMeta }).meta;
  if (typeof meta?.requestId !== 'string') return null;
  return { requestId: meta.requestId, status: meta.requestStatus };
}

function isAction(action: unknown): action is UnknownAction {
  return (
    typeof action === 'object' &&
    action !== null &&
    typeof (action as { type?: unknown }).type === 'string'
  );
}

/**
 * Drop the answers of requests that belong to a session which has since ended (#2253).
 *
 * The session-end reset (`rootReducer`, #2117) empties the slices once, on the
 * session-end action. A thunk dispatched before that action and settling after
 * it would otherwise reduce its answer into the freshly reset store: a slow list
 * load at the moment of a logout put the previous account's rows back, a
 * `loadMyTenants` re-persisted the previous account's tenant slug (which
 * `sessionListener` had just removed), and a `fetchProfile` marked the tab as
 * signed in again as the account that had just left.
 *
 * Every async thunk announces itself with a `pending` action carrying a unique
 * `requestId`; this middleware notes the session epoch it started in and lets
 * its `fulfilled` / `rejected` through only while that epoch is still current.
 * A settling action whose `pending` it never saw (dispatched by hand, or a thunk
 * whose `condition` skipped `pending`) is passed on unchanged.
 *
 * The thunk's own promise is unaffected — `createAsyncThunk` returns the final
 * action whether or not the store reduced it — so a caller awaiting `unwrap()`
 * still settles; only the store stays clean.
 *
 * Generic over every thunk on purpose: an allow-list of "data" thunks would
 * silently miss each slice added later, which is exactly how the reset itself
 * once covered only `auth`.
 */
export function createSessionEpochMiddleware(): Middleware {
  let epoch = 0;
  const startedIn = new Map<string, number>();

  return () => (next) => (action) => {
    const lifecycle = lifecycleOf(action);
    if (lifecycle?.status === 'pending') {
      startedIn.set(lifecycle.requestId, epoch);
    } else if (lifecycle && (lifecycle.status === 'fulfilled' || lifecycle.status === 'rejected')) {
      const started = startedIn.get(lifecycle.requestId);
      startedIn.delete(lifecycle.requestId);
      if (started !== undefined && started !== epoch) {
        return action;
      }
    }

    const result = next(action);
    // After `next`: the session-end action itself (a `logoutUser.fulfilled`
    // started in the session it ends) must still reach the reducer.
    if (isAction(action) && isSessionEnd(action)) {
      epoch += 1;
    }
    return result;
  };
}
