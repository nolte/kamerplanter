import { useCallback, useEffect, useMemo, useState } from 'react';
import { listPlans } from '@/api/endpoints/adminPlans';
import { isApiError } from '@/api/errors';
import type { Plan } from '@/api/types';

export type PlanCatalogueStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface PlanCatalogueState {
  plans: readonly Plan[];
  status: PlanCatalogueStatus;
  /** HTTP status of a failed read, `0` for a request that got no answer; `null` otherwise. */
  errorStatus: number | null;
  /** Read the catalogue again. The last list stays visible while it loads (no skeleton flash). */
  reload: () => void;
}

type Answer = { token: number; plans: readonly Plan[] } | { token: number; errorStatus: number };

const NO_PLANS: readonly Plan[] = [];

/**
 * The installation's plan catalogue (`GET /admin/platform/plans`, REQ-056 §7.6) for a platform admin.
 *
 * `enabled = false` reads nothing — the tenant page only needs the options once it knows the tenant
 * can take a plan at all. After the first answer a reload keeps the previous list on screen and only
 * swaps it when the new one arrives, so saving a plan does not blank the table.
 */
export function usePlanCatalogue(enabled = true): PlanCatalogueState {
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [token, setToken] = useState(0);

  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;
    listPlans()
      .then((plans) => {
        if (!cancelled) setAnswer({ token, plans });
      })
      .catch((err: unknown) => {
        if (!cancelled) setAnswer({ token, errorStatus: isApiError(err) ? err.statusCode : 0 });
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, token]);

  const reload = useCallback(() => setToken((n) => n + 1), []);

  return useMemo(() => {
    if (!enabled) return { plans: NO_PLANS, status: 'idle', errorStatus: null, reload };
    if (answer === null) return { plans: NO_PLANS, status: 'loading', errorStatus: null, reload };
    if ('errorStatus' in answer) {
      // A failed *reload* keeps nothing stale on screen either: the caller shows the error.
      return { plans: NO_PLANS, status: 'error', errorStatus: answer.errorStatus, reload };
    }
    return { plans: answer.plans, status: 'ready', errorStatus: null, reload };
  }, [enabled, answer, reload]);
}
