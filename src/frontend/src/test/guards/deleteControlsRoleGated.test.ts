import { describe, expect, it } from 'vitest';

/**
 * #1467 — every tenant-scoped delete control must carry the role predicate the
 * backend enforces.
 *
 * `require_permission(<resource>, Action.DELETE)` resolves through
 * `MembershipEngine.can_delete_resource`, which grants **lead only** (REQ-024
 * §1a.1, REQ-049 §2.3 irreversibility boundary). `useTenantPermissions` has
 * encoded that since it exists (`canDelete: role === 'lead'`), but before #1425
 * no production control read it: ~33 pages offered a destructive control to any
 * grower, which could only ever answer 403.
 *
 * The naive predicate finds nothing, because the gating expression and the
 * control are never on the same line. The predicate that works is per file and
 * has two operands: *does this file reach a lead-only delete endpoint* ×
 * *does it mention a `canDelete`-shaped role predicate*.
 *
 * Writings of "reaches a delete endpoint" this guard covers:
 *
 *  1. named import — `import { deleteSite } from '@/api/endpoints/sites'`
 *  2. **renamed** import — `import { deleteSite as dropSite }`; the import
 *     clause is what is read, not the call site, so the alias cannot hide it
 *  3. namespace import — `import * as api from '@/api/endpoints/sites'` plus
 *     any `api.deleteSite` member access
 *  4. indirection through a Redux thunk — a `store/slices/*.ts` thunk whose body
 *     calls a lead-only endpoint is itself treated as a lead-only reference, so
 *     the *component that dispatches it* is checked too (see {@link leadOnlyThunks})
 *  5. bypassing the endpoint layer entirely — a raw `apiClient.delete(` outside
 *     `src/api/` is rejected on sight, because no classification exists for it
 *
 * Known limit, deliberately not covered: a fully dynamic call
 * (`endpoints[name](key)` with `name` computed at runtime). Nothing in the tree
 * writes one, and detecting it needs type-level flow analysis rather than the
 * import-graph read done here. Rule 5 keeps the cheap escape hatch closed.
 */

/**
 * Sources are read through Vite's `import.meta.glob` rather than `node:fs`: the
 * app tsconfig carries no Node types, and the glob keeps the guard inside the
 * same module graph the app is built from.
 */
