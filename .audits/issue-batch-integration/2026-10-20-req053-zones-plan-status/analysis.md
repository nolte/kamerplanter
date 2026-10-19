# Group 2026-10-20-req053-zones-plan-status (transient - removed before the bundle merges)

- Group id: `2026-10-20-req053-zones-plan-status` (partition record G-A, `.audits/issue-backlog-partition/2026-10-19.md`)
- Tier: 2 (one repository, one strand). Mode: A (one integration branch, ordered commits, no sub-branches).
- Logical change: extend the irrigation-zone backend (REQ-053 wave 7) with plan/export integration, status and watering
  round, technical coupling and demand calculation.
- Authorisation: the dispatching session's task statement, covering all four members in order
  (`authorised_by: operator task of 2026-10-20 / group G-A`).
- Admitting predicate: dependency chain (#2468 -> #2469 -> #2470, #2471) and shared touch surface
  (`irrigation_zone_service.py`, `garden_plan_*`). Cluster kind: class cluster of "WP 7.x backend", re-checked against
  the live issues: all four are OPEN, `feat`, bounded.

## Members

| # | WP | Order | Result |
|---|----|-------|--------|
| 2468 | 7.2 zones in read model, export, import | 1 | implemented |
| 2469 | 7.3 status, log-watering, allocation, last_watered_at | 2 | implemented |
| 2471 | 7.5 demand calculator | 3 (needs 7.3) | implemented |
| 2470 | 7.4 coupling (actuator, HA flow rate, scope technical) | 4 (needs 7.3) | implemented |

Members were implemented inline in the orchestrating context, not through nested `issue-orchestrate` runs (the run
was itself delegated and a nested skill chain would have lost the shared state of one strand).

## Findings against the issue bodies

- #2470 names `require_admin_scope` (`common/auth.py:817`) as the gate. It is a router dependency and the PATCH
  carries both technical and ordinary fields, so the predicate lives in the service (`_require_technical`), as the
  issue itself says ("predicate in the service"); the route keeps `require_permission`.
- #2469 lists "Rain - skipped" under the placeholders (#2466 item 2) but not under What/Acceptance; it needs a
  third write route and its consumer is WP 7.7. Not delivered here.
- #2471 "x planted area of the bed": REQ-037 stores the area it computed with on the demand (`area_m2`, the bed's
  area); that stored value is used. A bed with several runs counts once (the larger litres), not by area share.
- `Location.irrigation_system` defaults to `manual`, so the conflict hint (placeholder item 3) fires for a `drip`
  zone over every bed that kept the default.

## Cross-member dependency order and shared touch surface

7.2 (plan/export/import) -> 7.3 (status, round) -> 7.5 (demand into the status) -> 7.4 (coupling into the consumption).
Shared: `domain/services/irrigation_zone_service.py`, `domain/models/irrigation_zone.py`, `api/v1/irrigation_zones/*`,
`data_access/arango/irrigation_zone_repository.py`, `garden_plan_service.py`.

## Completeness matrix (cell = change : proving check)

| Surface | 7.2 | 7.3 | 7.4 | 7.5 |
|---|---|---|---|---|
| Domain model | ExportZone, PlanBatchWrite.zone_* : test_garden_plan_zones.py | CareEvent.allocation, ZoneWateringInput : test_irrigation_zone_watering.py | coupling in IrrigationZone : test_irrigation_zone_coupling.py | demand calculator : test_irrigation_zone_demand_calculator.py |
| Service | read model, import : test_garden_plan_zones.py | log_watering, zone_status | patch/create coupling | zone_status demand + hints |
| Repository (Arango) | _insert_zones/_delete_zones : tests/integration/test_garden_plan_import.py | watering_queries.py : tests/integration/test_irrigation_zone_wave7.py | zone_actuated_by edge, state changes : same | bed_demands : same |
| API | PlanZoneResponse : tests/api | 2 routes : tests/api/test_irrigation_zones_api.py | scope 403 : same | status fields : same |
| Tenant isolation | not applicable (no new route) | 2 cases in test_garden_plan_tenant_isolation.py | foreign actuator 422 : unit + integration | not applicable |
| Guards | not applicable | route pin 877 -> 879, rate-limit decision, slot_keys reader register | unresolved-receiver ceiling kept (2802 < 2804) | not applicable |
| Migration | not applicable (no migration; no new index) | not applicable | not applicable | not applicable |
| i18n / frontend | not applicable (backend lane; zone panel is WP 7.6/7.7) | enum `CareEventAllocation` has no UI yet | not applicable | hint codes are stable identifiers for the UI |
| Docs | not applicable (no UI change) | not applicable | not applicable | not applicable |

## Out of scope

Rain-skipped round (WP 7.7), zone panel UI (WP 7.6), W-017 cap, by_demand allocation, "water now" (GP-FR-115),
spec folding (#2493).
