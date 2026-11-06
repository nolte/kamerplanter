# Group 2026-11-06-e2e-wave8 — E2E coverage of REQ-053 wave 8

- **Tier:** 2. **Source:** partition `.audits/issue-backlog-partition/2026-11-06b-req053.md` (approved 2026-11-06). Base `origin/develop` 92518a403.
- **Research question:** Which TC-053 cases and E2E tests cover the merged wave-8 features, and do they pass against the light and full stack?
- **Logical change (one sentence):** Cover the wave-8 features with TC-053 test cases and the two E2E suites (part A soil/dosing/history/rotation/suggestions, part B companion/site/photos/CSV).
- **Cluster kind:** symptom (confirmed: both members write the same TC file, page objects and new `tests/e2e/test_req053_wave8_*.py`; no defect class). **Type:** test (branch `feat/` per repo precedent `feat/2492-e2e-wave7-part-b`).

## Members
| # | WP | Predicate | Evidence | Order |
|---|---|---|---|---|
| #2673 | 8.30 | shared touch surface | Touch: `spec/e2e-testcases/TC-REQ-053.md`, `tests/e2e/test_req053_wave8_*.py`, page objects | 1 |
| #2674 | 8.31 | dependency chain + shared touch surface | "Depends on: … WP 8.30 (#2673)"; "Touch: as WP 8.30" | 2 |

All `Depends on:` WPs merged (latest: #2660 → #2761 `09be9d1b8`, #2668 → #2763 `92518a403`). No member asserts a cause.

## Mode
**Mode A** (one strand): test-only additions; a member that fails to go green is fixed or its case is marked with a reason, nothing to remove from production.

## Completeness matrix
| Member | TC rows | E2E module | Page objects | Run light | Run full | Screenshot review |
|---|---|---|---|---|---|---|
| #2673 | TC-053 rows for GP-FR-104/105/122/123/124/125/133/135/086 (test-case-extractor) | `test_req053_wave8_part_a.py` | extend existing gardenPlanner POs | `-m req053` light | full | e2e-result-reviewer |
| #2674 | TC-053 rows for GP-FR-051/134/145/161–168/174/175, GP-UX-057 | `test_req053_wave8_part_b.py` | same | light | full | e2e-result-reviewer; FieldBedSheet photo action ≥ 64 px |
| docs | not applicable — test-only change, no user-facing behaviour | | | | | |

## Risks
- Mobile profile viewport issue known from #2602 (390×844 vs 393×852) — record, don't fix here unless trivial.
- Stack availability for local runs.

## Out of scope
Fixing product defects the suites find → own issue (medium+), unless a one-line fix.

## Plan approval
Self-approved under the operator's standing authorisation 2026-11-06 ("arbeite die wellen möglichst autonom ab"). authorised_by: 2026-11-06-e2e-wave8/plan-approval.

## Member results
