# Requirements — actionlint + shellcheck as blocking gates

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (authoritative source at
claude-shared/spec/project/requirements-elicitation/en.md).
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

- **Working copy / branch:** `feat/ci-actionlint-shellcheck` (off `origin/develop` @ `78785f87b`)
- **Issue:** [#1295](https://github.com/nolte/kamerplanter/issues/1295) — classified
  `feature-request` (secondary `infra`) by `issue-orchestrate`
- **Trigger:** the nightly Nuclei command ran truncated for 22 consecutive nights
  (#1010 → fixed in #1294); a `#` on a backslash-continued line ended the logical
  line, and no linter in this repository was in a position to say so
- **Governing constraints:** NFR-018 §2 (a check that cannot report a failure must
  not exist), NFR-018 §4 (promotion of a gate to blocking is a measured decision),
  NFR-003 (source and GitHub-facing content in English)

## Bounded context

- **What:** Wire `actionlint` (with its shellcheck integration) over
  `.github/workflows/**` and `shellcheck` over the repository's own `*.sh` as
  **enforced, version-pinned** gates in the required `static` lane.
- **Why it matters now:** three workflows already *reason about* shellcheck in
  their comments — `e2e-smoke.yml:191`, `e2e-nightly.yml:106`,
  `security-nuclei-nightly.yml:181` — while neither shellcheck nor actionlint runs
  anywhere. The invariant was believed enforced and was not, which is how #1010's
  defect survived a required lane for three weeks.
- **For whom:** the CI lane, and anyone editing a workflow or a shell script.
- **Explicitly out of scope:** `src/backend/.venv/**` and `**/node_modules/**`
  (vendored third-party code); every non-shell linter; any substantive change to a
  workflow beyond what the gates compel.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question
  budget = `3` — the spec defaults, matching the precedent in
  `hadolint-dl3025-healthcheck.md`. As there, the requirement arrived
  **code-grounded**: every factual claim below was measured before the interview
  opened, so the specification uncertainty was concentrated in two decisions rather
  than spread across the eight dimensions.
- `U_gate = min_d c_d` over required dimensions = **0.88**
- Termination: `saturation`. Two of three budgeted turns used; the third was
  withheld under the EVPI rule (see below).

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.92 | interpretation | Both tools measured against this tree: `docker rhysd/actionlint:latest` over `.github/workflows/**` on `78785f87b` → zero findings; `shellcheck -S warning` over the 21 own `*.sh` → three findings, enumerated in R4 |
| `non_functional` | yes | 0.90 | specification→resolved | Operator chose "blocking from day one" over advisory and over a mixed gate, against a rendered preview naming the preconditions |
| `constraints` | yes | 0.92 | specification→resolved | Version pinning is part of the same authoritative answer; exclusions (`.venv`, `node_modules`) declared in the bounded context and confirmed at teach-back |
| `domain_objects` | yes | 0.95 | interpretation | Enumerated from source: 21 own `*.sh`, every file under `.github/workflows/`, the two tools, and `scripts/check_workflow_gate_integrity.py`'s fourth shape |
| `actors` | yes | 0.90 | interpretation | The required `static` lane; workflow and script authors; Renovate, which will own the version bumps once both tools are pinned |
| `acceptance_criteria` | yes | 0.88 | specification→resolved | Six criteria in #1295 plus R6's execution requirement; the operator's "blocking from day one" answer made R4 a precondition rather than a follow-up |
| `edge_cases` | yes | 0.85 | interpretation | The coverage boundary was measured, not assumed — see the self-consistency note; false-positive handling is fixed by R4's `disable`-with-reason form |
| `scope_boundaries` | yes | 0.90 | specification→resolved | Bounded context confirmed verbatim at teach-back, including both exclusions |

_Self-consistency (`k≥2`) evidence event:_ two independent readings of the
guard-overlap question diverged. Sketch A held that
`commented_continuation` merely duplicates `SC2215` and should be retired once
actionlint is enforced — which is what #1295 itself asserts. Sketch B held that
the two key on different things (structure vs. what follows the continuation) and
therefore cover different sets. The divergence put `edge_cases` below `τ_low`, so
the clarification was **mandatory**, and it was resolved by measurement rather than
by asking: three probe scripts through shellcheck 0.11.0 showed

| probe | line after the comment | shellcheck |
|---|---|---|
| A | `-tags exposure` (a flag) | `SC2215` |
| B | `dest.txt`, as `cp`'s second argument | `SC2225` (arity of `cp` is known to it) |
| C | `positional_arg` to an unknown command | **silent**, even at `-S style` |

Sketch B was correct and #1295's own wording ("It overlaps SC2215") is
**incomplete**: the coverage is partial. The operator then chose to keep both and
document the division of labour. Recorded here because the false claim originated
in this project's own issue text and would otherwise be inherited again.

_Withheld clarification (discretionary-zone restraint):_ the wiring mechanism —
a `.pre-commit-config.yaml` hook versus a dedicated GitHub Actions job, and the
corresponding pinning mechanism (`rev:` versus a pinned image digest) — was **not**
asked. This repository runs its pre-commit hooks inside the required `static` lane,
so the hook form satisfies R1–R3 without a second wiring, and the operator would
reasonably defer the mechanism to the implementer. EVPI did not exceed the cost of
a third turn. It survives as A1 below.

## Requirements

- **R1** — WHEN a file under `.github/workflows/**` is committed, the required
  `static` lane SHALL run `actionlint` with its shellcheck integration enabled and
  SHALL fail on any finding.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: operator answer
    "Blockierend ab Tag 1", against a preview reading `actionlint -> FAIL on any finding`
- **R2** — WHEN a shell script owned by this repository is committed, the `static`
  lane SHALL run `shellcheck` over it and SHALL fail on findings of severity
  `warning` or above.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: same answer,
    preview reading `shellcheck -> FAIL on >= warning`
- **R3** — The `actionlint` and `shellcheck` versions SHALL be pinned, so that an
  upstream release cannot turn the lane red without an explicit, reviewable bump.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: same answer,
    preview reading `beide Tools versionsgepinnt`. Rationale: "zero findings today"
    is a statement about today's rule set only, which is precisely the exposure
    NFR-018 §4 warns about when a gate is switched on early
- **R4** — BEFORE either gate becomes blocking, the three measured findings SHALL be
  resolved: `scripts/worktree_add.sh:69` (SC2088) by a `# shellcheck disable=SC2088`
  **carrying its reason** — the code deliberately expands a leading `~` itself, so
  this is a false positive, not a defect; `scripts/run-e2e.sh:33` (SC2155);
  `scripts/dev-teardown.sh:7` (SC2034).
  - _Placement correction, measured during WP-1 (2026-08-29)._ An earlier draft of this
    requirement read as if the directive belonged immediately above line 69. It does not,
    and following it literally **breaks the file**: shellcheck answers `SC1124`
    ("directives are only valid in front of complete commands like `case` statements, not
    individual case branches") plus `SC1073`, and then parses nothing further. The
    directive goes **before the whole `case`** (line 67). Accepted side effect, forced by
    the tool and not a choice: it then also covers the `"~")` branch, which reports
    nothing today — a loss of precision recorded here so nobody later "tightens" it back
    onto the branch and reintroduces `SC1124`.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: same
    answer, preview enumerating all three with their dispositions
- **R5** — The `commented_continuation` shape in
  `scripts/check_workflow_gate_integrity.py` SHALL be retained, and its docstring
  SHALL record the measured division of labour: shellcheck covers the flag case
  (`SC2215`) and commands whose arity it knows, and is silent on the generic
  positional case.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: operator answer
    "Beide behalten, Komplementarität dokumentieren", taken against the probe table
    above
- **R6** — WHEN #1010's comment placement is reintroduced into any workflow, the
  lane SHALL turn red, and this SHALL be demonstrated **by executing it**, not by
  reading the configuration.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: #1295
    acceptance criteria, reaffirmed at teach-back. A gate nobody has watched fail is
    a gate nobody knows works (NFR-018 §2)
  - _Scope correction, measured during WP-4 (2026-08-29)._ R6 as worded is satisfied —
    the lane does turn red — but it must **not** be read as "actionlint catches the
    #1010 form". Measured through `CI=true pre-commit run --all-files`: with a **flag**
    after the comment (the actual #1010 case) *both* halves report — the pre-existing
    `commented_continuation` guard and actionlint (`SC2215`); with a bare **positional**
    after the comment, actionlint is `Passed` and only the guard fires. So which half
    carries R6 depends on what follows the `#`, and the naive demonstration is
    **confounded** by the guard that has existed since #1294. The attributable proof for
    the half this issue adds is probe D (`sort f > f`, `SC2094`, no continuation
    involved): actionlint reports it, `check_workflow_gate_integrity.py` exits 0. That
    same measurement establishes R5's complementarity claim **through the lane** rather
    than only against the image.

## Assumptions and open risks

- **A1** (`assumed`) — Both gates are wired as `.pre-commit-config.yaml` hooks, which
  places them in the required `static` lane automatically, rather than as a separate
  GitHub Actions job. This is the established pattern in this repository
  (`workflow-gate-integrity` and the seed-schema hooks are wired exactly so), but the
  operator did not state it. If the implementer finds the hook form cannot pin the
  version reproducibly, this assumption is the one to revisit — R3 outranks it.
- **A2** (`assumed`) — `-S warning` is the right shellcheck floor. Nothing was
  measured about the `info`/`style` band; raising the floor later is a separate,
  additive decision.
- **Residual risk** — R3 bounds but does not remove the exposure: a pinned bump that
  introduces new rules will land as a red Renovate PR rather than a red nightly. That
  is the intended trade, and it is the reason R3 is a requirement rather than an
  implementation note.
- **Residual risk** — R5 leaves two checks over one broadly-shared invariant. The
  measured probe table is what keeps that from being undocumented duplication, and it
  belongs in the docstring rather than only here, because the next reader will meet
  the code before this artifact.
