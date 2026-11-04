# Group pre-analysis: 2026-11-04-reach-thresholds

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** Do #2666 and #2667 form one reviewable bundle, in which order, and which
repository surfaces must each change?

**The group's single logical change, in one sentence:** A bed gets a `bed.reach_too_wide` hint
computed from its geometry and access sides against site-configurable reach thresholds, and the
same site settings also make the sun-class thresholds and the aspect-derived orientation configurable.

**Out of scope:** #2653 (shares `bed/BedHeader.tsx`, runs after this group); any value without a source
(E-10 — thresholds 1.2/0.6 m and RHS sun classes are both `confirmed` in
`spec/analysis/agrobiology-thresholds-req-053.md:37-38`); inheritance from a site slope (decision
bundle question 4); `bed.path_too_narrow` (optional SHOULD in the spec addendum, not in either issue).

**Tier:** 2 — one repository, no published contract change beyond an additive site field and an additive enum.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2666 | feature-request | dependency chain (head of the chain; its own predecessor #2665 is merged, PR #2698) | issue body "Depends on: WP 8.22 (#2665)"; `gh issue view 2665` state CLOSED |
| #2667 | feature-request | dependency chain | body "Depends on: WP 8.23 (#2666)"; thresholds it adds feed #2666's calculator (`reach_thresholds` default 1.2 / 0.6 m) |

Re-check of the partition record: authors `nolte` (trusted), both OPEN, both bounded (one outcome, one strand,
no new roadmap item), no asserted cause. Record confirmed, nothing corrected. Provisional kind "symptom" is
**overturned**: there is no shared root cause; the group is a capability chain (**neither**, see below).

**Dependency ordering:** #2666 → #2667. #2666 ships the calculator with the defaults as module constants /
parameters; #2667 then makes them site configuration and routes the calculator's threshold argument from it.

**Shared touch surface:** none by file between the two (#2666: `reach_calculator.py`, `reach.ts`,
`garden-plan-vectors.json`, `bed/BedHeader.tsx`; #2667: `site.py`, `site_service.py`, `api/v1/sites/schemas.py`,
`bed/SunTileSelector.tsx`). Coupling is the data flow: threshold values from the site into the calculator call.
Against other work: `garden-plan-vectors.json` (also touched by merged #2664, now on `develop`);
`bed/BedHeader.tsx` with single #2653 (runs after); open PR #2701 (soil analysis, WP 8.7) touches the soil
profile, not these files — recheck at rebase.

## Mode decision

**Mode:** A — single strand.

**Reason:** No member is likely to need removal: acceptance is deterministic (vectors, unit table, 422), no
external dependency, no outstanding review that could reject a member. #2667 is size S and depends on #2666.

## Structural finding

**Cluster shape:** neither — a two-step feature chain, not a defect cluster.

**Root cause or defect class:** not applicable (feature chain: calculator → configuration of its inputs).

**Process finding:** none.

**Preventive change:** not applicable.

**Recurrence fed to the portfolio loop:** none.

**Measured observations that shape the plan** (from the primary checkout at `origin/develop`):

- `Orientation` has **4** values (`NORTH/SOUTH/EAST/WEST`, `src/backend/app/common/enums.py:487`) but #2667's acceptance
  needs **8** orientations from 0–359°. Reaching 8 needs an additive enum extension (NE/SE/SW/NW), DE/EN i18n in the same PR
  (guardrail "enums additive only"). Check consumers of `Orientation` before widening (see Risks).
- `SiteConditions` already carries `aspect_deg` (`site.py:272`, `0 <= x < 360`) and `access_sides` (`site.py:273`, enum
  `AccessSide` N/E/S/W, `enums.py:2109`); `Location.orientation` exists (`site.py:402`). The reach calculator needs no new bed field.
- Calculator pattern to mirror: `domain/calculators/site_fit_calculator.py` + `model/siteFit.ts`, vectors in
  `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (operations `site_fit`, `site_fit_axes`); a new operation `reach` must be
  added to the "runs elsewhere" lists in `tests/unit/domain/calculators/test_geometry_vectors.py:42` and
  `model/geometry.vectors.test.ts:27-34`, and to the `operations` block of the fixture header.
- `SunTileSelector.tsx:5-11` hard-codes the RHS thresholds in its help text and states "making them configurable is GP-FR-164".

## Plan approval

**Authorised by:** `2026-11-04-reach-thresholds/plan-approval`, covering the members, mode, and order
above. Revoked for undispatched members by any structural regression until re-approved.

**Group requirement artifact (class cluster only):** not applicable — not a class cluster, per-member elicitation.

## Completeness matrix

| Member | Backend code | Frontend code | Vectors / fixtures | Tests & guards | Docs & i18n |
|---|---|---|---|---|---|
| #2666 | `domain/calculators/reach_calculator.py` (pure; shortest side vs threshold, access from `access_sides`, else adjacent `path` objects derived from geometry); check: `.venv/bin/python -m pytest tests/unit/domain/calculators -q` | `model/reach.ts` port + hint badge/summary in `bed/BedHeader.tsx`, `lazy()` where it adds weight; check: `npx vitest run src/features/gardenPlanner` | new operation `reach` in `garden-plan-vectors.json`, runner on both sides, "runs elsewhere" lists updated; check: both vector suites green incl. 1.3 m bed with/without path | unit + vector tests, hint-never-error test; no new route expected → route guards unchanged (check: full `tests/unit/guards`) | user-guide DE/EN note on the hint; i18n keys DE/EN for badge |
| #2667 | `Site` fields `sun_class_thresholds`, `reach_thresholds` (`> 0` validated → 422), orientation derivation from `aspect_deg` in `site_service.py`, schemas in `api/v1/sites/schemas.py`; check: unit tests 0–359° → 8 orientations, `<= 0` → 422 | `SunTileSelector.tsx` help text reads site values; reach threshold passed into `reach.ts`; check: vitest shows configured value | `reach` vectors parameterised by thresholds (extra cases with non-default values) | service write takes `*, tenant_key: str`, extend `test_keyed_service_writes_take_the_tenant.py`; `tests/api` complete + all guards; tenant-isolation route walk if a route changes | enum additions (4 → 8 orientations) with DE/EN `enums.orientation.*`; DE/EN docs for the site settings; migration: not applicable — new optional fields default to `None`/defaults, confirm with M-3/M-5/M-6 only if a stored-shape change appears |

## Risks

- Widening `Orientation` to 8 values may break exhaustive consumers (frontend maps, seeds, `strict` Literal types, documents already stored with 4 values stay valid). Cost: a missed consumer fails at runtime; mitigation: grep every `Orientation`/`orientation` use before the change and run the full suites.
- `garden-plan-vectors.json` is shared with merged #2664; a rebase conflict is possible if another lane edits it before this group lands.
- Adjacent-`path` access derivation must reuse the `adjacent_to` geometry rule, not a second distance rule; a divergence would make Python and TS agree with each other but not with the placement model.
- Open PR #2701 may change `site.py`/`site_service.py` adjacency; recheck at integration-branch creation.
- Bundle budget `routeChunks.gardenPlanner` 120 KB must not be raised; the hint must not grow the main planner chunk.

## Open questions for the operator

- (answered 2026-11-04) Orientation is extended additively to 8 values with DE/EN i18n.

## Member results

Filled during implementation. Each entry records the dispatched specialist and the
**actual output** of every declared check, never an assertion that it passed.

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2666 | pending | pending | pending |
| #2667 | pending | pending | pending |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| — | — | none yet |
