---
audit-type: parallel-execution-plan
target-repo: kamerplanter
created: 2026-07-11
repo-revision: af9066c8a
scope: all open GitHub issues (parallel, dependency-aware, conflict-free, autonomous)
sources:
  - .audits/plans/01-backend-domain-scaffolds.md
  - .audits/plans/02-ai-assistance-family.md
  - .audits/plans/03-outdoor-weather-integration.md
  - .audits/plans/04-plant-property-data-model.md
  - .audits/plans/05-ui-nfr-polish.md
  - .audits/execution-roadmap.md
---

# Open-Issues Parallel Execution Plan

Cross-issue orchestration layer over the per-epic plans in `.audits/plans/01–05`.
Its job: schedule **every open issue** for **parallel** implementation that
**respects dependencies**, **avoids merge conflicts**, and can be driven
**autonomously to a sustainable, complete resolution**.

The per-epic plans (`01–05`) remain authoritative for the *internal* work packages
of each epic. This document is authoritative for the *cross-issue* concerns:
lane definition, the dependency DAG, the hot-file conflict map, the single global
migration-number queue, the wave schedule, and the autonomous per-lane recipe +
merge-queue discipline.

## 0. Scope & exclusions

Open issues at `af9066c8a` (18 total):

- **Excluded — not work packages:** `#12` (Renovate Dependency Dashboard, bot-owned),
  `#489` (Tasks↔Care analysis — **done**, PR #507 open).
- **16 actionable issues**, grouped into **lanes** below.

A **lane** = one branch + one worktree + one PR strand, owned by one dispatched
specialist, driven end-to-end (implement → 3-agent chain → quality-gate → PR →
merge-queue). Big epics fan out into several lanes.

## 1. Lane inventory

| Lane | Issue(s) | REQ | Class | Specialist | Branch (resume ⟳ / new ✚) | Size | Touches hot files? |
|---|---|---|---|---|---|---|---|
| **A1** Post-Harvest | #450 | REQ-008 | feature | fullstack-developer | ✚ `feat/req008-postharvest` | L | migrations, router, collections, i18n, FE-route |
| **A2** InvenTree | #450 | REQ-016 | feature | fullstack-developer | ⟳ `feat/req016-inventree` | M | migrations, router, collections, i18n, FE-route |
| **A3** Lineage | #450 | REQ-017 | feature | fullstack-developer | ⟳ `feat/req017-lineage` | L | migrations, router, collections, i18n, FE-route |
| **A4** Aquaponik | #450 | REQ-026 | feature | fullstack-developer | ✚ `feat/req026-aquaponik` | L | migrations, router, collections, i18n, FE-route |
| **A5** Actuators | #506 | REQ-018 | feature | fullstack-developer (+ ha-integration-developer) | ⟳ `feat/req018-actuators` | L (mostly done) | migrations, router, collections, i18n |
| **B1** AI foundation | #451 | REQ-031 | feature | fullstack-developer | ✚ `feat/req031-ai-assistant` | L | router, collections, i18n, FE-route |
| **B2** AI glossary | #451 | REQ-035 | feature | fullstack-developer | ✚ `feat/req035-glossary` | M | migrations, router, collections, i18n |
| **B3** AI diagnosis | #451 | REQ-036 | feature | fullstack-developer | ✚ `feat/req036-diagnosis` | L | migrations, router, collections, i18n, inference-service |
| **B4** MCP server | #451 | REQ-033 | feature/security | fullstack-developer | ✚ `feat/req033-mcp` | L | router, i18n |
| **C1** NASA POWER | #452 | REQ-041 | feature | fullstack-developer | ✚ `feat/req041-nasa-power` | M | collections(v0011 landed), router, adapter-registry |
| **C2** ET₀ | #452 | REQ-037 | feature | fullstack-developer | ⟳ `feat/req037-et0` | S-M | router, watering_service seam |
| **C3** Hardiness zones | #452 | REQ-039 | feature | fullstack-developer | ✚ `feat/req039-hardiness-zones` | M | collections(v0013 landed), router |
| **C4** CV diagnosis | #452 | REQ-038 | feature | fullstack-developer | ✚ `feat/req038-cv-diagnosis` | L | inference-service (isolated) |
| **D1** Plant backfill | #453 | — | data | seed-pipeline agents | ✚ `feat/plant-data-backfill` | L | seed YAML + Steckbriefe only |
| **D2** Toxicity badge | #453 | — | feature | fullstack-developer | ✚ `fix/toxicity-badge` | S | FE `SpeciesDetailPage`, i18n |
| **CARE** Care-reuse | #508→#511→#509→#510 | REQ-009/022/006 | bug/refactor | fullstack-developer | ✚ `refactor/care-task-reuse` | M | **care files (serial)** |
| **DASH-1** Resize bug | #487 | REQ-045 | bug | fullstack-developer | ✚ `fix/dashboard-resize-kebab` | S | FE dashboard EditGrid only |
| **DASH-2** Plant grid | #488 | REQ-009 | feature | fullstack-developer | ✚ `feat/plant-grid-widget` | M | FE GenericWidget + dashboard payload |
| **OW-1** REQ-047 verify | #477 | REQ-047 | verify+feature | fullstack-developer | ✚ `feat/req047-upgrade-paths` | M | season_state, care_engine (coord. w/ CARE) |
| **OW-2** OW filtering | #491 | REQ-047 | feature | fullstack-developer | ✚ `feat/overwintering-facets` | S-M | FE OverwinteringListPage, i18n |
| **SITE** Balcony outdoor | #492 | REQ-002 | bug | fullstack-developer | ✚ `fix/balcony-outdoor` | S | `common/enums.py` + FE site gating |
| **SPEC** Header actions | #490 | UI-NFR | spec-change | `spec` skill | ✚ `spec/ui-nfr-header-actions` | M | **spec/ only — no code** |
| **E2E** NFR-008a | #505 | NFR-008a | chore | e2e-test-reviewer | ✚ `test/e2e-nfr008a` | M | **tests/e2e/ only** |

> Note on D3 (optional hardening, #453 WP-6f/8/9): low priority, deferred; folded
> into D2's lane only if capacity allows. Not scheduled as its own lane.

## 2. Dependency DAG (hard blockers only)

```
Epic C:  C1 (REQ-041 climate_normals) ──▶ C2 (REQ-037 ET₀)
                                      └──▶ C3 (REQ-039 hardiness zones)
         C4 (REQ-038 CV) ── independent
Epic B:  B1 (REQ-031 foundation) ──▶ B2 (REQ-035) ─┐
                                  └──▶ B3 (REQ-036) ─┴──▶ B4 (REQ-033 MCP)
Epic A:  A2 (REQ-016) ─┐
         A3 (REQ-017) ─┴──▶ A5 (REQ-018 / #506 migration-renumber + merge)
         A1, A4 ── independent of A2/A3/A5
CARE:    #508 ─▶ #511 ─▶ #509 ─▶ #510   (single serial lane — see §3)
OW-1:    verify(read-only) ─▶ build AC-22/AC-4/AC-26/AC-29
```

All other lanes (**D1, D2, DASH-1, DASH-2, OW-2, SITE, SPEC, E2E**) have **no
blockers** and start immediately.

**Cross-epic soft dependency:** C2 (ET₀) is consumed by REQ-022 adaptive watering;
OW-1 (AC-4) is refined by C1/C3 climate normals. These are *enhancements*, not
blockers — land them in either order; the consumer seam is already inert-present.

## 3. Conflict map — hot files & serialization rules

The only real conflict risk is a set of **shared "wiring" files** every backend
epic appends to, plus the **care files** and **migration numbers**. Rules:

| Hot file | Lanes | Rule |
|---|---|---|
| `app/migrations/versions/vNNNN_*.py` | A1,A2,A3,A4,A5,B2,B3,C1,C3 | **Single global migration queue (§4).** A lane claims its number *only at merge time*, never picks one while developing in parallel. Next free = **v0015**. |
| `app/api/v1/router.py`, `app/api/v1/tenant_scoped/router.py` | A*,B*,C1,C2,C3 | Append-only router registration. Rebase-before-merge; conflicts are additive and trivially resolved. |
| `app/data_access/arango/collections.py` | A*,B2,B3,C1,C3 | Append-only collection/edge constants. |
| `app/common/enums.py` | SITE,A*,B*,C*,D2 | Append-only enum values / new constant (SITE adds `OUTDOOR_WEATHER_TYPES`). |
| `i18n/locales/{de,en}/translation.json` | almost all FE lanes | **Per-lane namespace prefix** (e.g. `postHarvest.*`, `aiAssistant.*`, `plantGrid.*`) → additive, textually disjoint. Append-only, rebase-before-merge. |
| frontend router (`App.tsx` / routes) | A*,B1,B3,C4,DASH-2 | Append-only route entries. |
| dashboard FE registry/catalog (`widgetRegistry.ts`, `dashboardWidgetCatalog.ts`) | DASH-2 | Only DASH-2 touches these; DASH-1 touches `DashboardEditGrid.tsx`/`WidgetFrame.tsx` → **disjoint from DASH-2**, parallel-safe. |
| care files: `care_reminder_service.py`, `care_tasks.py`, `task_service.py`, `task_repository.py` | CARE, OW-1 | **CARE is one serial lane** — its four issues touch these files mutually and MUST NOT be parallelized. OW-1's build step may touch `care_reminder_engine.py`/`season_state_service.py` (AC-22): **coordinate** — run OW-1's care-touching build *after* CARE merges, or confine OW-1 to `season_state_*`. Verify overlap at OW-1 start. |

**Disjoint-by-construction (no coordination needed):** SPEC (`spec/` only), E2E
(`tests/e2e/` only), C4 & B3-vision (`inference-service/` only), D1 (`spec/knowledge/`
seed YAML + Steckbriefe only). These merge out-of-queue anytime.

## 4. Global migration-number queue (the one true serialization)

Current max on `develop`: **`v0014_cv_diagnosis_collections.py`**. Every lane that
adds an Arango collection/index migration must claim the next free number **at the
moment it enters the merge queue** and renumber its migration file then — never
pre-assign in parallel (two parallel `v0015`s is the classic collision, cf.
`project_batch2_orchestration` v0015 triple-collision).

**Allocation ledger** (fill in as lanes merge; order = merge order, not start order):

| vNNNN | Lane | Collection(s) | Status |
|---|---|---|---|
| v0015 | _next to merge among {A2,A3,B2,B3,C1,C3,A5}_ | — | unclaimed |
| v0016 | _second_ | — | unclaimed |
| v0017 | _third_ | — | unclaimed |
| … | … | … | … |

**#506 (A5) special case:** its branch currently ships `v0015`. Because A5 merges
*after* A2/A3 (DAG), it renumbers to whatever is free at its merge turn (≥ v0017 if
A2+A3 each add one). The A5 issue body already calls this out; the renumber + smoke
test is a checklist item in its lane recipe.

**Merge-queue owner:** a single serialization point (the orchestrator, or a human
merge-captain) processes hot-file lanes one at a time: rebase onto develop tip →
assign migration number → resolve additive wiring conflicts → `pull-request-merge` →
verify develop green → advance. Non-hot-file lanes bypass the queue.

## 5. Wave schedule

Waves describe **when a lane may START** given the DAG. Development is fully
parallel; **merging** is serialized only through the §4 queue for hot-file lanes.
Concurrency cap: pick per machine (≈ 4–6 worktree agents at once is comfortable).

### Wave 0 — start immediately (zero blockers, mostly conflict-disjoint)
`SPEC` · `E2E` · `SITE` · `DASH-1` · `OW-2` · `D2` · `D1` · `CARE`(#508 first) · `C4`
- Fully isolated: SPEC (spec/), E2E (tests/e2e/), C4 (inference-service/), D1 (seed YAML).
- FE-only, disjoint files: SITE, DASH-1, OW-2, D2 — share only append-only i18n.
- CARE starts its serial chain with #508.

### Wave 1 — epic foundations (resume existing branches)
`A1` · `A2`⟳ · `A3`⟳ · `A4` · `B1` · `C1` · `DASH-2`
- A-domains are file-disjoint per §3; B1 unblocks B2/B3; C1 unblocks C2/C3.
- CARE advances: #508 merged → #511.

### Wave 2 — unblocked by Wave-1 foundations
`B2` ‖ `B3` (need B1) · `C2`⟳ ‖ `C3` (need C1) · `A5` (need A2+A3 merged) · `OW-1`-build
- CARE advances: #511 merged → #509.

### Wave 3 — aggregation layer
`B4` MCP (needs B2+B3 stable tool targets)
- CARE advances: #509 merged → #510 (last).

## 6. Per-lane autonomous recipe

Each lane runs this loop unattended. Steps are the project's standing conventions
(CLAUDE.md, `feedback_auto_docs`, `feedback_auto_ui_review`, quality-gate,
pull-request-workflow).

1. **Isolate.** New lane: `task worktree:add -- <branch> <slug>` off `origin/develop`.
   Resuming lane (⟳): create a worktree tracking the existing remote branch, then
   `git rebase origin/develop`.
2. **Load context.** Read the lane's work-package section in `.audits/plans/0X`; read
   the issue body + ACs; ground touched files against the worktree.
3. **Implement.** Dispatch the lane's specialist (`Agent(subagent_type=…,
   isolation:"worktree")`) with: problem statement, ACs, touched files, issue ref,
   and the **i18n namespace prefix** for this lane. (`fullstack-developer` for code;
   `ha-integration-developer` for A5's HA custom-integration side; `spec` skill for
   SPEC; `nolte-engineering:e2e-test-reviewer` for E2E; seed-pipeline agents
   `plant-info-document-generator`→`plant-info-to-seed-yaml`→`seed-data-validator`
   for D1.)
4. **Post-implementation 3-agent chain** (mandatory per `feedback_auto_docs`):
   frontend-touching lanes → `frontend-usability-optimizer` (UI review) →
   `unit-test-runner` (tests) → `mkdocs-documentation` (DE/EN docs). Backend-only
   lanes → `unit-test-runner` + docs.
5. **Security review** where a security path is touched: A5 (override cap / value
   clamp), B4 (MCP permission-matrix binding) → `code-security-reviewer` (scope) +
   `security-review` skill (diff). Record in PR.
6. **Quality gate.** `nolte-engineering:quality-gate` green; coverage floors
   (backend ≥ 60 %, frontend ≥ 80 %); `scaffoldNotice` removed; coverage-audit green.
7. **PR.** `pull-request-create`, `Closes #<n>` (epic-domain lanes reference the epic
   issue: e.g. A2 → `Refs #450`; A5 → `Closes #506`), draft.
8. **Merge queue.** Hot-file lane → enter §4 queue (rebase → claim migration number →
   resolve additive wiring → `pull-request-merge`). Disjoint lane → merge directly
   once CI green. **Never** `--admin`, never mask `static`.
9. **Verify sustainable close.** Issue auto-closes on the `main` fast-forward
   (pull-request-workflow); confirm the epic issue's checklist item ticks. Live-test
   lanes (DASH-1 needs a real `h=2` touch test; A5 UI) → `verify` skill / dev cluster.

## 7. Special-handling notes (per lane)

- **A2/A3/A5/C2 (resume branches):** the branches already carry real work
  (`feat/req016-inventree`, `feat/req017-lineage`, `feat/req018-actuators` = done +
  sec-reviewed, `feat/req037-et0`). **Resume, don't restart.** First step: rebase
  onto develop, re-run quality-gate to see current state, then close the gap.
- **A5 / #506:** code is done on branch; remaining = SEC-fix (a) cap override
  `expires_at` & enforce `> now`, (b) clamp command/override value to actuator
  min/max (both with tests); UI-usability pass; DE/EN docs; **migration renumber**
  (v0015 → next free at merge); PR → merge. Depends on A2+A3 merged first.
- **C1 vs. landed migrations:** `v0011 climate_normals`, `v0012 irrigation_demands`,
  `v0013 hardiness_zones`, `v0014 cv_diagnosis` **already on develop** — the
  collection scaffolds landed. C1/C2/C3/C4 must **verify what remains** (adapter
  impl, Celery, attribution, endpoints) rather than re-create collections. First
  step of each C-lane: diff branch vs. develop to find the real gap.
- **CARE lane order** (single worktree, sequential PRs, rebase between each):
  `#508` (exclude care from task counts — ships the user-visible fix first) →
  `#511` (DRY care-reminder Task builder — foundation) → `#509` (tenant-aware dedup
  helper — also closes the latent cross-tenant gap) → `#510` (reuse Task recurrence
  engine). Rationale + file map in `spec/analysis/tasks-vs-care-reminders-audit.md`.
- **OW-1 / #477:** step 1 is **read-only verification** of AC-1…29 against built
  code (no PR if all hold) → step 2 builds only the `Ausbaustufe` gaps (AC-22 event
  `quarter_climate_check`, AC-4 climatological tier-2 from `ClimateNormal`, AC-26
  `greenhouse_heated` + container→path-B, AC-29 no re-materialization post-flowering).
  Coordinate AC-22's care-file touch with the CARE lane (§3).
- **License gates (C-lanes):** aquacropeto BSD-3 ✅, PlantDoc CC-BY ✅, DWD/Open-Meteo
  CC-BY ✅ + attribution mandatory; 🔴 **no** pyTSEB (GPL-3), **no** USDA/PHZM data,
  **no** Growstuff merge. A hard gate in C1/C2/C4 review.
- **DASH-1 / #487:** touch-target geometry fix on `DashboardEditGrid.tsx` +
  `WidgetFrame.tsx`; **must be live-verified** on an `h=2` tile (a unit test can't
  prove pointer-event routing) — `verify` skill against the dev cluster.
- **SPEC / #490:** deliverable is a spec document only (decide UI-NFR-021 new vs.
  UI-NFR-017 extension at start), DE-canonical + EN-mirror per DOCS.md. Rolling pages
  onto the new rules is an explicit follow-up, not this lane. `spec` skill.
