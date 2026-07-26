# ADR-010: BDD Architecture for the E2E Suite (pytest-bdd, TC-004-092 as Proof of Concept)

**Status:** Accepted
**Date:** 2026-07-25
**Decision-makers:** Kamerplanter Development Team

## Context

Issue #761 asked whether the existing, purely Selenium/page-object-based E2E suite (`tests/e2e/`, 722 tests) should be complemented or replaced by a Gherkin/BDD layer in which test cases can be derived directly from the TC documents (`spec/e2e-testcases/`). The task explicitly did **not** ask for an opinion but for a substantiated proof of concept on exactly one test case — TC-004-092, "A single watering is reflected consistently in the global watering log, the plant's own watering log, and the task history" — plus a go/no-go recommendation, judged against six named criteria: spec-to-test traceability, authoring ergonomics, integration cost, reproducibility, reporting, and migration path.

The constraint for every option: no second test runner. The existing suite already has fixtures, `pytest.ini`, two orthogonal selection axes (`req<NNN>` derived from the filename, `FEATURES` as a module tuple), `--strict-markers`, `xdist` parallelism (`-n 4 --dist=loadfile`), JUnit XML with a `tc_id` property, and a Markdown protocol (`protokoll.md`) as the human-facing audit trail (NFR-008 §4.4). Any BDD solution had to fit into that, not sit beside it.

The portfolio had already pre-decided the framework question: `spec/project/behavior-driven-development/` (in the shared `claude-shared` repository) names Gherkin and the Cucumber family as its illustrative reference profile. The PoC had to substantiate that decision empirically, not reopen it.

