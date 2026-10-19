/**
 * The people the history can be filtered by (REQ-053 GP-API-034, E-16, SR-020): a viewer or grower
 * may filter only by themselves, so only they are on offer; a lead or a member with the
 * `management` scope sees every member. The first entry is always the signed-in user. The member
 * list is informational: a failed request leaves the user's own entry.
 */
import { useEffect, useMemo, useState } from 'react';
import * as tenantApi from '@/api/endpoints/tenants';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { useAppSelector } from '@/store/hooks';
import type { FilterOption } from './historyTypes';

export function usePersonOptions(): FilterOption[] {
  const slug = useAppSelector((state) => state.tenants.activeTenant?.slug ?? null);
  const user = useAppSelector((state) => state.auth.user);
  const { role, adminScopes } = useTenantPermissions();
  const mayNameOthers = role === 'lead' || adminScopes.includes('management');
  const [members, setMembers] = useState<FilterOption[]>([]);

  useEffect(() => {
    if (!mayNameOthers || slug === null) return undefined;
    let cancelled = false;
    tenantApi
      .listMembers(slug)
      .then((list) => {
        if (!cancelled) setMembers(list.map((member) => ({ key: member.user_key, label: member.display_name })));
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [mayNameOthers, slug]);

  return useMemo(() => {
    if (!user) return [];
    const me: FilterOption = { key: user.key, label: user.display_name };
    return [me, ...members.filter((member) => member.key !== user.key)];
  }, [user, members]);
}
