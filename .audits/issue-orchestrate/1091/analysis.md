---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "1091"
classification: "feature-request"
secondary-classes: [security, spec-change]
route: "direct"
status: approved
created: "2026-08-10"
approved: "2026-08-10"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on feat/1091-active-tenant-resolution, then removed
     with a fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. -->

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1091 — Org-context tenant resolution on global-but-tenant-aware routes (follow-up to #808 / REQ-049)
- **URL**: https://github.com/nolte/kamerplanter/issues/1091
- **Labels**: enhancement, security, backend
- **Linked items**: #808 assumption A1 (R-14); #780 / REQ-049 two-axis role model (#860/#861/#862); PR #1087 (delivered species scoping, F-5); #1090 / PR #1109 (cultivar scoping, C-3/C-4); **#1113** (SEC-005 from #1090 C-7 — role-gate species/cultivar create, explicitly gated on *this* work); #324 (both-direction visibility regression class); #1000 (tenant-body gate)
- **Prior art checked**: no PR references this issue; the four open PRs are Renovate-only and touch none of the files below. Not self-resolved — verified on the worktree base `4de2b03b4`: `get_active_tenant_key` still returns the personal tenant unconditionally (`app/common/auth.py:134-135`).

## Requirements gate

- **Grounded input**: `project/requirements/active-tenant-resolution.md` (teach-back confirmed 2026-08-10, `U_gate = 0.8 = τ_high`). Decomposition authorised by its consumer contract.
- **Requirement transfer**: R1 → A-2 · R2 → A-2 · R3 → A-2 (+A-5 proof) · R4 → A-5 · R5 → A-3 (+A-7 UI consequence) · R6 → A-2 scope note (+A-5 negative proofs) · R7 → A-1.
- All three surviving assumptions of the artifact were checked against the code; two refuted, one confirmed — see §Refutations.

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: security, spec-change
- **Rationale** (operator-confirmed): the strand adds a new request-borne authorisation input (`X-Active-Tenant`) and closes a latent write hole (#1113/SEC-005), so the security-review chain is mandatory before the PR; it also changes normative spec (ADR + REQ-049).

## Scope

- **In scope**: `X-Active-Tenant` header parsing, slug→tenant resolution and *active-membership* validation inside the single resolver (`get_active_tenant_key` / `get_creating_tenant_key` alias / `get_active_tenant_context`); oracle-free 403 for both invalid cases; role-gated interactive create for species **and** cultivar (closes #1113); frontend header attachment on the global axios client incl. stale-slug recovery; UI role-gating of the catalogue create actions; both-direction visibility proof; ADR + REQ-049 update; user docs (DE canonical + EN mirror).
- **Out of scope (requirement artifact, operator-confirmed)**: MCP catalogue tools stay global-only (→ follow-up F-1); favorites stay personal-across-tenants (verified: they bind `get_current_tenant` on `/t/{slug}/favorites`); `/t/{slug}/` routes keep path binding; no `/t/{slug}/` twins.
- **In scope (operator extension, Q1 2026-08-10)**: path-route oracle alignment — `get_current_tenant` on `/t/{slug}/` answers oracle-free 403 for unknown-slug AND non-member (today: 404 vs 403) → package A-11.
- **Out of scope (from this analysis)**: botanical-family mutations carry no role gate at all today (→ F-3 follow-up issue); service accounts acting "as an org" (→ F-4 follow-up issue); MCP catalogue tools (→ F-1 follow-up issue).

## Route

- **Decision**: direct (one coherent PR strand)
- **Rationale**: a single named design decision on an existing, well-isolated resolver whose docstring already promises "replace *only this function*"; all ACs machine-checkable; no roadmap item, no migration.

## Work packages

### A-1 — ADR + REQ-049 update (R7)

- **Problem statement**: the active-tenant signal is an architecture decision with cross-spec effect and is currently recorded only as a "known limitation" in a Python docstring.
- **Acceptance criteria**: (1) `spec/decisions/ADR-009-active-tenant-header.md` in the Nygard format per `spec/decisions/README.md` (ADR-009 = next free number in spec/decisions; docs-ADR numbering runs independently). (2) Alternatives named and rejected with reasons: JWT claim (token refresh on switch, claim outlives revoked membership), `/t/{slug}/` twins (rejected in the requirement artifact), tenant key instead of slug (slug chosen: human-readable, `/t/{slug}/` symmetry). (3) Decision states the invalid-header rule: 403, identical response for unknown slug and non-membership, never a silent fallback, and why. (4) `spec/req/REQ-049_Rollenmodell-und-Vokabular.md` gains §2.11 "Aktiver Mandant auf globalen Routen" (mechanism, role source = active tenant's membership, fail-safe), version 1.4 + Versionshistorie row referencing ADR-009. (5) #808 A1 marked closed with pointer to the ADR. (6) `spec/decisions/README.md` index row. (7) German prose, English identifiers.
- **Touched files**: `spec/decisions/ADR-009-active-tenant-header.md` (new), `spec/decisions/README.md`, `spec/req/REQ-049_Rollenmodell-und-Vokabular.md`
- **Specialist**: `claude-shared:spec` skill (fallback: generalist with the README format quoted)
- **Depends on**: none

### A-2 — The one resolver: header, membership validation, oracle-free 403 (R1, R2, R3)

- **Problem statement**: `get_active_tenant_key` (`auth.py:81-135`) and `get_active_tenant_context` (`auth.py:138-170`) both hard-resolve the personal tenant; a global route carries no org signal.
- **Acceptance criteria** (red-first on each 403 arm and the identity property):
  1. No header → today's behaviour byte-for-byte (personal tenant; none/anonymous → `""`); existing `test_active_tenant_key.py` / `test_creating_tenant_key.py` pass unchanged.
  2. Valid header (active membership) → that tenant's key; `get_active_tenant_context` returns the SAME tenant's key/slug and role/admin_scopes from THAT membership (org viewer → `viewer`, never the personal-tenant `lead`).
  3. Unknown slug → `ForbiddenError` (403). `TenantService.get_tenant_by_slug` raises `NotFoundError` (404) — must be caught and converted; a leaking 404 is a red-first test case.
  4. Non-member / inactive membership → 403 identical to AC 3 apart from `error_id` (same error_code `FORBIDDEN`, status, message); test asserts body equality after removing `error_id`.
  5. Never a silent fallback: no path answers 200-with-personal or 200-with-`""` when a header was present and invalid; status asserted.
  6. Empty/whitespace header value = absent (AC 1), documented as deliberate.
  7. Alias identity preserved: `get_creating_tenant_key is get_active_tenant_key` (existing assertion stays green).
  8. Non-divergence property: for all four input classes, `get_active_tenant_context(...).tenant_key == get_active_tenant_key(...)` (or same exception type); ONE shared internal resolution helper — a copy-paste second resolution is review-blocking.
  9. Light mode (REQ-027) proven: light-mode request WITH `X-Active-Tenant: mein-garten` resolves (seed creates the lead membership in `system-tenant`); WITHOUT header keeps today's behaviour.
  10. Header declared as FastAPI `Header(default=None, alias="X-Active-Tenant")` (appears in OpenAPI); `check_tenant_body_field.py` stays green (Header params excluded by construction).
  11. The "Known limitation (#808 A1)" docstring block replaced by the resolved mechanism + ADR-009 pointer.
  12. ruff clean; backend unit + api suites green.
- **Touched files**: `src/backend/app/common/auth.py`; `tests/unit/common/test_active_tenant_key.py`; new `tests/unit/common/test_active_tenant_header.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none

### A-3 — Role-gated interactive create for species and cultivar (R5, closes #1113/SEC-005)

- **Problem statement**: `POST /species` and `POST /species/{k}/cultivars` stamp the active tenant but run NO role check; the moment A-2 lands, an org viewer could create rows in a shared tenant.
- **Shape decision**: gate in the SERVICE layer as a shared `_authorize_tenant_owned_create(...)` sibling of `_authorize_tenant_owned_write` (a router-only check would be the second-copy drift class REQ-049 §2.3 already paid for); create needs only the `can_edit_resource` arm (no existing row → no foreign/global arms); system-context escape (`caller_role is None`) keeps seeds/imports working.
- **Acceptance criteria** (red-first: viewer-create returns 201 pre-change):
  1. Org viewer → POST species/cultivar 403 FORBIDDEN. 2. Grower/lead → 201. 3. Platform-admin bypass (light-mode curation keeps working). 4. Stamping unchanged: routes keep `Depends(get_creating_tenant_key)` for the stamp; overriding ONLY it still changes the stamp (alias must not become inert). 5. SEC-004 ordering preserved (422-no-tenant vs 403 order stated + tested). 6. System context unaffected (seeds/import regression-tested). 7. Mandatory fixture correction: `test_cultivar_tenant_ownership_api.py` must override the two new dependencies too; VERIFY with no ArangoDB reachable (localhost:8529 masks datastore calls locally). 8. Create-role matrix added to both authorization API test files; `test_origin_provenance.py` untouched green. 9. #1113 referenced; closable by this PR. 10. ruff + suites green.
- **Touched files**: `species_service.py`, `species/router.py`, `cultivars/router.py`, both authorization API test files, `test_cultivar_tenant_ownership_api.py`, unit tests
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: A-2

### A-4 — Frontend: attach `X-Active-Tenant` on the global client + stale-slug recovery

- **Problem statement**: catalogue endpoints use the global axios `client` (no tenant signal); the active slug already lives in `api/client.ts` (`getActiveTenantSlug()`, synced by `tenantSlice`).
- **Acceptance criteria**: (1) request interceptor sets the header when slug non-null, none when null. (2) NO bootstrap blocking (`waitForTenantSlug` NOT used — a pre-bootstrap request carries no header = personal scope; tested + comment). (3) Light mode: no header sent (or `mein-garten` — one decided answer, stated and tested; per operator decision below). (4) Stale-slug recovery: catalogue 403 with header → clear `kp_active_tenant_slug`, reload tenant list (tested with mocked 403). (5) Tenant switch works end-to-end (TenantSwitcher does full reload — no cache invalidation needed; explicit non-goal). (6) Frontend suites + lint green, no new `any`.
- **Touched files**: `src/frontend/src/api/client.ts`, possibly `tenantSlice.ts`, tests
- **Specialist**: `nolte-engineering:fullstack-developer` (+ `frontend-code-reviewer` review)
- **Depends on**: A-2

### A-5 — Both-direction visibility and stamping proof (R4, the #324 guard)

- **Acceptance criteria** (API level, real service + fake repo): (1) org member with header: global + org rows. (2) foreign tenant absent from list, 404 by key. (3) own PERSONAL rows NOT visible while org header set (header switches context, never unions — the direction most easily got wrong). (4) without header: today's behaviour unregressed. (5) write stamping binds the ACTIVE tenant (asserted on the persisted model). (6) anonymous → global-only. (7) same six for cultivar routes and botanical-family counts. (8) companion-planting anchor resolution moves with the header (fourth consumer, refutation R-1): foreign anchor 404s, org-owned anchor resolves.
- **Touched files**: new `tests/api/test_active_tenant_header_scope_api.py`
- **Specialist**: `nolte-engineering:integration-test-generator`
- **Depends on**: A-2, A-3

### A-6 — CORS preflight verification for the new header

- **Problem statement**: assumption refuted — `main.py:302-307` uses `allow_headers=["*"]`, no change needed; what is missing is a guard.
- **Acceptance criteria**: (1) preflight test (`OPTIONS` + `Access-Control-Request-Headers: x-active-tenant`) asserts the header is admitted. (2) docstring records why (non-safelisted header → preflight even on GET; narrowing to an explicit list later would silently drop the header and every org member would quietly fall back to personal scope). (3) NO change to main.py unless the test fails.
- **Touched files**: new `tests/api/test_cors_active_tenant_header.py`
- **Specialist**: `nolte-engineering:fullstack-developer` (foldable into A-2 dispatch)
- **Depends on**: none

### A-7 — UI role gating of the catalogue create actions

- **Acceptance criteria**: (1) species/cultivar create actions hidden or disabled-with-tooltip when `useTenantPermissions().canEdit` is false. (2) unchanged for grower/lead AND for no-active-tenant (`hasTenant === false` must NOT hide — the easy regression). (3) component tests viewer-hidden + grower-visible. (4) i18n DE+EN. (5) comment: UX consequence, backend gate is the authority.
- **Touched files**: `SpeciesListPage.tsx`, cultivar section, i18n, tests
- **Specialist**: `nolte-engineering:fullstack-developer` (+ `frontend-code-reviewer`)
- **Depends on**: A-3. **Splittable** if the strand grows too large.

### A-8 — User documentation (DE canonical + EN mirror)

- **Acceptance criteria**: (1) `docs/de/user-guide/tenants.md`: switching the active tenant switches catalogue visibility and create-target. (2) `docs/de/reference/roles-and-permissions.md`: create requires grower+ (viewer refused), consistent with REQ-049 §2.3. (3) EN mirrors; DOCS.md conventions. (4) `mkdocs build --strict` passes.
- **Specialist**: `kamerplanter:mkdocs-documentation`
- **Depends on**: A-2, A-3, A-4

### A-9 — Security review of the new authorisation input

- **Acceptance criteria**: (1) `code-security-reviewer` with explicit checklist: no invalid-header→200 path; membership check not bypassable via casing/whitespace/duplicate headers; role provably from the ACTIVE tenant's membership; no raw-header logging leaking slugs; 403 identical in both invalid cases. (2) built-in `security-review` on the diff (run from INSIDE the worktree — primary-checkout empty-diff trap). (3) findings fixed in-strand or filed with rationale.
- **Specialist**: `nolte-engineering:code-security-reviewer` + built-in `security-review`
- **Depends on**: A-2, A-3, A-4, A-5

### A-11 — Path-route oracle alignment (operator extension, Q1)

- **Problem statement**: `get_current_tenant` (`auth.py:67-70` via `TenantService.get_tenant_by_slug`) answers 404 for an unknown slug but 403 for a non-member on every `/t/{slug}/` route — a slug-existence oracle the header resolver (A-2) deliberately avoids. Operator decided to align NOW rather than defer.
- **Acceptance criteria** (red-first: unknown-slug currently 404, shown before the change):
  1. `/t/{unknown}/...` and `/t/{foreign}/...` answer 403 with identical bodies apart from `error_id` (same shape as A-2's header 403).
  2. The conversion happens in ONE place (the `get_current_tenant` dependency or a shared helper with A-2 — justify the choice; no per-router copies).
  3. Every existing test asserting 404 for unknown slugs on `/t/` routes is updated deliberately (each change listed in the dispatch result — this is a shipped-surface behaviour change, not a test fix).
  4. ADR-009 (A-1) documents the alignment in its Consequences (both surfaces oracle-free).
  5. ruff + backend suites green.
- **Touched files**: `src/backend/app/common/auth.py`, affected `/t/`-route test files, ADR-009 (via A-1)
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: A-2 (shares the 403 shape/helper)

### A-10 — Combined regression sweep and PR preparation

- **Acceptance criteria**: (1) backend unit+api+contracts, frontend vitest+lint, all task-check gates green. (2) pre-existing failures proven pre-existing vs base. (3) E2E not a merge gate (no E2E covers org context today). (4) PR references #1091 and #1113 (both closable), links ADR-009, states the classification.
- **Specialist**: `kamerplanter:unit-test-runner` sweep, then PR flow
- **Depends on**: all

## Dependency ordering

```
A-1 (spec)  ────────────────────────────────────┐
A-6 (cors)  ────────────────────────────────────┤
A-2 ─┬─> A-3 ─┬─> A-5 ──────────────────────────┤
     │        └─> A-7 ─────────────────┐        │
     └─> A-4 ──────────────────────────┴─> A-8 ─┴─> A-9 ─> A-10
```

Serialized dispatch: **A-2 → A-11 → A-3 → A-5 → A-6 → A-4 → A-7 → A-1 → A-8 → A-9 → A-10** (writing agents on a shared tree run sequentially; A-11 directly after A-2 so the shared 403 helper is settled before the dependent packages build on it).

## Refutations / corrections (first-class results)

- **R-1 (scope correction into R6)**: the resolver has FOUR consumer surfaces, not three — companion-planting router (`:40,55,104`) resolves anchor species via `get_active_tenant_key`. Must be tested (A-5 AC 8), not discovered later.
- **R-2 (assumption refuted — CORS)**: `allow_headers=["*"]` already admits the header; work item downgraded to regression guard (A-6). Dev traffic bypasses CORS entirely (Vite proxy).
- **R-3 (assumption refuted — frontend switcher)**: switcher exists and is complete (`TenantSwitcher.tsx`, `tenantSlice.ts`, `getActiveTenantSlug()`); frontend work collapses to one interceptor + recovery and STAYS in this strand.
- **R-4 (assumption confirmed — favorites)**: favorites bind `get_current_tenant` on `/t/{slug}/favorites`; the header cannot re-bind them.
- **R-5 (403-shape)**: no competing error contract; BUT the natural reuse of `get_tenant_by_slug` raises 404 — the single most likely implementation defect, pinned red-first (A-2 AC 3).
- **R-6 (pre-existing asymmetry)**: the `/t/{slug}/` path route already answers 404 unknown-slug vs 403 non-member — header oracle-freedom is local. → F-2 follow-up, open question.
- **R-7 (identifier collision)**: `SEC-005` names two different findings (companion-planting scoping from #808; create-role gap #1113). ADR-009 and comments must qualify (`SEC-005 (#1113)`).
- **R-8 (fixture hazard)**: `test_cultivar_tenant_ownership_api.py` overrides only `get_creating_tenant_key` to stay datastore-free; A-3's new deps break that — pinned as A-3 AC 7 with no-ArangoDB verification obligation.

## Risks

- Bootstrap window: pre-`loadMyTenants` requests carry no header (personal scope for a moment) — accepted deliberately, documented (A-4 AC 2).
- Stale persisted slug after membership revocation → catalogue-wide 403 lock-out; A-4 AC 4 is the mitigation.
- Inert-gate class (A-3 without A-5): red-first viewer-create + stamping assertion are the countermeasures; neither droppable.
- Alias inertness (A-3 AC 4): create route must keep `get_creating_tenant_key` as stamping source or four test files certify nothing.
- Role-source drift (A-2 AC 8): one shared helper, property-tested.
- Light-mode breakage (A-2 AC 9, A-4 AC 3): prove, don't assume.
- ADR-number race (ADR-009 free today); OpenAPI surface growth (openapi.json stays uncommitted).

## Open questions — all resolved by operator (2026-08-10)

- **Q1** → **in this strand**: path-route oracle aligned now (new package A-11); no F-2 follow-up issue.
- **Q2** → **send `mein-garten`**: the light-mode global client sends the header (uniform codepath); A-2 AC 9 proves the backend accepts it; A-4 AC 3 fixed accordingly.
- **Q3** → **A-7 stays in the strand**.
- **Q4/Q5** → **file all three follow-ups** (F-1 MCP, F-3 botanical-family role gates, F-4 service accounts) before the PR closes.

Plan approval (route `direct`, packages A-1..A-11) given by the operator on 2026-08-10; serial dispatch authorized starting with A-2.

## Dispatch log
