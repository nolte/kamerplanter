/**
 * Ask before an explicit logout discards buffered writes (REQ-053 WP 9.4, G-W9 b, UI-NFR-012 R-050/R-051).
 *
 * `guard(proceed)` counts the offline write buffer's entries of the signed-in user, in all their tenants. With
 * none, `proceed` runs at once; otherwise the dialog names the count, sends the active tenant's first when there is
 * a connection and lets the user discard and log out, or cancel. A tenant switch does not ask: it keeps them. The buffer module and the dialog load on demand — the app
 * shell carries neither. If they cannot load (an outdated chunk), the logout must still work: it proceeds.
 */
import { lazy, Suspense, useCallback, useMemo, useState, type ReactNode } from 'react';
import { approveWriteQueueDiscard } from '@/pwa/offlineData';
import { useAppSelector } from '@/store/hooks';

const UnsyncedWritesDialog = lazy(() => import('@/features/gardenPlanner/offline/UnsyncedWritesDialog'));

interface Scope {
  userKey: string;
  tenantKey: string;
}

interface PendingRequest {
  userKey: string;
  scope: Scope | null;
  /** `null` = the buffer could not be counted: the dialog asks without a number. */
  count: number | null;
  proceed: () => void | Promise<void>;
}

export interface UnsyncedWritesGuard {
  guard: (proceed: () => void | Promise<void>) => Promise<void>;
  /** Render this once; it is `null` unless the dialog is open. */
  dialog: ReactNode;
}

export function useUnsyncedWritesGuard(): UnsyncedWritesGuard {
  const userKey = useAppSelector((state) => state.auth.user?.key ?? null);
  const tenantKey = useAppSelector((state) => state.tenants.activeTenant?.key ?? null);
  const [request, setRequest] = useState<PendingRequest | null>(null);

  const guard = useCallback(
    async (proceed: () => void | Promise<void>) => {
      if (userKey === null) {
        await proceed();
        return;
      }
      const scope = tenantKey === null ? null : { userKey, tenantKey };
      let count: number | null;
      try {
        const { unsyncedEntries } = await import('@/features/gardenPlanner/offline/sessionChange');
        count = await unsyncedEntries(userKey);
      } catch {
        // The buffer module could not even load: log out, but WITHOUT the discard approval — the entries stay
        // for the owner's next sign-in (R-056 c: never discard unconfirmed).
        await proceed();
        return;
      }
      if (count === 0) {
        approveWriteQueueDiscard(userKey);
        await proceed();
        return;
      }
      setRequest({ userKey, scope, count, proceed });
    },
    [userKey, tenantKey],
  );

  const dialog = useMemo(
    () =>
      request ? (
        <Suspense fallback={null}>
          <UnsyncedWritesDialog
            userKey={request.userKey}
            scope={request.scope}
            count={request.count}
            onProceed={() => {
              // The user confirmed: this logout may discard what is left.
              approveWriteQueueDiscard(request.userKey);
              setRequest(null);
              void request.proceed();
            }}
            onCancel={() => setRequest(null)}
          />
        </Suspense>
      ) : null,
    [request],
  );

  return useMemo(() => ({ guard, dialog }), [guard, dialog]);
}
