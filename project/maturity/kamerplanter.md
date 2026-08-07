# Capability Maturity — Kamerplanter (whole application)

> Advisory graded classification per `spec/project/capability-maturity-assessment/`.
> This is **not** a merge gate, a priority ranking, or a dashboard — it grades the
> *current build maturity* of each capability so it is visible where implementation
> quality is lacking. Gating stays with `quality-gate`; prioritisation with
> `roadmap-plan`/`sprint-plan`.
>
> **Task-ready remediation:** the concrete, autonomously-actionable work packages to
> raise each capability toward Gold live in [`kamerplanter-remediation.md`](./kamerplanter-remediation.md)
> (systemic enablers `SYS-1…5` + per-capability tasks with betroffene Dateien, Umsetzung,
> Definition-of-Done). That doc is the intended input for `issue-orchestrate` /
> `feature-decompose`; this matrix stays the grading, not the plan.

## Assessment context

- **audience artifact**: `AUDIENCES.md` (present — real audience mapping)
- **capability sources**: REQ catalogue (CLAUDE.md · `spec/req/`) · `project/requirements/` · `.audits/req-coverage-audit.md` · the user-facing surface (routers, pages) — inventoried **top-down**, never from the directory tree
- **operation**: `assess` · **scope**: whole application (REQ-001…REQ-047), 30 business-facing capabilities
- **thresholds** (source: **reference defaults** — the project configures only a single 80 % frontend line gate, no maturity bands):
  - coverage bands (lines): **Bronze ≥ 60 % · Silver ≥ 80 % · Gold ≥ 90 %** — monotonic
  - complexity ceiling: **McCabe 10** · duplication bound: **3 %**
- **frameworks**: OpenSSF Bronze/Silver/Gold · ISO/IEC 25010 (Axis B) · Test Pyramid (Axis C)
- **scan**: read-only `capability-maturity-scanner` (2026-07-23). Toolchain green: `ruff` 0 findings, `ruff format` clean, `tsc` 0 errors, `eslint` 0 errors / 129 advisory `react-hooks` warnings; backend unit suite 4688 passed (3 env-gap failures, not code defects); frontend suite green.

### Systemic ceilings (why no capability reaches Gold overall)

These are **portfolio-level tooling gaps**, recorded once here rather than repeated per block. They cap two axes across the whole app; lifting them is the highest-leverage move.

- **Axis B ceiling = Silver.** Gold-B requires SAST-clean + low complexity throughout + no debt markers + passed human review. The repo has **no complexity tool** (ruff `select` omits `C90`; no radon/lizard), **no duplication tool** (no jscpd), **no source-SAST** (Nuclei/ZAP run only against the deployed instance per NFR-014/015, not the source), and **mypy `strict` is configured but not run in CI**. None of the Gold-B signals can be established → **Axis B is capped at Silver** this pass.
- **Axis C ceiling = Silver.** Gold-C requires ≥1 E2E through a mapped audience's real workflow **plus** upper-band coverage. The **E2E/Selenium suite has no CI runner** (deliberate — local `task test:e2e` only), **backend coverage is not measured in CI** (`backend.yml` runs `pytest` without `--cov`), and the frontend coverage snapshot covers only 10 of 30 capabilities. Gold-C is not establishable → **Axis C is capped at Silver** this pass.
- **Axis A ceiling = Silver (except stub-forced Bronze/Unrated).** Gold-A requires per-capability edge/failure handling, applicable NFRs met, no open TODOs, and end-user docs for *every* mapped audience. This top-down pass did **not** verify docs/edge-cases per capability, so Axis A is capped at Silver for fully-built capabilities; promote a specific capability to Gold-A via a focused `reassess` that confirms its docs + edge cases.

**Consequence:** the app-wide overall tier is **Silver at best today** (18 Silver, 12 Bronze, 0 Gold), dragged to Bronze by the twelve capabilities below. The two systemic levers — *(1) add complexity/duplication/SAST tooling + run mypy & backend coverage in CI; (2) wire the E2E suite into CI* — would unlock Gold grading across the board.

### Audience legend

`GROW` home grower/hobby gardener/houseplant owner · `CGA` community-garden admin ·
`HOST` self-hoster · `HA` Home Assistant integrator · `GDPR` data-protection ·
`PROV` external botanical data providers (all from `AUDIENCES.md`).

## Summary matrix