const ENDPOINT_SOURCES = import.meta.glob('/src/api/endpoints/*.ts', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const SLICE_SOURCES = import.meta.glob('/src/store/slices/*.ts', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const UI_SOURCES = import.meta.glob(
  [
    '/src/pages/**/*.ts',
    '/src/pages/**/*.tsx',
    '/src/components/**/*.ts',
    '/src/components/**/*.tsx',
    '/src/hooks/**/*.ts',
    '/src/hooks/**/*.tsx',
  ],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;

/** `/src/pages/x/Y.tsx` → `pages/x/Y.tsx`, the form the allowlist is keyed on. */
function rel(path: string): string {
  return path.replace(/^\/src\//, '');
}

function moduleStem(path: string): string {
  return (path.split('/').pop() as string).replace(/\.ts$/, '');
}

/** Anything named like a destructive operation, whatever the HTTP verb behind it. */
const DESTRUCTIVE_NAME = /(delete|remove|detach|discard)/i;

/**
 * Endpoint functions whose backend route is gated on the lead-only DELETE grant.
 *
 * Measured, per route, from the router decorators and signatures under
 * `src/backend/app/api/v1/**` — not assumed from the function name.
 */
const LEAD_ONLY: Record<string, string> = {
  // activity_plans/tenant_router.py — require_permission(TASK, DELETE)
  deleteTaskTemplate: 'tasks + activity-plans templates: require_permission(TASK, DELETE)',
  // calendar/tenant_router.py — require_permission(CALENDAR_FEED, DELETE)
  deleteCalendarFeed: 'require_permission(CALENDAR_FEED, DELETE)',
  // plant_instances/diary_router.py — require_permission("diary-entry", DELETE)
  deletePlantDiaryEntry: 'require_permission("diary-entry", DELETE)',
  // feeding_events/tenant_router.py
  deleteFeedingEvent: 'require_permission("feeding-event", DELETE)',
  // fertilizers/tenant_router.py
  deleteFertilizer: 'require_permission(FERTILIZER, DELETE)',
  deleteFertilizerStock: 'require_permission(FERTILIZER, DELETE)',
  // equipment/tenant_router.py — require_tenant_role(LEAD)
  deleteEquipment: 'require_tenant_role(TenantRole.LEAD)',
  // ipm/tenant_router.py — require_attachment_permission(DELETE); ATTACHMENT/DELETE is lead-only
  deletePestImage: 'require_attachment_permission(DELETE) → ATTACHMENT/DELETE = lead',
  // nutrient_plans/tenant_router.py
  deleteNutrientPlan: 'require_permission(NUTRIENT_PLAN, DELETE)',
  deletePhaseEntry: 'require_permission(NUTRIENT_PLAN, DELETE)',
  // overwintering_profiles/tenant_router.py
  deleteOverwinteringProfile: 'require_permission(OVERWINTERING_PROFILE, DELETE)',
  // phases/router.py — require_active_tenant_role(LEAD)
  deletePhaseHistory: 'require_active_tenant_role(TenantRole.LEAD)',
  // plant_instances/photo_router.py — require_attachment_permission(DELETE)
  deletePlantPhoto: 'require_attachment_permission(DELETE) → ATTACHMENT/DELETE = lead',
  // planting_runs/tenant_router.py
  deletePlantingRun: 'require_permission(PLANTING_RUN, DELETE)',
  deleteEntry: 'planting-run entry: require_permission(PLANTING_RUN, DELETE) — no frontend consumer today',
  // post_harvest/tenant_router.py — require_tenant_role(LEAD)
  deleteBatch: 'post-harvest batch: require_tenant_role(LEAD); substrate batch: SubstrateService lead/platform-admin',
  // sites / locations / slots
  deleteSite: 'require_permission(SITE, DELETE)',
  deleteLocation: 'require_permission(LOCATION, DELETE)',
  deleteSlot: 'require_permission(LOCATION, DELETE)',
  deleteSiteSensor: 'require_permission(SENSOR, DELETE)',
  deleteLocationSensor: 'require_permission(SENSOR, DELETE)',
  // species / cultivars / substrates — service-level three-way gate: own row → lead,
  // global seed row → platform admin, foreign → 404 (#808, #1090).
  deleteSpecies: 'SpeciesService.delete_species — lead (own) / platform admin (global)',
  deleteCultivar: 'SpeciesService.delete_cultivar — lead (own) / platform admin (global)',
  deleteSubstrate: 'SubstrateService.delete_substrate — lead (own) / platform admin (global)',
  // succession_plans / tanks
  deleteSuccessionPlan: 'require_permission(SUCCESSION_PLAN, DELETE)',
  deleteTank: 'require_permission(TANK, DELETE)',
  deleteSchedule: 'require_permission(TANK, DELETE)',
  deleteSensor: 'require_permission(SENSOR, DELETE)',
  // tasks/tenant_router.py
  deleteWorkflow: 'require_permission(TASK, DELETE)',
  deleteWorkflowPhase: 'require_permission(TASK, DELETE)',
  deleteTask: 'require_permission(TASK, DELETE)',
  deleteTaskComment: 'require_permission(TASK, DELETE)',
  batchDelete: 'POST /tasks/batch/delete — require_permission(TASK, DELETE)',
  // imports/router.py — ImportService.delete_job: own tenant (foreign → 404) then the
  // lead-only can_delete_resource predicate (#1501). An import job is tenant-owned
  // staged work, so it takes the tenant axis, not the platform-admin one its three
  // #1501 siblings take.
  deleteImportJob: 'ImportService.delete_job — own tenant (foreign → 404), then lead (can_delete_resource)',
  // watering_logs/tenant_router.py
  deleteWateringLog: 'require_permission("watering-log", DELETE)',
  // actuators/tenant_router.py — require_tenant_role(LEAD) on schedules/rules;
  // the bare actuator delete is TECHNICAL scope, listed under NOT_LEAD_ONLY.
  deleteActuatorSchedule: 'require_tenant_role(TenantRole.LEAD)',
  deleteControlRule: 'require_tenant_role(TenantRole.LEAD)',
  deletePhaseControlProfile: 'require_tenant_role(TenantRole.LEAD)',
  deleteSystem: 'aquaponik system: require_tenant_role(TenantRole.LEAD)',
  deleteFishStock: 'aquaponik fish stock: require_tenant_role(TenantRole.LEAD)',
  deleteProtocol: 'propagation protocol: require_tenant_role(TenantRole.LEAD)',
  deletePhenotypeNote: 'propagation phenotype note: require_tenant_role(TenantRole.LEAD)',
  deleteReference: 'inventree reference: require_tenant_role(TenantRole.LEAD)',
};

/**
 * Destructive endpoint functions whose backend route is *not* the lead-only
 * grant — each with the measured reason. Binding these to `canDelete` would take
 * away a call the backend accepts, which is the mirror defect of #1467.
 */
const NOT_LEAD_ONLY: Record<string, string> = {
  deleteAdminTenant: 'admin/platform/router.py — require_platform_admin; page sits behind the platform-admin route guard',
  deleteAdminUser: 'admin/platform/router.py — require_platform_admin',
  removeTenantMember: 'admin/platform/router.py — require_platform_admin',
  removeUserFromTenant: 'admin/platform/router.py — require_platform_admin',
  deleteOidcProvider: 'admin/oidc_providers/router.py — require_platform_admin',
  deleteHomeAssistantSettings: 'admin/settings/router.py — require_platform_admin',
  deletePlantIdentificationSettings: 'admin/settings/router.py — require_platform_admin',
  deleteStorageSettings: 'admin/settings/router.py — require_platform_admin',
  deleteAccount: 'users/router.py DELETE /me — get_current_user, self-service (DSGVO Art. 17)',
  deleteSession: 'users/router.py — get_current_user, own session',
  deleteProvider: 'users/router.py — get_current_user, own federated identity',
  deleteRestriction: 'privacy/router.py — get_current_user, own restriction',
  deleteConsent: 'privacy/router.py — get_current_user, own consent',
  removeFavorite: 'favorites/tenant_router.py — get_current_tenant only; a favourite is personal to the member',
  deleteConversation: 'ki_assistent/tenant_router.py — get_current_tenant only',
  deleteTaskPhoto: 'tasks/photo_router.py — require_attachment_permission(CREATE); the service splits per state (#1393): a referenced completion photo is lead-only, a staged upload may be withdrawn by its creator',
  removeFertilizerFromChannel: 'nutrient_plans — PUT entry, require_permission(NUTRIENT_PLAN, UPDATE)',
  removePlantPlan: 'plant_instances — require_permission(PLANT, UPDATE)',
  removePlantInstance: 'plant_instances POST /{key}/remove — require_permission(PLANT, UPDATE)',
  removeRunNutrientPlan: 'planting_runs — require_permission(PLANTING_RUN, UPDATE)',
  batchRemove: 'planting_runs POST /{key}/batch-remove — require_permission(PLANTING_RUN, UPDATE)',
  detachPlant: 'planting_runs POST /{key}/plants/{key}/detach — require_permission(PLANTING_RUN, UPDATE)',
  deleteConnection: 'inventree/tenant_router.py — require_admin_scope(TECHNICAL), not the domain rank',
  deleteActuator: 'actuators/tenant_router.py — require_admin_scope(TECHNICAL), not the domain rank',
  deleteTenant: 'tenants/router.py — require_admin_scope(MANAGEMENT), the orthogonal axis',
  removeMember: 'tenants/router.py — require_admin_scope(MANAGEMENT)',
  deleteAssignment: 'tenants/router.py — require_admin_scope(MANAGEMENT)',
  deleteApiKey: 'auth — own service-account key',
  removeReferenceImage: 'admin reference images — platform admin surface',
  deleteReferenceImage: 'admin reference images — platform admin surface',
  deleteWeatherProvider: 'admin weather providers — platform admin surface',
  deleteStarterKit: 'starter kits — platform admin surface',
};

/**
 * Destructive endpoint functions whose backend route is gated on
 * **platform admin** — #1501.
 *
 * A third class, because two were not enough. The rank axis (`canDelete`) and
 * "no rank at all" do not describe an installation-wide catalogue: a row every
 * tenant reads admits nobody below platform admin, so a *lead* is refused there
 * exactly as a viewer is. Before #1501 these entries sat in
 * {@link NOT_LEAD_ONLY} — literally true (the grant is not the lead one) and
 * useless, because that list asks for no binding at all, so the four that were
 * already gated and the six that were not looked identical.
 *
 * The predicate is `usePlatformAdmin` / `useCanEditInstallationCatalogue` (the
 * latter is the former, named for this use). As on the rank axis, this is a **UX
 * consequence of the gate and never a security control** — the API answers 403
 * whatever the hook returns.
 */
const PLATFORM_ADMIN_ONLY: Record<string, string> = {
  // Already gated when this class was introduced — they are what made the missing
  // six visible by contrast.
  deleteActivity: 'activities/router.py — require_platform_admin (installation catalogue)',
  deleteBotanicalFamily: 'botanical_families/router.py — require_platform_admin_for_global_catalogue',
  deleteGrowthPhase: 'growth_phases/router.py — require_platform_admin',
  deleteLocationType: 'location_types/router.py — require_platform_admin (no frontend consumer today)',
  // Closed by #1501. Measured: neither PhaseDefinition/PhaseSequence/PhaseSequenceEntry
  // nor Pest/Disease/Treatment carries a tenant_key, so there is no ownership arm —
  // these are the global-only shape, gated on the router AND in the service.
  deletePhaseDefinition: 'phase_sequences/router.py — require_platform_admin + PhaseSequenceService (#1501)',
  deletePhaseSequence: 'phase_sequences/router.py — require_platform_admin + PhaseSequenceService (#1501)',
  deleteSequenceEntry: 'phase_sequences/router.py — require_platform_admin + PhaseSequenceService (#1501)',
  deletePest: 'ipm/router.py — require_platform_admin + IpmService (#1501); no frontend consumer today',
  deleteDisease: 'ipm/router.py — require_platform_admin + IpmService (#1501); no frontend consumer today',
  deleteTreatment: 'ipm/router.py — require_platform_admin + IpmService (#1501); no frontend consumer today',
  deleteGlossaryTerm: 'glossar/admin_router.py — router-level require_platform_admin; no frontend consumer today',
};

/** Role predicates that count as "the file reads the platform-admin grant". */
const PLATFORM_ADMIN_PREDICATE = /usePlatformAdmin|useCanEditInstallationCatalogue/;

/**
 * Files reaching a platform-admin-only endpoint that must not carry the predicate.
 * Keyed the same way as {@link ALLOWLIST} and checked for obsolescence the same way.
 */
const PLATFORM_ADMIN_ALLOWLIST: Record<string, string> = {};

/** Files that reach a lead-only endpoint but must not carry `canDelete`, with the reason. */
const ALLOWLIST: Record<string, string> = {
  'store/slices/calendarSlice.ts':
    'data layer, renders nothing; the control lives in CalendarPage, which is gated. Thunk indirection is covered by the leadOnlyThunks rule below.',
  'store/slices/tasksSlice.ts':
    'data layer, renders nothing; WorkflowTemplateListPage / WorkflowDetailPage carry the predicate.',
  'store/slices/importSlice.ts':
    'data layer, renders nothing. Measured #1501: the deleteImportJob thunk has NO UI consumer at all — ImportPage never dispatches it — so there is no control to bind. Delete the thunk or bind its future caller.',
};

/** Role predicates that count as "the file reads the delete grant". */
const ROLE_PREDICATE = /canDelete/;

/** Every exported name of every endpoint module, per module stem. */
function endpointExports(): Map<string, Set<string>> {
  const byModule = new Map<string, Set<string>>();
  for (const [path, src] of Object.entries(ENDPOINT_SOURCES)) {
    const names = new Set<string>();
    for (const m of src.matchAll(/export\s+(?:async\s+)?(?:const|function)\s+([A-Za-z0-9_]+)/g)) {
      names.add(m[1]);
    }
    byModule.set(moduleStem(path), names);
  }
  return byModule;
}

const ENDPOINT_EXPORTS = endpointExports();

const ALL_DESTRUCTIVE = new Set<string>(
  [...ENDPOINT_EXPORTS.values()].flatMap((names) =>
    [...names].filter((n) => DESTRUCTIVE_NAME.test(n)),
  ),
);

/**
 * Names that count as "reaches a lead-only delete", including the Redux thunks
 * that wrap one — writing 4 in the list at the top of this file.
 */
function leadOnlyThunks(): Map<string, string> {
  const thunks = new Map<string, string>();
  for (const [path, src] of Object.entries(SLICE_SOURCES)) {
    const name = moduleStem(path);
    // `export const <thunkName> = createAsyncThunk(` … up to the next top-level
    // declaration. Cutting at the next `export ` matters: a fixed-size window
    // spilled into the following thunk and reported `fetchWorkflows` as a
    // lead-only reference, which would have made the rule pass for the wrong reason.
    for (const m of src.matchAll(/export const ([A-Za-z0-9_]+) = createAsyncThunk\(/g)) {
      const start = m.index ?? 0;
      const rest = src.slice(start + 1);
      const end = rest.search(/\nexport /);
      const body = end === -1 ? rest : rest.slice(0, end);
      for (const endpoint of Object.keys(LEAD_ONLY)) {
        if (new RegExp(`\\b${endpoint}\\s*\\(`).test(body)) {
          thunks.set(m[1], `${name} → ${endpoint}`);
        }
      }
    }
  }
  return thunks;
}

const LEAD_ONLY_THUNKS = leadOnlyThunks();

/** Every production source the rules below read, keyed `pages/x/Y.tsx`. */
const ALL_SOURCES: Map<string, string> = new Map(
  Object.entries({ ...UI_SOURCES, ...SLICE_SOURCES })
    .filter(([path]) => !/\.(test|spec)\.tsx?$/.test(path))
    .map(([path, src]) => [rel(path), src]),
);

/**
 * Which lead-only references a file reaches, read from its **import clauses**
 * (so a rename cannot hide one) plus namespace member access.
 */
function leadOnlyReferences(src: string): string[] {
  const hits = new Set<string>();

  // Named imports from an endpoint module or a store slice.
  for (const m of src.matchAll(
    /import\s*\{([^}]*)\}\s*from\s*'@\/(?:api\/endpoints|store\/slices)\/([^']+)'/g,
  )) {
    for (const spec of m[1].split(',')) {
      const original = spec.trim().split(/\s+as\s+/)[0].trim();
      if (!original) continue;
      if (original in LEAD_ONLY) hits.add(original);
      if (LEAD_ONLY_THUNKS.has(original)) hits.add(original);
    }
  }

  // Namespace imports: `import * as alias from '@/api/endpoints/<module>'`.
  for (const m of src.matchAll(
    /import\s*\*\s*as\s+([A-Za-z0-9_]+)\s+from\s*'@\/api\/endpoints\/([^']+)'/g,
  )) {
    const [, alias, moduleSpec] = m;
    const stem = moduleSpec.split('/').pop() as string;
    const exported = ENDPOINT_EXPORTS.get(stem) ?? new Set<string>();
    for (const use of src.matchAll(new RegExp(`\\b${alias}\\.([A-Za-z0-9_]+)`, 'g'))) {
      const name = use[1];
      if (exported.has(name) && name in LEAD_ONLY) hits.add(name);
    }
  }

  return [...hits].sort();
}


