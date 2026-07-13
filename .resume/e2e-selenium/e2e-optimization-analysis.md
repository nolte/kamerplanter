# E2E Suite Optimization Analysis — faster, more meaningful feedback

_Question: how do we get a meaningful result faster? 702 E2E tests feels like a lot._

## Governing spec (binding, not just advisory)

The robust-UI-test rules live in **`spec/project/e2e-test-automation/`** (+ the tier
model in `spec/project/test-pyramid-foundation/`, component tier in
`spec/project/test-tier-component/`). Several items below are therefore **spec
compliance**, not optional tuning:

- **§Deterministic waiting** — "Tests **MUST NOT** use fixed-duration sleeps; every
  wait **MUST** be an explicit condition." A fixed sleep **MAY** appear only inside a
  page object, only for a bounded animation/debounce, with a justifying comment and a
  small bound. → the 112 `time.sleep()` are mostly **violations**, not just latency.
- **§Locator strategy** — mandatory hierarchy `data-testid → id → role/semantic → CSS
  → XPath (last resort)`; **position-based XPath is forbidden** and selectors **MUST**
  survive cosmetic markup changes. → `.MuiSelect-select`, `cells[N]`, and
  `contains(text(), label)` are non-conformant; the R6 testids restore conformance
  (see `robustness-audit.md`).
- **§Test-tier completeness** — "The **E2E tier MUST** be reserved for user-journey
  verification, not for logic better tested a tier down." → the 702 count is the apex
  over-populated with tier-down logic. (The foundation forbids fixed cross-tier
  ratios, so "how many E2E" is a judgement per that rule, not a target.)
- **§Reference profile** — "The browser fixture **MUST** be session-scoped." →
  kamerplanter runs **function-scope** (documented wizard-state-bleed reason); this is
  a justified deviation whose cost is precisely the per-test overhead measured below.

## Measured baseline (this repo, light/desktop, 4 xdist workers)

| Metric | Value |
|---|---|
| E2E test functions | **702** (≈75 files) |
| Backend unit tests (pytest) | ~4891 |
| Frontend tests (vitest) | 334 files |
| Full light run | **~70–75 min** |
| Per-test duration | **median 21 s · p90 55 s · max 121 s** |
| Duration buckets (sample 322) | <5s: 59 · 5–15s: 88 · 15–30s: 74 · 30–60s: 75 · >60s: 26 |
| `time.sleep()` calls in page objects | **112** |
| `implicitly_wait` | **10 s** (conftest.py:588) |

**Two independent problems, two independent levers:**
1. **Too many E2E tests** (the top of the pyramid is over-populated).
2. **Each test is too slow** (a ~21 s median even for trivial assertions).

## Diagnosis

### 1. Inverted-ish pyramid at the top — hundreds of E2E tests test the wrong tier

The base is healthy (4891 backend + 334 frontend test files), but **702 is far too many E2E tests** — the E2E tier should be *dozens* of true cross-layer journeys, not hundreds of field-level checks. Name-pattern scan of demotion candidates (component/unit-tier behaviour currently paying the full E2E cost):

| Pattern | Count | Belongs in |
|---|---|---|
| `test_*_shows_*` | 98 | component (vitest) |
| `test_*_button*` | 66 | component |
| `test_*_renders/_displays*` | 46 | component |
| `test_*_visible*` | 40 | component |
| `test_*_validation/_validates/_required*` | 21 | component / unit |
| `test_*_empty*` | 17 | component |
| `test_*_disabled/_default*` | 16 | component |

Concrete example — `test_req003_phasensteuerung.py` alone spends **17 min** on 32 tests including `test_transition_dialog_shows_reason_field`, `_confirm_button_disabled_without_selection`, `_shows_target_phase_select`, `_reason_default_value` — each **33 s** to assert one prop of the `PhaseTransitionDialog`. A **vitest component test** does the same in **<100 ms**, with no browser, no stack, no flake.

A single true journey (`test_drive_phase_forward`, 69 s) is worth 20 of those field checks — *that* is what E2E is for.