The classic test `test_req004_watering_cross_view_consistency.py` (from PR #763, sister issue #760) served as the comparison baseline and remained unchanged throughout the PoC — replacing it before the go/no-go call would have defeated the PoC's purpose.

## Decision

We adopt **pytest-bdd** as a BDD layer **on top of** the existing Selenium/page-object suite, with Gherkin scenarios under `tests/e2e/features/*.feature` and step bindings in dedicated `test_req<NNN>_*_bdd.py` modules that access the browser exclusively through the existing page objects.

**Go, qualified** — not as a blanket migration of all ~90 REQ-004 test cases, but:

1. **Go** for newly written E2E test cases whose behavior fits a single, declarative scenario with clear Given/When/Then boundaries (typically: one user workflow, one cross-view consistency claim).
2. **Go** for the machine-checked traceability gate (`scripts/check_bdd_traceability.py`) as a standalone, reusable tool — independent of how much of the suite is BDD.
3. **No-go** for a blanket, short-term migration of the existing 722 classic tests. The integration cost (four previously undiscovered defects, see below) and the measured reuse yield justify a planned, incremental migration alongside new/changed test cases, not a big-bang rewrite.
4. **No-go** for `behave` or a second test runner (see the comparison below).

The classic test remains in place; both TC-004-092 implementations keep running in parallel permanently as a live dual-use proof for the shared page objects.

## Rationale

### 1. Spec-to-test traceability

Every BDD scenario carries a `@TC-<REQ>-<NNN>` tag (here `@TC-004-092`), carried through to the report via the JUnit `tc_id` user-property and the `protokoll.md` line. `scripts/check_bdd_traceability.py` verifies this binding **mechanically and in both directions**: a tag that resolves to no `## TC-<id>: <title>` heading under `spec/e2e-testcases/` is an error ("orphan tag"); a scenario with no tag at all is likewise an error ("untagged scenario"). The reverse direction — a declared test case without a scenario — is deliberately **not** an error, only an informational count: automation coverage grows over time.

The honest finding here: the check was deliberately **not** extended to the docstring-based TC-IDs of the classic tests (the `TC-REQ-004-W001` shape). `tests/e2e/README.md` openly documents that those test-declared IDs have already drifted from the spec IDs (`TC-004-NNN`). Extending the check would immediately report a mass of pre-existing defects — not because BDD broke anything, but because that drift predates it. That is exactly the argument **for** BDD traceability, not against it: the tag mechanism prevents the same drift from recurring for new scenarios, because it is enforced by an active gate instead of relying on docstring discipline.

### 2. Authoring ergonomics

The Gherkin language is English — an operator decision (2026-07-24), justified by NFR-003 (source code is English) and readability across the multilingual portfolio. For German-speaking, non-technical contributors this is a real cost: a gardener wanting to check a test case against `spec/e2e-testcases/TC-REQ-004.md` (German) has to read the English `.feature` file — the only bridge between the two is the `@TC-004-092` tag, not a translation. This is a deliberate trade-off, not a side effect.

That language alone is no guarantee of clean domain vocabulary is shown by the advisory editorial review pass over the scenario (P2): 0 critical findings, but a genuine vocabulary drift between "care task" and "watering task" in the first draft — a defect a plain code review (diffing Python assertions) would not have caught, because it lives in prose, not logic. All four findings (1 warning, 3 suggestions) were adopted.

The step vocabulary is now fully parameterized (see migration path below): counts and days are regular-expression parameters, never literal values baked into step text. That further lowers the ergonomics barrier for *reading* a scenario — a reader with no Selenium knowledge can understand `Given the plant has 1 watering task due` and reuse it unchanged for a different case (`3 watering tasks due`) without writing a new binding.

### 3. Integration cost

This is the heaviest finding of the PoC and is deliberately not soft-pedalled. **Four distinct defects** had to be fixed before a single scenario could run at all — all empirically documented in the audit trail (`.audits/issue-orchestrate/761/analysis.md`).

- **Hazard A** — pytest-bdd translates every Gherkin tag into a pytest marker without any validation (`getattr(pytest.mark, tag)`, no auto-registration). Under `--strict-markers`, a single unregistered tag does **not** fail one test — it produces a **collection error that aborts the entire run with exit code 2**, so all 722 existing tests then do not run at all. Observed: `Failed: 'TC-004-092' not found in markers configuration option`.
- **Hazard B** — pytest-bdd unconditionally overwrites `scenario_wrapper.__doc__` with `"<feature>: <scenario>"`, with no `functools.wraps`. The docstring channel that carries the classic tests' TC-ID into JUnit and `protokoll.md` is therefore structurally dead for BDD scenarios.
- **Hazard C** — discovered unprompted, and safety-critical for the acceptance criteria: `item.location[0]` points into site-packages for a pytest-bdd scenario instead of the calling module. The REQ axis `conftest.py` derives from it therefore **silently vanished** — `-m watering` found the scenario, `-m req004` did **not**, with no error at all. An acceptance criterion would have gone unmet without anyone noticing.
- **Dead hook** — a `pytest_bdd_after_step` hook defined inside the step module (`test_*.py`) itself is never registered by pytest's plugin manager and never fires; it has to live in `conftest.py`, where pytest looks for auto-registered plugins.

A related finding that bears on the reporting evaluation: the TC-ID has to be explicitly carried through `checkpoint.jsonl` for the `-n 4 --dist=loadfile` controller to reconstruct it — without that, it would be correct in a direct run and silently missing in the parallel CI run, a defect class that never shows up locally.

All four defects are now fixed (tag registration with a schema guard in `pytest_configure`, TC-ID derivation via the marker channel instead of the docstring, `item.path.name` instead of `item.location[0]`, moving the hook into `conftest.py`) and documented in `tests/e2e/README.md`. That does not change the core finding: **none of these four defects is obvious from the pytest-bdd documentation** — every one of them only surfaced through the real integration attempt. A team adopting BDD without this experience would hit the same four traps again.

### 4. Reproducibility

The scenario passed in the containerized stack, repeatedly, and in parallel under `-n 4 --dist=loadfile` on separate workers alongside the classic test — collision-free, thanks to a unique instance ID per run. It is self-provisioning: no dependency on pre-loaded seed data, no `pytest.skip` (NFR-008a). Verification (`nolte-engineering:e2e-test-reviewer`, P6-final) confirmed all seven required proofs: BDD solo run, classic solo run, repeats of each, parallel run, JUnit `tc_id` surviving the xdist merge, the protocol entry, and the correct screenshot count.

### 5. Reporting

The JUnit `tc_id` property survives the xdist merge. `protokoll.md` lists the scenario under test-case ID `TC-004-092` (this incidentally fixed a pre-existing bug independent of the BDD layer: `protocol_plugin.py` previously matched only the `TC-REQ-\d{3}-\d{3}` pattern, so the actually-used `TC-004-092` shape had already been missing from every protocol before this PoC — including the classic test's own, from PR #763).

One genuine, BDD-specific upside: screenshots are no longer hand-placed inside the test body (`screenshot("TC-004-092_view1-global", …)`, as in the classic test), but derived automatically from the Gherkin step text via the `pytest_bdd_after_step` hook. The final run produced **exactly 9 screenshots** for 1 `When` and 8 `Then` steps, none for the three `Given` steps — the hook correctly filters on `step.type` (the resolved step type), not `step.keyword` (the literal Gherkin word, which for an `And`-continued `Given` incorrectly reads `"And"` and, without the fix, would have photographed the precondition line too).

### 6. Migration path

The estimate rests on a **measured**, not guessed, ratio from the review pass: before parameterization, 5 of 9 steps had a count or a date baked directly into the step text, and 5 of 9 bindings were usable only for TC-004-092. After parameterization, **0 of 11 bindings** are bespoke, **9 of 11** are reusable as written. The remaining 2 are specialized to a plain, unfertilized watering — that is a different domain behavior (no fertilizer channel involved), not duplicated plumbing.

**Derivation for the ~90 REQ-004 cases:** assuming a substantial share of the remaining cases are variants of the same pattern (different quantities, a different application method, different starting states of the watering logs) — an assumption, not a measurement — the existing vocabulary (watering volume, application method, day token, count deltas) covers a meaningful share without new bindings. New bindings are only needed where a genuinely new domain concept is introduced (e.g., fertilizer channels, EC values, tank references) — not where only a parameter varies. A defensible effort estimate still requires triaging the ~90 cases along exactly that split (parameter variant vs. new concept) before a person-day figure can be named; that triage is itself a sensible next work item, not part of this PoC.

### `pytest-bdd` vs. `behave`

`pytest-bdd` was chosen because it **reuses rather than forks** the existing toolchain: the same fixtures (`conftest.py`), the same `pytest.ini`, the same two selection axes, the same `xdist` parallelism, the same page objects, the same JUnit/protocol reporting. `behave` is a standalone runner with its own fixture model (environment hooks instead of pytest fixtures) and would have forked every one of those building blocks — a second configuration source, a second parallelization solution, a second reporting path. The portfolio had already recorded this preference in `spec/project/behavior-driven-development/` as a reference profile; the PoC confirms it empirically rather than re-litigating it.

## Consequences

### Positive

- New test cases with a clear Given/When/Then structure can be authored as readable Gherkin scenarios derivable from the spec, mechanically checked for spec traceability.
- The traceability check (`scripts/check_bdd_traceability.py`) is usable standalone and already covers a real, previously invisible gap (docstring drift in the classic tests). That drift was closed in issue #771 by a shared SSOT (`tests/e2e/_gherkin.py`) both parsers now consume.
- Screenshots derived automatically from step text lower the maintenance cost of future scenarios compared to hand-placed `screenshot(...)` calls.
- The reusability claim is not asserted, it is measured: 9 of 11 bindings are literally reusable after parameterization.

### Negative

- Four integration hazards (A–C plus the dead hook) not obvious from the pytest-bdd documentation had to be discovered the hard way; any future team taking this path without this PoC would hit the same traps again, unless the guards produced here (tag registration, marker channel, `item.path.name`, hook placement) are adopted as a binding pattern.
- English Gherkin prose in a primarily German-documented project raises the entry barrier for non-technical, German-speaking contributors; the only bridge is the TC-ID tag.
- Two parallel implementations of the same test case (classic + BDD) mean duplicated maintenance during a transition period unless work is disciplined about consolidating into shared helpers/fixtures (`_journey_helpers.py`, `conftest.py`).
- The traceability check is deliberately **not** wired into a CI gate (only `static` is required on this repository) — it can drift silently unless someone runs it by hand.

### The most consequential finding — not a BDD topic, a CI-gate topic

The single most consequential finding of the entire PoC has nothing to do with BDD: **TC-004-092 had never passed.** The classic test was merged via PR #763 while its `E2E smoke (compose, light)` check was red — the merge went through because the only required check on this repository is `static`. Running the scenario for real in the containerized stack uncovered a genuine backend defect: `find_open_care_task(..., include_completed_today=True)` in `care_reminder_service.py` matches, by its own docstring, tasks completed *today* — including the very task the same call chain (`_complete_pending_care_task`) had just closed a few lines earlier. `ensure_next_watering_task` therefore always found a "satisfying" task and never scheduled the follow-up, so the watering coherence in view 3 never materialized — for the BDD **and** the classic implementation alike.

The defect affected **three** code paths: the dashboard confirmation, the watering-log entry, and `POST /tasks/{key}/complete` (`tenant_router.py`). The fix passes the just-closed task explicitly as `just_completed_task` into `ensure_next_watering_task`, so the dedup check can distinguish "a satisfying task already exists" from "the task I myself just closed" — without loosening the idempotency rule from issue #509 (a reminder already confirmed today must not re-materialize immediately) for any other caller. Two new tests guard the #509 rule for every other caller.

This finding is an argument about the CI gate — the red, non-required E2E smoke check — not about BDD. It is stated plainly here because it would otherwise be buried: without the real, containerized BDD run, this defect would not have surfaced in this PoC, only at the next incident.

### Follow-ups

- Migrating further TC-004 cases to BDD is a separate, downstream roadmap item — dependent on the "parameter variant vs. new concept" triage sketched above, not part of this decision.
- The four integration guards found here (schema-checked tag registration, marker-based TC-ID derivation, `item.path.name` instead of `item.location[0]`, hook placement in `conftest.py`) are documented as a binding pattern in `tests/e2e/README.md` and apply to every future `.feature` module.
- The red `E2E smoke (compose, light)` check on `develop` is resolved as a side effect of this PoC (the underlying backend defect is fixed); whether that check should become required in the future remains a separate decision outside this ADR.

## References

- Issue #761 — `test(e2e): PoC — BDD E2E architecture driven from TC docs (TC-004-092 as first scenario)`
- `.audits/issue-orchestrate/761/analysis.md` — orchestration audit trail with every empirical finding (Hazards A–C, BDR-001 through BDR-010, migration ratios)
- `tests/e2e/features/watering_cross_view_consistency.feature` — the Gherkin scenario
- `tests/e2e/test_req004_watering_cross_view_consistency_bdd.py` — the step bindings
- `tests/e2e/test_req004_watering_cross_view_consistency.py` — the classic comparison test
- `scripts/check_bdd_traceability.py` — the mechanical spec-to-test check
- `tests/e2e/README.md` — selection axes, tag scheme, TC-ID derivation order
- `spec/e2e-testcases/TC-REQ-004.md` — TC-004-092
- Issue #509 — idempotency rule for reminders already confirmed today
- PR #763 — classic implementation of TC-004-092 (sister issue #760)
