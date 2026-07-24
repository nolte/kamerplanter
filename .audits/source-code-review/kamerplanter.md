# Source Code Review — kamerplanter (whole tree)

> **Run:** 2026-07-24 · operation `review` · dispatched by `nolte-engineering:source-code-review`
> **Commit under review:** `f31766d51fae11669625759af45fa8836fc48103` (branch `develop`, plus uncommitted working-tree changes: `botanical_family_repository.py`, `species_repository.py`, `botanical_families/router.py`, two new test files)
> **Applied language profile:** Python reference profile (`spec/project/source-code-review/`)
> **Reviewer:** `python-code-reviewer` (read-only)
> **Unsupported languages:** TypeScript (`src/frontend`) — no language profile exists in `spec/project/source-code-review/`; per spec §Language profiles it is recorded here as unsupported, not reviewed ad hoc.

> Scope: roots `src/backend/{app,tests}`, `src/knowledge-service`, `src/inference-service`, `src/libs`, `scripts`; target: whole Python tree (~1400 files) plus the uncommitted working-tree changes. Excluded: `.venv/`, `node_modules/`, `__pycache__/`, `src/frontend` (TypeScript).
> Tooling baseline: FOUND. `src/backend/pyproject.toml` — ruff `E,F,I,N,W,UP,B,SIM` (ignore `B008`), **mypy `strict=true`** + pydantic plugin, black, pytest-asyncio `auto`. Microservices/libs (`knowledge-service`, `inference-service`, `kp_vectordb`; `inference-service` adds `A003` ignore) run ruff with the same rule set **but have no `[tool.mypy]` section** — see SCR-001. Tooling-first rule applied strictly: no mechanical ruff/mypy-reportable issues are re-reported.

## Overall assessment

The reviewed code is mature and disciplined. Domain rules are largely centralised (e.g. `calculate_svp`/Tetens lives once in `vpd_calculator.py`; the `get_or_raise` refactor already collapsed the ~118 duplicated `NotFoundError` blocks; AQL is parameterised through `AQLBuilder` with an operator/field whitelist). No mutable default arguments, no bare `except`, no `print` in production paths, no naive/aware datetime bugs, no `== None`/`is "literal"` pitfalls were found in `src/backend/app`. The two new working-tree test files are correct solitary unit tests that double the owned DB boundary. **No Critical findings.** The findings below are duplication/dead-code/idiom refinements plus one baseline gap.

| Dimension | Findings | Critical | Warning |
|-----------|----------|----------|---------|
| D1 Correctness | 1 | 0 | 0 |
| D2 Maintainability | 3 | 0 | 0 |
| D3 Design | 0 | 0 | 0 |
| D4 Domain duplication | 2 | 0 | 2 |
| D5 Idioms/typing | 2 | 0 | 1 |
| D6 Tests | 0 | 0 | 0 |
| D7 Performance | 0 | 0 | 0 |
| D8 API/contracts | 0 | 0 | 0 |
| D9 Reinvention | 0 | 0 | 0 |
| D10 Floors (routed) | 0 | 0 | 0 |
| **Total** | **8** | **0** | **3** |

D10 note: no security/observability/dependency floor smells surfaced during this pass worth routing out — auth (`inference-service/app/auth.py`, service-token fail-closed + `hmac.compare_digest`), secret fail-fast (`check_insecure_config`), and tenant-isolation guards (`base_repository._enforce_tenant_scope`, `_require_tenant_key`) are present and correct. A dedicated `code-security-reviewer` / `dependency-audit` pass remains the authority; nothing here pre-empts it.

## Warning

### SCR-001: Microservices and shared lib have no static type-checker in their tooling baseline
- **File:** `src/knowledge-service/pyproject.toml`, `src/inference-service/pyproject.toml`, `src/libs/kp_vectordb/pyproject.toml` (each: no `[tool.mypy]`) **Dimension:** D5 **Code:** production **Confidence:** confirmed
- **Problem:** The backend enforces `mypy strict=true`, but the three sibling Python packages ship only ruff. Type-level defects in those trees (`inference-service/app/main.py` alone carries several `# type: ignore` and `**row`/`**metrics.as_dict()` construction sites) are caught by neither tooling nor — per the tooling-first rule — by hand review. This is the single baseline-gap finding; it is why type-shape issues in those roots are not itemised individually below.
- **Recommended remediation (not applied):** Add a `[tool.mypy]` section (at minimum non-strict, ideally `strict=true` to match backend) to each of the three `pyproject.toml`s and wire it into the same CI `static` gate the backend uses.

### SCR-002: Duplicated image-or-embedding vector-resolution block across two inference endpoints
- **File:** `src/inference-service/app/main.py:375-393` (`upsert_reference`) and `src/inference-service/app/main.py:570-588` (`upsert_pest_reference`) **Dimension:** D4 **Code:** production **Confidence:** confirmed
- **Problem:** Both endpoints reimplement the identical trust-boundary rule "resolve the embedding vector from EITHER an uploaded image (embed it) OR a precomputed JSON `embedding` array, rejecting bad JSON and validating `len(vector) == model_dim`, else 400." The ~18-line block is byte-for-byte the same domain decision; a future change to dim-validation or error wording must be made in two places and will diverge.
- **Recommended remediation (not applied):** Extract one helper, e.g. `async def _resolve_vector(image: UploadFile | None, embedding: str | None) -> list[float]`, and call it from both endpoints as the single source of truth.

