# Requirements — Spec-Audit: vollständiger Pflanzen-Lifecycle über alle Arten

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What is being built:** An audit of the specification corpus under `spec/`
  along four axes — contradiction detection, downstream readiness, spec-vs-code
  drift, and completeness — **bundled through one domain lens: does the spec
  model the _complete plant lifecycle_, allowing that _different plant species
  have different lifecycles_** (annual / biennial / perennial, plus special
  cases: cannabis with post-harvest/cure, propagation via clone/cutting/graft,
  outdoor overwintering & dormancy).
- **For whom:** The operator (repo owner), as input for spec corrections and
  roadmap decisions; consumed alongside the existing `.audits/` corpus.
- **Deliverable:** A severity-sorted findings report under `.audits/spec-audit/`
  **and** direct spec fixes, each applied with a per-change diff review.
- **Explicitly out of scope:** Changing source code under `src/`; violating
  NFR-003 (specs/docs stay German, code stays English); silently rewriting a
  spec without a reviewed diff.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`,
  question budget = `~4` (spec defaults; unchanged).
- `U_gate = min_d c_d` over required dimensions = **0.78**
- Termination: `saturation` — the one dimension below `τ_high`
  (`acceptance_criteria`, 0.78) is derivable from the two confirmed decisions
  and each substantive fix is diff-reviewed, so its expected value of further
  questioning is below cost. Recorded as a named residual risk below.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.88 | specification | Teach-back confirmed: 4 axes bundled by the lifecycle-over-species lens |
| `non_functional` | yes | 0.82 | interpretation | Confirmed constraints: NFR-003 preserved; read-only default overridden to apply-fixes-with-diff-review |
| `constraints` | yes | 0.85 | specification | Confirmed: whole-corpus scan, per-change diff review, reuse existing runners/reviewer agents |
| `domain_objects` | yes | 0.82 | interpretation | Lifecycle archetypes named in teach-back and confirmed; grounded in CLAUDE.md domain model (REQ-003 phases, REQ-022 overwintering, REQ-017 lineage) |
| `actors` | yes | 0.80 | specification | Operator = report consumer + per-fix approver; reviewer subagents run the axes |
| `acceptance_criteria` | yes | 0.78 | interpretation | Derived (k=2 self-consistency) from the two confirmed decisions; not separately teach-backed → assumed |
| `edge_cases` | yes | 0.82 | specification | The note itself is the edge-case driver: biennials, perennials, dormancy/overwintering, cannabis post-harvest, propagation paths |
| `scope_boundaries` | yes | 0.85 | specification | Confirmed: whole `spec/` corpus, lifecycle as priority lens; `src/` out of scope |

## Requirements

<!-- EARS/CNL form; tagged confirmed/assumed with traceability. -->

- **R1** — WHEN the audit runs, the audit process SHALL evaluate the `spec/`
  corpus along all four axes (contradiction, readiness, spec-vs-code drift,
  completeness).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Widersprüche, Readiness, Spec-vs-Code-Drift, Vollständigkeit"

- **R2** — WHEN evaluating any lifecycle-bearing spec, the audit SHALL check it
  against each plant-lifecycle archetype — annual, biennial, perennial, cannabis
  (incl. post-harvest/cure), propagation (clone/cutting/graft), and outdoor
  overwintering/dormancy — and flag where the phase model or related specs fail
  to represent a given archetype.
  - _dimension_: `edge_cases` / `domain_objects` · _status_: `confirmed` · _source_: "Es soll der vollständige lifecycle der Pflanzen abgebildet werden, achte darauf das unterschiedliche arten unterschiedliche lifecycles haben."

- **R3** — WHEN scoping the audit, the audit SHALL scan the whole `spec/`
  corpus, with the lifecycle-over-species concern as the priority/sort lens
  rather than a hard filter.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: "Ja, aber ganzer Korpus"

- **R4** — WHEN the audit completes, the audit SHALL produce a severity-sorted
  findings report under `.audits/spec-audit/`, each finding traced to a spec
  file and classified by axis and by affected lifecycle archetype.
  - _dimension_: `acceptance_criteria` · _status_: `assumed` · _source_: derived from "Report + Spec-Fixes anwenden"

- **R5** — WHEN a finding warrants a spec correction, the audit SHALL apply the
  fix directly to the spec, presenting a diff for review before each change; and
  SHALL NOT alter `src/` code or violate NFR-003 (German docs / English code).
  - _dimension_: `non_functional` / `constraints` · _status_: `confirmed` · _source_: "Report + Spec-Fixes anwenden (mit Diff-Review pro Änderung)"

- **R6** — WHEN running the axes, the audit SHOULD reuse the existing tooling
  (`req-coverage-audit` runner, `spec-readiness-reviewer`,
  `requirements-contradiction-analyzer`, `spec-drift-audit`, persona reviewers)
  rather than rebuild equivalent passes; subagents run on Fable 5.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: plan invariants + "mach weiter nutze fabel 5"

## Surviving assumptions / open risks

- **[assumed · acceptance_criteria, c_d 0.78]** The precise "done" bar — how many
  findings / how deep before saturation — is not separately teach-backed. Treated
  as: report exists under `.audits/spec-audit/`, every lifecycle archetype is
  explicitly evaluated against REQ-003 and its lifecycle neighbours, and every
  substantive fix is diff-reviewed. Revisit if the first pass reveals the bar is
  wrong.
- **[risk]** Some lifecycle gaps require a spec _design decision_ (e.g. adding a
  biennial two-year phase path to the REQ-003 state machine), not a mechanical
  edit. These are surfaced in the report and applied only via per-change diff
  review (R5) — never auto-applied.
- **[risk]** Whole-corpus scan across four axes is broad; the lifecycle lens
  (R3) is the prioritiser so the report leads with lifecycle-critical findings
  and does not drown them in unrelated nits.

## Revisit 2026-07-02 — Fix-ambition changed (IKIWISI)

The operator changed the fix direction from **truthful correction (spec-hygiene)**
to **close the gaps now** for the structural D-class findings. Consequences:

- **R5 refined:** the audit now not only annotates but **specifies the missing
  lifecycle model** in the spec bodies. Because D6 depends on A1 and D7 on A3,
  the A-class fields (`flowering_strategy`, `cultivation_cycle_type`,
  `GrowthHabit` expansion) were actually added to the REQ-001 body and the
  earlier "planned, not in body" changelog annotations were withdrawn.
- **Scope boundary held:** implementation stays **spec-only** — `src/` untouched
  (NFR-003); backend/frontend/seed code + the ~210-species backfill remain
  backlog per `.audits/datenmodell-pflanzeneigenschaften-plan.md` (WP-1/3/4/5/10).
- **Delivered:** D1–D7 specified across REQ-001 (v4.5), REQ-003 (v2.8), REQ-017
  (v1.4), REQ-022 (v2.6), REQ-039 (v1.2). See
  `.audits/spec-audit/lifecycle-audit-report.md` §5.
