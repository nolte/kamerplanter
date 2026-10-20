# Group pre-analysis: 2026-10-20-bed-templates (partition group G-B)

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch.

## Scope of this analysis

**Research question:** Do #2474 (WP 7.8) and #2475 (WP 7.9) form one group, and which parts of the code do their
guardrails touch?

**The group's single logical change, in one sentence:** add bed templates (model, catalogue, system templates) and the
place-template batch endpoint with its file-schema key (REQ-053 wave 7, WP 7.8 + 7.9).

**Out of scope:** the template picker UI (WP 7.10), saving a bed as a template, template exchange as JSON (GP-FR-173),
applying `recurring_task_templates` on placement (operator decision 2026-10-19), spec/docs updates of wave 7 (WP 7.27).

**Tier:** 2 - one repository, an additive API and an additive file-schema key inside `schema_version "1"`.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2474 | feature-request | dependency chain | `Location.template_key` and `place-template` need the catalogue: `GardenPlanService.place_template` reads `IBedTemplateRepository` |
| #2475 | feature-request | dependency chain + shared touch surface | issue body "Depends on: WP 7.8 (#2474)"; both change `data_access/arango/collections.py`, `dependencies.py`, the garden-plan tenant-isolation walk |

**Dependency ordering:** #2474 -> #2475.

**Shared touch surface:** `common/dependencies.py`, `api/v1/tenant_scoped/router.py`, `tests/integration/test_garden_plan_tenant_isolation.py`,
`tests/unit/test_route_consumers_check.py`, `tests/unit/guards/test_keyed_service_writes_take_the_tenant.py`.

**Body claims checked against the code:** #2474 names migration `v0100`; develop's last migration is `v0100`
(plant location backfill, #2508), so this group ships `v0101` (no other open PR carries a migration). #2474 says
"`ErasureEngine.ANONYMIZE_COLLECTIONS` + Art.-15 export" - confirmed necessary: the guard
`test_garden_plan_collections_are_in_the_erasure_cascade.py` and `test_privacy_engines.py` demand both. No asserted
cause to verify (feature requests).

## Mode decision

**Mode:** A - single strand. **Reason:** both members are required together to be useful and neither is likely to be
removed; the operator decisions of 2026-10-19 fix the open points.

## Structural finding

**Cluster shape:** neither - a dependency chain of two features.
**Process finding:** none.

## Plan approval

**Authorised by:** `2026-10-20-bed-templates/plan-approval` - the group record admitted by `issue-backlog-partition`
(2026-10-19.md, G-B) and the operator's dispatch of this lane.

## Completeness matrix

| Layer | #2474 | #2475 | Proving check |
|---|---|---|---|
| Model | `domain/models/bed_template.py` | `Location.template_key`, `ExportLocation.template_key`, `TemplateLocationData` | `test_bed_template.py`, `test_garden_plan_place_template.py` |
| Repository | `bed_template_repository.py` (owner-named writes) | - (`visible_template_keys` via the same repo) | `test_bed_template_repository.py` (real ArangoDB) |
| Service | `bed_template_service.py` | `GardenPlanService.place_template` | `test_bed_template_service.py`, `test_garden_plan_place_template.py` |
| API | 4 routes `/bed-templates` | `POST /sites/{key}/plan/place-template` | `tests/api/test_bed_templates_api.py` (role matrix, SR-010) |
| Migration | v0101: index + 9 system templates | - | `test_v0101_*.py`, `test_bed_template_repository.py::TestMigrationV0101` |
| Erasure / Art. 15 | `ErasureEngine` rule + `DataExportEngine` source | - | `test_garden_plan_collections_are_in_the_erasure_cascade.py`, `test_privacy_engines.py` |
| Tenant export (REQ-056) | `HYBRID_CATALOGUES`, `recurring_task_templates` reference | `locations.template_key` reference | `test_tenant_export_*`, `test_tenant_reference_keys_are_resolved.py` |
| Isolation | route walk cases + `TestBedTemplatesAreScopedToTheTenant` | `place_template` case + reference case | `test_garden_plan_tenant_isolation.py` |
| Guards | `BedTemplateService` in keyed-write guard | `place_template` in the anchored-writer list | `tests/unit/guards` |
| Route pin | +4 | +1 | `test_route_consumers_check.py` (884) |
| Rate limit | not applicable (reads / low-volume writes) | `rate_limit_plan_batch` reused, no new setting | `test_expensive_routes_carry_a_per_user_limit` |
| Frontend / docs | not applicable (WP 7.10 / 7.27) | not applicable | - |
