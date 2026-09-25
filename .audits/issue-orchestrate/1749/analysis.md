# Pre-analysis — issue #1749

- **Issue:** #1749 "ci(lane-inputs): hold a delegated read's reader, not only its path, against the covering lane" (author: nolte, owner — trusted)
- **Classification:** `bug` (a guard that stays green over the defect class it exists for); secondary `infra`.
- **Requirements gate:** operator override (repository owner, 2026-09-24/25, full autonomy); the issue carries its own acceptance criteria.
- **Route:** implement directly (one coherent outcome, one PR strand, no roadmap item).

## Cause verified against the code (established)

- `_delegation_findings()` (`src/backend/tests/unit/guards/test_lane_filters_cover_measured_inputs.py:760-803`) holds each gap-hit read only as `p in covering.reads` — by path.
- The recorder (`scripts/ci/lane_inputs.py:353-410`) records one flat read set per invocation; `Trace` has no attribution to the test that made a read. So the claim "the guard cannot tell readers apart" holds: there is no data to tell them apart with.
- All 42 `covered_by` gaps are in `backend--lint-test.yaml`, all to `backend-guards.yml/guards` (measured: `grep -l covered_by .github/lane-inputs/*.yaml`).
- 2090 of the 4593 reads of `backend--lint-test` fall outside `backend.yml`'s filter (measured with `relevance_filter().rejects`).
- #1683 low finding: `read_drift`/`delegated_reads` take `next(...)`/`break` on the first matching gap; the guard iterates all gaps. Same mechanism (delegation semantics) → fixed here.

## Work packages

| ID | Problem | Acceptance | Files | Specialist |
|---|---|---|---|---|
| WP1 | Recorder attributes reads to the test module that made them (strace + pytest marker plugin, clone tracking for subprocesses) and records `test_modules` + `readers` | recorder test: a synthetic pytest file reading a tracked file is recorded as its reader, also through a subprocess | `scripts/ci/lane_inputs.py`, new plugin module, recorder tests | generalist (strand agent) — see deviation note |
| WP2 | Guard + compare hold each delegated read's readers against the covering lane's `test_modules` | red-first: a reader outside the covering lane turns guard and compare red while another covering-lane test reads the same path | guard test file, `lane_inputs.py` | same |
| WP3 | All matching gaps in `read_drift`/`delegated_reads` | test with two overlapping gaps carrying different `covered_by` | `lane_inputs.py`, recorder tests | same |
| WP4 | NFR-018 stale passage (~l.505-519) | passage matches the tree (no `backend--coverage`, guards manifest exists) | `spec/nfr/NFR-018*` | same |
| WP5 | Refresh manifests via CI recorder | `Compare` green on final head | `.github/lane-inputs/*.yaml` | recorder |

Ordering: WP1 → WP2 → WP3 → WP4 → WP5.

## Risks

- Manifest size grows by the reader map (measured after first recording).
- The lane-inputs workflow does not run on a PR that only adds a backend test; such a PR is caught by the weekly schedule / next recording (unchanged trigger, stated in the PR).
