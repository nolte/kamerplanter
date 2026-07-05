# Plan: E1 indoor light-schedule photoperiod trigger (REQ-018)

- **Issue:** #382 — `feat(lifecycle): E1 indoor light-schedule photoperiod trigger (REQ-018)`
- **Branch:** `feat/lifecycle-indoor-photoperiod`
- **Split off from:** #305 (REQ-003 E1 photoperiod trigger; outdoor path merged in #385)

## Goal

Make the `photoperiod_based` phase-transition trigger fire for **indoor** plants by
deriving the effective photoperiod (hours of light per day) from the configured
grow-light schedule (REQ-018), the way the outdoor path already derives it from
astronomical day length. Short-day *and* long-day induction must work from the
light schedule. Autoflower stays on `time_based` (no photoperiod rule — no code
change, just must not accidentally fire).

## Researched current state (verified in the worktree)

- **Evaluator is source-agnostic and needs NO change.**
  `TransitionTriggerEvaluator.photoperiod_should_fire(photoperiod_type,
  critical_day_length_hours, day_length_hours)`
  (`src/backend/app/domain/engines/transition_trigger_evaluator.py:29-46`) only
  compares an injected `day_length_hours` against the critical value
  (`SHORT_DAY` fires when `<`, `LONG_DAY` when `>`, `DAY_NEUTRAL`/`None` never).
  It does not care whether the hours came from the sun or a grow light.
- **The single seam is** `_day_length_for_plant(plant, site_repo)` in
  `src/backend/app/tasks/phase_transitions.py:20-31`, called from the
  `PHOTOPERIOD_BASED` branch at line 75-82. It currently returns outdoor day
  length (`plant.site_key` → `Site.gps_coordinates`/`timezone` →
  `calculate_sun_times`) or `None`. Its docstring carries the exact deferral
  marker for this issue (lines 22-23).
- **The indoor light schedule ALREADY exists and is persisted** on the
  `Location` model (`src/backend/app/domain/models/site.py:57-89`):
  `light_type: LightType` (`natural|led|hps|cmh|mixed`), `lights_on: "HH:MM"`,
  `lights_off: "HH:MM"`, `use_dynamic_sunrise: bool`. Reachable via
  `site_repo.get_location_by_key(key)`
  (`src/backend/app/data_access/arango/site_repository.py:54`) — **no new
  repository dependency needed**. A "hours of light per day" helper does NOT
  exist yet and must be written (with midnight wrap).
- **REQ-018 actuator layer is a non-functional scaffold** (`actuator.py`,
  `actuator_service.py` raise `NotImplementedError`, empty router). Do NOT depend
  on it — the schedule lives on `Location`.
- **Indoor discriminator:** no `is_indoor`/`light_source` flag on the
  species/lifecycle model. Indoor-ness is a property of the location: derive from
  `Location.light_type != NATURAL` (+ `lights_on`/`lights_off` present). Related
  signals that MAY be cross-checked: `Site.type` (`SiteType`,
  `common/enums.py:231`), `LocationType.is_indoor` (`location_type.py:11`).
- **Plant hook:** `PlantInstance.location_key` (`plant_instance.py:15`) is the
  indoor hook; `site_key` (`:14`) is the existing outdoor hook. A plant may carry
  both.
- **Tests:**
  - `src/backend/tests/unit/tasks/test_phase_transitions.py` — task-level; mocks
    `app.common.dependencies` getters into `sys.modules` before import;
    `_plant(**overrides)` helper builds a `SimpleNamespace` (default
    `site_key=None`, **no `location_key` yet — must be added**). Existing
    `test_photoperiod_fires_for_short_day` monkeypatches `_day_length_for_plant`
    directly; the new indoor tests should instead exercise the real function with
    a mock `site_repo.get_location_by_key(...)` returning a `Location`.
  - `src/backend/tests/unit/domain/engines/test_transition_trigger_evaluator.py`
    — pure evaluator contract tests (unchanged).

## Design decision (load-bearing)

**Extend `_day_length_for_plant` to resolve indoor photoperiod from
`Location.lights_on/lights_off` first, then fall back to the existing outdoor
GPS path.** The evaluator and the calling branch stay untouched. Add a small pure
helper (e.g. `_light_hours_from_schedule(lights_on, lights_off) -> float | None`)
that parses `"HH:MM"` and computes `(off - on) mod 24`, ideally placed in a
domain calculator (near `photoperiod_calculator.py`) so it is unit-testable in
isolation and reusable.

### Recommended resolutions to the open questions (defaults chosen for autonomy — validate against tests / spec while implementing)

1. **Precedence when a plant has BOTH an artificially-lit location and a GPS
   site.** → *Indoor wins.* An artificially lit plant does not experience the
   astronomical day length. Try indoor first; fall back to outdoor GPS only when
   the location gives no usable artificial schedule.
2. **What counts as "usable artificial schedule"?** → `light_type != NATURAL`
   **and** both `lights_on` and `lights_off` set **and**
   `use_dynamic_sunrise == False`. If `use_dynamic_sunrise == True`, the light
   tracks the sun → treat as outdoor (fall through to GPS path).
3. **`light_type == NATURAL` on an indoor/windowsill location (no grow light).**
   → No artificial schedule → fall through; if no GPS either, return `None`
   (trigger skipped, unchanged behaviour). Acceptable: a pure-daylight windowsill
   has no controllable photoperiod.
