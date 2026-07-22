---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: 713
classification: "feature-request"
secondary-classes: []
route: "direct"
status: draft
created: "2026-07-22"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #713 — Per-location season state: honour frost_exposed locations in the SeasonState lifecycle (follow-up to #706)
- **URL**: https://github.com/nolte/kamerplanter/issues/713
- **Labels**: enhancement, backend
- **Linked items**: follow-up to #706 / #709 (merged `7d3d7c6f5`); no open/linked PRs
- **Prior art checked**: #706 delivered `Location.frost_exposed` + `resolve_frost_exposure`; `season_state_service` gates at site granularity; `season_tasks` selects sites by type. No feature/roadmap item covers per-location season state.

## Classification

- **Primary class**: feature-request
- **Rationale**: extends existing season-state behaviour to honour a per-location signal — new capability, not a defect.

## Scope

- **In scope**: the SeasonState lifecycle (dormancy-care mode + season-triggered reminders) fires for a plant on a frost-exposed location under a non-frost site, and does **not** fire for a genuinely indoor plant on a mixed site — via **Option 1 (per-plant side-effect gating)**, keeping `season_states` 1:1 per site.
- **Out of scope**: per-location `season_states` collection / (site,location)-keyed states (Option 2 — larger, deferred); `frost_exposed`-null-reset (#714); any change to `resolve_frost_exposure` itself or the #706 plant-aware profile paths (already correct).

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome (season state honours location exposure), one PR strand, no new roadmap item. Confined to the season subsystem.

## Design decision (operator-confirmed)

**Option 1 — per-plant side-effect gating.** `season_states` stays 1:1 per site.
Three coupled changes:
1. **Site selection** widens: also evaluate sites that have ≥1 frost-exposed
   location, not only `OVERWINTERING_SITE_TYPES` sites.
2. **Site-level gate** becomes "site is frost-exposed **OR** has ≥1 frost-exposed
   location", so a mixed indoor site with a frost-exposed balcony location gets a
   season state.
3. **Per-plant gating**: side effects apply only to plants where
   `resolve_frost_exposure(plant_location, site)` is `True`. An indoor plant on a
   mixed site is never pushed into dormancy; a `frost_exposed=false` plant on an
   outdoor site is excluded.

`frost_exposed=None` / no location reproduces today's site-granular behaviour
bit-for-bit.

## Work packages

### P1 — Backend: location-aware season evaluation (site selection + site gate + per-plant gating)

- **Problem statement**: These three are one indivisible change to the season subsystem, sharing a `site-has-frost-exposure` predicate:
  - **Repo query** (new): `site_repository` gains a query returning the distinct `site_key`s that have at least one `Location` with `frost_exposed == true` (AQL over the locations collection). Reuse for both the task selection and the site gate.
  - **Task selection** (`tasks/season_tasks.py:35`): union the type-based `find_site_docs_by_types([OVERWINTERING_SITE_TYPES…])` set with the frost-exposed-location site set, so mixed indoor sites are evaluated. De-dup by `_key`.
  - **Site gate** (`season_state_service.evaluate_site_detailed` ~:95 and `get_state_for_site` ~:220): pass when `resolve_frost_exposure(None, site)` **OR** the site has ≥1 frost-exposed location. Introduce one helper (e.g. `_site_has_frost_exposure(site)`), used by both.
  - **Per-plant gating** (`_apply_side_effects` ~:128 via `_active_plants` ~:187): keep only plants where `resolve_frost_exposure(<plant's location>, site)` is `True`. Load each plant's location tenant/site-safely — reuse the #706 anchor `location.site_key == plant.site_key` (== `site.key`); a foreign/mismatched or absent location falls back to the site-type classification via the resolver. Do **not** load per-plant locations when the site itself is already frost-exposed and has no frost-exposed-location overrides that could *exclude* a plant — but a `frost_exposed=false` location on an outdoor site MUST still exclude that plant, so the per-plant resolve runs whenever any location override could change the outcome. Simplest correct form: always resolve per plant.
- **Acceptance criteria**:
  - A plant on a `frost_exposed=true` location under an `indoor` site receives the full SeasonState lifecycle (state advances; dormancy-care mode + season-triggered reminders fire).
  - A genuinely indoor plant (no override / `frost_exposed=false`) on a mixed site is **not** entered into dormancy.
  - A `frost_exposed=false` plant on an `outdoor` site is excluded from the side effects.
  - `frost_exposed=None` everywhere / no location reproduces current behaviour bit-for-bit (existing season tests stay green).
  - The evaluation task processes an indoor site that has a frost-exposed location.
- **Touched files / artifacts**: `src/backend/app/data_access/arango/site_repository.py` (+ interface `domain/interfaces/site_repository.py`), `src/backend/app/tasks/season_tasks.py`, `src/backend/app/domain/services/season_state_service.py`, possibly `src/backend/app/domain/engines/frost_exposure_resolver.py` (no change expected — reuse).
- **Specialist**: fullstack-developer
- **Depends on**: none

### P2 — Tests (backend)

- **Problem statement**: cover the new repo query, the widened task selection, the site gate, and the per-plant gating, plus the `None`-parity regression.
- **Acceptance criteria**: pytest green; new cases assert all AC directions of P1 (balcony plant on indoor site → dormancy; indoor plant on mixed site → not dormant; false-override on outdoor site → excluded; None → unchanged; indoor-with-frost-location site is evaluated).
- **Touched files / artifacts**: `src/backend/tests/unit/domain/services/test_season_*`, `src/backend/tests/unit/tasks/test_season_tasks.py`, repo test.
- **Specialist**: unit-test-runner
- **Depends on**: P1

### P3 — Docs (end-user)

- **Problem statement**: update the overwintering/season docs (DE-canonical + EN-mirror) to state that season-driven dormancy now follows a frost-exposed location, closing the #706-documented boundary.
- **Acceptance criteria**: DE + EN docs describe the location-aware season lifecycle; `mkdocs build --strict` passes.
- **Touched files / artifacts**: `docs/{de,en}/user-guide/overwintering.md` (and season-automation page if present).
- **Specialist**: mkdocs-documentation
- **Depends on**: P1

## Dependency ordering

`P1 → P2 ; P1 → P3`. Dispatch P1, then P2 and P3.

## Risks

- **Cross-tenant leak in per-plant location loading.** `season_tasks` iterates all tenants; the per-plant location load must anchor on `location.site_key == plant.site_key == site.key` (the #706 pattern), never trust an unfiltered read. Security-sensitive → `code-security-reviewer` + `security-review` before PR.
- **Over-materialisation.** Widening site selection could create season states for indoor sites that merely have a `frost_exposed=false` location (which must NOT trigger anything). The site gate must key on frost-*exposed* (true) locations, and per-plant gating must still exclude non-exposed plants. Covered by P2's "indoor plant on mixed site → not dormant" case.
- **Bit-parity regression.** The `None`/site-only path must stay identical; existing season tests are the guard.
- **Signal resolution for indoor sites.** A mixed indoor site may lack GPS/frost-dates; the SeasonSignalResolver's calendar/hemisphere fallback must still yield a season (no crash). Note for the implementer; assert no exception in P2.

## Open questions

- none (Option 1 confirmed by operator; requirements gate overridden — issue authored with the operator, carries problem/AC/directions).

## Requirements gate

No `project/requirements/` artefact. **Operator override recorded**: #713 was authored in-session with the operator and carries the problem statement, both design options, and testable acceptance criteria. `requirements-elicit` skipped by explicit operator decision.

## Dispatch log

<!-- appended during operation 5 -->
