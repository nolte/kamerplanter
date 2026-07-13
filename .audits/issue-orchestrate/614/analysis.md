---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "614"
classification: "bug"
secondary-classes: []
route: "direct"
status: done
created: "2026-07-13"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #614 — Bug: Aufgabenverlauf tab fails to load (limit=500 exceeds backend le=200 → HTTP 422) on plant-instance detail
- **URL**: https://github.com/nolte/kamerplanter/issues/614
- **Labels**: bug, fix, backend
- **Linked items**: none (no closing PRs)
- **Prior art checked**: `gh issue view` shows no linked/closing PRs; no open PR references #614; grep of the frontend confirmed the `limit=500` idiom is used widely but no fix is in flight.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: A structurally-invalid request (`limit=500` > backend `le=200`) yields a hard HTTP 422; a defect in shipped behaviour, not a new capability.

### Requirements gate

The issue body is a fully-specified requirement: it carries a code-grounded root cause and five testable acceptance criteria, all verified against the source during `acquire`. Per `spec/project/issue-orchestration/` requirements gate, a `requirements-elicit` dispatch is **overridden by the operator** — understanding is already at `τ_high` (root cause reproduced by reading `PlantInstanceDetailPage.tsx:413`, `pagination.py:15,31`, `tasks/tenant_router.py:320`). The scope expansion below was explicitly operator-confirmed.

## Scope