/** The {@link leadOnlyReferences} sibling for the platform-admin class. */
function platformAdminReferences(src: string): string[] {
  const hits = new Set<string>();

  for (const m of src.matchAll(
    /import\s*\{([^}]*)\}\s*from\s*'@\/(?:api\/endpoints|store\/slices)\/([^']+)'/g,
  )) {
    for (const spec of m[1].split(',')) {
      const original = spec.trim().split(/\s+as\s+/)[0].trim();
      if (original && original in PLATFORM_ADMIN_ONLY) hits.add(original);
    }
  }

  for (const m of src.matchAll(
    /import\s*\*\s*as\s+([A-Za-z0-9_]+)\s+from\s*'@\/api\/endpoints\/([^']+)'/g,
  )) {
    const [, alias, moduleSpec] = m;
    const stem = moduleSpec.split('/').pop() as string;
    const exported = ENDPOINT_EXPORTS.get(stem) ?? new Set<string>();
    for (const use of src.matchAll(new RegExp(`\\b${alias}\\.([A-Za-z0-9_]+)`, 'g'))) {
      const name = use[1];
      if (exported.has(name) && name in PLATFORM_ADMIN_ONLY) hits.add(name);
    }
  }

  return [...hits].sort();
}

describe('#1467 — tenant delete controls are bound to the lead-only grant', () => {
  it('classifies every destructive endpoint export as lead-only or not', () => {
    const classified = new Set([
      ...Object.keys(LEAD_ONLY),
      ...Object.keys(PLATFORM_ADMIN_ONLY),
      ...Object.keys(NOT_LEAD_ONLY),
    ]);
    const unclassified = [...ALL_DESTRUCTIVE].filter((n) => !classified.has(n)).sort();
    expect(
      unclassified,
      'A new destructive endpoint was added without deciding which role predicate its ' +
        'control needs. Measure the backend route ' +
        '(grep require_permission/require_tenant_role/require_admin_scope in the router) ' +
        'and add it to LEAD_ONLY, PLATFORM_ADMIN_ONLY or NOT_LEAD_ONLY with the measured reason.',
    ).toEqual([]);
  });

  it('never classifies the same endpoint in two of the three lists', () => {
    const lists: Record<string, Record<string, string>> = {
      LEAD_ONLY,
      PLATFORM_ADMIN_ONLY,
      NOT_LEAD_ONLY,
    };
    const overlaps: string[] = [];
    const names = Object.keys(lists);
    for (let i = 0; i < names.length; i += 1) {
      for (let j = i + 1; j < names.length; j += 1) {
        for (const n of Object.keys(lists[names[i]])) {
          if (n in lists[names[j]]) overlaps.push(`${n}: ${names[i]} + ${names[j]}`);
        }
      }
    }
    expect(overlaps).toEqual([]);
  });

  it('every platform-admin entry carries a measured reason', () => {
    for (const [name, reason] of Object.entries(PLATFORM_ADMIN_ONLY)) {
      expect(reason.length, `${name}: no usable reason`).toBeGreaterThan(20);
    }
  });

  it('every UI file reaching a platform-admin-only write reads the platform-admin predicate', () => {
    const offenders: string[] = [];
    for (const [relPath, src] of ALL_SOURCES) {
      if (relPath in PLATFORM_ADMIN_ALLOWLIST) continue;
      const hits = platformAdminReferences(src);
      if (hits.length === 0) continue;
      if (PLATFORM_ADMIN_PREDICATE.test(src)) continue;
      offenders.push(`${relPath} → ${hits.join(', ')}`);
    }
    expect(
      offenders,
      'These files offer a control for a route the backend grants to a PLATFORM ADMIN ' +
        'only — an installation-wide catalogue, where a lead is refused exactly as a ' +
        'viewer is (#1501). Bind the control to `useCanEditInstallationCatalogue()` ' +
        '(see pages/stammdaten/ActivityDetailPage.tsx), or add a ' +
        'PLATFORM_ADMIN_ALLOWLIST entry with the measured backend route.',
    ).toEqual([]);
  });

  it('every platform-admin allowlist entry still names a file that still needs it', () => {
    for (const [file, reason] of Object.entries(PLATFORM_ADMIN_ALLOWLIST)) {
      expect(reason.length, `${file}: allowlist entry needs a reason`).toBeGreaterThan(20);
      const src = ALL_SOURCES.get(file);
      expect(src, `${file} does not exist — drop the allowlist entry`).toBeDefined();
      expect(
        platformAdminReferences(src as string),
        `${file} no longer reaches a platform-admin-only write — drop the allowlist entry`,
      ).not.toEqual([]);
    }
  });

  it('every allowlist entry names a file that still exists and still needs the exemption', () => {
    for (const [file, reason] of Object.entries(ALLOWLIST)) {
      expect(reason.length, `${file}: allowlist entry needs a reason`).toBeGreaterThan(20);
      const src = ALL_SOURCES.get(file);
      expect(src, `${file} does not exist — drop the allowlist entry`).toBeDefined();
      expect(
        leadOnlyReferences(src as string),
        `${file} no longer reaches a lead-only delete — drop the allowlist entry`,
      ).not.toEqual([]);
    }
  });

  it('every UI file reaching a lead-only delete reads a canDelete predicate', () => {
    const offenders: string[] = [];
    for (const [relPath, src] of ALL_SOURCES) {
      if (relPath in ALLOWLIST) continue;
      const hits = leadOnlyReferences(src);
      if (hits.length === 0) continue;
      if (ROLE_PREDICATE.test(src)) continue;
      offenders.push(`${relPath} → ${hits.join(', ')}`);
    }
    expect(
      offenders,
      'These files offer a destructive control for a route the backend grants to a lead ' +
        'only (REQ-049 §2.3). Bind the control to `useTenantPermissions().canDelete` ' +
        '(see pages/pflanzen/photos/PlantPhotoGallery.tsx), or add an allowlist entry ' +
        'with the measured backend route if the rank really does not apply.',
    ).toEqual([]);
  });

  it('no UI file bypasses the endpoint layer with a raw apiClient.delete', () => {
    const offenders: string[] = [];
    for (const [relPath, src] of ALL_SOURCES) {
      if (/\bapiClient\s*\.\s*delete\s*[<(]/.test(src)) offenders.push(relPath);
    }
    expect(
      offenders,
      'A raw apiClient.delete outside src/api/ has no endpoint function to classify, ' +
        'so the role predicate above cannot see it. Route it through src/api/endpoints/.',
    ).toEqual([]);
  });

  it('sees a lead-only reference through a rename, a namespace and a thunk', () => {
    // The guard is only worth its runtime if its reader actually catches the
    // writings the class hid behind. Falsifying each shape here keeps that honest.
    expect(leadOnlyReferences("import { deleteSite } from '@/api/endpoints/sites';")).toEqual([
      'deleteSite',
    ]);
    expect(
      leadOnlyReferences("import { deleteSite as dropIt } from '@/api/endpoints/sites';"),
    ).toEqual(['deleteSite']);
    expect(
      leadOnlyReferences(
        "import * as api from '@/api/endpoints/sites';\nawait api.deleteSite(key);",
      ),
    ).toEqual(['deleteSite']);
    // A thunk name is only recognised because its slice body was read.
    expect(LEAD_ONLY_THUNKS.has('deleteWorkflowThunk')).toBe(true);
    expect(
      leadOnlyReferences("import { deleteWorkflowThunk } from '@/store/slices/tasksSlice';"),
    ).toEqual(['deleteWorkflowThunk']);
    // A non-destructive neighbour from the same module is not a hit.
    expect(leadOnlyReferences("import { getSite } from '@/api/endpoints/sites';")).toEqual([]);
    // …and neither is the thunk declared *next to* a destructive one. A fixed-size
    // read window made `fetchWorkflows` a hit, which would have satisfied the rule
    // on files that never touch a delete at all.
    expect(LEAD_ONLY_THUNKS.has('fetchWorkflows')).toBe(false);
    expect(LEAD_ONLY_THUNKS.has('fetchCalendarEvents')).toBe(false);
    expect(
      leadOnlyReferences("import { fetchWorkflows } from '@/store/slices/tasksSlice';"),
    ).toEqual([]);
  });

  it('sees a platform-admin reference through a rename and a namespace', () => {
    expect(
      platformAdminReferences(
        "import { deletePhaseDefinition } from '@/api/endpoints/phaseSequences';",
      ),
    ).toEqual(['deletePhaseDefinition']);
    expect(
      platformAdminReferences(
        "import { deletePhaseDefinition as dropIt } from '@/api/endpoints/phaseSequences';",
      ),
    ).toEqual(['deletePhaseDefinition']);
    expect(
      platformAdminReferences(
        "import * as api from '@/api/endpoints/ipm';\nawait api.deletePest(key);",
      ),
    ).toEqual(['deletePest']);
    // The two readers must not answer for each other's class, or an entry moved
    // between the lists would keep passing under the old rule.
    expect(
      platformAdminReferences("import { deleteSite } from '@/api/endpoints/sites';"),
    ).toEqual([]);
    expect(
      leadOnlyReferences(
        "import { deletePhaseDefinition } from '@/api/endpoints/phaseSequences';",
      ),
    ).toEqual([]);
  });
});
