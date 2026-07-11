# Pre-Analysis — Issue #489

- **Issue:** [#489 — analysis: reconcile Tasks vs. Care reminders — model/layer duplication & reuse audit](https://github.com/nolte/kamerplanter/issues/489)
- **State:** OPEN · **Labels:** `chore`, `backend` · **Milestone:** none · **Assignee:** none
- **Acquired / grounded:** 2026-07-11
- **Worktree:** `chore/489-tasks-vs-care-reminders-audit` (off `origin/develop`)

## Classification

- **Primary class:** `question`
- **Rationale:** The issue's declared deliverable is a *written findings report*
  (duplication map + count analysis + spec reconciliation + prioritized
  recommendation). It explicitly states: "Any code consolidation is a **follow-up**
  gated by the findings and existing requirements — this issue does not prescribe or
  perform the refactor." No production code is mutated → an answer/analysis, not a
  code work package. Class = `question`.
- **Secondary dimension (informational):** `refactor` — the analysis scopes a
  possible future duplication-reduction refactor, which lands as separate follow-up
  issues, not here.

## Operator gates recorded

- **Scope confirmation:** operator confirmed the acquired issue and analysis-only
  scope (2026-07-11).
- **Requirements-elicitation consumer gate:** EXEMPT — a `question`-class issue
  yields no work packages and never reaches decomposition
  (`spec/project/requirements-elicitation/` §H; orchestration spec §Issue acquisition).
  No `requirements-elicit` dispatch required.
- **Operator override of the strict `question` short-circuit:** operator chose
  "question → Bericht + PR": instead of stopping at an issue comment, persist the
  findings report as a checked-in document under `spec/analysis/` and open a PR
  (`Closes #489`) plus post a summary comment. Recorded here as the explicit
  override.
- **Route:** direct implementation, single PR strand (bounded — one coherent
  outcome: the analysis document; no new/retargeted roadmap item).
- **Investigation depth:** thorough, single-session — read-only Explore agents per
  layer, synthesized by the orchestrator.

## In scope

- Read-only audit across backend layers (enum/model, repository, engine, service,
  API, frontend) of whether Tasks (REQ-006) and Care reminders (REQ-022) are one
  concept or two, and where logic is duplicated vs. shared.
- Dashboard count overlap / double-counting analysis (`open_tasks_today`,
  `overdue_tasks`, `care_reminders_due` — REQ-009).
- Requirements reconciliation (REQ-006, REQ-022, REQ-009, NFR-001): is the
  separation required by spec or an implementation artifact?
- A prioritized recommendation, staying within existing requirements.

## Out of scope

- Any production code change / refactor / consolidation (explicit follow-up).
- Changing the dashboard widget behaviour or the data model.
- Creating roadmap items or features (recommendations may seed follow-up issues,
  authored separately).

## Work packages

None — `question`-class issue produces no work packages
(orchestration spec §Classification). The whole job is the answer: the findings
report. The read-only layer investigation below feeds the synthesis; it is not
specialist remediation dispatch.

## Deliverable

- `spec/analysis/tasks-vs-care-reminders-audit.md` — the findings report.
- PR to `develop`, `Closes #489`, adding only the report document.
- Summary comment posted back to the issue.

## Grounding (verified in source, off `develop`)

- `TaskCategory.CARE_REMINDER` exists (`app/common/enums.py:757`).
- `care_reminder_service.py` both **reads** tasks by `category == CARE_REMINDER`
  (lines 276, 542, 651) and **creates** such tasks (lines 558, 695) — dual role
  confirmed.
- Parallel care-reminder stack: `care_reminder_service.py`,
  `care_reminder_engine.py`, `data_access/arango/care_reminder_repository.py`.
- Dashboard exposes three counts in `dashboard_service.py:48-51`
  (`open_tasks_today`, `overdue_tasks`, `care_reminders_due`), surfaced via
  `api/v1/dashboard/tenant_router.py`.
- No prior art: no analysis report, no open PR, no requirement artifact for #489.

## Risks / open questions

- Count-overlap conclusion depends on the exact predicate each count uses; must be
  read precisely from `dashboard_service.py`, not assumed.
- Recommendations must stay strictly within existing REQ/NFR intent (the issue bars
  prescribing the refactor).
