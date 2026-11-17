# Requirements — Multiple dashboards, views and care widgets (#2502)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Interview conducted 2026-11-17 with the operator (German); artifact in English.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
Audit basis (2026-11-17): REQ-045 v1 implemented — one layout per user in
`UserPreference.dashboard_layout` (schema_version 2, user_preference.py:13-98),
user-global not per tenant (user_preferences/tenant_router.py:4-5), no config
validation (user_preference_service.py:18-40), catalog drift FE/BE
(dashboardWidgetCatalog.ts vs dashboard_widget_catalog.py), 10/15 widgets on
GenericWidget, multi-instance possible in the model but not offered in the UI.
-->

## Bounded context

- **What (first release of epic #2502):** the foundation (versioned server-side model for multiple dashboards with multiple views, migration of today's single layout, server-side widget config validation, FE/BE catalog alignment, the widget contract), **A** dashboard and view management, and **B** care widgets with real data and direct actions.
- **For whom:** every signed-in user; anonymous light-mode users with local storage as today.
- **Out of scope (later):** the five themed templates (houseplants, balcony, vegetable garden, greenhouse, hydroponics); sensor/Home Assistant widgets (only the widget contract prepares them); sharing dashboards or publishing a tenant default (REQ-045 phase 2); a widget marketplace, user JavaScript, a free pixel canvas.
- _source_: Q1 "A,B", Q2 "passt".

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `8` (6 used)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` (final teach-back Q6 confirmed)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification (resolved) | Q4, Q5, Q6 teach-back |
| `non_functional` | yes | 0.8 | specification | responsive/a11y as today (Q6) |
| `constraints` | yes | 0.85 | specification (resolved) | Q3 "A" tenant scope; limits Q4 |
| `domain_objects` | yes | 0.85 | interpretation | dashboard → views → widget instances + placements (Q4) |
| `actors` | yes | 0.9 | specification | Q2 |
| `acceptance_criteria` | yes | 0.8 | specification | epic AC narrowed by Q2, Q6 |
| `edge_cases` | yes | 0.8 | specification | last dashboard/view, default deletion, unknown widget, invalid config (Q4, Q6) |
| `scope_boundaries` | yes | 0.9 | specification (resolved) | Q2 |

Self-consistency (k=2) diverged on the core motivation (four readings → Q1), on the release cut (templates in/out → Q2) and on the tenant scope (three models → Q3).

## Requirements

- **R1** — Dashboards SHALL belong to a user within a tenant (REQ-045 §2); WHEN a user opens the dashboard in a tenant for the first time after the change, the backend SHALL migrate today's single layout into a first dashboard with one view in that tenant.
  - _dimension_: `constraints`, `domain_objects` · _status_: `confirmed` · _source_: Q3 "A", Q6
- **R2** — The persisted model SHALL be a versioned schema (v3): dashboard {name, order, is_default} → 1..n views {name, order} → widget instances {instance_id, widget_key, config} with placements per breakpoint (lg/md/sm); one user's dashboards SHALL not be readable or writable by another user.
  - _dimension_: `domain_objects`, `constraints` · _status_: `confirmed` · _source_: Q4, Q6
- **R3** — The dashboard page SHALL offer a dashboard selector and tabs for the views (scrollable tabs or a select on mobile), addressable as `/dashboard/<dashboard>/<view>`; opening the dashboard SHALL show the default dashboard's first view.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q4 "passt"
- **R4** — Users SHALL create, rename, duplicate, delete and reorder dashboards and views; deleting SHALL ask for confirmation; the last dashboard and the last view of a dashboard SHALL not be deletable (only resettable); deleting the default dashboard SHALL make the first remaining one the default.
  - _dimension_: `functional`, `edge_cases` · _status_: `confirmed` · _source_: Q4
- **R5** — A user SHALL have at most 10 dashboards per tenant and 10 views per dashboard.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Q4
- **R6** — A new dashboard SHALL start empty or as a copy of today's default for the user's experience level.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q2, Q4
- **R7** — Widgets SHALL be addable directly on the dashboard from a searchable, categorised catalog, including several instances of the same type.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q2, Q6
- **R8** — Every widget SHALL declare a configuration schema in one catalog shared by frontend and backend; the UI and the server SHALL validate instance config against it, and the server SHALL reject invalid config with 422; the FE/BE catalog drift SHALL be removed.
  - _dimension_: `constraints`, `non_functional` · _status_: `confirmed` · _source_: Q2 foundation, Q6
- **R9** — WHEN a stored widget is unknown or its module is hidden, the dashboard SHALL show a "not available" placeholder with a remove action instead of dropping it silently.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q6
- **R10** — `tasks_today` SHALL show due and overdue tasks with plant/location, due date and urgency (overdue highlighted), allow marking a task done and open it on tap; settings: location filter, limit, include overdue.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q5 "passt!"
- **R11** — `care_reminders` SHALL show watering, fertilising and repotting of the next days with plant photo/name and due date, allow confirming ("watered"/"done") and snoozing as in REQ-022; settings: location filter, care type, time range (today/3/7 days).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q5
- **R12** — `active_plants_summary` SHALL show counts per phase or location and plants needing action, linking to the plant or the filtered list; setting: grouping.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q5
- **R13** — Care actions SHALL use the existing backend APIs; no care logic SHALL be duplicated in the frontend; every widget SHALL have meaningful empty, loading and error states.
  - _dimension_: `constraints`, `edge_cases` · _status_: `confirmed` · _source_: Q5, epic
- **R14** — `plant_grid` SHALL be part of the default from the beginner level.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q5
- **R15** — Desktop, tablet and mobile SHALL stay usable with the existing keyboard/menu alternatives to drag and drop and 48 px touch targets.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: Q6
- **R16** — Anonymous light-mode users SHALL get the same model in local storage, migrated to the server after signup.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q4 point 6
- **R17** — REQ-045 (phase 2 → v2, tenant scope, `config_schema`), REQ-009 and the user documentation SHALL be updated.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Q6

- **R18** — Dashboards SHALL be stored in a new collection `dashboards` (one document per dashboard, `tenant_key` + `user_key`); REQ-045's "no new collections" is amended.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: revisit 2026-11-17 decision 1 "ja"
- **R19** — The migration SHALL be lazy: a read derives the first dashboard from today's layout without writing (#1461), the first write materialises it; a `null` layout stays "level default" and keeps following level changes.
  - _dimension_: `constraints`, `edge_cases` · _status_: `confirmed` · _source_: revisit decision 2
- **R20** — `plant_grid` joins the level default from beginner; users without a stored layout see it immediately (intended change); R1's "unchanged" applies to stored layouts.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: revisit decision 3
- **R21** — Unknown or module-hidden widget instances SHALL be kept on save (not dropped), hidden in read mode and shown as a placeholder with remove in edit mode; invalid config of a known widget SHALL be rejected with 422; REQ-045 scenarios 3 and 5 are amended.
  - _dimension_: `edge_cases`, `constraints` · _status_: `confirmed` · _source_: revisit decision 4 (refines R9)
- **R22** — Every member including viewers SHALL manage their own dashboards (personal view configuration, not tenant data); REQ-045 §4 is amended; tenant-bound API keys stay excluded (`require_account_principal`).
  - _dimension_: `actors` · _status_: `confirmed` · _source_: revisit decision 5
- **R23** — Dashboards SHALL be excluded from the tenant archive, deleted on tenant erasure and when the membership ends, and included in the user's GDPR export.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: revisit decision 6
- **R24** — The settings tab SHALL become a link "edit dashboards"; management happens only on the dashboard; F-11 precedes F-23, which then owns `dashboard-personalization.md`.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: revisit decision 7
- **R25** — An unknown or deleted `/dashboard/<d>/<v>` SHALL show the 404 page with a link to the default dashboard (UI-NFR-005 R-018).
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: revisit decision 8
- **R26** — The care-dashboard endpoint SHALL gain location, photo and time range; each widget instance SHALL load its own data with its filters; "needs action" = an overdue task or an overdue care reminder; care tasks SHALL not appear in `tasks_today` (#508); viewers SHALL see no action buttons.
  - _dimension_: `functional`, `actors` · _status_: `confirmed` · _source_: revisit decision 9
- **R27** — F-24 SHALL only consume the task and care APIs and be re-checked if F-9 changes their contracts.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: revisit decision 10

## Surviving assumptions / open risks

- **Revisit 2026-11-17:** the consistency check of F-22..F-24 found the storage/migration constraints (#1461, unique user index, erasure/export classification), the plant_grid default conflict, the REQ-045 scenario conflicts, roles, the F-11 overlap, URL errors and the care data sources; the operator accepted all ten recommendations (R18–R27).

- **Per-tenant migration:** a user in several tenants gets today's layout copied into each tenant on first access; later edits diverge per tenant — intended by R1.
- **Widget limit per view:** kept as today if one exists; not measured. `assumed`.
- **Snooze/confirm endpoints:** established — `care_reminders/router.py:143,173`, task complete `tasks/tenant_router.py:749`.
- **Templates later:** the five themed templates (epic workstream 6) need their own roadmap item after this release.
