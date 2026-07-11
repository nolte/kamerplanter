# Requirements — Photo-identification species deduplication via scientific_name normalization (Issue #436)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (methodology spec shipped in claude-shared).
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** Canonically normalize `scientific_name` along the photo-identification
  → species-creation path so deduplication works, eliminating duplicate species
  records that differ only by the hybrid marker (`×` U+00D7 vs ASCII `x`), casing,
  or whitespace. Plus a user-in-the-loop disambiguation flow with a remembered
  decision for uncertain (non-exact) matches.
- **For whom:** Users of the "Per Foto hinzufügen" (Pl@ntNet/DINOv2) flow, and
  data-quality stewards who must not accumulate duplicate species ("Datenleichen").
- **Split (route decision, operator-confirmed):**
  - **Part 1 — bounded bugfix, implemented directly (this PR):** normalization
    utility, persisted normalized lookup key, both dedup paths routed through it,
    idempotent `create_species`, backfill migration reconciling the observed
    `Fragaria` pair, unit tests.
  - **Part 2 — feature, routed to the formal pipeline (`roadmap-plan` /
    `feature-decompose`):** interactive disambiguation dialog, tenant-local
    remembered-decision store, similar-candidate ranking, frontend dialog.
- **Out of scope (both parts):** fully automatic fuzzy taxonomic resolution
  (author citations, `subsp.`/`var.`, full synonym graphs). Candidate ranking
  starts simple and is refined in a follow-up.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `6` (used: 4)
  <!-- spec defaults; unchanged. Issue body carried a detailed root-cause,
       expected behavior, proposed approach, and explicit AC, so the bugfix
       dimensions started high; the 4 questions targeted the feature design gaps. -->
- `U_gate = min_d c_d` over required dimensions = **0.82**
- Termination: `saturation` (all required dimensions ≥ τ_high after the 4 decision answers; no positive-EVPI question remained for Part 1; residual Part-2 refinements deferred to the pipeline)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.88 | specification | Issue root-cause + operator answers (create_species idempotent; dialog trigger = exact-only auto) |
| `non_functional` | yes | 0.82 | interpretation | Issue: persisted normalized key → fast indexed equality lookup (no scan); teach-back |
| `constraints` | yes | 0.85 | specification | Operator: tenant-local store; preserve original display spelling (Issue); reuse existing `_normalize` in photo_quality_assessor |
| `domain_objects` | yes | 0.83 | specification | Species + `scientific_name_normalized`; tenant-local alias mapping (operator answer) |
| `actors` | yes | 0.85 | interpretation | Identifying user, identification engine, species service, tenant (Issue + REQ-024) |
| `acceptance_criteria` | yes | 0.86 | specification | Issue's explicit AC checklist + operator decisions |
| `edge_cases` | yes | 0.80 | specification | `×`↔`x`, genus-hybrid prefix `× `/`x `, casing, whitespace, merge preserving active-plants row (Issue) |
| `scope_boundaries` | yes | 0.84 | specification | Issue "Notes / Scope Boundaries" + operator split decision |

## Requirements

<!-- Part 1 (P1-*) is the directly-implemented bugfix. Part 2 (P2-*) is routed to
     the formal pipeline and recorded here so feature-decompose inherits a
     confirmed requirement set. -->

### Part 1 — Bounded bugfix (implemented directly)

- **R1** — WHEN a `scientific_name` is normalized, the system SHALL unify the hybrid
  marker (`×` U+00D7 ↔ ASCII `x`, including the genus-hybrid prefix form `× `/`x `),
  `casefold()` the value, collapse internal whitespace, and strip — producing a
  single canonical key.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue "Proposed Approach → Normalization rules"
- **R2** — The system SHALL persist the canonical key as `scientific_name_normalized`
  on the Species document, populated on create and update, so lookup stays a fast
  indexed equality query rather than a scan.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: Issue "Proposed Approach → Persisted normalized lookup key"
- **R3** — The system SHALL preserve the original human-facing `scientific_name`
  display value; normalization SHALL NOT overwrite the user's/provider's chosen
  spelling.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Issue "Keep the original human-facing scientific_name display value intact"