4. **Autoflower.** → No code change. Autoflower species carry no
   `PHOTOPERIOD_BASED` rule, so they never enter this branch. Add a regression
   test asserting a `time_based` autoflower plant does not fire via photoperiod.
5. **Midnight wrap.** `lights_on="18:00"`, `lights_off="06:00"` → 12h. Formula
   `(off_minutes - on_minutes) mod (24*60)`. `on == off` → 0h (or treat as None?
   decide: 0h = permanent dark is nonsensical → treat equal as 24h? **Flag:**
   confirm the 0/24 edge with a test; lean to `on==off → None` (ambiguous,
   skip)).

> These are recommended defaults, not frozen. If the REQ-018 spec or the existing
> `Location` validators contradict any of them, the spec/validators win — adjust
> and note it in this plan.

## Ordered work steps

1. **(requirements-elicit gate)** Capture the requirement precisely; confirm the
   five open-question defaults above against `spec/req/REQ-018*` and
   `spec/req/REQ-003*`. Adjust the plan if the spec disagrees.
2. Write the pure helper `_light_hours_from_schedule` (or
   `effective_light_hours`) + unit tests (midnight wrap, equal, unset, invalid).
   Prefer a home under `src/backend/app/domain/calculators/`.
3. Extend `_day_length_for_plant` in `tasks/phase_transitions.py`: resolve
   `plant.location_key` → `Location` via `site_repo.get_location_by_key`; if it
   yields a usable artificial schedule, return the light hours; else fall back to
   the current outdoor GPS logic. Update the docstring (remove the deferral
   marker). Guard for a plant without `location_key`.
4. Extend the task test fixture `_plant` to carry `location_key`; add indoor
   tests: short-day induction fires when light hours < critical; long-day fires
   when > critical; `use_dynamic_sunrise=True` falls back to outdoor; autoflower
   (`time_based`) does not fire via photoperiod. Exercise the real
   `_day_length_for_plant` with a mocked `get_location_by_key`.
5. Run the quality gate (backend pytest + ruff + any touched frontend — none
   expected here). Follow the mandatory post-implementation 3-agent chain
   (UI-review not applicable → tests + docs) per project feedback rules.
6. Update docs if REQ-003/REQ-018 user-guide pages describe photoperiod triggers
   (check MkDocs `user-guide` for a lifecycle/photoperiod page).
7. Open the PR to `develop` via `pull-request-create` (English title/body,
   Conventional Commits), link issue #382.

## Invariants & guardrails (from CLAUDE.md + specs)

- Source code English only (NFR-003); German only in docs/comments where the
  project already does so.
- Strict 5-layer architecture (NFR-001): the task orchestrates; derivation logic
  belongs in a domain calculator/engine, not inlined business rules in the task.
- No new Celery beat wiring needed — `check_auto_transitions` already runs.
- Do NOT depend on the REQ-018 actuator scaffold (raises `NotImplementedError`).
- Phase engine has no backward transitions; do not weaken that.
- Multi-tenancy: the system task already iterates `all_tenants=True`;
  `get_location_by_key` must not leak across tenants — verify the location lookup
  respects the plant's tenant (check whether `get_location_by_key` is
  tenant-scoped; if not, ensure we only read a location belonging to the plant).
- Keep the diff focused: no unrelated refactors of the outdoor path.
- Work happens only in this worktree; primary checkout stays on `develop`.

## Status / resume-anchor checklist

- [x] 1. requirements-elicit gate passed; open-question defaults confirmed vs REQ-018/REQ-003 spec
      → artifact `project/requirements/indoor-photoperiod-trigger.md` (U_gate=0.85); spec confirms Q4 (autoflower time_based) & the read model; user teach-back confirmed Q1 (indoor wins; dynamic→outdoor) & Q5 (on==off → None). Q2/Q3 defaults stand (no spec contradiction).
- [x] 2. `effective_light_hours` helper (`domain/calculators/photoperiod_calculator.py`) + 9 unit tests written & green (midnight wrap, equal→None, missing, malformed). Note: single `except ValueError` — avoids the ruff-format tuple-except SyntaxError bug.
- [x] 3. `_day_length_for_plant` split into `_indoor_light_hours_for_plant` (indoor-first, tenant-guarded, natural/dynamic-sunrise fall-through) + `_outdoor_day_length_for_plant`; deferral marker removed; `LightType`+`effective_light_hours` imported.
- [x] 4. Indoor task tests green: short-day fires, long-day fires, dynamic-sunrise→outdoor fallback, natural-light no-fire, autoflower(day-neutral) no-fire, cross-tenant location ignored. Fixture `_plant` now carries `location_key`+`tenant_key`.
- [x] 5. Quality gate: `ruff check`+`ruff format --check` clean on touched files; `pytest tasks/ domain/` = 2255 passed. UI-review N/A (no frontend); tests role done (46 targeted + 2255 suite); docs role = box 6.
- [x] 6. Docs updated (DE canonical + EN mirror in sync): `user-guide/growth-phases.md` photoperiod section + tip admonition now describe indoor light-schedule source (indoor wins) vs outdoor GPS.
- [ ] 7. PR to develop opened (via pull-request-create), #382 linked

> **Resume anchor:** the next session resumes at the first unchecked box above.
