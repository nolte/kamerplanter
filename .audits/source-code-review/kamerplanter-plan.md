# Implementation Plan — Source-Code-Review Remediation (kamerplanter, whole tree)

> **Grounded input:** `.audits/source-code-review/kamerplanter.md`
> (dispatched by `nolte-engineering:source-code-review`, run 2026-07-24)
> **Reviewed revision:** `f31766d51fae11669625759af45fa8836fc48103` (branch `develop`, plus uncommitted working-tree changes)
> **Language profile:** Python reference profile (`spec/project/source-code-review/`); TypeScript recorded unsupported/not reviewed
> **Per-dimension counts (review):** 8 findings total — 0 Critical, 3 Warning (SCR-001 D5, SCR-002 D4, SCR-003 D4). Suggestion/Info (SCR-004..008) left unpackaged by review contract.
> **Plan authored:** 2026-07-24 · issue-orchestration §Decomposition · review-driven path
> **Routing (inherited from report, unchanged):** all packages are production-code remediation → `fullstack-developer`. No tier-conformance or D10-floor findings.

## Detected context (reproducibility)

- **Stack:** Python 3.14+ across four Python trees — `src/backend` (FastAPI, 5-layer, pytest + pytest-asyncio, mypy `strict=true` declared), plus three sibling packages `src/inference-service` (DINOv2/pgvector), `src/knowledge-service` (RAG), `src/libs/kp_vectordb` (shared pgvector pool). All four use ruff `E,F,W,I,UP,B,SIM` (ignore `B008`; inference-service adds `A003`).
- **Test runners:** backend `pytest tests/unit/` + `tests/api/`; each microservice/lib has its own `tests/` (`asyncio_mode = "auto"`), driven by FastAPI `TestClient` with a fake repo/embedder in `conftest.py`.
- **`static` CI gate:** `.github/workflows/build-static-tests.yaml` → job `static` → `nolte/gh-plumbing/.github/workflows/reusable-pre-commit.yaml`. The gate runs `.pre-commit-config.yaml`. **No mypy hook exists there today**, and `backend.yml` runs ruff/pytest but **no mypy step**. → The backend's declared `mypy strict=true` is therefore *not* enforced by any CI gate at the reviewed revision (grep-confirmed). This contradicts the report's phrase "wire it into the same CI static gate the backend uses"; see WP-3 open question.
- **Affected source lines (grounded):**
  - `src/inference-service/app/main.py:375-393` (`upsert_reference`) and `:570-588` (`upsert_pest_reference`) — byte-identical vector-resolution blocks; both reference `_require_embedder`, `_read_upload`, `settings.model_dim`.
  - `src/backend/app/domain/engines/aquaponics_engine.py` — `_evaluate_hardness` (`:343`, `kh_dh < 4`), `check_alkalinity_crash_risk` (`:438`, `kh_dh < 4`); dead `StockingDensityCalculator.FEED_PER_M2` (`:453`); unused `system_type` param on `calculate_fish_plant_ratio` (`:469-471`, internal call site `:487` passes `system.system_type`); unused `period_days` on `calculate_mortality_rate` (`:867`, docstring implies windowing; callers at `aquaponik_service.py:196` and `:882` pass no `period_days`).
- **Existing guarding tests (must stay green):** `src/inference-service/tests/test_api.py` (`/reference` image + embedding + dim-mismatch paths), `test_pest_api.py` (`/pest/reference`); `src/backend/tests/unit/domain/engines/test_aquaponics_engine.py` (`check_alkalinity_crash_risk` at `:197-199`, `calculate_mortality_rate` at `:401-404`) and `tests/api/test_aquaponics_router.py`.

## Scope boundary

**In scope:** the three Warning-derived work packages WP-1..WP-3 exactly as the report decomposed them, refined into atomic, individually-verifiable sub-tasks with the test edits and verification commands each needs. Opportunistic same-file Suggestions SCR-004/SCR-005 stay folded into WP-2 (report-sanctioned).

**Out of scope:** SCR-006 (`knowledge-service/app/main.py`), SCR-007 (`species_repository.py` LIKE-escaping), SCR-008 (`botanical_families/router.py` local imports) — Suggestion/Info, left unpackaged by the report contract. They touch files not claimed by any package here and can be picked up independently later without collision. No behavioural change to production semantics beyond the named refactors. No new features. No git mutation, dispatch, or PR (planning stage only).

