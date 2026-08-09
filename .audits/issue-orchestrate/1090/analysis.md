---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "1090"
classification: "security"
secondary-classes: [feature-request]
route: "direct"
status: approved
created: "2026-08-09"
approved: "2026-08-09"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on feat/1090-cultivar-tenant-ownership, then removed
     with a fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. -->

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1090 — Cultivar tenant ownership (follow-up to #808 species-only scope)
- **URL**: https://github.com/nolte/kamerplanter/issues/1090
- **Labels**: enhancement, security, backend
- **Linked items**: #808 (R-14 species scope), PR #1087 (delivered species pendant, merged 2026-08-09), #324 (regression class), #816 (`TestSpeciesScopeConsistency`), #1000 (tenant-body gate)
- **Prior art checked**: no open/linked PRs address #1090; not self-resolved (verified on origin/develop 8f32c5143). Requirement artefact `project/requirements/species-tenant-ownership.md` explicitly defers Cultivar to this issue.

## Requirements gate

- **Operator override recorded (2026-08-09)**: no dedicated cultivar requirement artefact; issue #1090 (operator-authored, testable ACs, confirmed cutover/#324 decisions) plus `project/requirements/species-tenant-ownership.md` (U_gate 0.85) accepted as the requirements basis. `requirements-elicit` explicitly waived.
- Requirement transfer: R1→C-1, R2→C-1, R3→C-3/C-5, R4→C-3 (call the shared helper, no 5th copy), R5→already present, R6→C-2, R7→C-6, R8→C-6.

## Classification

- **Primary class**: security
- **Secondary class(es)**: feature-request
- **Rationale**: cross-tenant leak — tenant-created cultivars are visible to and mutable by every tenant. Operator-confirmed 2026-08-09; security audit chain (code-security-reviewer + security-review) required before PR.

## Scope

- **In scope**: `Cultivar.tenant_key` + write-path stamping incl. ownership preservation; cutover migration `v0038`; tenant-aware reads via `tenant_scope.py::tenant_union_predicate`; ownership/role gate on GET/PUT/DELETE (SEC-002 pendant); MCP cultivar read tools (SEC-003 pendant, → Q1); tests (both-direction leak, role matrix, scope consistency per #816).
- **Out of scope (hard, operator-confirmed)**: `tenant_has_access` edge (separate deferred item); frontend origin-filter (#397).
- **In scope (operator extension, 2026-08-09)**: owned-reference verification of `plant_instance.cultivar_key` (Q2 → package C-9).
- **Out of scope (from analysis)**: all dereference paths resolving an already-anchored cultivar (`print_service:289`, `care_reminder_service:1124`, `watering_service:322`, `plant_instance_service:880`, `planting_runs/tenant_router:322`, AQL `DOCUMENT()` joins in `plant_instance_repository:390`, `calendar_aggregation_engine:367`) stay system context (`tenant_key=None`), exactly like the species pendant.

## Route

- **Decision**: direct
- **Rationale**: a proven pattern transferred to a second entity; one coherent outcome, single PR strand, every AC machine-checkable, no new roadmap item.

## Work packages

### C-1 — `Cultivar.tenant_key`, write stamping, ownership preservation

- **Problem statement**: `Cultivar` has no owner field; interactive create stamps only `origin`; PUT and the `seed_data` upsert could silently erase future ownership.
- **Acceptance criteria**:
  1. `Cultivar.tenant_key: str = ""` documented in the style of `Species.tenant_key` (`models/species.py:443-457`), incl. `origin`=provenance vs. `tenant_key`=ownership distinction.
  2. POST stamps via `Depends(get_creating_tenant_key)`; `CultivarCreate` carries no tenant field; value never from `body.model_dump()` (#1000); `tenant-body-field` gate green.
  3. SEC-004 analogon: `full` mode without active tenant → 422; light mode untouched (model: `species/router.py:143-144`) — per Q5 decision.
  4. Global paths leave `""`: `cultivar_seed.build_cultivar`, `import_service.py:126` — test analogous to `test_seed_species_global_tenant_key.py`.
  5. `update_cultivar` preserves `cultivar.tenant_key = existing.tenant_key` (analogous to `origin`, `species_service.py:402-404`).
  6. The repository-direct seed upsert cannot erase ownership (P2): test with a same-named tenant-owned cultivar, red-first.
  7. `tenant_key` added to `_CULTIVAR_MODEL_RUNTIME_ONLY` (`test_seed_schema_conformance.py:227`) with rationale; seed schema unchanged (P1).
  8. `CultivarResponse` does NOT expose `tenant_key` (per Q4 decision).
  9. ruff clean, unit suite green.
- **Touched files / artifacts**: `domain/models/species.py`, `api/v1/cultivars/router.py`, `domain/services/species_service.py`, `data_access/arango/species_repository.py` (`update_cultivar`), possibly `migrations/seed_data.py`, `tests/unit/migrations/test_seed_schema_conformance.py`, new tests.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: none

### C-2 — Cutover migration `v0038` (existing rows stay global)

- **Problem statement**: existing cultivars (incl. `origin: tenant`) lack the attribute; the confirmed cutover rule keeps them global — no default-tenant stamp (#324 regression class, owner not recoverable).
- **Acceptance criteria**: module `v0038_cutover_cultivar_tenant_key.py` modelled on `v0036`; sets `""` only where the attribute is missing (`FILTER doc.tenant_key == null`), incl. `origin: tenant`; docstring justifies no-default-stamp with #324; `CULTIVARS` NOT added to `backfill_tenant_key.TOP_LEVEL_COLLECTIONS`, absence pinned by test; idempotent (`changed == 0` on re-run); `dry_run` writes nothing; `reversible = False`; report shows `origin_tenant_left_global` separately; discovery sequence accepts v0038; dedicated test modelled on `test_v0036_…`.
- **Touched files / artifacts**: `migrations/versions/v0038_cutover_cultivar_tenant_key.py`, `tests/unit/migrations/versions/test_v0038_…`, absence pin for `backfill_tenant_key.py`.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: C-1

### C-3 — Tenant-aware cultivar read paths (union predicate)

- **Problem statement**: all cultivar reads are unscoped (`species_repository.py:220/230/233`); `find_by_field`'s AND-joined `extra_filters` cannot express the three-arm OR union (P3).
- **Acceptance criteria**:
  1. `get_cultivars(species_key, *, tenant_key=None)` — `None` unchanged; otherwise hand-written AQL using `tenant_union_predicate` (analogous to `species_repository.py::get_all:43-53`), no 5th inline copy.
  2. `list_cultivars`/`get_cultivar` pass `tenant_key` through; `get_cultivar` checks after unscoped load `cultivar.tenant_key not in (tenant_key, "")` → `NotFoundError` (404, never 403), exactly like `get_species:105-108`.
  3. Router wires both GETs with `Depends(get_active_tenant_key)`.
  4. Species existence check in `list_cultivars` co-scoped → foreign species = 404 (per Q3 decision).
  5. Repo stays `is_tenant_scoped = False` (P4); `""` yields global-only, never an error, never all tenants — proven by test.
  6. All existing callers without tenant argument stay working (P5: keyword-only, default `None`).
  7. Stale docstring `species_repository.py:152-153` corrected (E2).
  8. Red-first proof for the foreign-tenant case.
- **Touched files / artifacts**: `data_access/arango/species_repository.py`, `domain/services/species_service.py`, `api/v1/cultivars/router.py`, new tests.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: C-1

### C-4 — Ownership/role gate on PUT/DELETE (SEC-002 pendant)

- **Problem statement**: cultivar mutations carry no gate at all; the species pendant (`_authorize_species_write:272-309`) defines the confirmed behaviour matrix.
- **Acceptance criteria**: authorization function modelled on `_authorize_species_write` (system context → no gate; foreign → 404; global → platform admin only, else 403; own → `MembershipEngine.can_edit_resource` / `can_delete_resource` lead-only per REQ-049 §2.3); service signatures keyword-only with backwards-compatible defaults; router wired with `get_active_tenant_context` + `get_is_platform_admin`; full behaviour matrix tested (foreign GET/PUT/DELETE→404; global PUT/DELETE non-admin→403, admin→200/204; own viewer→403; own grower update→200, delete→403; own lead delete→204).
- **Touched files / artifacts**: `domain/services/species_service.py`, `api/v1/cultivars/router.py`, new tests.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: C-3

### C-5 — Scope MCP cultivar read tools (SEC-003 pendant)

- **Problem statement**: `list_cultivars` (`mcp_server/tools/species.py:230`), `get_cultivar` (`:250`) and the cultivar block of `describe_species` (`:201`) expose every tenant's cultivars to an LLM (E1); PR #1087 closed this for species with `tenant_key=""`.
- **Acceptance criteria**: the three MCP surfaces read with `tenant_key=""` (comment pattern `tools/species.py:84-92`); test proves a tenant-owned cultivar is absent from the list and `get_cultivar` answers `not_found`; K3 fixed: `links` points at the real route (`/api/v1/species/{species_key}/cultivars/{key}`, not the non-existent `/api/v1/cultivars/{key}`); `test_catalog_tools.py`/`test_tools.py` green.
- **Touched files / artifacts**: `mcp_server/tools/species.py`, MCP tests.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: C-3

### C-9 — Owned-reference guard for `plant_instance.cultivar_key` (operator extension, Q2)

- **Problem statement**: a tenant can bind a foreign tenant's cultivar to their plant; the owned-reference mechanism (#948, `base_repository.py:397-436`) exists and lets global rows stay referenceable, but `cultivar_key` is not registered.
- **Acceptance criteria**: `plant_instance_repository._owned_reference_fields` extended with `{"cultivar_key": col.CULTIVARS}`; test proves a foreign cultivar reference is rejected while a global and an own cultivar stay bindable; existing plant-instance suites green; red-first proven.
- **Touched files / artifacts**: `data_access/arango/plant_instance_repository.py`, plant-instance tests.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: C-1

### C-6 — Both-direction isolation proof + scope consistency

- **Problem statement**: the delivered guards must be proven non-inert (project's most expensive failure class) — both directions (#324: global visible AND foreign hidden), at repo/service AND API level, plus a scope-consistency guard analogous to `TestSpeciesScopeConsistency` (#816).
- **Acceptance criteria**: both-direction tests at repository/service and API level; anonymous/`""` sees exactly the global catalog; scope-consistency test on the generated AQL — if structurally only one narrowing read path exists, an absence guard is formulated with a docstring rationale (per Q6 decision); red-first proven; existing suites (`test_seed_schema_conformance`, `test_cultivar_seed`, `test_origin_provenance`, `test_species`, `TestSpeciesScopeConsistency`) green.
- **Touched files / artifacts**: new/extended tests under `src/backend/tests/unit/`.
- **Specialist**: nolte-engineering:integration-test-generator + nolte-engineering:unit-test-generator (sequential)
- **Depends on**: C-3, C-4, C-5

### C-7 — Security review of cultivar isolation

- **Problem statement**: security-class issue requires the audit chain before PR.
- **Acceptance criteria**: verdict on (a) remaining unscoped read paths, (b) consistency of the 404/403 boundary / no existence oracle, (c) `tenant_key` reachable from no request body, (d) no write path resets ownership to global.
- **Touched files / artifacts**: read-only.
- **Specialist**: nolte-engineering:code-security-reviewer (+ built-in `security-review` skill on the diff at verify)
- **Depends on**: C-6

### C-8 — Combined regression sweep

- **Problem statement**: full-suite proof before PR.
- **Acceptance criteria**: `pytest src/backend/tests` in one run with reported count; ruff + repo gates green; every non-pass classified with `file:line`.
- **Touched files / artifacts**: read-only / test fixes only.
- **Specialist**: kamerplanter:unit-test-runner + nolte-engineering:test-result-analyzer
- **Depends on**: C-7

## Dependency ordering

```
C-1 ─┬─> C-2
     ├─> C-9 ─────────────┐
     └─> C-3 ─┬─> C-4 ─┐  │
              └─> C-5 ─┴──┴─> C-6 ─> C-7 ─> C-8
```

Serialized dispatch **C-1 → C-2 → C-3 → C-4 → C-5 → C-9 → C-6 → C-7 → C-8** (writing agents on a shared tree run sequentially per project rule; C-4/C-5/C-9 are file-disjoint and could parallelize only with multiple trees). C-7's review surface includes C-9.

## Refutations / corrections (specialist findings, first-class results)

- **Hypothesis holds — no refutation.** Verified: `Cultivar` carries no `tenant_key` (`models/species.py:75-121`); create stamps only `origin` (`api/v1/cultivars/router.py:40-44`); reads unfiltered; PUT/DELETE ungated; nowhere already scoped.
- **K1 (path)**: file is `src/backend/app/api/v1/cultivars/router.py`, create at `:40-44` (issue said `species/cultivars/router.py:42`).
- **K2 (route vs. file)**: router prefix stays `"/species/{species_key}/cultivars"` — the HTTP route is unchanged; only the file moved. Tests/docs must mirror the route, not the file path.
- **K3 (pre-existing defect)**: `mcp_server/tools/species.py:257` links to `/api/v1/cultivars/{key}`, which does not exist — fixed in C-5.
- **P1**: `test_cultivar_model_fields_have_schema_property` goes red immediately; correct fix is `_CULTIVAR_MODEL_RUNTIME_ONLY`, NOT extending the seed schema (YAML must not set ownership). No species pendant for this guard — #1087 never met it.
- **P2 (most important finding)**: `migrations/seed_data.py:514` calls `species_repo.update_cultivar` repository-direct, matched by name — would clobber a same-named tenant-owned cultivar back to global. Ownership preservation must sit in the repository (or seed_data becomes ownership-aware).
- **P3**: list read not scopeable via `find_by_field` (AND-only) — hand-written AQL branch required.
- **P4**: `is_tenant_scoped = True` would break the hybrid catalog for anonymous/light-mode callers (REQ-027) — species deliberately doesn't set it.
- **P5**: four seeders call `get_cultivars(sp_key)` tenant-less; six call sites resolve cultivars in system context — signatures keyword-only with default `None`.

## Risks

- **Inert field** (C-1 without C-3): project's best-known failure class → same PR, red-first proof in C-6.
- **P2 clobber**: silent ownership loss on next seed run if C-1 AC 6 is dropped.
- **P1 wrong fix**: extending the seed schema would let YAML set ownership — forbidden.
- **Migration number**: `v0038` is free today; a migration merging first forces loud renumbering (discovery enforces gapless monotony).
- **Behaviour tightening on global cultivars** (C-4): not reachable from today's UI (`useOriginProtection.ts`; E2E TC-REQ-001-042..047 only create new cultivars) — residual risk low, confirm in pre-merge E2E.
- **No FE change needed** while Q4 stays "don't expose".
- **Security-sensitive paths**: code-security-reviewer (C-7) + built-in `security-review` on the diff are mandatory before the PR opens.

## Open questions — all resolved by operator (2026-08-09)

- **Q1** → **include**: C-5 stays in this strand (closes the MCP read path + dead link K3).
- **Q2** → **in this strand**: added as package C-9 (owned-reference guard, own test).
- **Q3** → **yes**: foreign species in the cultivar list → 404, not an empty list.
- **Q4** → **don't expose**: `CultivarResponse` without `tenant_key`, mirroring `SpeciesResponse`.
- **Q5** → **yes**: interactive create in `full` mode without active tenant → 422 (SEC-004 analogon).
- **Q6** → **yes**: the absence guard suffices as the #816 pendant when only one narrowing read path exists (docstring rationale required).

Plan approval (route `direct`, packages C-1..C-9) given by the operator on 2026-08-09; serial dispatch authorized starting with C-1.

## Dispatch log

- 2026-08-09 C-1 dispatched to nolte-engineering:fullstack-developer — DONE. Field + stamping + 422 gate + ownership preservation at service AND repository level (justified deviation: both layers — repository guards field, seed_data guards content); extra defect found & fixed: seed name-match would have replaced a tenant row's field content and shadowed the global seed entry (`seed_cultivars()` extracted, matches global rows only). Red-first proven (P1 + P2 both levels). Suites: 6613 unit + 836 api + 27 contracts passed; all repo gates green. Pre-existing failure reported (boundary-validation ceiling 54 vs 46 — repo-wide gate maintenance, outside scope; proven unchanged vs HEAD via git archive). Note for C-3: `seed_data.seed_cultivars()` needs the unscoped read (`tenant_key=None`).
- 2026-08-09 C-2 dispatched to nolte-engineering:fullstack-developer — DONE. `v0038_cutover_cultivar_tenant_key` (number verified free): absent-attribute-only stamp incl. `origin:tenant`, idempotent, dry-run inert, `origin_tenant_left_global` split in report. Justified extensions: executable absence pin for SPECIES+CULTIVARS across ALL backfill phases (v0036 only claimed it in prose); AQL-text pins closing the fake-DB vacuity hole; owned-row fixture proves no flattening. Migrations suite 579 passed; ruff clean; mutation-proven non-inert. Note for C-3: union predicate must keep matching `tenant_key == ""` — strict `== @caller` reproduces #324 on the legacy population. Doc note for PR: v0038 leaves legacy tenant-created cultivars global by design, irreversible.
- 2026-08-09 C-3 dispatched to nolte-engineering:fullstack-developer — DONE. Union predicate on list read (hand-written AQL, shared helper, AQL text pinned); Q3 co-scoped species check (404, `get_cultivars` proven not called); post-load ownership check on single read (404-parity with absent key, no oracle); both GETs wired. Justified deviation: single-row repository loads stay unscoped — the species-style post-load check requires the row; also keeps the six system-context dereference call sites untouched. Red-first proven incl. live leak probe; router mutation proves guards load-bearing. Suites: 6653 unit + 845 api + 27 contracts; ruff + 5 custom gates green. NEW FINDING handed to C-4: `create_cultivar` calls `get_species` unscoped → POST under a foreign species = cross-tenant existence oracle (201-vs-404) + `has_cultivar` edge on the foreign species. Note for C-5: `list_cultivars(..., tenant_key="")` on a tenant-owned species now raises NotFoundError — MCP must map to `not_found`. Note for C-6: exactly one narrowing read path → Q6 absence-guard form applies.
- 2026-08-09 C-4 dispatched to nolte-engineering:fullstack-developer — DONE. Shared `_authorize_tenant_owned_write` + thin species/cultivar bindings (species call sites byte-identical); full matrix pinned at service (22) + HTTP (16); C-3 finding fixed (create co-scopes parent species → 404, no foreign edge). Red-first: 26/38 failed pre-change (foreign PUT 200→404, global non-admin 204→403, foreign-species POST 201→404). Suites: 6675 unit + 861 api + 27 contracts; ruff + 7 gates green. Residuals for C-7: (a) create scoped but role-ungated (viewer may create — species parity, likely intentional); (b) global-cultivar curation now needs platform admin (light mode unaffected); (c) E2E crosses no new 403 (founder = LEAD, e2e only creates). Note for C-6: write matrix already pinned twice — avoid a third copy; C-4's non-inertness proven red-first against committed C-3. Note for C-9: plant_instance.cultivar_key is the last path a foreign cultivar key can enter tenant data.
- 2026-08-09 C-5 dispatched to nolte-engineering:fullstack-developer — DONE. Three MCP read surfaces scoped to `tenant_key=""` (tool is `get_species_info`, not `describe_species`); not_found mapping incl. wire-contract code; K3 link fixed. Red-first: 6/6 failed pre-change + live leak probe (foreign 'Secret Cross' visible, empty-list oracle). Fake-signature trap found & closed: GetSpeciesInfo's blanket except turns signature drift into silent green — new test pins the recorded tenant_key argument. REQ-033 finding: permission matrix is orthogonal to visibility (READ granted to every role via _strongest_role) — could never have closed the leak. Residual for C-7: `diary.py:221 _cultivar_name` reads unscoped — dereference path on an anchored key, system-context category per analysis, deliberately left (tightening would degrade legacy foreign references to None). Suites: 412 mcp + 6681 unit + 888 api/contracts; ruff + 7 gates green.
- 2026-08-09 C-9 dispatched to nolte-engineering:fullstack-developer — DONE. Hypothesis held and was too narrow: PUT was a second bypass (create-global-then-swap-foreign) — closed via new opt-in `_verify_references_on_update` (verifies only actually-changed references; orphaned legacy refs stay editable, missing-vs-foreign identical 404). `CULTIVARS` added to `OWNERSHIP_VERIFIABLE_COLLECTIONS` (mandatory — declaration alone would have fail-closed rejected even global cultivars). Both global forms bindable (`""` and v0038 attribute-less legacy). Write-path audit: all covered; propagation field-dict writers carry no cultivar_key. Red-first: 10 failed pre-change incl. POST 201 + PUT 200 with foreign cultivar. Suites: 6693 unit + 877 api + 27 contracts; ruff + gates green; mypy no new errors. FOLLOW-UP CANDIDATES (out of scope, for PR notes + issues): (1) `PlantingRunEntry.cultivar_key` — same leak class, body-sourced, no tenant_key on entry (needs harvest-observation pattern, declaration alone skips tenantless rows); run detail view resolves a foreign cultivar's name unscoped; materialisation fails late (404 at plant_repo.create). (2) One-line candidates where the declaration works directly: `PropagationEvent`, `SuccessionPlan`. (3) Known behaviour delta: clone of a plant with orphaned cultivar_key fails 404 at create — caught & logged in phase callback, transition unbroken.
