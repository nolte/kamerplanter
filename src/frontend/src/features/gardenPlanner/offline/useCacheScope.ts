/**
 * The plan cache scope of the signed-in user in the active tenant (REQ-053 WP 9.2): `null` while
 * either is unknown, so nothing is cached or read outside a complete `user_key` + `tenant_key` pair.
 * One rule for thunks and components: {@link scopeFromState}; `shallowEqual` keeps the object stable.
 */
import { shallowEqual } from 'react-redux';
import { useAppSelector } from '@/store/hooks';
import { scopeFromState, type CacheScope } from './planCache';

export function useCacheScope(): CacheScope | null {
  return useAppSelector(scopeFromState, shallowEqual);
}