**Route recommendation:** **bounded direct implementation** (three parallel `fullstack-developer` dispatches), *conditional* on resolving the WP-3 CI-wiring open question first. Rationale: WP-1 and WP-2 are pure, well-tested, single-file refactors with clear testable acceptance criteria — ideal for direct dispatch. WP-3 is a tooling-baseline change whose second half ("wire into the static gate") rests on a false premise and may surface pre-existing type errors of unbounded size; its pyproject half is bounded, its CI-wiring half needs an operator decision (see open questions). Nothing here belongs in the formal `roadmap → feature → sprint` pipeline.

## Parallel-safety (preserved from report)

All three packages have **disjoint file sets** and **no ordering dependencies** — concurrently dispatchable, one worktree-isolated specialist per package:
- WP-1 → `src/inference-service/app/main.py` (+ its `tests/`)
- WP-2 → `src/backend/app/domain/engines/aquaponics_engine.py` + `aquaponik_service.py` call-site + backend `tests/`
- WP-3 → three `pyproject.toml` files + (pending decision) `.pre-commit-config.yaml`

WP-1 and WP-3 both live under the inference-service package but touch different files (`app/main.py` vs `pyproject.toml`), so they remain disjoint and parallel-safe. WP-2's call-site edit in `aquaponik_service.py` is inside WP-2's own backend tree and touches no file claimed by another package.

## Work packages

| # | Findings | Files | Specialist | Depends on |
|---|----------|-------|------------|------------|
| WP-1 | SCR-002 | `src/inference-service/app/main.py`, `src/inference-service/tests/test_api.py`, `.../tests/test_pest_api.py` | fullstack-developer | — |
| WP-2 | SCR-003 (+ SCR-004, SCR-005) | `src/backend/app/domain/engines/aquaponics_engine.py`, `src/backend/app/domain/services/aquaponik_service.py`, `src/backend/tests/unit/domain/engines/test_aquaponics_engine.py` | fullstack-developer | — |
| WP-3 | SCR-001 | `src/inference-service/pyproject.toml`, `src/knowledge-service/pyproject.toml`, `src/libs/kp_vectordb/pyproject.toml`, (pending decision) `.pre-commit-config.yaml` | fullstack-developer | — (CI-wiring sub-task blocked on open question OQ-1) |

### WP-1 — Extract single `_resolve_vector` helper (SCR-002)

**Problem statement:** The ~18-line "image-or-precomputed-embedding → validated vector, else 400" trust-boundary block is byte-identical in `upsert_reference` (`main.py:375-393`) and `upsert_pest_reference` (`:570-588`); a future dim-validation or error-wording change must be made twice and will diverge.

**Atomic tasks:**
1. Add `async def _resolve_vector(image: UploadFile | None, embedding: str | None) -> list[float]` in `main.py`, containing the exact current logic: image → `_require_embedder().embed(_read_upload(...)).tolist()` with the `ModelNotReadyError → 503` mapping; `embedding` → JSON-array parse with `(JSONDecodeError, TypeError, ValueError) → 400`; `len(vector) != settings.model_dim → 400`; neither → 400 "Provide either an image or a precomputed embedding."
2. Replace both inline blocks with `vector = await _resolve_vector(image, embedding)`; leave the downstream `repo.upsert_reference(...)` / `pest_repo.upsert_prototype(...)` calls and response construction untouched.

**Acceptance criteria (user-observable, testable):**
- `POST /reference` and `POST /pest/reference` behave identically to before for all four branches: valid image → 200; valid JSON embedding of correct dim → 200; malformed JSON / wrong element type → 400 with body `"embedding must be a JSON array of floats."`; wrong-length embedding → 400 with body `"embedding dim {n} != model dim {m}."`; neither supplied → 400 "Provide either an image or a precomputed embedding."; model-not-ready on the image path → 503.
- The vector-resolution logic exists in exactly one place (grep: one `_resolve_vector` definition, zero remaining inline `json.loads(embedding)` in the two endpoints).

**Test edits:** existing `test_api.py` / `test_pest_api.py` cases already assert the 200/400/dim-mismatch branches and are the regression guard — keep them green. Add one focused case per branch that is currently only covered on the `/reference` side but not `/pest/reference` (or vice versa) if a branch is asymmetrically covered, so the shared helper is exercised from both entry points.

