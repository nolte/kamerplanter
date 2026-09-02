import type { TenantRole } from '@/api/types';

/**
 * The route × backend-gate decision table (#1261).
 *
 * ## Why a table and not "we added the guard where it was needed"
 *
 * Adding a role guard to the one route that motivated the issue would reproduce
 * the defect it fixes one level up: a guard applied at the call site, on the
 * routes somebody happened to look at. That is the most expensive recurring
 * failure in this repository — #948 repaired two of four sibling routes and the
 * other two stayed open for months. So the unit of work is not "the guarded
 * routes" but **every** route, each carrying a recorded decision, with
 * `scripts/check_route_role_guards.py` refusing a route that carries none.
 *
 * ## How the decisions were derived (reproducible)
 *
 * Every `require_tenant_role` / `require_permission` / `require_admin_scope`
 * dependency on the mounted FastAPI app (216 gated operations of 789) was
 * resolved by walking `app.routes` through the `_IncludedRouter` wrappers, then
 * joined against the frontend by following each route's page through its import
 * graph to the `src/api/endpoints/*` functions it can reach, and matching those
 * on method + path. Measured on `develop` @ b23f39400, 2026-09-01.
 *
 * ## The measurement that decided the shape of the guard
 *
 * **No route in this application qualifies for a whole-route block.** Every single
 * route that carries a gated write also serves reads that are open to every
 * tenant member by design — reads are open by REQ-049 §2.3, and #1260 kept
 * `GET /identification/history` open on purpose while gating the three writes
 * beside it. Blocking or redirecting would take away read access the API grants:
 * a frontend guard that is *looser* than the API is a security bug, one that is
 * *stricter* is a usability bug. {@link RequireRole} therefore restricts rather
 * than blocks, and no blocking mode exists — an unused mode is a guard with no
 * call site.
 */
export interface RoleGuardedRoute {
  /** Minimum domain role, matching the backend gate named in `gate`. */
  min: TenantRole;
  /** The backend operation whose gate this mirrors — the authority, verbatim. */
  gate: string;
}

/**
 * Routes wrapped in `<RequireRole>` in `AppRoutes.tsx`.
 *
 * The criterion is narrow and checkable: **the page's primary action — the one in
 * its `PageTitle` header — is a write the API refuses below `min`, and the rest of
 * the page is a read of that action's results.** Those are the pages where a
 * refused member would otherwise start a flow that can only end in a 403, which is
 * exactly the report in #1261. Restricting them removes the header action (via
 * {@link useRoleRestriction}, read centrally by `PageTitle`) and leaves the reads.
 *
 * A route is *not* listed here merely because it reaches a gated endpoint — 40 do.
 * See {@link ACTION_GATED_ROUTES}.
 */
export const ROLE_GUARDED_ROUTES: Readonly<Record<string, RoleGuardedRoute>> = {
  // REQ-029 — the route #1261 was filed about. Header action opens the
  // identification wizard; the body is the identification history, which
  // `GET /identification/history` keeps open to every member (#1260).
  'pflanzen/identifikation': {
    min: 'grower',
    gate: 'POST /api/v1/t/{tenant_slug}/identification/identify — require_tenant_role(grower)',
  },
  // REQ-008 — header action starts a drying run; the body lists batches with
  // drying progress and mould alerts, all open reads.
  'ernte/nachernte': {
    min: 'grower',
    gate: 'POST /api/v1/t/{tenant_slug}/post-harvest/start-drying — require_tenant_role(grower)',
  },
  // REQ-016 — header action creates equipment; the body is the equipment list
  // and the InvenTree connection status.
  inventree: {
    min: 'grower',
    gate: 'POST /api/v1/t/{tenant_slug}/equipment — require_tenant_role(grower)',
  },
  // REQ-026 — header action creates an aquaponics system; the body is water
  // quality, cycling progress and fish stocks.
  aquaponik: {
    min: 'grower',
    gate: 'POST /api/v1/t/{tenant_slug}/aquaponics/systems — require_tenant_role(grower)',
  },
  // REQ-017 — header action records a propagation event; the body is the
  // lineage/descendants graph and the event log.
  vermehrung: {
    min: 'grower',
    gate: 'POST /api/v1/t/{tenant_slug}/propagation/events — require_tenant_role(grower)',
  },
};

/**
 * Routes that reach a gated backend operation but deliberately carry **no** route
 * guard: the page is a read surface with gated actions embedded in it (a row
 * menu, a dialog, an inline control), so restricting the route would either
 * remove read access or hang a banner over a page whose write affordances the
 * banner cannot reach — a guard that is visible and inert, which is worse than
 * none.
 *
 * These are not "done". They are the backlog of **action-level** gates, and the
 * measured gate per route is in the pull request for #1261. Moving one here to
 * {@link ROLE_GUARDED_ROUTES} is a deliberate edit that the router, the
 * parametrised test and the static check all follow automatically.
 */
