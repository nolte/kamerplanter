import { usePlatformAdmin } from '@/hooks/usePlatformAdmin';

/**
 * Whether the acting user may edit an **installation-wide** catalogue (#1402 C).
 *
 * Seven routers serve catalogues that belong to the installation rather than to a
 * tenant — growth phases, location types, requirement/nutrient profiles, lifecycle
 * configs, activities, crop-rotation successors, enrichment. Their writes changed
 * what every tenant sees while resolving the caller through `get_current_user`
 * alone, so any authenticated member could rewrite them; they now carry
 * `require_platform_admin`.
 *
 * **This is a UX consequence of that gate, never a security control.** The API
 * refuses a non-admin with 403 whatever this hook returns. Hiding the affordance
 * only removes a control that answers a refusal — the state #1261 describes.
 *
 * Distinct from {@link useCanCreateCatalogEntry}, which gates the **tenant-owned**
 * half of the hybrid catalogue (species, cultivars) and therefore admits a grower.
 * These catalogues admit nobody below platform admin, so the two predicates are not
 * interchangeable and a site that swaps one for the other widens or narrows a real
 * gate.
 *
 * **Light mode is already handled** and must not be special-cased here. The backend
 * gate delegates to `app.common.auth.is_platform_admin`, which returns `True`
 * unconditionally when `KAMERPLANTER_MODE=light`, and `/users/me` reports
 * `is_platform_admin` by calling that same function. Client and server therefore
 * read one value from one implementation and cannot drift; adding a mode check here
 * would introduce the second source of truth that absence currently prevents.
 *
 * Returns a primitive, so no `useMemo` is owed (FRONTEND.md §6.1).
 */
export function useCanEditInstallationCatalogue(): boolean {
  return usePlatformAdmin();
}
