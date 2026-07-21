---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: 706
classification: "feature-request"
secondary-classes: ["refactor"]
route: "direct"
status: draft
created: "2026-07-21"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #706 — Locations must be explicitly flaggable as outdoor/frost-exposed (decouple overwintering from site type)
- **URL**: https://github.com/nolte/kamerplanter/issues/706
- **Labels**: enhancement, backend, frontend
- **Linked items**: none (no linked/closing PRs, no open PRs referencing 706)
- **Prior art checked**: `Site.type` + `OVERWINTERING_SITE_TYPES`/`WEATHER_RELEVANT_SITE_TYPES` frozensets (delivered #406/#410); `Location`/`LocationType` models; no feature/roadmap item covers per-location frost exposure. No merged fix.

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: refactor (secondary drift: BALCONY missing from three batch-task tuples)
- **Rationale**: A missing capability (location-level outdoor/frost flag), not a defect; the drift fix is an incidental refactor toward the existing single-source frozensets.

## Scope

- **In scope**: A `Location` can be explicitly marked outdoor/frost-exposed independent of its site; the overwintering / season-state / frost logic resolves exposure **location-first, falling back to the site type**; the location create/edit UI exposes the toggle; the secondary `BALCONY` drift in the three batch tasks is fixed.
- **Out of scope**: Redesign of `Site`/`SiteType` itself; introducing per-location GPS/climate-zone/frost-date fields (those stay at site level); `WEATHER_RELEVANT_SITE_TYPES` backend consumption beyond the balcony drift fix; reactive frost-warning engine redesign (already location-modelled).

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome (make locations frost-flaggable and honour it in winter logic) delivered in a single PR strand; no new or retargeted roadmap item; touches many files but is one feature, matching the #406/#410 precedent.

## Design decision (operator-confirmed)

**Option A — nullable flag on `Location`.** New field `frost_exposed: bool | None = None`:
`None` = inherit from the site type (current behaviour), `True` = force frost-exposed,
`False` = force sheltered/indoor. Resolution:

```python
exposed = (
    location.frost_exposed
    if location is not None and location.frost_exposed is not None
    else site.type in OVERWINTERING_SITE_TYPES
)
```

`LocationType.is_indoor` stays a UI-only filter (not consulted by winter logic).
No data backfill required — `None` reproduces today's site-derived behaviour exactly.

## Work packages

### P1 — Backend: `frost_exposed` field on Location (model + schema + persistence + API)

- **Problem statement**: `Location` carries no outdoor/frost flag. Add `frost_exposed: bool | None = None` to the `Location` model, the `LocationCreate`/`LocationUpdate` (or equivalent) schemas, the ArangoDB repository read/write mapping, and the locations router so the value round-trips through the REST API. Add a versioned migration only if the migration framework requires field registration (Arango is schemaless; `None`-default means no data backfill).
- **Acceptance criteria**: Creating a location with `frost_exposed` ∈ {null, true, false} persists it; GET returns it; PATCH/update changes it; omitting it defaults to `null`. Existing locations read back `null` (inherit) with no behavioural change.
- **Touched files / artifacts**: `src/backend/app/domain/models/site.py` (`Location`), `src/backend/app/api/.../locations/schemas.py`, locations router, `src/backend/app/data_access/arango/*location*`, migration under `src/backend/app/migrations/` (if needed).
- **Specialist**: fullstack-developer
- **Depends on**: none

### P2 — Backend: exposure resolution helper + winter-logic wiring

- **Problem statement**: Introduce a single `resolve_frost_exposure(location, site) -> bool` helper (co-located with `OVERWINTERING_SITE_TYPES` in `common/enums.py` or a domain helper) implementing the location-first/site-fallback chain, and route every winter decision through it: `overwintering_profile_service` (`site_overwinterable` ~:254, hardiness gate ~:839), `plant_instance_service` eager create/move triggers (~:430, ~:454), `season_state_service` materialisation gates (~:86, ~:208). Each call site must load the plant's `location_key` and pass the resolved `Location` (or `None`).
- **Acceptance criteria**: A plant on a `frost_exposed=True` location under an `indoor` site receives an overwintering profile / season state; a plant on a `frost_exposed=False` location under an `outdoor` site is excluded from winter logic; `frost_exposed=None` reproduces current site-type behaviour. Covered by backend unit tests (P5).
- **Touched files / artifacts**: `src/backend/app/common/enums.py` (or new helper), `overwintering_profile_service.py`, `plant_instance_service.py`, `season_state_service.py`.
- **Specialist**: fullstack-developer
- **Depends on**: P1

### P3 — Backend: fix BALCONY drift in batch tasks (secondary)

- **Problem statement**: `hardiness_tasks.py:26` (`_ZONE_SITE_TYPES`), `climate_tasks.py:31` (`_CLIMATE_SITE_TYPES`), `irrigation_tasks.py:32` (`_IRRIGATION_SITE_TYPES`) hard-code `("outdoor","greenhouse")` and skip balcony sites. Route them through the shared frozensets (`WEATHER_RELEVANT_SITE_TYPES` / `OVERWINTERING_SITE_TYPES`) so balcony sites are included, per the SSOT intent.
- **Acceptance criteria**: A `BALCONY` site is processed by hardiness-zone resolution, climate-normals, and irrigation climate correction (unit test asserts balcony no longer filtered out).
- **Touched files / artifacts**: `src/backend/app/tasks/hardiness_tasks.py`, `climate_tasks.py`, `irrigation_tasks.py`.
- **Specialist**: fullstack-developer
- **Depends on**: none (independent; can dispatch in parallel with P1)

### P4 — Frontend: outdoor/frost toggle in Location create/edit UI

- **Problem statement**: `LocationCreateDialog.tsx` (and the location detail/edit path) has no frost/outdoor control. Add a tri-state control (Inherit from site / Outdoor–frost-exposed / Indoor–sheltered) mapped to `frost_exposed` = `null`/`true`/`false`, with a descriptive helper text explaining the effect on overwintering, mobile-first, i18n DE/EN (`pages.*`, `enums.*`).
- **Acceptance criteria**: When creating/editing a location the user can pick frost exposure; the choice is sent to and returned from the API; the current value renders on edit; default is "Inherit from site". Descriptive text present in DE and EN.
- **Touched files / artifacts**: `src/frontend/src/pages/standorte/LocationCreateDialog.tsx`, location edit/detail component, API layer types, `src/frontend/src/i18n` translation files.
- **Specialist**: fullstack-developer
- **Depends on**: P1

### P5 — Tests (backend + frontend)

- **Problem statement**: Cover the resolution helper, the three winter-logic wirings, the batch-task balcony inclusion (backend, pytest), and the frontend toggle (vitest). Ensure `frost_exposed=None` regression-safety.
- **Acceptance criteria**: Backend + frontend suites green; new tests assert all three acceptance directions of P2 and the P3 balcony inclusion and the P4 toggle round-trip.
- **Touched files / artifacts**: `src/backend/tests/`, `src/frontend/src/**/__tests__` / `src/frontend/src/test`.
- **Specialist**: unit-test-runner
- **Depends on**: P1, P2, P3, P4

### P6 — Docs (end-user + fact/behaviour)

- **Problem statement**: Document the new per-location outdoor/frost flag and its effect on overwintering (DE-canonical + EN-mirror) per `spec/style-guides/DOCS.md`; update any standort/overwintering guide that states frost is site-only.
- **Acceptance criteria**: DE + EN docs describe the location frost flag and the inherit/override semantics; MkDocs strict build passes.
- **Touched files / artifacts**: `docs/` standort / overwintering pages.
- **Specialist**: mkdocs-documentation
- **Depends on**: P1, P2, P4

## Dependency ordering

`P1 → P2 ; P1 → P4 ; P3 (independent) ; {P1,P2,P3,P4} → P5 ; {P1,P2,P4} → P6`

Dispatch: **P1 + P3** (parallel, independent) → **P2 + P4** (parallel, both on P1) → **P5** → **P6**.

## Risks

- **Cross-tenant / ownership leaks** in the new location field write paths — mitigate: reuse existing tenant/ownership guards on the locations router; P2 wiring must not bypass the `_verify_*_ownership` checks the winter services already apply. Security-sensitive path → `code-security-reviewer` + `security-review` before PR.
- **`None` semantics regression** — a call site that treats `None` as `False` (or vice-versa) silently disables winter logic for existing outdoor locations. Mitigate: P2 helper is the only place resolving `None`; P5 asserts the `None` legacy direction explicitly.
- **Frozenset drift re-emerging** — P3 must consume the shared frozensets, not add a fourth hard-coded tuple. Mitigate: reviewer checks no new literal site-type tuple is introduced.
- **Frontend tri-state ↔ nullable mapping** — `false` vs `null` conflation in the form. Mitigate: explicit three-way control, P5 vitest round-trip test.

## Open questions

- none (design confirmed as Option A by operator; requirements gate overridden — see below).

## Requirements gate

No `project/requirements/` artefact meets `τ_high`. **Operator override recorded**: issue #706 was co-authored with the operator and already carries as-is analysis (file:line), the gap, a confirmed design direction (Option A), and testable acceptance criteria — it functions as the confirmed requirement. `requirements-elicit` skipped by explicit operator decision.

## Dispatch log

- 2026-07-21 P1 dispatched to fullstack-developer — `Location.frost_exposed: bool|None` added; round-trips via CRUD; no migration (None inherits). Commit 854ea56fb.
- 2026-07-21 P2 dispatched to fullstack-developer — `resolve_frost_exposure` engine + wired overwintering/plant_instance/season_state; tenant-guarded location loads. Commit 79cfacdc1.
- 2026-07-21 P3 dispatched to fullstack-developer — three batch tasks route through `WEATHER_RELEVANT_SITE_TYPES`; balcony no longer skipped. Commit 2a63b9b39.
- 2026-07-21 P4 dispatched to fullstack-developer — tri-state frost-exposure select in location create/edit UI, DE/EN. Commit a3284be06.
- 2026-07-21 UI review dispatched to frontend-usability-optimizer — field regrouped, helper text tightened, panel desc extended. Commit 17ad2cf36.
- 2026-07-21 Security review dispatched to nolte-engineering:code-security-reviewer — agent stalled (watchdog); orchestrator completed the critical thread: found the location tenant-guard was inert (locations persist tenant_key=""). Fix dispatched to fullstack-developer — guard re-anchored on `location.site_key == plant.site_key`. Commit 0549d6588.
- 2026-07-21 P5 dispatched to unit-test-runner — 14 resolver + 4 service (incl. AC-1 regression anchor) + frozenset + 4 frontend cases; backend 42/42, frontend 11/11 green. Commit ef68129aa.
- 2026-07-21 P6 dispatched to mkdocs-documentation — DE/EN docs for the location frost flag (in progress).
- Pending verify: quality-gate, security-review skill on final diff, pull-request-create (Closes #706).
