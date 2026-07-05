# Requirements — Issue #367: Docs-audit follow-up code discrepancies

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (methodology spec shipped in claude-shared).
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back or
an authoritative decision by the user.
-->

## Bounded context

- **What:** Close the 14 code-side discrepancies collected in
  [#367](https://github.com/nolte/kamerplanter/issues/367), surfaced during the
  documentation-reconciliation waves (#354 + #357/#363/#364/#366). The docs
  already describe the *intended* observable behaviour with honest "noch nicht
  implementiert" markers; this working copy brings the **code** up to that
  documented target so each marker can be removed and every #367 checkbox is
  independently verifiable. Findings are code-verified against `develop`
  (2026-07-05) with exact file:line locations in
  `.resume/issue-367-docs-audit-followup/plan.md`.
- **For whom:** End users hitting the affected flows (importers, notification
  recipients, task schedulers, harvesters), and the maintainers who own the
  reconciled docs. The security item (#8) protects every tenant from a global
  write by any authenticated user.
- **Scope:** All 14 items, delivered as **4 risk-prioritised PRs on one feature
  branch** (`fix/issue-367-docs-audit-followup` → `develop`): PR1 critical
  (#8 admin-guard, #4 e-mail key mismatch, #1/#2/#3 import), PR2 tasks (#6/#7),
  PR3 logic (#9/#14), PR4 enrichment/frost/routing (#10/#11/#12/#13).
- **Out of scope:** Routing the four KI/Glossar/Diagnose/Aquaponik scaffolds
  (REQ-031/035/036/026) — closed as deliberately deferred, non-MVP (Q4). Any
  documentation edits beyond removing "not yet implemented" markers once the
  backing code lands (docs already reconciled by #354ff). No enum *removals*
  (additive-only, per the Enum-Retirement alt-volume-crash trap).

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `7` (spec defaults; budget = the 7 plan open questions, all answered)
- `U_gate = min_d c_d` over required dimensions = **0.78** (driven by `edge_cases`)
- Termination: **operator-accepted proceed (§H override).** All decision-bearing
  dimensions (`functional`, `scope_boundaries`, `constraints`, `domain_objects`,
  `non_functional`) are ≥ `τ_high` on authoritative answers to the 7 plan
  questions. The single below-`τ_high` cell (`edge_cases` = 0.78) is residual
  *interpretation* uncertainty whose remedy is code inspection **inside PR1–PR3**,
  not a further user decision; no remaining question has positive net EVPI. The
  user directed proceeding once at threshold; the residual is surfaced below as a
  named risk rather than silently treated as understood.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | specification | Authoritative answers to all 7 plan questions (AskUserQuestion selections) + code-verified findings in plan |
| `non_functional` | yes | 0.88 | interpretation | Plan invariants: 5-layer (NFR-001), quality-gate green, #8 rejects non-admin with 403 + cross-tenant negative test (NFR-015) |
| `constraints` | yes | 0.90 | interpretation | CLAUDE.md guardrails: English source (NFR-003), additive-only enums, versioned migration framework (NFR-016/ADR-005), per-cluster PRs |
| `domain_objects` | yes | 0.90 | interpretation | Every one of the 14 findings code-verified with exact file:line in the plan |
| `actors` | yes | 0.85 | interpretation | auth-user vs platform-admin (#8), importer (#1–#3), notification recipient (#4/#5), HA consumer (#11) |
| `acceptance_criteria` | yes | 0.85 | specification | Each #367 checkbox independently verifiable; docs markers removed on landing; deferred items justified in issue |
| `edge_cases` | yes | 0.78 | interpretation | `k=2` self-consistency: divergent readings survive on harvest-complete semantics (#14: last-batch vs immediate) and partial-harvest interplay; RRULE↔legacy-cron coexistence (#6); frost data source (#11) — resolvable by code inspection, not user question |
| `scope_boundaries` | yes | 0.92 | specification | Bounded context above: all 14, KI-scaffolds deferred (Q4), 4 PRs |

## Requirements

<!-- Each requirement in EARS/CNL form, tagged confirmed/assumed, with
     traceability to the authoritative decision / finding that produced it. -->

### Import (REQ-012)

- **R1** (#1) — WHEN an import job whose entity type is `CULTIVAR` is confirmed,
  the `ImportService` SHALL create `Cultivar` records via a real create function
  (not the `noop` fallback in `_get_create_fn`).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #367 item + Q1 (all 14 in scope)
- **R2** (#2) — WHEN species are imported, the `ImportService` SHALL persist all
  **17** CSV-template columns to their `Species` model fields (not only
  `scientific_name`/`common_name`/`description`); only `scientific_name` SHALL be
  required, the remaining columns optional/empty-tolerant. The exact
  column→field mapping SHALL be verified against the CSV template in PR1.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q "Alle 17 Template-Spalten 1:1 mappen"
- **R3** (#3) — WHEN the user selects the "update" duplicate strategy,
  `ImportService.confirm()` SHALL pass `find_fn`/`update_fn` to
  `confirm_import()` so existing records are updated (the engine already
  supports the update branch when `update_fn` is set).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #367 item + Q1

### Notifications (REQ-030)

- **R4** (#4) — The e-mail channel config keys SHALL be reconciled on the
  **canonical `email`/`digest`** keys: the frontend `NotificationSettingsTab`
  SHALL write `config.email`/`config.digest` (not `address`/`digest_mode`), and a
  **shared contract test** SHALL assert `CHANNEL_KEYS` parity between the FE
  writer and the BE reader so the mismatch cannot silently regress.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q "Frontend → email/digest" + Notification-Channels contract-test invariant
- **R5** (#5) — Apprise SHALL be declared as an `optional-dependencies` extra in
  `src/backend/pyproject.toml`; the `AppriseNotificationChannel` SHALL register
  only when the package is importable and report unavailable cleanly otherwise
  (no silent failure, no forced image bloat).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Q "Optional-Extra + Conditional-Register"

### Tasks (REQ-006)

- **R6** (#6) — WHEN a task recurrence is processed, the backend SHALL parse the
  frontend's RRULE format (`FREQ=…`) via `dateutil.rrule` instead of `croniter`;
  existing cron strings MAY be tolerated as legacy but RRULE is the canonical
  format (aligns with REQ-015 iCal-token).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q "Backend → RRULE"
- **R7** (#7) — `TaskCategory` SHALL **additively** include `watering` and
  `pest_control` (and any other categories the workflow/task-template editor
  emits); no existing enum value SHALL be removed (alt-volume seed-read crash
  trap).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #367 item + additive-only invariant

### Companion planting (REQ-028)

- **R8** (#8, SECURITY) — WHEN a non-platform-admin user POSTs
  `/companion-planting/compatible` or `/incompatible`, the system SHALL reject
  the write (403); only platform admins MAY write these global edges. Light-Mode
  (no platform tenant) SHALL bypass per the admin-gating pattern, and a
  cross-tenant negative test (NFR-015) SHALL cover the guard.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: #367 Decision E-1 + security-first plan guardrail
- **R9** (#9) — WHEN `PlantingRunService.create_plants` creates run batches, it
  SHALL run `CompanionPlantingEngine` + `CropRotationValidator` (as the
  single-plant path does), so neighbour/rotation checks are not bypassed for
  batch creation.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #367 item + Q1

### Enrichment (REQ-011)

- **R10** (#10) — The `Species` model + enrichment engine SHALL populate the
  `origin` field, and the frontend `TODO: REQ-001 v5.0 origin field — backend
  pending` markers SHALL be removed once the field is served.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #367 item + Q1

### Sensors / HA (REQ-005/018/039)

- **R11** (#11) — A backend task SHALL detect frost conditions and publish the
  `binary_sensor.kp_{location}_frost_warning` HA entity; the docs "noch nicht
  befüllt" marker SHALL be removed once the entity is backed. The frost data
  source SHALL be chosen during PR4 (weather-API / sensor threshold).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: #367 item + Q1

### Routing (REQ-025 / REQ-031/035/036/026)

- **R12** (#12) — `PrivacySettingsPage` SHALL be added as a `<Route>` in
  `AppRoutes.tsx` (its backing API is complete per Decision E-2).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q "Privacy routen"
- **R13** (#13) — The four `KIAssistentPage` / `GlossarPage` / `DiagnosePage` /
  `AquaponikPage` scaffolds SHALL NOT be routed; the #367 item SHALL be closed as
  **deliberately deferred (non-MVP)** with a recorded rationale in the issue.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q "KI deferred"

### Harvest (REQ-007)

- **R14** (#14) — WHEN a harvest is explicitly marked complete (a dedicated
  "Ernte abschließen" flag/action), the harvest flow SHALL transition the plant
  instance to `harvested` **via the phase engine** (`LifecycleEndReason.HARVESTED`,
  no raw state write, no backward transition), covering both the single-plant and
  the run-batch path. The first `create_harvest_batch` SHALL NOT auto-transition.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q "Expliziter 'Ernte abschließen'-Flag"

### Cross-cutting (delivery & quality)

- **R15** — Each fix SHALL preserve the 5-layer architecture (NFR-001, engines
  pure/testable), keep source code English (NFR-003), and land as its own
  risk-prioritised PR to `develop`; any data migration SHALL use the versioned
  migration framework (NFR-016/ADR-005), never ad-hoc. Each PR SHALL pass the
  quality-gate (ruff/eslint/tsc/pytest/vitest) green before `pull-request-create`.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan invariants + CLAUDE.md
- **R16** — WHEN a cluster's code lands, the corresponding #367 checkbox SHALL be
  independently verifiable and the docs' "noch nicht implementiert" marker
  removed; deliberately deferred items (R13) SHALL be justified in the issue
  rather than silently dropped. Each implementation cluster SHALL run the
  mandatory 3-agent chain (UI-review → tests → docs).
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: #367 acceptance + feedback_auto_docs invariant

## Surviving assumptions / open risks

- **A1** (assumed, below-`τ_high` driver — `edge_cases` = 0.78) — **Harvest-complete
  semantics (#14/R14).** The explicit-flag decision fixes *how* the transition
  fires but not the partial-harvest interplay: whether a plant with multiple
  open harvest batches transitions on the *flag* regardless of remaining batches
  (assumed: yes — the flag is the operator's explicit "done" signal, independent
  of batch count). Remedy: confirm against `harvest_service.py` + phase-engine
  rules during PR3; conservative default = flag-driven only, never auto.
- **A2** (assumed) — **Species 17-column mapping (#2/R2).** The exact
  column→`Species`-field mapping and which columns are safely empty-tolerant is
  derived from the CSV template, not user-stated. Remedy: verify against the
  actual template file in PR1; only `scientific_name` is required by decision.
- **A3** (assumed) — **RRULE↔legacy-cron coexistence (#6/R6).** Whether existing
  persisted cron recurrence strings must keep working is assumed "tolerated as
  legacy, RRULE canonical." Remedy: check for existing seed/persisted cron
  strings before removing the croniter path; keep a legacy branch if any exist.
- **A4** (assumed) — **Frost data source (#11/R11).** Weather-API vs local sensor
  threshold for frost detection is deferred to PR4 design; assumed to reuse the
  existing outdoor weather-API chain (DWD/OpenWeatherMap/Open-Meteo) already in
  the hybrid sensor model. Remedy: confirm the available source in PR4.
- **A5** (assumed) — **TaskCategory extra values (#7/R7).** Beyond `watering`/
  `pest_control`, "and others used in the workflow/task-template editor" is not
  enumerated. Remedy: grep the FE task-template editor for emitted category
  values in PR2 and add the full set additively.
