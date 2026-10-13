import { useCallback, useEffect, useMemo, useState } from 'react';
import { getTenantEntitlements } from '@/api/endpoints/tenants';
import { isApiError } from '@/api/errors';
import type { TenantEntitlements } from '@/api/types';

export type EntitlementsStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface TenantEntitlementsState {
  entitlements: TenantEntitlements | null;
  status: EntitlementsStatus;
  /** HTTP status of a failed read, `0` for a request that got no answer; `null` otherwise. */
  errorStatus: number | null;
  reload: () => void;
}

/** One answer, tagged with the request it belongs to so a stale one is never shown for another garden. */
type Answer =
  | { slug: string; token: number; entitlements: TenantEntitlements }
  | { slug: string; token: number; errorStatus: number };

/**
 * The active garden's plan and quotas (`GET /tenants/{slug}/entitlements`, REQ-056 §7.7).
 *
 * Every member may read it; the backend leaves out the lead-only dimensions for everybody else and
 * counts `ai_calls_per_user_day` for the caller only, so the hook passes the answer through untouched.
 * A failed read is a state of its own: "no quotas" and "we could not tell" must not look alike.
 */
export function useTenantEntitlements(slug: string | null | undefined): TenantEntitlementsState {
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [token, setToken] = useState(0);

  useEffect(() => {
    if (!slug) return undefined;
    let cancelled = false;
    getTenantEntitlements(slug)
      .then((entitlements) => {
        if (!cancelled) setAnswer({ slug, token, entitlements });
      })
      .catch((err: unknown) => {
        if (!cancelled) setAnswer({ slug, token, errorStatus: isApiError(err) ? err.statusCode : 0 });
      });
    return () => {
      cancelled = true;
    };
  }, [slug, token]);

  const reload = useCallback(() => setToken((n) => n + 1), []);

  return useMemo(() => {
    if (!slug) return { entitlements: null, status: 'idle', errorStatus: null, reload };
    if (answer === null || answer.slug !== slug || answer.token !== token) {
      return { entitlements: null, status: 'loading', errorStatus: null, reload };
    }
    if ('errorStatus' in answer) {
      return { entitlements: null, status: 'error', errorStatus: answer.errorStatus, reload };
    }
    return { entitlements: answer.entitlements, status: 'ready', errorStatus: null, reload };
  }, [slug, answer, token, reload]);
}