### 2. Per-test overhead dominates — the ~21 s median

Even fast tests rarely dip under 5 s. Fixed costs paid **per test**:

- **`implicitly_wait(10)` (biggest single lever).** Mixed with explicit `WebDriverWait`, every *absence* check and every locator-fallback miss blocks up to **10 s**. The robustness fallback chains (`open_select`, the `.MuiSelect-select` legacy fallbacks, `is_present` on missing elements) each pay this. This is an anti-pattern — implicit and explicit waits should never be mixed.
- **112 fixed `time.sleep()`** in page objects — pure dead time + a flake source.
- **Function-scope browser** — a fresh Remote WebDriver session per test (~1–2 s alloc+quit ×702). Documented as necessary for wizard state-bleed, but most read-only tests don't need it.
- **UI-based data provisioning** — the self-provisioning journeys build data through the create dialogs (species→plant→…), ~**64 s mean**. The seed fixture already does the same via API in ~1 s.
- **180 s backend seed** on every stack bring-up (fixed per run, not per test).

## Recommendations (prioritized by impact ÷ effort)

### Tier 1 — quick wins (hours, no test rewrite, big % off the clock)

1. **Remove `implicitly_wait(10)`** → set `0` and rely on explicit condition waits. Every absence-check and locator-fallback stops paying 10 s. Expect the largest single reduction. (Requires auditing a few page objects that lean on implicit waits.)
2. **Delete the 112 `time.sleep()`** → replace with `wait_for_element_*` /
   `wait_for_element_hidden` (the robustness pass already started this pattern).
   **Spec-mandated** (§Deterministic waiting: sleeps forbidden except a commented,
   bounded animation/debounce inside a page object) — so this is compliance, not just
   speed.
3. **`--durations=25`** on every run to keep the slow tail visible; **`-p no:randomly`**-style stable ordering for reproducibility.
4. **Raise parallelism** to host cores: bump xdist `-n` and Chrome `SE_NODE_MAX_SESSIONS` / add chrome replicas. Wall-clock scales ~linearly until the stack saturates.

### Tier 2 — the real answer to "700 is too many" (days, structural)

5. **Rebalance the pyramid: demote the field/component-level E2E tests to vitest
   component tests.** **Spec-mandated** (§Test-tier completeness: the E2E tier MUST be
   reserved for user-journey verification, not logic better tested a tier down). Rule
   of thumb to keep as E2E: *does it cross ≥2 layers and exercise a real user journey
   end-to-end?* If it asserts one dialog field / button state / empty state / label →
   it's a component test. The foundation forbids fixed cross-tier ratios, so treat the
   target as "a lean journey set" (order of ~100–150 here) — a judgement, not a quota.
   Tooling: the `nolte-engineering:test-pyramid-check` skill audits tier completeness
   against the foundation + E2E discipline; `nolte-engineering:component-test-generator`
   scaffolds the replacements.
6. **Provision journey data via API, not the UI.** Extend the `e2e_seed_data` fixture pattern (or a helper) so journeys start from seeded state and only the *asserted* interaction runs through the browser. Cuts the 64 s-mean journeys to seconds.

### Tier 3 — tiering for fast feedback (the "meaningful result faster" ask)

7. **Three tiers, not one 700-test run:**
   - **`smoke`** (already marked) — trimmed to a true <10 min core-path gate for local/PR feedback.
   - **`core`** — the ~dozen self-provisioning journeys: the confidence signal.
   - **full** — nightly / on-demand only (there is deliberately no CI job — GH runners too weak).
   Give a fast `task test:e2e:core` so a developer gets a meaningful answer in minutes, not 75.

### Tier 4 — infra

8. **Session/class-scope browser** for read-only test classes (keep function-scope only for the wizard/state-mutating ones the conftest comment calls out).
9. **Snapshot the seeded DB volume** and reuse it to skip the 180 s seed per run.

## Measured result (Tier 1, partial — implicit wait only)

