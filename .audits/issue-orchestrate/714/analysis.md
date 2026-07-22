---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: 714
classification: "bug"
secondary-classes: []
route: "direct"
status: draft
created: "2026-07-22"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #714 — Location update cannot reset a nullable field (frost_exposed) back to inherit/null (follow-up to #706)
- **URL**: https://github.com/nolte/kamerplanter/issues/714
- **Labels**: enhancement, backend, frontend
- **Linked items**: follow-up to #706/#709 (merged). No open PR (the "#715" search hit is the #713 PR, unrelated).
- **Prior art checked**: `plant_instance_repository.update` and `glossary_repository` already implement the null-preserving pattern (`exclude_none=False` + `keep_none=False`); `attachment_repository` uses AQL `OPTIONS {keepNull:true}`. Location update uses the generic `_update_doc` (`exclude_none=True` + Arango merge) — the root cause.

## Classification

- **Primary class**: bug
- **Rationale**: the tri-state "inherit" option the #706 UI offers does not persist — a stored `frost_exposed` value cannot be reset to null. A correctness defect in the update contract, not a new capability.

## Scope

- **In scope**: an explicit `frost_exposed: null` on the location update **clears** the field so it reads back as `None` (inherit from site type), completing the already-full-replace PUT contract. Remove the now-obsolete "known limitation" doc note.
- **Out of scope**: introducing a PATCH endpoint / partial-update semantics (Option B, rejected); changing the base `_update_doc` for all repositories (blast radius avoided — fix scoped to the location update); any change to `resolve_frost_exposure` or the season/overwintering consumers (they already treat `None` as inherit).

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome (location update honours explicit null), one PR strand, no roadmap item. One repository method + tests + a doc-note removal.

## Design decision (operator-confirmed)

**Option A — `keep_none=False` null-preserving update.** Give the location update
its own null-preserving persistence, mirroring the existing
`plant_instance_repository.update` pattern: dump with `exclude_none=False` and call
`collection.update(..., keep_none=False)` so an explicit `null` removes the
attribute (which then reads back as the Pydantic default `None` = inherit). The PUT
is already full-replace (`LocationCreate` body, no `exclude_unset`) and the frontend
already sends `frost_exposed` explicitly (`LocationDetailPage.tsx:305`), so this only
makes the repository honour the replace the contract already implies — no endpoint,
schema, or frontend change.

## Work packages

### P1 — Backend: null-preserving location update

- **Problem statement**: `SiteService.update_location` → `site_repository.update_location` (`data_access/arango/site_repository.py:121`) delegates to the generic base `update`/`_update_doc`, which dumps with `exclude_none=True` and does a `collection.update` merge (Arango default `keepNull=true`), so an explicit `null` is dropped and the stored value survives. Give the location update its own persistence mirroring `plant_instance_repository.update` (`plant_instance_repository.py:47-57`): `model_dump(by_alias=True, exclude_none=False, mode="json")`, pop `_key`/`created_at`, set `updated_at`, `collection.update({"_key": key, **data}, return_new=True, keep_none=False)`, reconstruct via `_from_doc`. Keep the `NotFoundError` (1202) handling equivalent to the base.
- **Acceptance criteria**:
  - After a location has `frost_exposed = true|false`, an update sending `frost_exposed = null` persists it as absent → GET returns `frost_exposed = null` (inherit); the plant's winter logic falls back to the site type.
  - `true ↔ false` and setting a value still work.
  - Other nullable fields sent as null (e.g. `tank_key`, `orientation`) are likewise cleared (consistent full-replace PUT semantics).
  - Non-null fields (`name`, `area_m2`, `light_type`, `irrigation_system`, `lights_on/off`) round-trip unchanged.
  - **No regression on computed fields**: `site_key`, `depth`, `path`, `parent_location_key` are written exactly as the current update writes them (the `exclude_none` change must not corrupt them — they are non-null today and stay so). Confirm parity; do not attempt to fix any pre-existing depth/path behaviour here.
- **Touched files / artifacts**: `src/backend/app/data_access/arango/site_repository.py` (`update_location`). No frontend change (FE already sends explicit null).
- **Specialist**: fullstack-developer
- **Depends on**: none

### P2 — Tests (backend)

- **Problem statement**: cover the reset-to-null path and the round-trip/parity guarantees.
- **Acceptance criteria**: pytest green; cases assert (a) `true → null` clears to inherit (read-back `frost_exposed is None`); (b) `true ↔ false` works; (c) another nullable field clears on null; (d) non-null fields round-trip; (e) `site_key`/`depth`/`path` unchanged by an update; existing location/site repo + router tests stay green.
- **Touched files / artifacts**: `src/backend/tests/unit/data_access/arango/` (site repository), and the locations router test if one exists.
- **Specialist**: unit-test-runner
- **Depends on**: P1

### P3 — Docs

- **Problem statement**: #706 documented this as a "known limitation" warning in the locations guide. Now fixed — remove/replace that warning (DE-canonical + EN-mirror) so the docs don't describe a resolved constraint.
- **Acceptance criteria**: the "cannot reset to inherit" warning is gone/updated in `docs/{de,en}/user-guide/locations-substrates.md`; `mkdocs build --strict` passes.
- **Touched files / artifacts**: `docs/de/user-guide/locations-substrates.md`, `docs/en/user-guide/locations-substrates.md` (and any other page that repeated the caveat).
- **Specialist**: mkdocs-documentation
- **Depends on**: P1

## Dependency ordering

`P1 → P2 ; P1 → P3`. Dispatch P1, then P2 and P3.

## Risks

- **Over-clearing computed fields.** `exclude_none=False` + `keep_none=False` writes the full model; `depth`/`path`/`site_key` must not be corrupted. They are non-null today, so parity is preserved — P2 asserts it. (A pre-existing depth/path recompute-on-update question, if any, is out of scope.)
- **Full-replace clears omitted nullable fields.** With the frontend sending the full form this is correct; a hypothetical API client relying on partial-merge PUT would see nullable fields cleared. This is HTTP-correct PUT semantics and the contract was already full-replace at the schema level — accepted, noted in the PR.
- **Tenant/ownership.** Update already gates via `_verify_location_tenant`; unchanged. Low security surface — a light diff-scoped check suffices, not a full audit.

## Open questions

- none (Option A confirmed; requirements gate overridden — issue authored in-session with the operator, carries problem/root-cause/AC).

## Requirements gate

No `project/requirements/` artefact. **Operator override recorded**: #714 authored in-session with the operator with root-cause and acceptance criteria. `requirements-elicit` skipped by explicit operator decision.

## Dispatch log

- 2026-07-22 P1 dispatched to fullstack-developer — `_LocationRepository.update` (exclude_none=False + keep_none=False, 1202→NotFoundError), mirrors plant_instance pattern; base untouched. 23 site/location tests green. Commit 5630775b9.
- 2026-07-22 Security check dispatched to nolte-engineering:code-security-reviewer — tenant isolation intact, no field over-clearing, no injection; no PR-introduced findings. Noted a pre-existing, out-of-scope info item: PUT does not re-verify the new body.site_key against the tenant (candidate separate issue).
- 2026-07-22 P2 dispatched to unit-test-runner — 14 cases (reset-to-null, true↔false, other nullable clears, non-null round-trip, computed-field parity, NotFound, keep_none=False assertion); 969 data-access tests green. Commit <P2>.
- 2026-07-22 P3 dispatched to mkdocs-documentation — replaced the #706 "known limitation" warning with a tip (DE+EN); mkdocs --strict exit 0.
- Pending verify: full backend suite as quality gate, pull-request-create (Closes #714).
