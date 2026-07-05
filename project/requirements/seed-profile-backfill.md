# Requirements — Seed-Profile Data Backfill (Issue #301)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (authoritative source at
claude-shared/spec/project/requirements-elicitation/en.md).
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

- **Issue:** https://github.com/nolte/kamerplanter/issues/301
- **Branch / worktree:** `feat/seed-profile-backfill`
- **Upstream:** PR #300 (capability shipped); review `spec/analysis/seed-pipeline-agent-review.md` (B7, Phase 5)
- **Plan:** `.resume/seed-profile-backfill/plan.md`

## Bounded context

- **What:** Populate the `seed_profile` sub-object (germination/sowing metadata) for **every
  seed-propagated species** using the seed-profile-aware pipeline shipped in PR #300. The
  *capability* (schema, `SeedProfile` model, enums, import mapping) already exists; this issue
  delivers the **data**. All `seed_profile` values are currently `null`.
- **For whom:** Onboarding beginners (REQ-020 starter-kits / REQ-021 experience levels) and users
  of common vegetables/herbs who need sowing and germination guidance.
- **Explicitly out of scope:** No pipeline/schema/model changes, no new enum or field definitions,
  no weakening of existing schema/enum constraints. Purely vegetatively propagated species stay
  `seed_profile: null` **by design**.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `6`
  (spec defaults; unchanged — this is a data-backfill of an existing capability, not a novel design,
  so the default risk posture applies).
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` (every required dimension ≥ `τ_high`; no remaining question has positive
  net EVPI — the Steckbrief→YAML source-of-truth loop was withheld as a discretionary-zone question
  because it is already established in the plan and covered by the invariants).

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Teach-back of pipeline flow + field list accepted; grounded against schema (`_defs.schema.yaml:241`, `plant_info.schema.yaml:359`) |
| `non_functional` | yes | 0.85 | interpretation | Invariants confirmed (≥2 independent sources, no fabrication, validator-clean, EN source per NFR-003); `k=2` sketch of "no-fab" converged |
| `constraints` | yes | 0.85 | interpretation | Pipeline agents + Steckbrief-as-source confirmed; grounded against on-disk agents and `propagation_configs` enum |
| `domain_objects` | yes | 0.90 | interpretation | `SeedProfile` fields enumerated from schema; `seed`/`self_seeding` propagation enum verified in data |
| `actors` | yes | 0.85 | interpretation | 4-stage pipeline + operator + validator/skill confirmed from plan |
| `acceptance_criteria` | yes | 0.85 | specification→resolved | Definition-of-Done teach-back presented; PR-cut = single PR (authoritative answer); null-gate explicitly confirmed |
| `edge_cases` | yes | 0.85 | specification→resolved | Null-marking convention decided authoritatively: **rule-based, no marker** (forced clarification below `τ_low`) |
| `scope_boundaries` | yes | 0.85 | specification→resolved | Authoritative answer: **all seed-propagated species, one PR**; enumeration rule grounded via `k=2` data self-consistency check (see R2 risk) |

_Self-consistency (`k≥2`) evidence event:_ two independent enumeration sketches of "all seed-propagated
species" were generated and **diverged** — sketch A ("`seed`/`self_seeding` ∈ `propagation_configs`")
yielded 55 species from `plant_info*.yaml`; sketch B (add "presence of sowing fields") additionally
caught ~42 `species.yaml` base entries with no propagation info but clear sowing signals (e.g.
*Solanum lycopersicum*). The divergence is the ambiguity signal that lowered raw `c_d` on
`scope_boundaries` and produced the refined determination rule (R2) plus its residual risk.

## Requirements

- **R1** — WHEN a species is seed-propagated, the backfill SHALL populate its `seed_profile`
  (`germination_temp_min_c`/`_max_c`, `sowing_depth_cm`, `days_to_germination`, `seed_viability_years`,
  `light_germination`, `pretreatment`, `thousand_seed_weight_g`, `sowing_density_per_m2`) from the
  Steckbrief §Saatgut section, leaving any individually unknown field `null`.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: teach-back of pipeline flow + plan field list

- **R2** — WHEN enumerating "seed-propagated" species, the backfill SHALL classify a species as
  seed-propagated if its `propagation_configs`/`propagation_methods` contain `seed` or `self_seeding`,
  **or** it carries sowing signals (`sowing_indoor_*`, `sowing_outdoor_*`, `direct_sow_months`);
  ambiguous cases SHALL be resolved from the Steckbrief §Vermehrung, never guessed.
  - _dimension_: `scope_boundaries` · _status_: `assumed` · _source_: derived from the `k=2` topology
    self-consistency check (operator confirmed *"alles Samen-Vermehrte"*; the exact enumeration rule
    was delegated, not dictated)

- **R3** — The backfill SHALL cover **both** seed-data layers in scope: `species.yaml` (base species)
  and `plant_info*.yaml` (`new_species` + `species_enrichment`). `seed_profile` for a `species.yaml`-only
  species SHALL be written as a `species_enrichment` block in a `plant_info*.yaml` file (the importer
  `seed_plant_info.py` merges `seed_profile` onto the existing species by `scientific_name`); `species.yaml`
  SHALL NOT be hand-edited. Of the 115 seed species: 91 already have a `plant_info` entry; 24 are
  `species.yaml`-only and receive a new enrichment block.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: resolved from import code
    (`seed_plant_info.py:246/257`; `species_enrichment` is a dict keyed by `scientific_name`)

- **R4** — WHEN a species is purely vegetatively propagated (no `seed`/`self_seeding` method and no
  sowing signal), the backfill SHALL leave `seed_profile: null` and this SHALL be treated as the
  **expected, non-gap state derived from the propagation data** — no per-species marker and no schema
  field is added; the validator / `check-seed-data` SHALL derive "expected null" from `propagation_configs`.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: operator answer "Regelbasiert, kein Marker"

- **R5** — Every populated `seed_profile` value SHALL trace to **≥2 independent authoritative sources**
  (ISTA / RHS / University-Extension); a value that cannot be sourced twice SHALL remain `null` rather
  than be estimated.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan invariant "No fabrication", teach-back accepted

- **R6** — The Steckbrief (`spec/knowledge/plants/*.md`) SHALL remain the single source of truth; the
  YAML `seed_profile` SHALL be generated from it via the pipeline
  (`plant-info-document-generator` → `plant-info-to-seed-yaml`) and SHALL NOT be hand-edited into drift.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: plan invariant + teach-back accepted

- **R7** — The delivery SHALL be a **single pull request** covering the full confirmed seed-propagated
  set, and SHALL be considered done only WHEN: (a) `seed-data-validator` is structurally clean on all
  touched files, (b) `check-seed-data` is factually clean on the touched species, (c) all vegetative-only
  species remain provably-intentional `null` per R4, and (d) backend seed/migration tests + `ruff` are green.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: operator answer "Ein einziger PR" + DoD teach-back

- **R8** — Source code SHALL stay English (NFR-003); Steckbriefe and end-user docs stay German.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: project CLAUDE.md / NFR-003

## Surviving assumptions / open risks

- **[R2 — enumeration completeness]** The seed-vs-vegetative determination rule is `assumed`, not
  operator-confirmed field-by-field. The naive `propagation_configs`-only rule misses ~42 `species.yaml`
  base entries (incl. the most common vegetables). The refined rule (add sowing signals) is the working
  hypothesis; each genuinely ambiguous species is resolved from the Steckbrief §Vermehrung during
  research. **Risk:** a seed-propagated species with neither a `seed` method nor sowing fields would be
  silently skipped — mitigated by cross-checking the final worklist against the starter-kit species and
  the Steckbrief corpus before research starts.
- **[R3 — two-layer scope]** Writing `seed_profile` into `species.yaml` (base) vs `plant_info*.yaml`
  (enrichment) is `assumed`; the exact write target per species follows the pipeline's existing
  convention (Steckbrief → `plant-info-to-seed-yaml`). If the converter only targets `plant_info*`,
  base-only species (e.g. tomato) need an enrichment entry or a `species.yaml` write — to confirm at
  the first conversion step.
- **[Scope magnitude]** The confirmed "all seed-propagated, one PR" scope is ~55 (`plant_info`) + ~24
  (`species.yaml` with seed method) + a subset of the 42 no-propagation-info base species = **~80–90
  species** to research at ≥2 sources each. This is a large single PR; the operator explicitly chose it
  over incremental PRs. Reviewer load is a known, accepted trade-off.
- All eight required dimensions are ≥ `τ_high`; no dimension is below threshold at termination.