**Verification:**
```
cd src/inference-service && ruff check . && ruff format --check .
cd src/inference-service && pytest tests/test_api.py tests/test_pest_api.py -q
```

### WP-2 — Name the KH-crash threshold; drop dead constant and unused params (SCR-003 + SCR-004 + SCR-005)

**Problem statement:** The safety-relevant rule "KH below 4 °dH ⇒ pH-crash risk" is encoded twice with a bare `4`/`4.0` literal (`aquaponics_engine.py:343` and `:438`), against the module's own constant convention (`FREE_AMMONIA_SAFE_MGL`, `CYCLING_STABLE_DAYS_REQUIRED`); the two thresholds can silently diverge. Same file additionally carries dead knowledge (`FEED_PER_M2`) and two lying signatures (`system_type`, `period_days`).

**Atomic tasks:**
1. **SCR-003:** introduce module constant `KH_CRASH_THRESHOLD_DH = 4.0` next to the existing safety constants; reference it in both `_evaluate_hardness` (`:343` comparison and the `limit=` field) and `check_alkalinity_crash_risk` (`:438` comparison and `limit=`). Keep the DE/EN message text and the `limit=4.0` output value identical.
2. **SCR-004:** remove `StockingDensityCalculator.FEED_PER_M2` (grep-confirmed single definition, zero readers).
3. **SCR-005a:** drop the unused `system_type: AquaponicSystemType` param from `calculate_fish_plant_ratio`; update the single internal caller at `aquaponics_engine.py:487` to stop passing `system.system_type`.
4. **SCR-005b:** drop the unused `period_days` param from `calculate_mortality_rate` **and** correct the docstring so it no longer claims windowing ("cumulative mortality fraction relative to the initial stock" describes the actual, un-windowed behaviour). Callers at `aquaponik_service.py:196` and `:882` already pass no `period_days`, so no call-site change is required. (Alternative honoured by the report — actually implement the window — is out of scope unless the operator requests the behavioural change.)

**Acceptance criteria (testable):**
- `check_alkalinity_crash_risk(3.0, 50.0)` returns a warning; `(6.0, 50.0)` and `(3.0, 0.0)` return `None` (unchanged — existing test `:197-199`). The KH threshold appears as exactly one named constant; grep shows zero remaining bare `< 4` / `4.0` KH literals in the two sites.
- `_evaluate_hardness` still emits the KH warning for `kh_dh < 4.0` with `limit=4.0` and the unchanged DE/EN messages (GH branches untouched).
- `calculate_fish_plant_ratio(daily_feed_g, grow_area_m2)` computes the same `round(daily_feed_g / grow_area_m2, 1)` (0.0 when area ≤ 0); no signature carries `system_type`. Internal caller compiles.
- `calculate_mortality_rate(stock)` returns the same value; signature carries no `period_days`; docstring matches behaviour. Existing test `:401-404` green.
- `FEED_PER_M2` no longer resolves anywhere (grep: zero hits).

**Test edits:** existing engine tests are the regression guard. Adjust any test that passes `system_type` positionally into `calculate_fish_plant_ratio` (grep before editing — router-level tests pass `system_type` as request payload, not as this method arg, so likely no change). Optionally add a test asserting the KH warning fires exactly at the constant boundary (`kh_dh` just below vs at `KH_CRASH_THRESHOLD_DH`).

**Verification:**
```
cd src/backend && ruff check . && ruff format --check .
cd src/backend && pytest tests/unit/domain/engines/test_aquaponics_engine.py tests/api/test_aquaponics_router.py -q
```

### WP-3 — mypy baseline for the microservices/lib and CI wiring (SCR-001)

**Problem statement:** The backend declares `mypy strict=true`, but `inference-service`, `knowledge-service`, and `kp_vectordb` ship only ruff — type-level defects in those trees (e.g. `inference-service/app/main.py` `# type: ignore` + `**row` construction sites) are caught by neither tooling nor, under the tooling-first rule, by hand review.

