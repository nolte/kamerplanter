import { useMemo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import {
  NOT_RESTRICTED,
  ROLE_RANK,
  RoleRestrictionContext,
  type RoleRestriction,
} from '@/auth/roleRestriction';
import type { TenantRole } from '@/api/types';

interface RequireRoleProps {
  /** Minimum domain role the route's gated action needs, per the backend gate. */
  min: TenantRole;
  children: ReactNode;
}

/**
 * Route-level domain-role guard (#1261, REQ-049 §2.3).
 *
 * Wraps a route whose **primary action is a write the API refuses below `min`**,
 * so the decision sits next to the route table and a reader sees which pages are
 * gated without opening each one. Before this existed nothing in the router
 * consulted the caller's role at all: after #1260 gated `POST /identify`, a viewer
 * could still open `/pflanzen/identifikation`, work through the whole wizard, and
 * collect a 403 on the last step.
 *
 * **Refusal restricts the page; it does not replace it.** The reason is measured,
 * not preferred — see `roleGuardedRoutes.ts`: *every* route in this application
 * that carries a gated write also serves reads that are open to every member by
 * design (the identification history, the equipment list, the drying progress).
 * A whole-route block or a redirect would take away read access the API grants,
 * which is the mirror image of the defect being fixed: a frontend guard that is
 * looser than the API is a security bug, one that is stricter is a usability bug.
 * So a refused member keeps the page and its reads, is told in plain words which
 * role the action needs, and loses only the affordance that could have ended in a
 * 403. There is deliberately no blocking mode: the inventory found no route it
 * would fit, and a mode with no call site is a guard nobody exercises.
 *
 * **This is a UX consequence of the backend gate, never a security control.** The
 * API is the authority — `require_tenant_role(GROWER)` refuses a viewer whatever
 * this component renders.
 *
 * The predicate is deliberately *"there IS an active tenant whose role ranks below
 * `min`"*, not *"sufficient role could not be proven"* — the same distinction
 * `useCanCreateCatalogEntry` draws, for the same reason: `hasTenant` is briefly
 * false during the auth bootstrap and during the stale-slug recovery (#1091 A-4),
 * and reading "cannot prove" as a refusal would flash the restriction banner at
 * every member on every reload.
 *
 * No platform-admin bypass, unlike that global-catalogue create: the gates this
 * mirrors are the tenant-scoped `require_tenant_role` / `require_permission`
 * dependencies, and neither consults `is_platform_admin`. A platform admin holding
 * a viewer membership in *this* tenant is refused by the API, so unlocking the
 * affordance here would put the frontend on the looser side of it.
 */
export default function RequireRole({ min, children }: RequireRoleProps) {
  const { t } = useTranslation();
  const { role, hasTenant } = useTenantPermissions();

  const restriction = useMemo<RoleRestriction>(() => {
    if (!hasTenant || !role) return NOT_RESTRICTED;
    return ROLE_RANK[role] < ROLE_RANK[min] ? { restricted: true, min } : NOT_RESTRICTED;
  }, [hasTenant, role, min]);

  if (!restriction.restricted) {
    return <>{children}</>;
  }

  const roleLabel = t(`enums.tenantRole.${min}`);

  return (
    <RoleRestrictionContext.Provider value={restriction}>
      {/* Matches the horizontal padding every page uses for its own content box,
          so the notice lines up with the page title instead of sitting flush
          against the layout edge (UI-NFR-001, mobile-first). */}
      <Box sx={{ px: { xs: 2, sm: 3 }, pt: { xs: 2, sm: 3 } }}>
        <Alert severity="info" data-testid="role-restriction-notice">
          <AlertTitle>{t('roleGuard.title', { role: roleLabel })}</AlertTitle>
          {t('roleGuard.description', { role: roleLabel })}
        </Alert>
      </Box>
      {children}
    </RoleRestrictionContext.Provider>
  );
}