- **R4** — WHEN the identify/match step (`_match_candidates`) looks up a suggestion,
  the system SHALL match against existing species using the normalized key, so
  `Fragaria × ananassa` resolves to an existing `Fragaria x ananassa` and reports
  `species_in_database=true` without creating a duplicate.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue AC #1 + root-cause point 1
- **R5** — WHEN `create_species` is called with a name whose normalized key already
  exists, the system SHALL resolve to (return) the existing species idempotently
  rather than raising an error or creating a duplicate.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Operator decision "create_species → auf bestehende Spezies auflösen (idempotent)"
- **R6** — The system SHALL provide a one-off backfill migration that populates
  `scientific_name_normalized` for existing species and reconciles the observed
  `Fragaria × / x ananassa` duplicate pair, preserving the row carrying active
  plants and the richer metadata (family, cultivars).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue AC #3 + "one-off migration"
- **R7** — Unit tests SHALL cover the normalization (`×`↔`x`, case, whitespace) and
  both dedup paths (`_match_candidates`, `create_species`).
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Issue AC #4

### Part 2 — Interactive disambiguation feature (routed to the pipeline)

- **R8** — WHEN a suggestion has no exact-after-normalization match, the system SHALL
  NOT silently create a new species; it SHALL present the suggestion alongside a
  ranked list of similar existing candidates and let the user choose "use existing"
  or "create new".
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue "Interactive Disambiguation" + operator decision "Exakt-nach-Normalisierung = Auto; sonst Dialog"
- **R9** — The exact-after-normalization match SHALL remain the auto-accept fast path
  (resolves to `species_in_database=true` without prompting); the interactive step
  applies only to non-exact cases.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue notes + operator "100%-certain" = exact-only definition
- **R10** — The system SHALL persist the user's disambiguation decision as a
  **tenant-local** mapping from the suggestion identity (incoming scientific
  name / provider suggestion key) to the resolved species — including explicit
  "keep new" outcomes — and re-apply it on the next identification of the same
  suggestion (auto-resolve or pre-select), and SHALL NOT re-propose a deliberately
  kept-separate suggestion for merging.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: Issue "Remember the decision / Re-offer" + operator decision "tenant-lokale Alias-Tabelle"
- **R11** — WHEN populating the disambiguation candidate list, the system SHALL rank
  similar existing species by a simple normalized string-distance heuristic
  (Trigram/Levenshtein on the normalized name), as a first version refined later.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Operator decision "Simpel: normalisierte String-Distanz (Start einfach)"
- **R12** — Tests SHALL cover: uncertain match → prompt; remembered "use existing"
  → auto-resolves next time; remembered "keep new" → not re-proposed for merge.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Issue AC #7

## Surviving assumptions / open risks

- **A1 (Part 1, assumed):** A shared normalization utility is introduced and the
  existing `_normalize` in `src/backend/app/domain/engines/photo_quality_assessor.py`
  is refactored to consume it (rather than a second parallel implementation).
  Confirm during implementation. _dimension_: `constraints`.
- **A2 (Part 1, assumed):** The backfill migration runs under the existing versioned
  migration framework (`app.migrations`, `schema_migrations`) rather than an ad-hoc
  script. _dimension_: `non_functional`.
- **A3 (Part 1, open risk):** `casefold()` on the normalized *key* is safe because
  the human-facing display value is preserved (R3); the normalized key is never
  shown to the user. Verify no code path reads `scientific_name_normalized` for
  display.
- **A4 (Part 2, deferred to pipeline):** The exact data model of the tenant-local
  remembered-decision store (collection vs. edge, key = provider+suggestion string),
  the confidence/ranking refinement beyond the simple heuristic, and the frontend
  dialog UX are left to `feature-decompose`; this artifact fixes the behavioral
  contract (R8–R12), not the schema.
- **A5 (Part 2, open risk):** Cross-tenant leakage — the remembered-decision store
  and the candidate list must be strictly tenant-scoped (SEC-001 pattern seen in
  prior PRs). Must be a hard test in the feature work.
