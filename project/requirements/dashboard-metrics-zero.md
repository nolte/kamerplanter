# Requirements — Dashboard metrics show hard 0 despite existing active plants

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back or
an authoritative user answer.
-->

## Bounded context

- **What:** The dashboard metrics area renders hard `0` for every cardinal count
  — "Aktive Pflanzen" (`plants_total` / `plants_active`), "Aufgaben heute"
  (`open_tasks_today`) and "Pflegeerinnerungen" (`care_reminders_due`) — **even
  when active plants exist**. Root cause (Explore, 2026-07-05): the
  `DashboardService` probes each metric source via `hasattr(...)` and silently
  falls back to `0`; **none** of the expected `count_*` / `list_*` repository
  methods is implemented anywhere, so the guards short-circuit **before** any DB
  access and the correctly-threaded `tenant_key` is never used. It is a
  **missing-implementation bug masked by defensive `hasattr` guards** — not a
  tenant-filter bug. The fix implements the missing tenant-scoped repository
  counts/lists and hardens the service so a future missing method can no longer
  silently collapse to `0`.
- **For whom:** Kamerplanter users (grower / viewer) reading the tenant-scoped
  dashboard overview (REQ-009). All counts are strictly tenant-isolated
  (SEC-001).
- **Scope (confirmed, expanded to all probed methods):** implement every method
  the service probes — `PlantInstanceRepository.count_for_tenant` /
  `count_active_for_tenant`; task-repo `count_open_due_on` / `count_overdue` /
  `list_upcoming`; care-reminder-repo `count_due_on`; tank-repo
  `count_below_threshold`. The eighth probed method, activity-repo `list_recent`,
  is **deferred** (see R5): there is no per-tenant activity event log to feed it,
  so `recent_activities` is an explicit empty section rather than a scan of the
  global activity-type catalog. All backend repos are already wired into
  `get_dashboard_service` (`common/dependencies.py:1058-1068`).
