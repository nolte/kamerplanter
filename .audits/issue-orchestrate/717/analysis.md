---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: 717
classification: "security"
secondary-classes: []
route: "direct"
status: draft
created: "2026-07-22"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #717 — Location update does not re-verify body.site_key against the tenant (create/update asymmetry)
- **URL**: https://github.com/nolte/kamerplanter/issues/717
- **Labels**: bug, backend
- **Linked items**: surfaced by the #714/#716 diff-scoped security check (pre-existing item, out of scope there). No open PR.
- **Prior art checked**: `create_location` (router) already verifies `body.site_key` against the tenant; `update_location` does not. Confirmed against develop (post-#716).

## Classification

- **Primary class**: security
- **Rationale**: a tenant-authorization gap — the location update persists a client-supplied `site_key` without verifying the target site belongs to the caller's tenant. (Labelled `bug` on the issue; the primary orchestration class is `security` as it is an access-control defect.)

## Scope

- **In scope**: the location update (`PUT /locations/{key}`) re-verifies the incoming `body.site_key` against the caller's tenant before persisting, mirroring `create_location`. Reject a foreign/unauthorized `site_key`.
- **Out of scope**: recomputing `site_key`/`depth`/`path` from `parent_location_key` on update the way `create_location` does (a separate consistency concern); any change to the create path (already correct); the graph `CONTAINS` edge re-parenting.

## Route

- **Decision**: direct
- **Rationale**: one coherent access-control fix, one PR strand, no roadmap item. A single guard call + tests.

## The defect (grounded)

- `create_location` (`api/v1/locations/tenant_router.py:66`): `service.get_site(body.site_key, tenant_key=ctx.tenant_key)` — verifies the **new** site against the tenant. ✅
- `update_location` (`tenant_router.py:79-81`): `_verify_location_tenant(key, ctx, service)` verifies the **existing** location's site (`_verify_location_tenant` at `:17-21` checks `loc.site_key`), then builds `Location(**body.model_dump())` and calls `service.update_location(key, location)` — which persists `body.site_key` with **no** tenant check (`site_service.py:72-74` calls `get_location(key)` without `tenant_key`). ❌

## Work packages

### P1 — Backend: re-verify body.site_key against the tenant on update

- **Problem statement**: In the `update_location` handler, after building `location` from the body and before persisting, verify the incoming `site_key` belongs to the caller's tenant — mirror `create_location`: `service.get_site(location.site_key, tenant_key=ctx.tenant_key)` (raises the standard not-owned error). Keep the existing `_verify_location_tenant(key, ctx, service)` call (which guards the target location itself). Prefer the router-level mirror for consistency with `create_location`; if a service-level guard is cleaner, ensure all callers still pass the tenant. Do not change create; do not add `site_key`/`depth`/`path` recompute (out of scope).
- **Acceptance criteria**:
  - `PUT .../locations/{key}` with a `site_key` the caller's tenant does not own is rejected (same status the create path returns for a foreign site — 403/404), not persisted.
  - Updating a location while keeping (or moving to another of the caller's **own**) `site_key` still succeeds.
  - The create path and all other location fields are unchanged.
- **Touched files / artifacts**: `src/backend/app/api/v1/locations/tenant_router.py` (`update_location`); possibly `src/backend/app/domain/services/site_service.py` (`update_location`) if the guard lands service-side.
- **Specialist**: fullstack-developer
- **Depends on**: none

### P2 — Tests (backend)

- **Problem statement**: cover the authorization gap and the legitimate paths.
- **Acceptance criteria**: pytest green; cases assert (a) updating a location with a foreign-tenant `site_key` is rejected (not 200); (b) updating within the caller's own site(s) succeeds; (c) create-path behaviour unchanged; existing locations router/service tests stay green.
- **Touched files / artifacts**: the locations router/service test module (locate the existing `PUT /locations` coverage or add to the router test).
- **Specialist**: unit-test-runner
- **Depends on**: P1

## Dependency ordering

`P1 → P2`.

## Risks

- **Legitimate moves between own sites must still work.** The guard checks tenant ownership of the target site, not equality with the old site — a move within the tenant is allowed. P2 asserts this.
- **Error-status parity with create.** Use the same failure the create path raises for a foreign site, so clients see consistent behaviour. P2 asserts the reject status.
- **Security-sensitive path.** Verify via `code-security-reviewer` + the `security-review` skill on the diff before PR (operation 6).

## Open questions

- none (fix is the create-path mirror; requirements gate overridden — issue authored in-session from a security finding, carries root-cause + AC).

## Requirements gate

No `project/requirements/` artefact. **Operator override recorded**: #717 authored in-session from the #714/#716 security-check finding with root-cause, proposed fix, and acceptance criteria. `requirements-elicit` skipped by explicit operator decision.

## Dispatch log

<!-- appended during operation 5 -->
