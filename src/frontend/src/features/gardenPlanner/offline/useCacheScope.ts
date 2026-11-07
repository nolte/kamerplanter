/**
 * The plan cache scope of the signed-in user in the active tenant (REQ-053 WP 9.2): `null` while
 * either is unknown, so nothing is cached or read outside a complete `user_key` + `tenant_key` pair.
 */
import { useMemo } from 'react';
import { useAppSelector } from '@/store/hooks';
import type { CacheScope } from './planCache';

export function useCacheScope(): CacheScope | null {
  const userKey = useAppSelector((state) => state.auth.user?.key ?? null);
  const tenantKey = useAppSelector((state) => state.tenants.activeTenant?.key ?? null);
  return useMemo(() => (userKey && tenantKey ? { userKey, tenantKey } : null), [userKey, tenantKey]);
}
