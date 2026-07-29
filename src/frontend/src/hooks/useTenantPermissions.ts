import { useMemo } from 'react';
import { useAppSelector } from '@/store/hooks';
import type { AdminScope, TenantRole } from '@/api/types';

/**
 * What the acting user may do in the active tenant, on both REQ-049 axes.
 *
 * The axes do not imply each other in either direction — that separation is the
 * whole point of the model, so the flags are derived independently:
 *
 * - `canEdit` / `canDelete` come from the ranked **domain role**. Deleting is
 *   lead-only, because the grower/lead boundary runs along irreversibility.
 * - `canManageMembers` / `canConfigureIntegrations` come from the additive
 *   **administrative scopes**. A viewer may keep the member list; a lead
 *   without the scope may not.
 */
interface TenantPermissions {
  role: TenantRole | null;
  adminScopes: AdminScope[];
  /** Create and change domain data (grower and above). */
  canEdit: boolean;
  /** Destroy domain records — lead only. */
  canDelete: boolean;
  /** Members, invitations, tenant settings — the `management` scope. */
  canManageMembers: boolean;
  /** The same scope: issuing an invitation is member management. */
  canInvite: boolean;
  /** Integrations, sensors, import, enrichment — the `technical` scope. */
  canConfigureIntegrations: boolean;
  hasTenant: boolean;
}

const NO_PERMISSIONS: TenantPermissions = {
  role: null,
  adminScopes: [],
  canEdit: false,
  canDelete: false,
  canManageMembers: false,
  canInvite: false,
  canConfigureIntegrations: false,
  hasTenant: false,
};

export function useTenantPermissions(): TenantPermissions {
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);

  return useMemo(() => {
    if (!activeTenant) return NO_PERMISSIONS;

    const role = activeTenant.role;
    // A tenant record cached before REQ-049 carries no scopes at all; read that
    // as "no administrative rights" rather than crashing on undefined.
    const adminScopes = activeTenant.admin_scopes ?? [];
    const hasManagement = adminScopes.includes('management');

    return {
      role,
      adminScopes,
      canEdit: role === 'lead' || role === 'grower',
      canDelete: role === 'lead',
      canManageMembers: hasManagement,
      canInvite: hasManagement,
      canConfigureIntegrations: adminScopes.includes('technical'),
      hasTenant: true,
    };
  }, [activeTenant]);
}