Reducing `implicitly_wait(10) → 3` (one line, no test-behaviour change) already
**cut the smoke suite from 52:17 to 20:37 — a ~2.5× speedup**, same set green
(`141 passed · 42 skipped · 5 xpassed · 0 failed`). Confirms the diagnosis: the mixed
implicit/explicit wait was the dominant per-test cost (every absence-check and
locator-fallback miss paid the full 10 s). Removing the 112 `time.sleep()` and moving
implicit → 0 (with explicit waits everywhere) compounds this further.

## Expected outcome

- Tier 1 (implicit wait + sleeps + parallelism) roughly **halves-or-better** wall-clock
  with zero test-behaviour change — **measured 2.5× on smoke from the wait change alone**.
- Tier 2 (pyramid rebalance) is the structural fix: **702 → ~150 E2E**, most former E2E coverage running 100–1000× faster as component tests, and far less flake.
- Net: a **meaningful PR/local signal in single-digit minutes** (smoke+core), full E2E reserved for nightly.

## Appendix — concrete Tier-2 demotion plan (measured)

A full classification of the 702 tests against the journey-vs-single-surface rule:

| Bucket | Tests | Share | Runtime @ ~21 s |
|---|---|---|---|
| **DEMOTE** (single-surface / logic → vitest component/unit) | **~526** | **~75 %** | ~184 min |
| **KEEP** (true cross-layer journey) | **~176** | **~25 %** | ~62 min |

**~3 of 4 E2E tests assert component-level behaviour.** Demoting them reclaims ~3 h
of E2E wall-clock per full run and leaves a lean ~176-journey suite.

**Top demotion clusters** (biggest savings; "extend" = a vitest test exists,
"create" = new `src/frontend/src/test/pages/*.test.tsx`):

| E2E source | ~Demote | Target component | vitest |
|---|---:|---|---|
| `test_req002_standorte.py` | 30 | SiteList/Detail, LocationDetail, SiteCreateDialog | extend |
| `test_req003_phasensteuerung.py` | 28 | **PhaseTransitionDialog** + PlantInstanceListPage | mixed (dialog: create) |
| `test_req014_tank.py` | 26 | TankList/Detail | mixed |
| `test_req004_fertilizer.py` | 20 | Fertilizer list/dialog/detail | mixed |
| `test_req004_nutrient_calculations.py` | 20 | **pure calc → `*.ts` unit test** | extend/move |
| `test_req020_onboarding_wizard.py` | 19 | onboarding step components | create |
| `test_req021_experience_level.py` | 18 | ExperienceLevelStep + level-gated dialogs | create |
| `test_req004_nutrient_plan.py` | 18 | NutrientPlanDetail | extend |
| `test_req013_planting_run.py` | 18 | PlantingRun list/detail | create |
| `test_req022_pflege_dashboard.py` | 17 | PflegeDashboard, CareConfirmDialog | create |

**Exemplar (recommended first migration):** `TestPhaseTransitionDialog`
(`test_req003_phasensteuerung.py`, ~7 field-assert tests, each ~33 s and
self-provisioning a live plant just to open one dialog) →
one `src/frontend/src/test/pages/PhaseTransitionDialog.test.tsx` (~10 ms):
`shows target-phase-select / reason field / reason default 'manual' / confirm
disabled without selection / reason editable / cancel closes / opens`. The two
genuinely cross-layer tests in that file (`_cancel_preserves_phase`, the
`TestCoreLifecycleJourneyPhaseTransitions` journeys) stay at the E2E tier.

**Execution order:** (1) create the exemplar `PhaseTransitionDialog.test.tsx`
(proves the pattern, removes 7 slow tests); (2) extend existing vitest tests for
the "extend" clusters (lowest friction); (3) create new component tests for
planting-run / onboarding / experience-level / pflege-dashboard; (4) move pure
logic (nutrient calc math, botanical-family validation rules, i18n) down to unit
tests. Audit with `nolte-engineering:test-pyramid-check`; scaffold replacements
with `nolte-engineering:component-test-generator`.