- **Out of scope (explicit):**
  - Frontend widget shell — the three tiles render correctly via
    `GenericWidget.tsx`; the payload is empty, not the renderer. This fix is
    **backend-first**.
  - WebSocket live fan-out, configurable widget grid persistence, per-user widget
    pinning (kept on the REQ-009 roadmap, per `dashboard_service.py:12-16`).
  - Interactive editing UI for the new `Tank.low_threshold_percent` field
    (tank-detail/edit form) — the count reads the per-tank default when unset;
    surfacing an edit control is an **abgegrenzter Folge-Scope**.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question
  budget = 8 (spec defaults; not overridden).
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` — every required dimension ≥ `τ_high` with an
  authoritative answer or code-derived self-consistency evidence, and no
  remaining candidate question has positive net EVPI.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation → resolved | Q1/Q2/Q4 authoritative answers + code (`dashboard_service.py`, `plant_instance_repository.get_survival_stats`) |
| `non_functional` | yes | 0.85 | interpretation | SEC-001 tenant-isolation + Q3 hardening (Protocol/ABC) authoritative answer |
| `constraints` | yes | 0.90 | interpretation | CLAUDE.md 5-layer + NFR-001/003 + `domain/interfaces/` precedent (`activity_repository.py`) |
| `domain_objects` | yes | 0.85 | specification → resolved | Q5(tank) authoritative answer; PlantInstance/Task/CareReminder/Tank/Activity models read directly |
| `actors` | yes | 0.90 | interpretation | tenant-scoped router `tenant_router.py:106-124`, `get_current_tenant` |
| `acceptance_criteria` | yes | 0.85 | specification | Q-regression taken as committed AC; teach-back on counting contract |
| `edge_cases` | yes | 0.80 | interpretation | empty-`tenant_key` reject precedent (`get_survival_stats:161-164`); Q4 overdue-care answer; Q3 no-silent-0 |
| `scope_boundaries` | yes | 0.85 | specification → resolved | Q2 (all 8) + Q5 (tank field) authoritative answers |

## Requirements

- **R1** — WHEN the dashboard summary is built for a tenant, the
  `PlantInstanceRepository` SHALL return `count_for_tenant` = the number of plant
  instances with `p.tenant_key == @tenant_key`, and `count_active_for_tenant` =
  the subset additionally satisfying `p.removed_on == null`.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Aktiv-Def:
    removed_on == null (alive)" + code self-consistency (survival-stats
    `terminated = removed_on != null`; lineage query line 83 `FILTER v.removed_on == null`)
- **R2** — WHEN counting open tasks, the task repository SHALL treat a task as
  "open" iff its `status ∈ {pending, in_progress}` (i.e. not `completed` / not
  `skipped`); `count_open_due_on(tenant, today)` SHALL count open tasks whose
  `due_date` falls on `today`, and `count_overdue(tenant, today)` SHALL count open
  tasks whose `due_date` is strictly before `today`.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: structural —
    `DashboardCounts` separates `open_tasks_today` from `overdue_tasks`; visible
    tile `tasks_today` slices to `{open_tasks_today, upcoming_tasks}` only
    (`tenant_router.py:_slice_summary_for`); `TaskStatus` enum
- **R3** — WHEN counting due care reminders, `count_due_on(tenant, today)` SHALL
  count reminders that are actionable now, i.e. due `today` **plus** overdue,
  because the dashboard carries a single `care_reminders_due` count with no
  separate overdue channel.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Care-Fälligkeit:
    Heute + überfällige (actionable)"
  - **Data-model amendment (implementation-verified 2026-07-05):** a care reminder
    has **no persisted, tenant-scoped, due-dated document** — `CareProfile` carries
    neither `tenant_key` nor `due_date`, and `CareDashboardEntry` is a transient
    live-computed view model. The only persisted, tenant-scoped, due-dated form is
    a `Task` with `category == care_reminder` (materialized by the care engine).
    `count_due_on` therefore counts the tenant's **open care-reminder tasks** with
    `due_date <= today`. A count over `care_profiles` would have been hard `0`
    (reproducing the very bug). **Intentional overlap:** because the existing
    user-facing task queue (`get_all_tasks`) does not partition `care_reminder`
    tasks out, a care-reminder task due today is counted in **both** the
    "Aufgaben heute" tile (R2, total open tasks) and the "Pflegeerinnerungen" tile
    (R3, the care subset). This mirrors existing app semantics (care reminders are
    a task subtype); the tiles read as "all tasks today" vs. "of which, care".
- **R4** — WHEN counting low tanks, `count_below_threshold(tenant)` SHALL, per
  tenant tank, take the most recent `TankState.fill_level_percent` and count tanks
  whose latest fill level is below that tank's `low_threshold_percent`; the
  `Tank` model SHALL gain a `low_threshold_percent` field (default 20%) so the
  threshold is per-tank configurable.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Tank-low: Neues
    low_threshold_percent-Feld pro Tank" (no prior tank-threshold concept exists in
    code)
- **R5** — WHEN building the upcoming-tasks list, `list_upcoming(tenant, today,
  window_end, limit)` SHALL return open tasks with `today <= due_date <=
  window_end` (service passes `today + 7d`), sorted by `due_date` ascending,
  capped at `limit`.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: service call
    signature + existing `get_all_tasks` ordering precedent
  - **`list_recent` / `recent_activities` deferred (review-verified 2026-07-05):**
    there is **no per-tenant activity event log** to feed a "recent activities"
    list. The `activities` collection is a global catalog of activity-type
    *definitions* (`tenant_key == ""`, fields `forbidden_phases` /
    `species_compatible` / `is_system` / `sort_order`), not a record of performed
    actions — a tenant-scoped scan of it returns `[]` dressed up as an implemented
    feature (the exact masking this change removes). `_recent_activities`
    therefore returns an explicit `[]` (documented deferral to the REQ-009
    roadmap); `activity_repo` stays wired for a future event-log source. No
    `list_recent` method is shipped.
- **R6** — WHERE any of these repository methods is tenant-scoped, the method
  SHALL filter `FILTER doc.tenant_key == @tenant_key` and SHALL reject an empty
  `tenant_key` with a `ValueError` before issuing any query (SEC-001 / SEC-B4),
  mirroring `get_survival_stats:161-164`.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: SEC-001
    invariant + Q3; plan "Tenant-Isolation (SEC-001)"
- **R7** — The `DashboardService` SHALL invoke the repository counts/lists
  through a typed interface (Protocol in `domain/interfaces/`) rather than silent
  `hasattr`→`0` probes. A **missing** required method SHALL surface as a loud
  error (an up-front `_require_methods` existence check, before the query call),
  while an error raised **while a present method runs** (including an internal
  `AttributeError`) SHALL be degraded per-section to `0`/`[]`. The two must stay
  distinguishable so a genuine runtime error never masquerades as a missing
  method, and vice-versa.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_:
    "hasattr-Härtung: Protocol/ABC in domain/interfaces"; refined by review
    finding #4 (a blanket `except AttributeError: raise` would 500 the whole
    dashboard on an internal `AttributeError`)
- **R8** — WHEN active plant instances exist for a tenant, the aggregated
  dashboard response SHALL report `plants_active > 0` (correct cardinality), and a
  regression test SHALL prove that (a) real active plants yield a non-zero count
  and (b) a missing repository method does **not** silently degrade to `0`.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_:
    plan Open Question 5, taken as committed AC (recommended by skill, accepted)
- **R9** — Each new `count_*` / `list_*` method SHALL be covered by a repository
  unit test asserting tenant isolation (a foreign-tenant record is **not** counted)
  and empty-`tenant_key` rejection.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_:
    SEC-001 cross-tenant test obligation (plan invariants)

## Surviving assumptions / open risks

- **`low_threshold_percent` default = 20 %** — `assumed`. Chosen as a documented
  default for the new per-tank field; the count uses it when a tank has no
  explicit value. Adjustable without changing the counting contract.
- **Latest-`TankState` resolution** — `assumed`. `count_below_threshold` needs the
  *most recent* `TankState` per tank (fill level lives on `TankState`, not
  `Tank`); the AQL must resolve newest-per-tank (e.g. `COLLECT tank_key … `
  max `recorded_at`). Interpretation detail resolved at implementation time from
  the tank-state read pattern.
- **Tank-field editing UI** — deferred. Surfacing `low_threshold_percent` in the
  tank-detail/edit form is out of scope now; if it is added, the frontend
  3-agent chain (UI-review → tests → docs) applies. The dashboard count works off
  the default meanwhile.
- **`edge_cases` at `τ_high` (0.80), not above** — the overdue/timezone boundary
  for "today" uses `now.date()` from the service clock (server/UTC); no per-tenant
  timezone handling is introduced. Accepted as-is (matches current service
  behaviour); revisit only if tenant-local day boundaries become a requirement.