| id | capability | A | B | C | overall | lever |
|----|-----------|---|---|---|---------|-------|
| C1 | Stammdatenverwaltung | Silver | **Bronze** | Silver | **Bronze** | B (NFR-001 layering) |
| C2 | Standortverwaltung | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C3 | Phasensteuerung/Lifecycle | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C4 | Dünge-/Nährstoff-Logik | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C5 | Hybrid-Sensorik | **Bronze** | Silver | Silver | **Bronze** | A (MQTT stage 1 · calibration · anomaly unbuilt) |
| C6 | Aufgabenplanung | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C7 | Erntemanagement | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C8 | Post-Harvest | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C9 | Dashboard | Silver | Silver | Silver | **Silver** | C (branch cov 61 %) |
| C10 | IPM-System | **Bronze** | **Bronze** | Silver | **Bronze** | A+B (REQ-043 stub) |
| C11 | Externe Anreicherung | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C12 | Stammdaten-Import | Silver | Silver | **Bronze** | **Bronze** | C (thin tests) |
| C13 | Pflanzdurchlauf | Silver | Silver | **Bronze** | **Bronze** | C (cov 73 %) |
| C14 | Tankmanagement | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C15 | Kalenderansicht | **Bronze** | **Bronze** | Silver | **Bronze** | A+B (aggregation TODO) |
| C16 | InvenTree (optional) | Silver | Silver | **Bronze** | **Bronze** | C (thin FE/integration) |
| C17 | Vermehrung/Lineage | Silver | Silver | Silver | **Silver** | C (un-skip integration) |
| C18 | Umgebungssteuerung/Aktorik | **Bronze** | Silver | Silver | **Bronze** | A (control UI missing — API-only) |
| C19 | Substratverwaltung | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C20 | Onboarding-Wizard | Silver | Silver | **Bronze** | **Bronze** | C (no wizard test) |
| C21 | UI-Erfahrungsstufen | Silver | Silver | **Bronze** | **Bronze** | C (no dedicated test) |
| C22 | Pflegeerinnerungen | Silver | Silver | Silver | **Silver** | C (branch cov 55 %) |
| C23 | Auth & Benutzerverwaltung | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C24 | Mandanten & RBAC | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C25 | DSGVO/Betroffenenrechte | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C26 | Light-Modus | Silver | Silver | **Bronze** | **Bronze** | C (cohesive suite) |
| C27 | Mischkultur/Companion | Silver | Silver | Silver | **Silver** | C (E2E-in-CI) |
| C28 | Druck/Export | Silver | Silver | **Bronze** | **Bronze** | C (thin tests) |
| C29 | Wissensassistent/RAG | Silver | Silver | Silver | **Silver** | C (KIAssistentPage test + KS contract) |
| C30 | Foto-Galerie & -Erkennung | Silver | Silver | Silver | **Silver** | C (branch lift + S3 test) |

**Distribution:** Silver 18 · Bronze 12 · Unrated 0 · Gold 0.

> **Correction (post-deep-review).** Four rows were re-graded after the per-capability
> REQ/code deep-read (below) overrode the scanner's surface signals — exactly the
> Axis-A judgement the skill owns, not the scanner:
> **C29 Unrated→Silver** and **C30 Bronze→Silver**: the scanner's `NotImplementedError`
> markers (`KiAssistentService.answer`, `VisionEngine.normalise_predictions`) are
> **dead orphaned scaffolds** (only self-referenced; verified by grep) — the real,
> wired, tested paths are `AiAssistantService` and the identification adapters. The
> "crashing core path" never runs. **C5 Silver→Bronze** and **C18 Silver→Bronze**:
> the deep-read found genuine cross-surface completeness gaps the surface scan missed
> (C5: MQTT ingestion stage, calibration, anomaly/quality, sensor-health unbuilt vs
> REQ-005 ACs; C18: full control backend exists but no UI for schedules/rules/override).

---

## C1 — Stammdatenverwaltung
- description: Create/edit/search species, cultivars, and botanical families — the master-data spine every other capability reads.
- audiences: GROW, CGA
- axis-a (completeness): Silver — fully built across API+UI+i18n, no stubs; under active refinement (uncommitted search/repository work).
- axis-b (code quality): **Bronze** — NFR-001 layering violation: API routers depend on the ArangoDB repository directly (`src/backend/app/api/v1/species/router.py:15,37,59,97,111`, `src/backend/app/api/v1/botanical_families/router.py:9`) instead of going through a service. Lint/format/type all clean.
- axis-c (test coverage): Silver — backend unit (`test_species_service.py`, `test_botanical_family_repository.py`, `test_species_repository_search.py`) + FE component (20 tests) green; FE coverage stammdaten lines 89.6 %/branches 82.7 % (Silver band).
- overall (weakest-link): **Bronze**
- improvement-lever: **B** — route the routers through a service layer to restore the 5-layer boundary; that alone lifts overall to Silver.
- rationale: A/C are Silver; the single Bronze is the layering breach. Fixing it is mechanical and high-value because C1 is the architectural reference other master-data code copies.

