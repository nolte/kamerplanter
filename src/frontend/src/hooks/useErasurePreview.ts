import { useEffect, useMemo, useState } from 'react';
import { getAdminUserErasurePreview } from '@/api/endpoints/adminPlatform';
import { getErasurePreview } from '@/api/endpoints/privacy';
import type { ErasurePreviewTenant } from '@/api/types';

export type ErasurePreviewStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface ErasurePreviewState {
  /** The caller's personal tenants an account erasure takes with it, with a count of the others. */
  tenants: readonly ErasurePreviewTenant[];
  status: ErasurePreviewStatus;
}

/**
 * Which personal tenants confirming the account erasure would delete (REQ-025
 * AK-FK-06, #1824). Loaded when `enabled` turns on, so a page that only holds
 * the delete button does not ask until the person is about to confirm.
 *
 * With `targetUserKey` a platform admin reads the preview of *that* account
 * (`GET /admin/platform/users/{key}/erasure-preview`, #1961) instead of their own.
 *
 * A failed read is a state of its own, not an empty list: "nothing is affected"
 * and "we could not tell" must not look alike before an irreversible action.
 */
export function useErasurePreview(enabled: boolean, targetUserKey?: string): ErasurePreviewState {
  // `null` — not answered yet; `'error'` — the read failed. Deriving the status
  // from it keeps a state write out of the effect body.
  const [result, setResult] = useState<readonly ErasurePreviewTenant[] | 'error' | null>(null);

  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;
    const read = targetUserKey === undefined ? getErasurePreview() : getAdminUserErasurePreview(targetUserKey);
    read
      .then((preview) => {
        if (!cancelled) setResult(preview.personal_tenants);
      })
      .catch(() => {
        if (!cancelled) setResult('error');
      });
    return () => {
      cancelled = true;
      // Forget the answer when the surface closes: a reopened dialog must not
      // show last time's member count while the new one loads.
      setResult(null);
    };
  }, [enabled, targetUserKey]);

  return useMemo(() => {
    if (result === 'error') return { tenants: [], status: 'error' };
    if (result !== null) return { tenants: result, status: 'ready' };
    return { tenants: [], status: enabled ? 'loading' : 'idle' };
  }, [result, enabled]);
}
