/**
 * Who is responsible for which bed (REQ-053 GP-FR-050, `location_assignments`, REQ-024/049 §3.5).
 * An assignment shows responsibility only - it is no write boundary - so the list is informational
 * and a failed request leaves every bed unassigned instead of failing the page.
 */
import { useEffect, useMemo, useState } from 'react';
import * as tenantApi from '@/api/endpoints/tenants';
import { useAppSelector } from '@/store/hooks';
import type { BedAssignee } from './types';

export interface BedAssignments {
  /** Assignees per location key; a bed without an entry has nobody assigned. */
  byLocation: ReadonlyMap<string, readonly BedAssignee[]>;
  /** The beds assigned to the signed-in user ("My beds"). */
  mine: ReadonlySet<string>;
  /** `false` until the first answer (or failure) arrived. */
  ready: boolean;
}

const NONE: BedAssignments = { byLocation: new Map(), mine: new Set(), ready: false };

export function useBedAssignments(enabled: boolean): BedAssignments {
  const slug = useAppSelector((state) => state.tenants.activeTenant?.slug ?? null);
  const userKey = useAppSelector((state) => state.auth.user?.key ?? null);
  const [loaded, setLoaded] = useState<{ slug: string; value: BedAssignments } | null>(null);

  useEffect(() => {
    if (!enabled || slug === null) return undefined;
    let cancelled = false;
    Promise.all([tenantApi.listMembers(slug), tenantApi.listAssignments(slug)])
      .then(([members, assignments]) => {
        if (cancelled) return;
        const people = new Map(members.map((member) => [member.key, member]));
        const byLocation = new Map<string, BedAssignee[]>();
        const mine = new Set<string>();
        for (const assignment of assignments) {
          const member = people.get(assignment.membership_key);
          if (!member) continue;
          byLocation.set(assignment.location_key, [
            ...(byLocation.get(assignment.location_key) ?? []),
            {
              membershipKey: member.key,
              userKey: member.user_key,
              displayName: member.display_name,
            },
          ]);
          if (member.user_key === userKey) mine.add(assignment.location_key);
        }
        setLoaded({ slug, value: { byLocation, mine, ready: true } });
      })
      .catch(() => {
        if (!cancelled) setLoaded({ slug, value: { ...NONE, ready: true } });
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, slug, userKey]);

  return useMemo(() => (loaded && loaded.slug === slug ? loaded.value : NONE), [loaded, slug]);
}
