---
review-type: agent-review
target: ".claude/agents/unit-test-runner.md"
target-kind: agent
specs-applied:
  - slug: agent-management
    revision: "0e3b6f9"
  - slug: skill-vs-agent
    revision: "0e3b6f9"
  - slug: review-plan
    revision: "0e3b6f9"
  - slug: agent-review
    revision: "0e3b6f9"
repo-revision: "c558f311"
created: "2026-04-27"
status: in-progress
---

# Agent Review: unit-test-runner

## Scope

Target: `.claude/agents/unit-test-runner.md` (frontmatter + body, ~215 lines, no sibling assets under `.claude/agents/unit-test-runner/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, factual correctness of the bash commands, the dispatching skill (none declared but `quality-gate` skill is conceptually adjacent).

## Summary

- BLOCKER: 4
- WARNING: 4
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations: body is German, no rationale section, no upfront output contract, hard-coded absolute paths in bash commands violate the no-absolute-paths invariant and the runtime-location MUST NOT-assume invariant. Plus a duplicate-prevention overlap with the `quality-gate` skill.
Next concrete action: author addresses the four BLOCKERs (translate body, add rationale, lift output contract, replace absolute paths with project-relative paths) and clarifies the boundary against the `quality-gate` skill.

## Findings

### BLOCKER

- [ ] [agent-management.english-body] Frontmatter `description` and the entire body are German; `agent-management` Structure-MUST requires English content for token efficiency and portability.
      Where: `.claude/agents/unit-test-runner.md:4` (description) and lines 10-215 (entire body — step headings, prose, table columns, abgrenzung table).
      Fix: Translate description, all step headings ("Schritt 1: Statische Analyse — Backend" → "Step 1: Static analysis — Backend"), prose, and tables to English. Keep German only when literally quoting style-guide section names like "Abschnitt 16 (Tests)".
      Verify: A `lang detect` pass on body returns >95% English; section headings read `## Step N:` etc. in English.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/unit-test-runner.md:1-215` (no rationale section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly *context-window protection* (large pytest/vitest output kept out of the main thread), *self-contained input/output* (run tests, return result + fixes), and *parallelism* (can run alongside other implementation agents). Cite at least one counter-dimension. Especially important given the `quality-gate` skill exists in this functional cluster.
      Verify: Section reading "## Rationale" or equivalent exists naming ≥1 decisive dimension; grep returns ≥1 hit for "context-window", "self-contained", or "parallelism".

- [ ] [agent-management.output-shape] Expected output shape is described only in Step 6 as a Markdown report skeleton; the file lacks an upfront "Output contract" stating what the parent caller receives.
      Where: `.claude/agents/unit-test-runner.md:159-191`.
      Fix: Add an "Output contract" section near the top stating: (a) what the parent receives (a structured chat report — no files written, see write-effects finding below), (b) the report's required tables (statische Analyse, Unit-Tests, Durchgefuehrte Fixes, Offene Findings, Merge-Bereitschaft), (c) explicit go/no-go statement at the bottom (`MERGE-BEREIT` / `NICHT MERGE-BEREIT`).
      Verify: A "Output contract" section exists near the top; reading it tells a parent caller the deliverable shape.

- [x] [agent-management.no-hard-coded-absolute-paths] Body contains hard-coded absolute paths like `/home/nolte/repos/github/kamerplanter/src/backend` in five `cd` commands; per `agent-management.runtime-location` the agent MUST NOT assume a particular absolute install location and per `agent-review` no hard-coded absolute paths in body or sibling assets is a MUST.
      Where: `.claude/agents/unit-test-runner.md:42-43, 64-65, 86, 92, 147-148, 152` (every `cd /home/nolte/...` block).
      Fix: Replace absolute paths with paths relative to the repository root (e.g. `cd src/backend`) and document the assumption that the parent invokes the agent with `cwd` at the repo root. Alternatively, parameterize via `${REPO_ROOT}` and state in the body that the orchestrator sets it.
      Verify: `grep "/home/nolte" .claude/agents/unit-test-runner.md` returns zero matches; bash blocks use repo-relative paths.

### WARNING

- [ ] [agent-review.duplicate-prevention] Material capability overlap with the `quality-gate` skill (lint + typecheck + tests in parallel, taskfile-aware); the agent and the skill cover the same functional cluster. Per `skill-vs-agent.duplicate-prevention` this is a MUST-NOT for `nolte-shared` plugin artifacts; for this project-distribution agent, it is at minimum a WARNING that requires negative triggers.
      Where: `.claude/agents/unit-test-runner.md:4` (description) vs. the `quality-gate` skill in `nolte-shared` (lint + typecheck + tests, also a quality gate).
      Fix: Add explicit negative triggers to `description` ("don't use for taskfile-aware lint+typecheck+test gating across the whole repo — use the `quality-gate` skill; this agent is for fast unit-test feedback during the implement→test loop in the project context"). Also note the boundary: this agent edits test files autonomously, the skill orchestrates and reports.
      Verify: `description` contains "don't use for" naming the `quality-gate` skill and stating the autonomous-edit boundary.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona, then style-guide pointer, then "Regeln", then steps; the role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is not honored — output shape only emerges in Step 6.
      Where: `.claude/agents/unit-test-runner.md:10-215`.
      Fix: Restructure: persona paragraph → "Output contract" → procedure (Steps 1-6) → guardrails (Regeln, Timeout-Verhalten, Abgrenzung). Style-guide pointer can stay at the top under the persona.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; tags `quality-gate` would apply per `agent-management.tag-vocabulary` SHOULD; the agent's own description ("Tests + Lint + statische Analyse") matches the starter vocabulary verbatim.
      Where: `.claude/agents/unit-test-runner.md:1-8` (frontmatter).
      Fix: Add `tags: [quality-gate]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.write-effects-documented] Agent declares `Edit` and `Bash`; the body legitimately edits test files (Step 3-4 fix-loop) and runs pytest/ruff/eslint via bash. The body documents *what* it edits (test files only, not production code) but the *preconditions* for those edits are scattered across "Regeln" 1-5; per `agent-management.acceptance` write-effect goals and preconditions SHOULD be consolidated.
      Where: `.claude/agents/unit-test-runner.md:5` (`tools: Read, Edit, Bash, Glob, Grep`) and lines 27-34 (Regeln) + Steps 3-4.
      Fix: Add an explicit "File outputs and edits" subsection near the top declaring (a) edits are confined to `src/backend/tests/**` and `src/frontend/src/test/**`, (b) preconditions (test failure analyzed first; minimal fix; never delete tests blindly), (c) the bash invocations (ruff, pytest, tsc, eslint, npm test) are the only execution side effects.
      Verify: A "File outputs and edits" section exists; it scopes edits to test directories, names preconditions, and lists allowed bash commands.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is *interactivity* (an author may want to approve test-file edits before they land), which would push toward a skill (precisely what `quality-gate` is).
      Where: `.claude/agents/unit-test-runner.md:1-215` (will be addressed once rationale section exists).
      Fix: Within the rationale section, add one bullet naming interactivity (test-edit approval) as the counter-dimension and the reason it was outweighed (e.g. PR review provides post-hoc gate; test edits are minimal and confined to test directories).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: haiku` and the comment line states a rationale ("Tests ausfuehren + Fehler nach klaren Patterns klassifizieren … haiku ausreichend fuer Mustererkennung"), satisfying `agent-management.model-selection` SHOULD; informational, no action required. The model choice plausibility check (haiku for a test-runner with pattern-classification only) passes per `agent-review.model-choice-checks`.
      Where: `.claude/agents/unit-test-runner.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; matches project-scoped reuse.
      Where: `.claude/agents/unit-test-runner.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/unit-test-runner.md:1-215`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-28 — agent-management.no-hard-coded-absolute-paths — replace 6 hard-coded /home/nolte/... paths with repo-relative paths and add cwd-assumption note — verified: re-read agent file, finding condition no longer holds