**Atomic tasks:**
1. Add a `[tool.mypy]` section to each of `src/inference-service/pyproject.toml`, `src/knowledge-service/pyproject.toml`, `src/libs/kp_vectordb/pyproject.toml`. **Start non-strict** (`python_version = "3.14"`; no `strict = true` initially), per the report's "at minimum non-strict", to bound the blast radius — enabling strict on trees full of untyped `**row`/`# type: ignore` sites may surface a large, unbounded error set. Add `mypy` to each package's `[project.optional-dependencies].dev`.
2. Run mypy locally against each tree and **triage the surfaced errors** (see risk R-3): fix the cheap ones; for anything that would balloon scope, record it as a follow-up rather than expanding this package. The package is "done" when mypy runs clean (or clean-modulo-recorded-follow-ups) on all three trees at the chosen level.
3. **CI wiring — blocked on OQ-1.** The intended "same static gate the backend uses" does not exist (no mypy in pre-commit or `backend.yml`). Once OQ-1 is decided, wire mypy accordingly — most faithfully as a new `local` mypy hook in `.pre-commit-config.yaml` scoped to the three package roots (that genuinely lands it on the `static`/`reusable-pre-commit.yaml` gate), each hook `cd`-ing into its package like the existing ruff hooks and carrying `additional_dependencies: ['mypy>=1.13.0']`.

**Acceptance criteria (testable):**
- `mypy` run in each of the three package directories exits 0 at the chosen strictness (or exits 0 modulo an explicitly-recorded follow-up list).
- Each of the three `pyproject.toml`s contains a `[tool.mypy]` section and lists `mypy` under `dev`.
- After OQ-1 is resolved: the `static` gate (pre-commit) executes mypy over the three trees — demonstrable by `pre-commit run mypy-<pkg> --all-files` (or equivalent) passing, and by an intentionally-introduced type error being caught locally.

**Verification:**
```
cd src/inference-service && pip install -e '.[dev]' && mypy app
cd src/knowledge-service && pip install -e '.[dev]' && mypy app
cd src/libs/kp_vectordb && pip install -e '.[dev]' && mypy kp_vectordb
# after CI wiring:
pre-commit run --all-files
```

## Cross-package dependency ordering

Directed acyclic ordering: **none.** WP-1 ⟂ WP-2 ⟂ WP-3 (disjoint files, no shared symbols). All three may be dispatched concurrently. The only internal ordering is *within* WP-3: task 1 (pyproject) → task 2 (triage) → task 3 (CI wiring, gated on OQ-1).

## Risks

- **R-1 (WP-1):** `_resolve_vector` must preserve the `ModelNotReadyError → 503` mapping that only exists on the image path; a naive extraction that drops it changes the contract. Mitigated by the image-path test cases.
- **R-2 (WP-2):** dropping `system_type` from `calculate_fish_plant_ratio` is safe only because the sole caller is internal (`:487`); any out-of-tree caller (none found) would break. The mortality-window "alternative" (actually honour `period_days`) is a behavioural change and is deliberately excluded.
- **R-3 (WP-3):** enabling mypy on trees with existing `# type: ignore` and untyped `**row`/`**metrics.as_dict()` construction may surface a large error set. Bounded by starting non-strict and treating strict-mode adoption / large fixes as recorded follow-ups, not in-package scope creep.
- **R-4 (WP-3):** the report's premise "the same static gate the backend uses" is inaccurate — see OQ-1; proceeding on the literal wording would wire nothing.

## Blocking preconditions / open questions

- **OQ-1 (blocks WP-3 task 3):** The backend's declared `mypy strict=true` is **not** wired into any CI gate today (no mypy in `.pre-commit-config.yaml` or `backend.yml`). "Wire it into the same static gate the backend uses" therefore has no existing referent. Operator decision required: (a) add a new `local` mypy pre-commit hook for the three microservice/lib roots (the faithful realisation, lands on the `static` gate) — and optionally extend it to the backend to close the pre-existing backend gap; or (b) land only the `[tool.mypy]` pyproject baselines now and defer CI enforcement to a follow-up. Default recommendation: (a) scoped to the three packages, backend gap noted as a separate follow-up.
- **OQ-2 (WP-3 strictness):** confirm non-strict start (recommended) vs. matching the backend's `strict=true` immediately (higher up-front remediation cost per R-3).
- **No requirements/issue gate applies:** this is the review-driven path; the grounded source is the persisted `source-code-review` report, not a `requirements-elicit` artifact or a GitHub issue. No `τ_high` requirements gate is owed.
