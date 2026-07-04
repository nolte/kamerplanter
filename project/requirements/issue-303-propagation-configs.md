# Requirements — Issue #303: Reconcile propagation fields in database-schema.md

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (methodology spec shipped in claude-shared).
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back or
an authoritative decision by the user.
-->

## Bounded context

- **What:** Documentation-only rewrite of the propagation-field subsections in
  the reference docs `docs/de/reference/database-schema.md` (canonical) and
  `docs/en/reference/database-schema.md` (mirror). The deprecated flat fields
  (`propagation_methods`, `propagation_months`, `propagation_notes`) are still
  documented as the current data model with per-field tables; they must be
  replaced by the structured `propagation_configs` model (REQ-017) as the
  canonical documentation.
- **For whom:** Readers of the schema reference (developers, integrators,
  contributors) who model propagation data against the API / seed pipeline.
- **Out of scope:** Any change to backend models, enums, the seed importer, or
  other collections/subsections in the two files. No new API behaviour. This is
  strictly a docs reconciliation (label: `docs`).

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `4` (spec defaults, unchanged)
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` — the four load-bearing specification decisions were
  resolved by explicit authoritative answers; no positive-EVPI question remains.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | specification | Authoritative answers to Q1–Q4 (AskUserQuestion selections) |
| `non_functional` | yes | 0.90 | interpretation | Plan invariants: `mkdocs build --strict`, DE/EN parity, Lektorat DoD (D1–D6) |
| `constraints` | yes | 0.95 | interpretation | Plan guardrails + `spec/style-guides/DOCS.md` (docs-only, REQ-IDs in HTML comments, verbatim identifiers) |
| `domain_objects` | yes | 0.95 | interpretation | Code research: `species.py:134-161,283`, `enums.py:39-71` |
| `actors` | n/a — documentation task; sole actor is the schema-doc reader, no behavioural system role | — | — | — |
| `acceptance_criteria` | yes | 0.90 | specification | Q1–Q4 decisions + build/parity/Lektorat gates |
| `edge_cases` | yes | 0.85 | interpretation | 13→17 enum omission; `wood_stage` only for cutting-type methods; months validator; import-adaptation mapping |
| `scope_boundaries` | yes | 0.95 | specification | Bounded context above; docs-only, both files, no code |

## Requirements

<!-- Each requirement in EARS/CNL form, tagged confirmed/assumed, with
     traceability to the utterance / authoritative decision that produced it. -->

- **R1** — WHEN the schema reference documents species propagation, the two
  `database-schema.md` files SHALL present `propagation_configs` (REQ-017) as the
  canonical model in one consolidated `#### Species — field propagation_configs`
  subsection, written in the established nested-object prose style (cf. the
  `toxicity` / `seed_profile` subsections).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: plan "Design decision (load-bearing)" + Q4 selection
- **R2** — The new subsection SHALL list all **17** `PropagationMethod` enum
  values verbatim from `common/enums.py` (`seed, cutting, leaf_cutting, division,
  rhizome_division, bulb, bulbil, tuber, offset, runner, grafting, layering,
  air_layering, water_propagation, tissue_culture, spore, self_seeding`),
  fixing the current 13-value omission.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q1 = "Alle 17 Werte listen"
- **R3** — The new subsection SHALL describe the embedded `PropagationConfig`
  subfields (`method`, `months` `list[int]` 1–12 deduped+sorted, `wood_stage`
  only meaningful for cutting-type methods, `difficulty`, `notes` max 1000 chars)
  with their allowed enum values (`WoodStage`, `PropagationDifficulty`).
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: code research `species.py:134-161`, `enums.py:59-71`
- **R4** — The new subsection SHALL NOT cite a hard population count; propagation
  coverage SHALL be conveyed by a neutral note or omitted entirely (no stale
  numeric like "207" or "183 species").
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q2 = "Counts weglassen / neutrale Notiz"
- **R5** — The collection overview table (currently EN L28) SHALL replace the
  `propagation_methods[]` key field with `propagation_configs[]`.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q3 = "Ja, ersetzen"
- **R6** — The three flat fields SHALL NO LONGER have their own per-field tables;
  they SHALL be mentioned only in one brief "deprecated / adapted on import"
  note (repurposing the existing deprecation blockquote, EN L80).
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q4 = "Nur kurze Deprecation-Notiz"
- **R7** — WHEN the rewrite is complete, the docs SHALL build with
  `mkdocs build --strict` in the isolated docs venv with no nav/anchor/parity
  errors, and the DE (canonical) and EN (mirror) files SHALL keep identical
  slugs, anchors, field names and enum values.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan invariants + `spec/style-guides/DOCS.md`
- **R8** — The edited prose SHALL pass the docs Lektorat DoD (D1–D6): informal
  "du" voice in DE, REQ-IDs only inside HTML comments, admonition conventions.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: plan step 5 + `spec/style-guides/DOCS.md`

## Surviving assumptions / open risks

- **A1** (assumed) — The `toxicity` / `seed_profile` prose style is the correct
  target convention for the consolidated subsection. Low risk: both are adjacent
  nested-object subsections in the same file; confirmed as the doc's established
  pattern, not user-stated. Remedy if wrong: adjust to a Property/Value table.
- **A2** (assumed) — "Neutral note" for coverage (R4) means a short qualitative
  phrase (e.g. "maintained for most seed-pipeline species") rather than dropping
  all mention. If the user prefers zero mention, trim the note. Below-`τ_high`
  driver for `edge_cases` (0.85), surfaced here as the residual wording risk.
- Population numbers observed in the live EN file (143 crop species, 183 with
  propagation methods) differ from the plan's `207` figure — reinforces R4
  (drop hard counts) rather than re-citing any of them.