export const ACTION_GATED_ROUTES: readonly string[] = [
  'settings',
  'tenants/settings',
  'ueberwinterung/profile',
  'kalender',
  'stammdaten/species',
  'stammdaten/species/:key',
  'stammdaten/companion-planting',
  'standorte/sites',
  'standorte/sites/:key',
  'standorte/locations/:key',
  'standorte/slots/:key',
  'standorte/watering-events',
  'umgebungssteuerung',
  'standorte/tanks',
  'standorte/tanks/:key',
  'pflanzen/plant-instances',
  // Also reaches the #1333-gated pest writes through `PestScanButton`; that
  // button hides itself below grower, so the gate is on the shared component,
  // not on this route.
  'pflanzen/plant-instances/:key',
  'duengung/fertilizers',
  'duengung/fertilizers/:key',
  'duengung/plans',
  'duengung/plans/:key',
  'duengung/feeding-events',
  'duengung/feeding-events/:key',
  'giessprotokoll',
  'giessprotokoll/:key',
  // #1333 — server-side gate ADDED (`POST /pests/detect` →
  // require_tenant_role(grower)), so the earlier reason "ungated server-side"
  // has expired. It stays here rather than moving to ROLE_GUARDED_ROUTES because
  // that criterion needs a read body to leave behind, and §7 omits history from
  // this page deliberately: the body *is* the gated write. `<RequireRole>`'s
  // restrict-only mode would withhold the retake button, leave the capture panel
  // standing and let a viewer reach the 403 anyway — visible and inert. The gate
  // is therefore on the capture panel itself, in PestIdentificationPage.
  'pflanzenschutz/erkennung',
  'pflanzenschutz/pests',
  'pflanzenschutz/pests/:key',
  'ernte/batches',
  'ernte/batches/:key',
  'aufgaben/queue',
  'aufgaben/tasks/:key',
  'aufgaben/workflows',
  'aufgaben/workflows/:key',
  'durchlaeufe/planting-runs',
  'durchlaeufe/planting-runs/:key',
  'durchlaeufe/succession-plans',
  'durchlaeufe/succession-plans/:key',
  'dashboard',
];

/**
 * Routes with no domain-role-gated backend operation reachable from their page,
 * measured by the join described at the top of this file. Nothing to guard.
 *
 * Three sub-cases share the bucket, all verified individually:
 * - pure redirects (`pflege`, `aufgaben/activity-plans*`) and the catch-all `*`,
 *   which have no page at all;
 * - pages that call nothing (`diagnose`, `glossar`, `kiosk`, `connect`) or only
 *   open reads (the catalogues, the substrate pages, the calculators);
 * - the **platform-admin** surfaces (`admin/*`) and the DSGVO self-service
 *   (`privacy`). Those are gated on a different axis — `require_platform_admin`
 *   and per-user ownership — which `<RequireRole>` deliberately does not model
 *   (REQ-049 §2.4 keeps the axes disjoint). A route guard for the platform-admin
 *   axis is a separate gap, recorded in the #1261 pull request, not silently
 *   folded in here.
 */
export const UNGATED_ROUTES: readonly string[] = [
  'connect',
  'auth/callback',
  'login',
  'register',
  'verify-email/:token',
  'password-reset',
  'password-reset/:token',
  'kiosk',
  'privacy',
  'admin/tenants/:key',
  'admin/users/:key',
  'tenants/create',
  'invitations/accept',
  'pflege',
  'onboarding',
  'stammdaten/botanical-families',
  'stammdaten/botanical-families/:key',
  'stammdaten/species/:speciesKey/cultivars/:cultivarKey',
  'stammdaten/crop-rotation',
  'stammdaten/activities',
  'stammdaten/activities/:key',
  'stammdaten/import',
  'standorte/substrates',
  'standorte/substrates/:key',
  'standorte/substrates/batches/:key',
  'pflanzen/calculations',
  'ki-assistent',
  'glossar',
  'diagnose',
  'duengung/calculations',
  'tagebuch',
  'pflanzenschutz/diseases',
  'pflanzenschutz/treatments',
  'pflanzenschutz/treatments/:key',
  'aufgaben/activity-plans',
  'aufgaben/activity-plans/:speciesKey',
  'phasen/definitionen',
  'phasen/definitionen/:key',
  'phasen/ablaeufe',
  'phasen/ablaeufe/:key',
  '*',
];