- **E2E / #505:** reference files first (`test_req001_*`, `test_req002_standorte.py`)
  → then sweep remaining `tests/e2e/test_req*.py` with
  `nolte-engineering:e2e-test-reviewer`; one PR per logical batch; no behavioural
  change to assertions; `pytest --collect-only --strict-markers` stays green.
- **SITE / #492:** introduce a single `OUTDOOR_WEATHER_TYPES`/`is_weather_relevant`
  SSOT in `common/enums.py` (mirroring `OVERWINTERING_SITE_TYPES`) and route the
  scattered `outdoor || greenhouse` FE checks (`SiteDetailPage`, `SiteCreateDialog`,
  `siteForm.ts`) through it; balcony included; indoor types stay disabled.

## 8. Autonomous-run control loop (orchestrator)

To drive the whole board unattended:

1. **Seed the queue** with Wave-0 + Wave-1 lanes up to the concurrency cap; dispatch
   each as a worktree-isolated lane per §6.
2. **On each lane completion** (task-notification): run its merge-queue turn (§4/§8),
   then pull the next ready lane whose DAG predecessors have merged.
3. **Migration ledger** (§4) is the shared mutable state — update on every hot-file
   merge; it is the single writer-serialized resource.
4. **Failure handling:** a red quality-gate or CI keeps the lane in `draft`, routes
   to `nolte-engineering:test-result-analyzer` → `test-code-adapter` (fix-forward,
   never `--amend` a pushed commit); a genuine spec ambiguity pauses the lane and
   surfaces an operator question — it does not silently guess.