### SCR-003: pH-crash carbonate-hardness threshold duplicated as a bare literal, against the file's own constant convention
- **File:** `src/backend/app/domain/engines/aquaponics_engine.py:343` (`_evaluate_hardness`, `kh_dh < 4`) and `src/backend/app/domain/engines/aquaponics_engine.py:438` (`check_alkalinity_crash_risk`, `kh_dh < 4`) **Dimension:** D4 **Code:** production **Confidence:** confirmed
- **Problem:** The safety-relevant domain rule "KH below 4 °dH ⇒ pH-crash risk" is encoded twice with an unnamed `4` / `4.0` literal and near-duplicate DE/EN messages. The module already names comparable safety limits (`FREE_AMMONIA_SAFE_MGL`, `CYCLING_STABLE_DAYS_REQUIRED`), so this is both semantic duplication and an inconsistency with the established convention — the two thresholds can silently diverge.
- **Recommended remediation (not applied):** Introduce a module constant `KH_CRASH_THRESHOLD_DH = 4.0` and reference it from both sites (ideally factor the shared warning-construction too).

## Suggestion

### SCR-004: Dead class constant `FEED_PER_M2`
- **File:** `src/backend/app/domain/engines/aquaponics_engine.py:453` **Dimension:** D2 **Code:** production **Confidence:** confirmed
- **Problem:** `StockingDensityCalculator.FEED_PER_M2` is defined but referenced nowhere in the tree (grep-confirmed, single hit). ruff's `ARG`/dead-attribute rules are not enabled, so tooling does not flag it. Dead knowledge invites drift.
- **Recommended remediation (not applied):** Remove the constant, or wire it into `calculate_fish_plant_ratio` if it was intended as the per-system feed reference.

### SCR-005: Unused parameters (one with a misleading docstring)
- **File:** `src/backend/app/domain/engines/aquaponics_engine.py:469-471` (`calculate_fish_plant_ratio(..., system_type)`) and `:867` (`calculate_mortality_rate(fish_stock, period_days=7)`) **Dimension:** D2 **Code:** production **Confidence:** confirmed
- **Problem:** `system_type` is never read. `period_days` is never read yet the docstring says the result is "cumulative mortality fraction relative to the initial stock" — the parameter implies a windowing that does not happen, so the signature lies about behaviour. Not ruff-reportable (`ARG` not enabled).
- **Recommended remediation (not applied):** Drop the unused parameters, or actually honour `period_days` (filter mortality to the window) and correct the docstring.

### SCR-006: Duplicated `KnowledgeChunkResponse` mapping in the knowledge-service router
- **File:** `src/knowledge-service/app/main.py:176-186` (`/search`) and `:210-220` (`/ask`) **Dimension:** D2 **Code:** production **Confidence:** confirmed
- **Problem:** The same 8-field `VectorChunk -> KnowledgeChunkResponse` projection is copy-pasted into two endpoints; a new chunk field must be added in both.
- **Recommended remediation (not applied):** Add a small `_to_chunk_response(c: VectorChunk) -> KnowledgeChunkResponse` and reuse it.

### SCR-007: Unescaped LIKE metacharacters in species search
- **File:** `src/backend/app/data_access/arango/species_repository.py:99` **Dimension:** D1 **Code:** production **Confidence:** confirmed
- **Problem:** `builder.filter("scientific_name", "LIKE", f"%{name}%")` binds the value safely (no AQL injection), but `%` and `_` inside user-supplied `name` are treated as AQL LIKE wildcards, so a query containing them silently broadens/alters matching rather than searching literally.
- **Recommended remediation (not applied):** Escape `%`, `_`, `\` in `name` before wrapping (AQL LIKE supports `\` escaping), or document the wildcard behaviour as intentional.

## Info

### SCR-008: Function-local imports of `NotFoundError` in the botanical-families router
- **File:** `src/backend/app/api/v1/botanical_families/router.py:39` and `:49` **Dimension:** D5 **Code:** production **Confidence:** confirmed
- **Problem:** `from app.common.exceptions import NotFoundError` is imported inside `get_family` and `get_family_species` bodies rather than at module top; there is no circular-import reason (the exception module is leaf-level). Minor idiom inconsistency with the rest of the file. Not ruff-reportable.
- **Recommended remediation (not applied):** Hoist to a single top-level import.

## Work packages (Critical + Warning; disjoint file sets)

| # | Findings | Files | Goal | Routing target | Depends on |
|---|----------|-------|------|----------------|------------|
| WP-1 | SCR-002 | `src/inference-service/app/main.py` | Extract one `_resolve_vector` helper and call it from both reference-upsert endpoints | fullstack-developer | — |
| WP-2 | SCR-003 (opportunistically SCR-004, SCR-005 — same file) | `src/backend/app/domain/engines/aquaponics_engine.py` | Name the KH-crash threshold as a module constant used by both sites; drop dead `FEED_PER_M2` and the unused params (fix the mortality docstring) | fullstack-developer | — |
| WP-3 | SCR-001 | `src/knowledge-service/pyproject.toml`, `src/inference-service/pyproject.toml`, `src/libs/kp_vectordb/pyproject.toml` | Add a `[tool.mypy]` baseline to the microservices/lib and wire it into the `static` CI gate | fullstack-developer | — |

All three packages have disjoint file sets and no ordering dependencies — they are parallel-safe. WP-1 and WP-3 both touch the inference-service package but different files (`app/main.py` vs `pyproject.toml`), so they remain disjoint. The Suggestion/Info findings SCR-006, SCR-007 and SCR-008 are left unpackaged by contract (not Critical/Warning); SCR-006 (`src/knowledge-service/app/main.py`) and SCR-007/SCR-008 touch files not claimed by any package above, so they can be picked up independently without collision.
