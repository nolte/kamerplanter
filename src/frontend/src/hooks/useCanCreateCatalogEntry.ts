import { usePlatformAdmin } from '@/hooks/usePlatformAdmin';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';

/**
 * Whether the create affordance for a tenant-owned catalogue entry — species and
 * cultivar (the hybrid catalogue, REQ-001) — should be offered to the acting user.
 *
 * **This is a UX consequence of the backend gate, never a security control.**
 * `POST /species` and `POST /species/{key}/cultivars` are authorised server-side by
 * `_authorize_tenant_owned_create` (SEC-005 / #1113, delivered as issue #1091 A-3):
 * a tenant `viewer` is refused with 403 no matter what this hook returns. Hiding the
 * button only removes a dead affordance — one that, since the active tenant became a
 * request-borne input (#1091 A-2), an organisation viewer would otherwise see and
 * click straight into a refusal. The API remains the authority.
 *
 * The predicate is deliberately **"there IS an active tenant whose role cannot
 * edit"** and not "edit permission could not be proven". The difference is the whole
 * point, because "cannot prove" is true in three situations where creating is in
 * fact allowed:
 *
 * - **No active tenant** (`hasTenant === false`). That is not a refusal: in full mode
 *   the create answers 422 ("pick a tenant"), and in light mode (REQ-027) it takes the
 *   platform-admin arm and succeeds with 201. Hiding here would remove the *only*
 *   create path of a light-mode installation.
 * - **The recovery window.** While the stale-slug recovery (#1091 A-4) clears a
 *   persisted slug and reloads the tenant list, `activeTenant` is briefly `null`.
 *   A "cannot prove" predicate would make the button flicker away and back.
 * - **Platform admin with a viewer membership.** The server-side gate bypasses the
 *   domain rank for a platform admin, so hiding on `canEdit` alone would deny an
 *   affordance the backend answers with 201. Both sides read the same
 *   `is_platform_admin` value produced by `app.common.auth.is_platform_admin`
 *   (`/users/me`), so they cannot drift apart.
 *
 * Gating hangs on `canEdit` — lead **and** grower — never on `canDelete`/lead: the
 * lead boundary is about irreversibility (REQ-049 §2.3), not about creating.
 *
 * Returns a primitive, so no `useMemo` is owed (FRONTEND.md §6.1).
 */
export function useCanCreateCatalogEntry(): boolean {
  const { canEdit, hasTenant } = useTenantPermissions();
  const isPlatformAdmin = usePlatformAdmin();

  return !hasTenant || canEdit || isPlatformAdmin;
}