5. **Definition of "sustainably solved"** per lane: issue closed via `main`
   fast-forward, epic-checklist item ticked, coverage floors met, `scaffoldNotice`
   gone, docs (DE/EN) shipped, no new drift in `.audits/req-coverage-audit.md`.
6. **Whole-board done:** re-run `python3 .claude/skills/req-coverage-audit/run_audit.py`;
   the open-issue set is empty except bot-owned `#12`.

## 9. Verify-at-start checklist (before dispatching a lane)

- [ ] Resuming lane: does the remote branch still exist and rebase cleanly?
- [ ] C-lanes: which collections/migrations already landed (v0011–v0014) — what is
      the *actual* remaining gap vs. develop?
- [ ] `fix/dashboard-editgrid-rendering`, `fix/e2e-selenium-executability`,
      `fix/frontend-mobile-card-actions` remote branches — are they stale, already
      merged (cf. #487 says #480 merged), or the real start point for DASH-1/E2E?
      Reconcile before creating a fresh branch.
- [ ] OW-1 ∩ CARE care-file overlap: read AC-22's touch surface before parallelizing.
- [ ] i18n namespace prefix assigned and unique per FE lane.

## 10. At-a-glance schedule

| Wave | Lanes (parallel) | Gate to advance |
|---|---|---|
| **0** | SPEC, E2E, SITE, DASH-1, OW-2, D2, D1, C4, CARE#508 | none (start now) |
| **1** | A1, A2⟳, A3⟳, A4, B1, C1, DASH-2, CARE#511 | Wave-0 hot-file lanes drained from queue |
| **2** | B2‖B3, C2⟳‖C3, A5, OW-1-build, CARE#509 | B1, C1, (A2+A3) merged |
| **3** | B4, CARE#510 | B2+B3 merged |

_This plan is additive and removes no audit. Per-epic detail stays in
`.audits/plans/01–05`; strategic prioritization in `.audits/execution-roadmap.md`._