- **In scope**: Eliminate the `limit`-exceeds-backend-cap 422 class across the frontend. Primary target is #614's Aufgabenverlauf tab; the operator confirmed expansion to the full sibling set of oversized-`limit` call sites found during grounding. Harden `loadPlantTasks` error handling so a future contract mismatch is diagnosable rather than masked.
- **Out of scope**: Raising the shared backend `le=200` cap (the issue's least-preferred option — it would legitimise oversized requests). Endpoints already within contract (e.g. `listSpecies(0,500)` against `species` `le=1000`) are left untouched. No changes to the pagination contract itself.

## Grounding findings (evidence)

Confirmed by reading source in the primary checkout:

- **Root cause (#614)**: `PlantInstanceDetailPage.tsx:413` → `taskApi.listTasks(0, 500, …)`; `list_tasks` (`app/api/v1/tasks/tenant_router.py:320`) depends on `get_pagination` → `app/common/pagination.py:15,31` caps `limit` at `le=200` → FastAPI 422 before the handler. The Info tab (`:337`, `limit=50`) hits the same endpoint and works.
- **Dedicated route available**: `GET /tasks/plants/{plant_key}` (`tasks/tenant_router.py:390`, `get_tasks_for_plant`) is pagination-free — the operator-chosen fix for the tasks tab.
- **Secondary defect**: `loadPlantTasks` catch block (`PlantInstanceDetailPage.tsx:416`) discards the error and forces `errors.loadFailed`.
- **Sibling 422 call sites (same class)** — FE signatures pass `limit` through unclamped:

  | Call site | FE call | Backend cap | Status |
  |---|---|---|---|
  | `PlantInstanceDetailPage.tsx:413` | `listTasks(0,500)` | tasks `le=200` | #614 primary |
  | `PestContributionsAdminCard.tsx:71` | `listPests(0,500)` | pest_detection `le=100` | latent 422 |
  | `WateringEventListPage.tsx:48` | `listPlantInstances(0,500)` | `le=200` | latent 422 |
  | `LocationDetailPage.tsx:236` | `listPlantInstances(0,500)` | `le=200` | latent 422 |
  | `HarvestBatchListPage.tsx:50` | `listPlantInstances(0,500)` | `le=200` | latent 422 |
  | `FeedingEventListPage.tsx:47` | `listPlantInstances(0,500)` | `le=200` | latent 422 |
  | `WateringLogCreateDialog.tsx:112` | `listPlantInstances(0,500)` | `le=200` | latent 422 |
  | `WateringLogCreateDialog.tsx:115` | `fetchFertilizers(0,500)` | fertilizers `le=200` | latent 422 |
  | `SpeciesCropRotationTab.tsx:75` | `listBotanicalFamilies(0,500)` | `le=200` | latent 422 |
  | `PlantInstanceListPage.tsx:56` etc. | `listSpecies(0,500)` | species `le=1000` | OK — out of scope |

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome ("no frontend caller exceeds its endpoint's pagination cap"), a single PR strand, no new or retargeted roadmap item. "Bounded" is about planning shape, not file count — the class-wide fix is still one strand.
- **Pipeline hand-off**: n/a

## Work packages

### P1 — Fix #614 Aufgabenverlauf tab (primary) + harden error handling

- **Problem statement**: The tasks-history tab issues `listTasks(0, 500, …)` which 422s; the catch masks the real error.
- **Acceptance criteria**:
  - The Aufgabenverlauf tab loads task history for a plant instance without a 422 (verified on a plant with tasks, e.g. `FRAGA-0712-TCJ`), by switching to the pagination-free `GET /tasks/plants/{plant_key}` route (`getTasksForPlant`). Preserve the existing active/archived split and any status/entity filtering the tab relies on.
  - `loadPlantTasks` (`:408–421`) no longer swallows the underlying error; a real failure surfaces a diagnosable message/log (distinguish 4xx validation from network), without regressing the empty-state fix noted at `:405–407` (#578).
  - `data-testid="tasks-tab"` and the active/archived `DataTable` rendering remain intact.
- **Touched files / artifacts**: `src/frontend/src/pages/pflanzen/PlantInstanceDetailPage.tsx` (tasks tab load path, catch block), possibly `src/frontend/src/api/endpoints/tasks.ts` (ensure `getTasksForPlant` exists / is used).
- **Specialist**: `fullstack-developer`
- **Depends on**: none

### P2 — Bring sibling oversized-`limit` call sites within backend contract

- **Problem statement**: ~7 further call sites request `limit=500` against endpoints capped below 500, each a latent 422.
- **Acceptance criteria**:
  - Every sibling call site in the grounding table (excluding the species `le=1000` ones) issues a request within its endpoint's declared cap (no 422). `listPests` → ≤100; `listPlantInstances` / `fetchFertilizers` / `listBotanicalFamilies` → ≤200.
  - No **silent truncation** of realistic datasets: where "fetch all" is genuinely needed and could exceed the cap (notably `listPlantInstances` for a tenant with many plants), the specialist either paginates to completeness or documents the bound in code — a silent cap that drops rows is not acceptable (`continuous-improvement` no-silent-caps).
  - A closing audit confirms no remaining frontend `list*`/`fetch*` call passes a `limit` above its endpoint's cap.
- **Touched files / artifacts**: `PestContributionsAdminCard.tsx`, `WateringEventListPage.tsx`, `LocationDetailPage.tsx`, `HarvestBatchListPage.tsx`, `FeedingEventListPage.tsx`, `WateringLogCreateDialog.tsx`, `SpeciesCropRotationTab.tsx` (all under `src/frontend/src/`).
- **Specialist**: `fullstack-developer`
- **Depends on**: P1 (same frontend tree — co-dispatched sequentially to one specialist to avoid shared-tree write conflicts, per project convention "schreibende Agenten auf geteiltem Tree sequenziell").

## Dependency ordering

P1 → P2 (both dispatched to a single `fullstack-developer` run, in this order, because they share the frontend working tree).

## Risks

- **Truncation vs. contract**: Reducing `limit` to the cap could silently drop rows on large tenants. Mitigation: P2 AC forbids silent truncation; specialist paginates or documents the bound.
- **Tasks-tab filter parity**: The dedicated `/tasks/plants/{key}` route takes only `status`; the tab may rely on richer filtering than `listTasks`. Mitigation: P1 AC requires preserving the active/archived split; specialist verifies the route returns the same task set the tab renders.
- **Empty-state regression**: The catch rework must not reintroduce the #578 "stuck on empty CTA" bug (`:405–407`). Mitigation: P1 AC explicitly guards it.
- **Security-sensitive paths**: none touched (no auth/tenant-isolation/crypto path in scope); `security-review` not required for this diff.

## Open questions

none — scope and fix approach operator-confirmed.

## Dispatch log

- 2026-07-13 P1+P2 dispatched to `fullstack-developer` (single sequential run, shared FE tree) — DONE. P1: tasks tab now loads via `getTasksForPlant` (pagination-free), catch hardened via `resolveLoadErrorKey` (4xx/5xx/network/timeout), #578 empty-state guard intact. P2: sibling call sites converted to new paginate-all helpers `listAllPlantInstances` / `fetchAllFertilizers` / `listAllPests` (pattern of existing `listAllBotanicalFamilies`, #550) — no silent truncation; closing audit clean. lint/tsc PASS, vitest 3327/3328 (1 known unrelated HA-flake). New/updated tests incl. 422 regression test.
- 2026-07-13 verify: UI-review by `frontend-usability-optimizer` — DONE. Found + fixed a UX bug: 422 was mapped to `errors.validation` ("check your input") on a read-only view; remapped to generic `errors.loadFailed`. i18n DE/EN complete; loading/error/empty/data states cleanly separated; #578 guard confirmed. tsc/lint clean, tasks-tab test 5/5.
- 2026-07-13 independent gate re-run in worktree: lint 0 errors (129 pre-existing warnings), tsc clean, vitest 3327/3328 (the 1 failure is the known unrelated `AccountSettingsPageFlows` HA-connection timeout flake — matches project memory `project_coverage_suite_flake`).
- 2026-07-13 operator-added refinements (in-scope, after live test on `FRAGA-0712-TCJ`): (A) missing i18n key `common.status` rendered raw in the tasks-tab column header → add `common.status="Status"` in all locales; (B) tasks tab should offer the same per-row actions as the Aufgabenwarteschlange (start/complete/skip) instead of only quick-complete → mirror `TaskQueuePage` handlers (`startTask`/`completeTask`/`skipTask`), status-gated, refetch via `loadPlantTasks()`. Re-dispatched to `fullstack-developer` — DONE. (A) `common.status="Status"` added to de+en. (B) `renderTaskActions` with `handleStartTask`/`handleCompleteTask`/`handleSkipTask` (unified `taskActionLoading` lock, replaces quick-complete), status-gated exactly like the queue's `isActionable` (pending → start/complete/skip; in_progress → complete/skip; archived → none), `stopPropagation` on wrapper + buttons, refetch via `loadPlantTasks()`, available on desktop table + mobile cards. New tests for each action + gating.
- 2026-07-13 final gate re-run in worktree: lint 0 errors, tsc clean, **vitest 3331/3331 (334/334 files) — fully green** (HA flake did not recur, confirming flake not defect). Ready for PR.