## C2 — Standortverwaltung
- description: Manage sites and their locations (climate zone, timezone, frost exposure, slots) that plants and sensors attach to.
- audiences: GROW, CGA, HOST
- axis-a: Silver — full CRUD across surface incl. recent climate/timezone dropdowns and GPS zone detection; no stubs.
- axis-b: Silver — clean static analysis, no layering flag; routers modestly sized.
- axis-c: Silver — broad backend unit + API tests, FE component tests; coverage standorte lines 82.6 %/branches 83.3 % (Silver band).
- overall: **Silver**
- improvement-lever: **C** — a CI-run E2E through a grower's "add a site → add a location" workflow plus upper-band coverage would reach Gold.
- rationale: Balanced Silver across all axes; only the systemic C ceiling holds it back.

## C3 — Phasensteuerung / Lifecycle-Engine
- description: Drive a plant through its phase state machine (germination→…→harvest, perennial cycles) with phase-specific targets.
- audiences: GROW
- axis-a: Silver — engine genuinely implemented (#385, after the earlier "inert" state); no stubs found.
- axis-b: Silver — clean; engines moderately sized (`phase_transition_engine.py` 305 lines); complexity unmeasured (systemic).
- axis-c: Silver — very broad unit (28 files) + FE component (19 files) green. *Scanner proposed Gold; overridden to Silver* — no E2E-in-CI and no upper-band coverage number to confirm Gold-C.
- overall: **Silver**
- improvement-lever: **C** — this is the strongest Axis-C candidate; wiring its E2E into CI + a coverage number would make it the first Gold.
- rationale: Deep unit+component coverage; capped by the systemic C ceiling only.

## C4 — Dünge-/Nährstoff-Logik
- description: Compute nutrient plans and mixing order (Silicon→CalMag→Base→Acids), EC-net, area-based dosing.
- audiences: GROW
- axis-a: Silver — full calc path; one non-primary gap: plan-copy endpoint "not implemented yet" (`NutrientPlanDetailPage.tsx:91`).
- axis-b: Silver — clean; 9 advisory react-hooks warnings only.
- axis-c: Silver — rich unit (`test_nutrient_engine.py` 26, `test_nutrient_plan_engine.py` 18, …) + FE component; coverage duengung lines 94.8 %/branches 84.5 %.
- overall: **Silver**
- improvement-lever: **C** — E2E-in-CI; the copy-endpoint gap is the only Axis-A item and is secondary.
- rationale: One of the best-tested capabilities (FE lines already in Gold band); systemic C ceiling holds overall at Silver.

## C5 — Hybrid-Sensorik
- description: Ingest sensor data through the fallback chain (IoT/MQTT → Home Assistant → weather API → manual) with provenance.
- audiences: GROW, HA
- axis-a: **Bronze** (re-graded from Silver on deep-read) — the core sensor path (HA + weather-API + manual, with provenance) is built and reachable, but the deep-read against REQ-005 found significant unbuilt ACs: **fallback stage 1 (direct IoT/MQTT ingestion) is missing** (docs flag it "geplant"), and the **calibration workflow, anomaly/Z-score flagging, quality-scoring/interpolation, and sensor-health/offline auto-task** are absent (`observation_service.py` is CRUD-only; `sensor_ingestion_tasks.py` only has `ingest_ha_readings`). That is a cross-surface completeness gap, not just edge cases. (`weather_adapter.py:52` `NotImplementedError` is a normal ABC default, not a gap.)
- axis-b: Silver — clean; capped by the systemic B ceiling.
- axis-c: Silver — very broad unit (25 files) + API + FE component. `test_observation_repository.py` uncollectable locally (missing `psycopg` in scan venv — env gap, CI installs it).
- overall: **Bronze**
- improvement-lever: **A** — build the missing REQ-005 stages (MQTT ingestion, calibration, anomaly/quality, health) to complete the capability; that lifts A to Silver. See remediation C5-A1…A5.
- rationale: The adapter landscape is broad and well-tested, which masked that half of REQ-005's ACs (auto-ingestion, calibration, anomaly detection, health) are unbuilt — a real completeness gap.

## C6 — Aufgabenplanung
- description: Plan and track tasks/workflows across the grow lifecycle for growers and shared gardens.
- audiences: GROW, CGA
- axis-a: Silver — full path; non-primary gap: workflow-copy endpoint "not implemented yet" (`WorkflowDetailPage.tsx:580`). Note: `TC-REQ-006.md` is mid-edit (uncommitted).
- axis-b: Silver — clean; 6 advisory warnings.
- axis-c: Silver — broad unit + FE component green.
- overall: **Silver**
- improvement-lever: **C** — E2E-in-CI.
- rationale: Solid across axes; systemic C ceiling.

## C7 — Erntemanagement
- description: Record harvests, enforce the Karenz gate, complete harvest for a run/batch.
- audiences: GROW
- axis-a: Silver — implemented incl. run-batch complete-harvest (#415); no stubs.
- axis-b: Silver — clean; 6 advisory warnings.
- axis-c: Silver — unit (`test_harvest_karenz_gate.py`, `test_harvest_complete.py`, `test_harvest_engines.py`) + FE component.
- overall: **Silver**
- improvement-lever: **C** — E2E-in-CI + coverage number.
- rationale: Complete and tested; systemic C ceiling.

## C8 — Post-Harvest
- description: Post-harvest treatment / curing workflows after harvest completion.
- audiences: GROW
- axis-a: Silver — implemented (was a GAP-B1 scaffold in the 2026-04 audit; scanner finds no current stub markers).
- axis-b: Silver — clean; 2 advisory warnings.
- axis-c: Silver — unit + API + FE component (incl. mobile) green.
- overall: **Silver**
- improvement-lever: **C** — E2E-in-CI.
- rationale: Now genuinely built; systemic C ceiling.

## C9 — Dashboard
- description: Aggregate lifecycle/care/harvest metrics into a personalisable dashboard.
- audiences: GROW, CGA
- axis-a: Silver — implemented; hard-coded-zero metrics fixed (#399), personalisation (#378); no stubs.
- axis-b: Silver — clean.
- axis-c: Silver — the **only** capability with a confirmed **contract** tier (`test_dashboard_widgets_contract.py` + `dashboardWidgets.contract.test.ts`), plus unit+component; coverage lines 83.7 % (Silver band) but **branches only 61.3 %**. *Scanner proposed Bronze on the low branch number; overridden to Silver* because line coverage clears the middle band and the tier stack (unit+component+contract) is the strongest in the repo — the weak branch coverage is the improvement note, not a demotion.
- overall: **Silver**
- improvement-lever: **C** — raise branch coverage toward 80 % and add a CI-run E2E of the edit-grid workflow.
- rationale: Best tier breadth in the repo; branch coverage is the soft spot.

## C10 — IPM-System
- description: Integrated pest management — pest/treatment records, detail pages, and photo-based health assessment.
- audiences: GROW
- axis-a: **Bronze** — core IPM (records, detail pages #258) ships, but the health-assessment path is a documented stub: `pest_detection_service.py:186` "TODO(REQ-043): HealthAssessmentEngine ist noch nicht implementiert"; plus open DSGVO/model TODOs in `kindwise_pest_adapter.py:8,69`, `local_pest_adapters.py:104`.
- axis-b: **Bronze** — the same core-path TODO/stub markers sit in the IPM/diagnosis code, below the Silver "no debt in core path" bar.
- axis-c: Silver — unit (26 hits) + FE component; coverage pflanzenschutz lines 85.6 %/branches 76.0 %.
- overall: **Bronze**
- improvement-lever: **A+B** — implement `HealthAssessmentEngine` (REQ-043) and resolve the adapter TODOs; both the A and B tiers rise together and overall reaches Silver.
- rationale: Well-tested shell around an unfinished health-assessment core; the stub drags two axes to Bronze.

## C11 — Externe Stammdatenanreicherung
- description: Enrich species master data from GBIF/Perenual with provenance tracking.
- audiences: GROW, PROV
- axis-a: Silver — GBIF/Perenual adapters + enrichment engine implemented; only a minor informational TODO (`inaturalist_media_client.py:46`).
- axis-b: Silver — clean.
- axis-c: Silver — unit (adapter/engine/model/task) + API tests; server-side capability, no FE tier needed.
- overall: **Silver**
- improvement-lever: **C** — contract test against the external provider seam + a CI-run enrichment path.
- rationale: Solid server-side coverage; systemic C ceiling.

## C12 — Stammdaten-Import
- description: Import master data (CSV) into the catalogue.
- audiences: GROW, CGA
- axis-a: Silver — implemented across surface; no stubs.
- axis-b: Silver — clean, lean router.
- axis-c: **Bronze** — thinnest test base in the master-data area: only `test_import_service.py` + `test_import_engine.py` (unit) and `importSlice.test.ts` + `endpoints/import.test.ts` (FE); **no test for `ImportPage.tsx` itself**, no coverage number.
- overall: **Bronze**
- improvement-lever: **C** — add a component test for `ImportPage` and an integration test through a real CSV parse.
- rationale: Feature is complete but under-verified; Axis C is the gap.

## C13 — Pflanzdurchlauf
- description: Manage planting runs/batches incl. succession plans and per-run phase editing.
- audiences: GROW, CGA
- axis-a: Silver — implemented incl. SuccessionPlan (#361); no stubs.
- axis-b: Silver — clean, but the **highest advisory-warning density** in the repo (22 react-hooks warnings across `PhaseKamiTimeline.tsx`, `PlantingRunDetailPage.tsx`, `SuccessionPlanDialog.tsx`, …).
- axis-c: **Bronze** — many component files, but FE coverage durchlaeufe lines **72.6 %**/branches 66.7 % — below the 80 % middle band.
- overall: **Bronze**
- improvement-lever: **C** — raise line/branch coverage over 80 %; the many components exist but under-exercise their branches.
- rationale: Broad surface, under-covered; the 22 warnings also make it the best candidate to clear once memoization hints are addressed.

## C14 — Tankmanagement
- description: Manage nutrient tanks, fills, and maintenance schedules.
- audiences: GROW
- axis-a: Silver — implemented (v1.6 water-source cascade); no stubs.
- axis-b: Silver — clean; 4 advisory warnings.
- axis-c: Silver — unit (`test_tank*`) + FE component (`TankDetailPage`, `TankStateChart`, `tanksSlice`); coverage unavailable (not in snapshot).
- overall: **Silver**
- improvement-lever: **C** — E2E-in-CI + a measured coverage number.
- rationale: Complete and reasonably tested; systemic C ceiling.

## C15 — Kalenderansicht
- description: Aggregate tasks, phases, and sowing windows into a calendar (incl. light-mode iCal token).
- audiences: GROW, CGA
- axis-a: **Bronze** — aggregation is incomplete on its primary path: `calendar_aggregation_engine.py:19` "TODO: Update AQL to also traverse HAS_PHASE_SEQUENCE edges once PhaseSequence migration is complete" — phase-sequence events are not yet aggregated.
- axis-b: **Bronze** — the same core-engine TODO is a functional debt marker in the aggregation logic.
- axis-c: Silver — unit (`test_calendar_service.py`, `test_calendar_aggregation_engine.py`, `test_sowing_calendar_engine.py`) + FE component.
- overall: **Bronze**
- improvement-lever: **A+B** — finish the aggregation AQL to traverse `HAS_PHASE_SEQUENCE` edges; that closes the completeness gap and clears the core-path debt marker.
- rationale: Tested but functionally incomplete on the aggregation path.

## C16 — InvenTree-Integration (optional)
- description: Optional two-way inventory sync with an InvenTree instance.
- audiences: HOST, GROW
- axis-a: Silver — implemented (#513, after being a scaffold); optional by design.
- axis-b: Silver — clean.
- axis-c: **Bronze** — unit + API + sync-engine tests exist, but only **one** FE page test and no coverage number; thin for the FE surface.
- overall: **Bronze**
- improvement-lever: **C** — broaden FE/integration coverage. Low priority given the optional nature.
- rationale: Backend solidly tested, FE thin; Axis C is the gap but the capability is opt-in.

## C17 — Vermehrungsmanagement & Lineage
- description: Track genetic lineage (descended_from edges), clones, seed crosses, grafting, division.
- audiences: GROW
- axis-a: Silver — implemented (#537 + clonal continuation #390); no stubs.
- axis-b: Silver — clean.
- axis-c: Silver — unit + API + one of the repo's **3 real integration tests** (`tests/integration/test_propagation_lineage_tenant_isolation.py`), though it is `skip`-marked without a live ArangoDB locally. *Scanner proposed Gold; overridden to Silver* — no E2E-in-CI/upper band, and the integration test is skipped in the local run.
- overall: **Silver**
- improvement-lever: **C** — ensure the integration test runs in CI (ArangoDB service) and add an E2E through a lineage workflow.
- rationale: Has an integration tier most capabilities lack; systemic C ceiling holds it at Silver.

## C18 — Umgebungssteuerung & Aktorik
- description: Close the sensor→actuator control loop with hysteresis and a priority system.
- audiences: GROW, HA
- axis-a: **Bronze** (re-graded from Silver on deep-read) — the **backend is complete** (schedules, rules incl. hysteresis/compound/safety, manual override, phase-control profiles, dry-run, emergency-stop, energy, HA status via `actuators/tenant_router.py`), but **there is no UI** for any of it: `EnvironmentControlPage.tsx` offers only actuator CRUD + turn_on/off + `fire_alarm`. Silver-A requires completeness across the full surface (API+UI) — the primary grower workflow (create a schedule/rule, set an override, view the event log) is unreachable in the UI. Docs honestly flag this as "API only".
- axis-b: Silver — clean; capped by the systemic B ceiling.
- axis-c: Silver — unit (`test_actuator_service.py`, `test_actuator_control_engine.py`) + FE component (`EnvironmentControlPage`) for the built surface.
- overall: **Bronze**
- improvement-lever: **A** — build the control UI (schedules, rules, override, phase profiles, event log, energy) against the existing endpoints; that lifts A to Silver. See remediation C18-A1…A3.
- rationale: A fully-built control backend with no operator-facing UI is a genuine cross-surface completeness gap, not an edge case; the scanner saw the backend and missed the missing UI.

## C19 — Substratverwaltung
- description: Manage substrates and mixes, with substrate-independent nutrient adaptation.
- audiences: GROW
- axis-a: Silver — implemented incl. seed substrates (#398); no stubs.
- axis-b: Silver — clean; 4 advisory warnings.
- axis-c: Silver — unit + broad FE component (5 tests).
- overall: **Silver**
- improvement-lever: **C** — E2E-in-CI + coverage number.
- rationale: Complete and tested; systemic C ceiling.

## C20 — Onboarding-Wizard
- description: Guide a new user/tenant through initial setup.
- audiences: GROW, CGA
- axis-a: Silver — implemented; one cross-feature TODO (`onboarding_service.py:240` "TODO: REQ-027 — full mode-switch integration", shared with C26). Primary onboarding path complete.
- axis-b: Silver — clean; 2 advisory warnings.
- axis-c: **Bronze** — only `test_onboarding_engine.py` (unit) + two FE slice/endpoint tests; **no test for `OnboardingWizard.tsx` or its `steps/`**.
- overall: **Bronze**
- improvement-lever: **C** — add component tests driving the wizard and its steps.
- rationale: Built but the multi-step UI itself is untested; Axis C is the gap.

## C21 — UI-Erfahrungsstufen
- description: Adapt UI depth to the user's experience level (beginner/intermediate/expert) and module visibility.
- audiences: GROW
- axis-a: Silver — implemented as a cross-cutting concern (enums, onboarding, widget catalog, user preferences).
- axis-b: Silver — clean; spread across modules with no single home (inherent to the feature).
- axis-c: **Bronze** — **no dedicated test** for experience levels; only indirect coverage via `onboardingSlice`, `userPreferencesSlice`, `ModuleGuard`, `useModuleVisibility` tests.
- overall: **Bronze**
- improvement-lever: **C** — add a dedicated test asserting UI adapts per experience level.
- rationale: A genuine capability with only incidental verification; Axis C is the gap.

## C22 — Pflegeerinnerungen
- description: Generate season- and hemisphere-aware care reminders (9 presets, FAMILY_CARE_MAP, overwintering).
- audiences: GROW
- axis-a: Silver — implemented incl. OverwinteringProfile (#360) and interval reschedule; no stubs.
- axis-b: Silver — clean.
- axis-c: Silver — broad unit (8 files); FE coverage pflege lines 89.0 % but **branches 54.7 %** on the measured slice (partial snapshot — only `SpringReturnAssistant.tsx` measured).
- overall: **Silver**
- improvement-lever: **C** — raise branch coverage and measure the full `pflege` FE tree.
- rationale: Strong backend verification; branch coverage is the soft spot.

## C23 — Benutzerverwaltung & Authentifizierung
- description: Local + federated (OIDC) auth, JWT access/refresh, service accounts for M2M.
- audiences: GROW, CGA, HOST, GDPR
- axis-a: Silver — broad implementation (14/14 in the audit); no stubs.
- axis-b: Silver — clean; 13 advisory warnings in `pages/auth`.
- axis-c: Silver — broad unit (OAuth engine, callbacks, platform-admin, remember-me, light/full providers) + 15 FE auth pages; coverage auth lines 84.3 %/branches 75.7 % (right at the hard 75 % gate).
- overall: **Silver**
- improvement-lever: **C** — E2E through a real login/refresh flow in CI + lift branch coverage above the gate margin.
- rationale: Security-critical and well-built; systemic C ceiling.

## C24 — Mandantenverwaltung & RBAC
- description: Tenant isolation, per-tenant roles (admin/grower/viewer), permission matrix, invitations.
- audiences: CGA, HOST
- axis-a: Silver — broad implementation (11/11); no stubs.
- axis-b: Silver — clean.
- axis-c: Silver — very broad unit (17 hits: tenant guards, purge, ownership, scope guard) + API; FE page tests not individually confirmed.
- overall: **Silver**
- improvement-lever: **C** — a cross-tenant negative E2E (the exact scenario NFR-015 covers only against the deployed app) run in CI.
- rationale: Deep backend isolation testing; systemic C ceiling. Cross-tenant leakage is security-sensitive — the E2E lever here is worth more than elsewhere.

## C25 — Datenschutz & Betroffenenrechte (DSGVO)
- description: Self-service DSGVO subject rights (Art. 15–21), retention enforcement, consent, erasure.
- audiences: GDPR, GROW
- axis-a: Silver — implemented (5/5). Note: `privacy_service.py:274` has an `except NotImplementedError:` guard — a path worth confirming is fully wired.
- axis-b: Silver — clean.
- axis-c: Silver — broad unit (11 hits: privacy/erasure/retention/consent) + FE page.
- overall: **Silver**
- improvement-lever: **C** — E2E through an erasure/export request in CI; confirm the guarded path in Axis A.
- rationale: Legally significant and well-tested; systemic C ceiling.

## C26 — Light-Modus (anonymer Zugang)
- description: Anonymous, auth-bypassed operation for a single-user light deployment.
- audiences: GROW, HOST
- axis-a: Silver — implemented (4/4) via feature guard + settings; the mode-switch integration TODO (C20) is the one loose end.
- axis-b: Silver — clean; feature-flag mechanics across 9 backend files.
- axis-c: **Bronze** — `test_seed_light_mode.py` + `MainLayout.light.test.tsx` + scattered touches, but **no cohesive suite** for the full light-mode path.
- overall: **Bronze**
- improvement-lever: **C** — a cohesive light-mode test suite covering the auth-bypass and module-visibility path end to end.
- rationale: A cross-cutting deployment mode verified only in fragments; Axis C is the gap.

## C27 — Mischkultur & Companion Planting
- description: Graph-based companion-planting compatibility recommendations for outdoor beds.
- audiences: GROW
- axis-a: Silver — implemented (edges + engine); no stubs.
- axis-b: Silver — clean (1 advisory warning).
- axis-c: Silver — unit (`test_companion_planting_engine.py`) + API + FE component.
- overall: **Silver**
- improvement-lever: **C** — E2E-in-CI.
- rationale: Complete and tested; systemic C ceiling.

## C28 — Druckansichten & Export
- description: Print views and data export (PDF via weasyprint, iCal, data export).
- audiences: GROW, CGA
- axis-a: Silver — implemented; no stubs.
- axis-b: Silver — clean; weasyprint (PDF) is a core dependency.
- axis-c: **Bronze** — narrow base (3 backend, 2 FE); the two print tests were uncollectable locally (missing `tinyhtml5` in the scan venv — env gap, present in CI), so effective verification is thin.
- overall: **Bronze**
- improvement-lever: **C** — broaden print/export tests and ensure the PDF-render deps are exercised in CI.
- rationale: Built but under-verified, and its tests are env-fragile; Axis C is the gap.

## C29 — Wissensassistent / RAG
- description: Natural-language plant/care assistant backed by the RAG knowledge service.
- audiences: GROW
- axis-a: Silver (re-graded from Unrated — scanner false-flag) — the scanner's "core stub" `ki_assistent_service.py:16 KiAssistentService.answer` is **dead orphaned code**: grep confirms the class is referenced only by itself. The real, user-facing path is `AiAssistantService` (`ai_assistant_service.py:54`, wired via `get_ai_assistant_service` at `dependencies.py:1440` → public/tenant/global routers), covering all four REQ-031 functions + light-mode + KS-failure fallback (W-011) + the 3-stage consent toggle. End-user docs exist DE/EN. Core path complete and reachable → Silver; Gold needs edge-case tests + operator/GDPR docs.
- axis-b: Silver (re-graded from Bronze) — once the dead `KiAssistentService` scaffold is deleted (remediation C29-A1), the only local debt marker is gone; the real service is clean and docstring-documented. Capped by the systemic B ceiling.
- axis-c: Silver (re-graded from Bronze) — the real path has unit (`test_ai_assistant_service.py`), API (`test_ai_endpoints.py`) and E2E (`test_req031_ki_assistent.py`), plus FE `components/ai/*.test.tsx`. Gap: no dedicated `KIAssistentPage.tsx` component test and no KS-schema contract test.
- overall: **Silver**
- improvement-lever: **C** — add a `KIAssistentPage` component test + a knowledge-service schema contract test (and delete the dead scaffold to clear the false flag). See remediation C29.
- rationale: The "Unrated" was a bottom-up scanner artefact on a dead scaffold; the real assistant is a wired, tested Silver-tier capability.

## C30 — Pflanzenfoto-Galerie & Foto-Erkennung
- description: Plant-photo gallery plus photo-based plant/pest identification (PlantNet phase 1, DINOv2 few-shot).
- audiences: GROW
- axis-a: Silver (re-graded from Bronze — scanner false-flag) — the scanner's stub `vision_engine.py:18 VisionEngine.normalise_predictions` is **dead orphaned code** (grep confirms no referent); prediction normalisation already happens inline in the identification adapters (`local_embedding_adapter.identify`, `plantnet_adapter`), which ship (DINOv2 #256, PlantNet) and are E2E-tested (`test_req029_recognition.py`). `local_embedding_adapter.py:86`/`plantnet_adapter.py:155` `NotImplementedError` on `diagnose()` is the documented, gated out-of-scope health branch (correct capability contract, not a gap). Core identification + gallery + object storage (NFR-013) complete → Silver.
- axis-b: Silver (re-graded from Bronze) — once the dead `VisionEngine` scaffold is deleted (remediation C30-A1), no local debt marker remains; capped by the systemic B ceiling.
- axis-c: Silver — unit (14 hits) + FE component (recognition pages lines 86.7 %/branches 82.4 %). `test_s3_adapter.py` had 3 local failures (missing `boto3` — env gap; mock with `moto` — C30-C1).
- overall: **Silver**
- improvement-lever: **C** — lift recognition branch coverage to 90 %, harden `test_s3_adapter` against the boto3 env-gap, add an inference-client contract test (and delete the dead scaffold). See remediation C30.
- rationale: A well-tested UI over a working recognition core; the Bronze was a bottom-up scanner artefact on a dead scaffold.

## Open items

- **Scanner false-flags corrected (C29, C30).** Two `NotImplementedError` markers the scanner read bottom-up as "crashing core paths" are **dead orphaned scaffolds** (`KiAssistentService.answer`, `VisionEngine.normalise_predictions` — only self-referenced, verified by grep). The real paths (`AiAssistantService`, the identification adapters) are wired and tested. C29 moved Unrated→Silver, C30 Bronze→Silver. **Remediation deletes the dead scaffolds** (C29-A1, C30-A1) so a re-scan won't re-flag them. Lesson: a bottom-up stub marker is *evidence*, never a tier — the deep-read is what decides.
- **C5, C18 re-graded down (Silver→Bronze) on cross-surface gaps the surface scan missed.** C5: REQ-005's auto-ingestion stage (MQTT), calibration, anomaly/quality and sensor-health are unbuilt. C18: the control backend is complete but has **no UI** for schedules/rules/override. Both are genuine Axis-A completeness gaps.
- **C10 / C15 — genuine core-path gaps** hold Axis A (and B) at Bronze: `HealthAssessmentEngine`/REQ-043 is truly unbuilt (spec status `Entwurf`); the calendar aggregation AQL silently drops PhaseSequence-driven plants. These are real, not scanner artefacts.
- **C1 — NFR-001 layering violation** is the only structural code-quality defect found; mechanical to fix and worth prioritising because C1 is a reference pattern.
- **Stale "not implemented yet" comments (C4, C6).** The copy-as-template buttons are disabled with obsolete comments — the backend endpoints already exist; only the UI wiring (+ an `as_template` flag) is missing. Quick wins.
- **Systemic tooling gaps** (recorded in the header) cap Axes B and C at Silver app-wide: no complexity/duplication/SAST tooling, mypy not in CI, backend coverage not measured in CI, E2E suite not in CI. Two portfolio-level moves would unlock Gold grading everywhere — they belong to `roadmap-plan`, not this advisory matrix.
- **Axis A not promoted to Gold per capability**: this top-down pass did not verify end-user docs + edge-cases per capability. A focused `reassess` on a specific capability can establish Gold-A.
- **Coverage numbers** are available for only ~10/30 capabilities (partial frontend v8 snapshot; no backend coverage in CI). Axis C for the rest was graded on **test-tier presence + pass status**, not a coverage %, and says so.
- **Per-audience divergence**: no capability showed a *material* maturity split between its mapped audiences this pass (e.g. C5's GROW and HA paths are both built and tested); recorded as none.
