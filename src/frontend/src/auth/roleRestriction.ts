import { createContext, useContext } from 'react';
import type { TenantRole } from '@/api/types';

/** REQ-049 §2.3 domain-role rank. Mirrors `role_order` in `app/common/auth.py`. */
export const ROLE_RANK: Record<TenantRole, number> = { viewer: 0, grower: 1, lead: 2 };

export interface RoleRestriction {
  /** True when the acting member's role is below the route's declared minimum. */
  restricted: boolean;
  /** The minimum the route declared — `null` outside a guarded route. */
  min: TenantRole | null;
}

export const NOT_RESTRICTED: RoleRestriction = { restricted: false, min: null };

/**
 * Published by `<RequireRole>` for the subtree of a route whose declared minimum
 * domain role the acting member does not reach (#1261).
 *
 * Lives in its own module rather than beside the component so the shared page
 * chrome can read it without importing the guard (and so the guard file stays a
 * component-only module for react-refresh).
 */
export const RoleRestrictionContext = createContext<RoleRestriction>(NOT_RESTRICTED);

/**
 * Whether the current route refused the acting member's domain role.
 *
 * Read by {@link PageTitle} so a restricted route drops its primary action
 * without every page having to remember to ask — the placement matters, because
 * "each page checks for itself" is opt-in at the call site, the drift class this
 * guard exists to avoid. A page needs this hook directly only when it owns a
 * second write affordance outside the page header.
 *
 * Returns a stable object (the provider memoises it), so no `useMemo` is owed at
 * the call site (FRONTEND.md §6.1).
 */
export function useRoleRestriction(): RoleRestriction {
  return useContext(RoleRestrictionContext);
}
