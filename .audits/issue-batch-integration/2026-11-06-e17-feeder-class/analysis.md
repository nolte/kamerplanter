# Group pre-analysis: 2026-11-06-e17-feeder-class

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** What is still left of the legacy feeder-class model (`nutrient_demand_level` / `NutrientDemandLevel.NITROGEN_FIXER` / `_FEEDER_EC_FACTOR`) on `origin/develop` `9adddd092` after operator decision E-17 variant A (#2643 answer 2026-11-03, Q1), and what has to change in code and spec to carry the decision through?

**The group's single logical change, in one sentence:** Carry operator decision E-17 variant A through code and spec — remove the inert feeder-class EC factor and the legacy `nutrient_demand_level`/`nitrogen_fixer` model from the EC and area-dosing paths and from REQ-003/REQ-001/ZG-002.

**Out of scope:**
- The `NutrientDemandLevel` enum and the `Species.nutrient_demand_level` field stay (#2654: "the enum itself stays (additive only)"; enum retirement crashes the start on an old volume, see memory "Enum-Retirement → Startup-Crash"). Only their docstrings are corrected.
- Seed YAML values `nutrient_demand_level:` in `migrations/seed_data/` and the M6 migration tests (`v0096`) — historical data, read by M6.
- A salt-limit **threshold value** (R-001 / #2643 Q10 still open): the hint ships inert, default `null` (E-10).
- `spec/analysis/agrobiology-req-053-wave8-ec.md` historical text (#2685: stays).
- REQ-053 §32: E-17 (Ergebnis) is already recorded (`REQ-053_Grafische-Garten-Beetplanung.md:2088`, changelog 1.10 at `:22`).

**Tier:** 2 — one repository; the API change is additive (new optional request field, `demand_level` kept as deprecated alias), no published contract breaks.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2685 | spec-change | thematic coupling | spec side of E-17 A; legacy hits on `origin/develop`: `REQ-003_Phasensteuerung.md:1911,1912,1924`, `REQ-001_Stammdatenverwaltung.md:108,605,627,1109` (+ changelog lines 18/19, historical), `ZG-002_Freilandgaertner.md:125` (`git grep -n "nutrient_demand_level\|nitrogen_fixer" refs/remotes/origin/develop -- spec/req spec/target-audiences`) |
| #2654 | refactor | thematic coupling | code side of E-17 A; `_FEEDER_EC_FACTOR` at `domain/engines/phase_resource_resolver.py:26-31`, applied at `:224`; nitrogen-fixer warning at `area_dosing_engine.py:73` |

**Dependency ordering:** #2685 → #2654 (spec states the rule, code follows). Independent in files; order only for review readability.

**Shared touch surface:** none at file level. Coupling is the decision itself; #2685 asks to report `src/` hits, which #2654 fixes.

## Cause verification (#2654 asserts a cause)

Asserted: "the factor table is inert in production — its only production caller `resource_profile_generator.py:124` never passes `nutrient_demand_level`".

Measured on `origin/develop` `9adddd092`:

```
$ git grep -n "resolve_nutrient\|phase_resource_resolver" refs/remotes/origin/develop -- src/backend/app
src/backend/app/api/v1/profiles/router.py:16:  import nutrient_profile_guidance
src/backend/app/domain/engines/resource_profile_generator.py:3: import resolve_nutrient
src/backend/app/domain/engines/watering_volume_engine.py:18: import resolve_irrigation
```

`resource_profile_generator.py:124-129` calls `resolve_nutrient(phase_name, base_npk=…, base_ec_ms=…, base_ph=…)` — no `nutrient_demand_level`. → `factor` is always `_FEEDER_EC_FACTOR[MEDIUM_FEEDER] = 1.0`. **Cause verified** (only remaining production reachers are unit tests `tests/unit/domain/engines/test_phase_resource_resolver.py`).

Also measured: the enum docstring `common/enums.py:455-461` and the field comment `domain/models/species.py:331-334` both claim "still scales the EC target" — false today, false after the change.

Area dosing: `AreaDosingRequest.demand_level` (`api/v1/nutrient_calculations/schemas.py:223`) → `FertilizerService.calculate_area_dosage` (`fertilizer_service.py:319-340`) → `AreaDosingCalculator.calculate(…, demand_level)`; the only frontend sender is `pages/duengung/NutrientCalculationsPage.tsx:143,224,798` (feeder-class select).

## Mode decision

**Mode:** A — single strand

**Reason:** no member is likely to need removal: both are bounded, decision answered (Q1 = A), predecessors WP 8.5 (#2686) and WP 8.6 (#2684) merged; no outstanding review can reject either.

## Structural finding

**Cluster shape:** symptom cluster

**Root cause or defect class:** an operator decision (E-17 A) was recorded in REQ-053 §32 but not yet propagated to the older specs and to the code that implements the superseded model.

**Process finding:** none — the propagation was planned as WP 8.11 + the readiness finding #2685; nothing slipped.

**Preventive change:** not applicable (planned work, not a defect escape).

**Recurrence fed to the portfolio loop:** none.

## Plan approval

**Authorised by:** `2026-11-06-e17-feeder-class/plan-approval`, covering the members, mode, and order above. Approved under the standing wave-8 authorisation (operator 2026-11-04, memory `feedback-req053-wave8-autonomous-run` item 3: "approve group plan gates myself when no genuine decision is open"); no decision is open. Revoked for undispatched members by any structural regression until re-approved.

**Group requirement artifact (class cluster only):** not applicable — symptom cluster, per-member elicitation.

## Planned change per member

**#2685 (spec):**
- `REQ-003_Phasensteuerung.md` 1911–1924: replace the feeder-class EC scaling with: EC per phase from the profile; **no scaling by feeder class** (E-17 A); field soil EC is only a salt-limit hint (REQ-053 §15.1 / GP-FR-125); the feeder level `nutrient_demand` (3 values) plus `nitrogen_fixing` drive hint text and rotation only. Changelog line.
- `REQ-001_Stammdatenverwaltung.md:627`: column → `nutrient_demand` (+ `nitrogen_fixing` where the row had `nitrogen_fixer`); `:108` / `:1109` text "bleibt im Code (EC-Resolver)" → "kein Leser mehr außer M6 (E-17 A)". Changelog line.
- `ZG-002_Freilandgaertner.md:125`: `nutrient_demand_level` → `nutrient_demand`, `nitrogen_fixing`.
- REQ-004-A: checked — the phase-based EC logic needs no `nutrient_demand` (variant A drops feeder scaling for substrate too, since `_FEEDER_EC_FACTOR` goes entirely); record that in #2685's PR text, no edit.

**#2654 (code, variant A):**
- `phase_resource_resolver.py`: delete `_FEEDER_EC_FACTOR` and the `nutrient_demand_level` parameter of `resolve_nutrient`; `target_ec_ms = base_ec_ms`; module docstring line 10-11; note text without feeder class.
- `area_dosing_engine.py`: parameter `nitrogen_fixing: bool = False` instead of `demand_level`.
- `fertilizer_service.calculate_area_dosage`: new optional `species_key` → reads `Species.nitrogen_fixing` of a species visible to the tenant (404 otherwise); legacy `demand_level == NITROGEN_FIXER` still maps to `nitrogen_fixing = True` (deprecated input, OpenAPI `deprecated`), so no old client silently loses the warning.
- `api/v1/nutrient_calculations/schemas.py`: `species_key: str | None` (ARANGO key pattern), `demand_level` marked deprecated.
- New `domain/engines/soil_salinity_hint.py`: pure function — soil profile (`ec_ms_cm`, `ec_method`) + config (threshold, method it holds for, `source`; default `None`) → reason `check_salt_content` or nothing; never a dose. Wired as an additive reason code into the bed nutrient hint (`domain/models/nutrient_hint.py` reason literals, `nutrient_hint_engine.py`). Inert by default — named in the PR.
- `common/enums.py:455-461`, `species.py:331-334`: docstrings corrected (legacy field, read only by M6).
- Frontend `NutrientCalculationsPage.tsx`: feeder-class select replaced by a species choice sending `species_key` (DE/EN i18n); `api/types.ts`.

## Completeness matrix

| Member | Source | Spec | Tests | Docs | Config / workflows | Generated index |
|---|---|---|---|---|---|---|
| #2685 | not applicable — spec-only issue ("No code change") | REQ-003 1911–1924, REQ-001 108/627/1109, ZG-002:125 + changelog lines; check: `git grep -n "nutrient_demand_level\|nitrogen_fixer" -- spec/req spec/target-audiences` returns only changelog/historical lines | not applicable — no executable spec | `docs/de/user-guide/plant-management.md:42` (+ EN mirror) field row → `nutrient_demand`/`nitrogen_fixing`; check: `mkdocs build --strict` | not applicable — no config | not applicable — no spec index regenerated by these files (`spec/req/` has no generated index) |
| #2654 | resolver, area dosing engine/service/schema, `soil_salinity_hint.py`, nutrient hint wiring, docstrings, `NutrientCalculationsPage.tsx`; check: `task lint` (ruff, mypy, eslint, tsc) | REQ-053 §15.1/GP-FR-125 reason code `check_salt_content` row if the reason list is enumerated there; check: grep of the reason list in REQ-053 | `test_phase_resource_resolver.py` (no feeder factor: heavy_feeder in → base EC out; static test no `_FEEDER_EC_FACTOR`), `test_area_dosing_engine.py` (warning fires for `nitrogen_fixing=True` species with legacy level `null`), API test area-dosing with `species_key` (own/global OK, foreign 404), unit tests salinity hint (null threshold → no hint; above threshold with matching method → hint; other method → none), vitest NutrientCalculationsPage; check: `.venv/bin/python -m pytest` on those + `tests/api` + guards, `npx vitest run` | `docs/{de,en}/user-guide/fertilization.md` §Flächendosierung step for the species choice; `docs/{de,en}/reference/api-reference.md:158` reason list + `check_salt_content`; check: `mkdocs build --strict` | settings: salinity threshold only in code config (default `None`) — not applicable for env/Helm (no env var, no value without source) | not applicable — OpenAPI is generated at runtime, no committed snapshot (verify in member run) |

## Risks

- Removing `demand_level` handling would silently drop the N-fixer warning for an old client — mitigated by keeping it as deprecated alias.
- `species_key` lookup must respect the hybrid catalog visibility (own ∪ global ∪ granted, memory "Tenant-Katalog-Union-Regression #324") — a strict tenant filter would 404 global species.
- Salinity hint ships inert (no sourced threshold) — "implemented but inert" pattern; acceptable per E-10, named in the PR and REQ-053.

## Open questions for the operator

- none blocking (salt threshold value stays open in #2643 Q10).

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2685 | no matching specialist — main session (spec text) | `git grep -n "nutrient_demand_level\|nitrogen_fixer" -- spec/req spec/target-audiences` | only changelog rows, struck-through field (REQ-001:109), M6 text, reason codes `*_nitrogen_fixer`, REQ-053 §16.3 motivation (:1046, outside #2685's files) |
| #2654 | fullstack-developer (commit 686bc82ec) | `ruff check app tests && ruff format --check app tests` | `All checks passed!` / `2929 files already formatted` |
| #2654 | fullstack-developer | `scripts/check_mypy_ratchet.py` | `3419 findings now, 3434 recorded ... GREEN` |
| #2654 | fullstack-developer | `pytest tests/unit/domain/engines tests/unit/guards tests/api -q -x` | `1 failed, 7560 passed, 3 skipped` — failure `test_limiter_outage_on_real_routes.py::test_a_storage_never_reached_since_start_logs_an_error` (order-dependent, `4 passed` alone; `tests/api` rest `3508 passed, 1 deselected`); untouched by the diff |
| #2654 | fullstack-developer | `npx tsc --noEmit`; `npx eslint` (8 files); `npx vitest run` (3 files) | exit 0; exit 0; `Tests 59 passed (59)` |
| #2654 | main session re-run | `pytest` resolver, area-dosing, salinity, nutrient-hint engine+service, nutrient_calculations router | `166 passed, 84 warnings in 12.49s` |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| all | local adaptation | branch type `feat/` instead of `refactor/`: `scripts/worktree_add.sh` allows only feat/ fix/ chore/ docs/ exp/ ci/; the group adds a user-visible species choice and the salt hint, so feat. |

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| `common/dependencies.py:1048` production wiring `species_repo=get_species_repo()` untested (API tests override `get_fertilizer_service`) | member verification pass | fixed directly: `tests/unit/api/test_fertilizer_service_wiring.py` | without the kwarg: `1 failed`; restored: `1 passed` | — |
| `NutrientCalcFertilizerFields.tsx:113-139` own `listAllSpecies` fetch next to `hooks/useCatalogue.ts` | member verification pass | not fixed — non-blocking duplication, bounded catalogue (~210), same pattern at 6 other sites | read of both files | — |
| salt threshold only configurable in code (`DEFAULT_CONFIG`), no settings/env path | member verification pass | not fixed — same pattern as every other nutrient-hint threshold; no sourced value exists (#2643 Q10) | `nutrient_hint_service.py` uses `DEFAULT_CONFIG` | — |
| `tests/api/test_limiter_outage_on_real_routes.py::test_a_storage_never_reached_since_start_logs_an_error` fails in the full `-x` run | check | not caused by the diff (rate limiter untouched, `4 passed` alone); CI decides | full run vs single run | — |
