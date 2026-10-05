import { useCallback, useContext, useSyncExternalStore } from 'react';
import { ReactReduxContext } from 'react-redux';
import type { RootState } from '@/store/store';

const noop = () => undefined;

/**
 * The signed-in account's key, or `undefined` — also outside a Redux `Provider`.
 *
 * For hooks that only *consult* the account (the favorites carry-over, #2117)
 * and are otherwise store-free: `useAppSelector` would make every one of their
 * consumers need a `Provider`, this reads the store when there is one and
 * re-renders when the key changes.
 */
export function useSignedInUserKey(): string | undefined {
  const store = useContext(ReactReduxContext)?.store;
  const subscribe = useCallback(
    (onChange: () => void) => (store ? store.subscribe(onChange) : noop),
    [store],
  );
  const read = useCallback(
    () => (store?.getState() as RootState | undefined)?.auth?.user?.key ?? undefined,
    [store],
  );
  return useSyncExternalStore(subscribe, read, read);
}
