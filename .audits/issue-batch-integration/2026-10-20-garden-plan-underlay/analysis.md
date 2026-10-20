# Group analysis: 2026-10-20-garden-plan-underlay (transient, removed before the bundle merges)

- Group id: `2026-10-20-garden-plan-underlay` (partition record: `.audits/issue-backlog-partition/2026-10-19.md`, group G-E)
- Tier: 2. Mode: A (one strand; the frontend member consumes the backend member's contract, no removable member).
- Authorisation: `authorised_by: G-E/partition-approval` (operator confirmed #2466 item 6; caller dispatched the group).
- One-sentence change: add the background underlay of the garden plan - storage, calibration and PDF opt-in on the backend, upload and two-point calibration in the editor (REQ-053 wave 7, WP 7.14 + 7.15).
- Question the research answered: where does the underlay live, how does it reach the PDF without breaking the SVG allowlist, and what keeps it out of every export?

## Members

| # | WP | Predicate | Class | Specialist |
|---|----|-----------|-------|------------|
| 2480 | 7.14 | dependency chain (first) | feature | backend implementation (this run) |
| 2481 | 7.15 | dependency chain (consumes 2480) | feature | frontend implementation (this run) |

Order: #2480 then #2481. Cluster kind: class cluster of none; a feature pair (no structural cause to find).

## Claims checked against the code

- `SitePlan` at `domain/models/site.py` ~96 and `AttachmentCategory` at `common/enums.py` ~1502: as the issue says.
- `PrintEngine` already has a `RestrictedURLFetcher` (data: and template tree only); the issue's "restrictive url_fetcher (#2434 item 4)" is already in place, so the PDF path only needs a `data:` URI. Body claim confirmed, no contradiction.
- The SVG writer forbids `<image>`/`href` by design (SR-015), so the underlay is NOT drawn into the SVG: the PDF template lays it as a second `<img>` under the plan figure. The SVG route never carries it.
- `ExportPlanSettings` has explicit fields; `plan.underlay` cannot leak into the JSON export (pinned by test).
- CSP `img-src 'self' data: blob:` (`src/frontend/nginx-security-headers.inc`): the editor loads the picture through the authenticated client as a `blob:` URL; no CSP change needed.

## Completeness matrix (cells: change -> proving check)

| Layer | Change | Check |
|---|---|---|
| Model | `SiteUnderlay` / `UnderlayCalibration`, finite numbers only | `tests/unit/domain/models/test_site_underlay.py` |
| Enum + settings | `AttachmentCategory.garden_plan_underlay`, photo MIME class, erasure scope | `test_photo_types_the_pipeline_admits_are_strippable.py`, privacy tests |
| Repository | `set_site_underlay` (tenant-guarded merge, outside the revision) | `tests/integration/test_garden_plan_repository.py` |
| Service | `GardenPlanUnderlayService`, `*, tenant_key` without default | unit + `test_keyed_service_writes_take_the_tenant.py` |
| API | `PUT|DELETE /sites/{key}/plan/underlay`, `underlay` in the plan read model, `underlay=true` on the PDF | `tests/api/test_garden_plan_underlay_api.py` |
| Tenancy | route walk + `reference.not_found` case + falsification | `tests/integration/test_garden_plan_tenant_isolation.py` |
| Export | never in JSON/SVG; PDF only on request | unit + API tests |
| Deletion | superseded attachment deleted through the holder-asking delete | `test_stored_object_deletes_ask_for_other_holders.py` |
| Pins | route count 885 -> 887; unresolved receivers below ceiling | `test_route_consumers_check.py`, `test_write_route_gates.py` |
| Frontend | calibration maths, dialog (lazy), renderer layer, layer registry, i18n DE/EN | vitest (calibration 400 px / 4.0 m = 100 px/m), axe |
| Migration | not applicable: additive optional field on an existing embedded object | - |
| Rate limits / settings classification | not applicable: existing `rate_limit_plan_batch` reused; one MIME override setting added (empty default) | `tests/e2e_selftest` |
| Export inventory / Art. 15 | `plan.underlay` rides inside the site document; no new collection | privacy inventory tests |

## Deferred / out of scope

- Deleting a site does not yet delete its underlay attachment (it goes with the tenant erasure).
- E2E for this wave is WP 7.26.
