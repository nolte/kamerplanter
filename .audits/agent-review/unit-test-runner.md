---
review-type: agent-review
target: ".claude/agents/unit-test-runner.md"
target-kind: agent
specs-applied:
  - slug: agent-management
    revision: "7772341"
  - slug: skill-vs-agent
    revision: "0e3b6f9"
  - slug: review-plan
    revision: "0e3b6f9"
  - slug: agent-review
    revision: "7772341"
repo-revision: "728ac421"
created: "2026-04-28"
status: open
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: unit-test-runner

## Scope

Iteration 2 of this plan. Two changes since iteration 1: (a) the `agent-management` and `agent-review` specs have been revised — a project-distribution agent in a project whose `CLAUDE.md` authorizes a non-English documentation language for agent prose may author its `description` and body in that language. Kamerplanter's `CLAUDE.md` lines 9-11 explicitly authorize German for `.claude/agents/`, so what was a German-prose BLOCKER in iteration 1 demotes to INFO here. (b) The Quick-Wins iteration replaced the hard-coded `/home/nolte/...` paths with repo-relative `cd src/backend` / `cd src/frontend` and added the explicit "cwd is the repo root" assumption (lines 16-18). The iteration-1 no-hard-coded-absolute-paths BLOCKER is therefore resolved.

Target: `.claude/agents/unit-test-runner.md` (frontmatter + body, ~217 lines, no sibling assets).
Specs applied: `agent-management` rev 7772341, `skill-vs-agent`, `review-plan`, `agent-review` rev 7772341 (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, factual correctness of the embedded bash commands, the `nolte-shared:quality-gate` skill itself (only the boundary against this agent is reviewed).

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three remaining MUST violations after the language and absolute-paths relaxations: missing rationale section, missing upfront output contract, and consolidated write-effect goals/preconditions for the `Edit`+`Bash` surface (test-only edits) that are scattered across "Regeln 1-5".
Next concrete action: author addresses the three remaining BLOCKERs (rationale section anchored in `skill-vs-agent`; explicit Output contract block; consolidated write-effects section listing test-only edit boundary) and adds the negative trigger naming the `quality-gate` skill.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`. Especially important given the `nolte-shared:quality-gate` skill exists in this functional cluster.
      Where: `.claude/agents/unit-test-runner.md:1-217` (no rationale section anywhere).
      Fix: Add a short rationale paragraph or 2-4 bullet list near the top naming decisive dimensions — most plausibly context-window protection (large pytest/vitest output kept out of the main thread), self-contained input/output (run tests, return a structured chat report), and parallelism (can run alongside other implementation agents). Cite at least one counter-dimension. Distinguish from the broader `quality-gate` skill (taskfile-aware, repo-wide) versus this agent (fast unit-test feedback during the implement→test loop).
      Verify: A "Rationale" section near the top names ≥1 decisive dimension; grep returns ≥1 hit for "context-window", "self-contained", or "parallelism".

- [ ] [agent-management.output-shape] Expected output shape is described only in Step 6 as a Markdown report skeleton; the file lacks an upfront "Output contract" stating what the parent caller receives.
      Where: `.claude/agents/unit-test-runner.md:161-193`.
      Fix: Add an "Output contract" section near the top stating (a) what the parent receives (a structured chat report — no files written beyond test edits, see write-effects finding below), (b) the report's required tables (statische Analyse, Unit-Tests, Durchgefuehrte Fixes, Offene Findings, Merge-Bereitschaft), (c) explicit go/no-go statement at the bottom (`MERGE-BEREIT` / `NICHT MERGE-BEREIT`).
      Verify: An "Output contract" section exists near the top; reading it tells a parent caller the deliverable shape.

- [ ] [agent-management.write-effects-documented] Agent declares `Edit` and `Bash`. The body legitimately edits test files (Step 3-4 fix-loop) and runs pytest/ruff/eslint via bash. The body documents *what* it edits (test files only, not production code) but the *preconditions* for those edits are scattered across "Regeln" 1-5; per `agent-management.acceptance` write-effect goals and preconditions SHOULD be consolidated.
      Where: `.claude/agents/unit-test-runner.md:5` (`tools: Read, Edit, Bash, Glob, Grep`) and lines 28-36 (Regeln) + Steps 3-4.
      Fix: Add a single "File outputs" / write-effects section consolidating: (a) only `tests/` paths under `src/backend/` and `src/test/` under `src/frontend/` may be edited; (b) production code under `app/` and `src/` (excluding tests) must never be edited (only reported as `[PROD-FIX]` findings); (c) `Bash` is used for pytest/ruff/eslint/tsc invocations only.
      Verify: Body contains a single consolidated write-effects section naming the test-only edit boundary; grep for "tests/" and "production code" both return hits in that section.

### WARNING

- [ ] [agent-review.duplicate-prevention] Material capability overlap with the `nolte-shared:quality-gate` skill (lint + typecheck + tests in parallel, taskfile-aware); the agent and the skill cover the same functional cluster. Per `skill-vs-agent.duplicate-prevention` this is a MUST-NOT for `nolte-shared` plugin artifacts; for this `distribution: project` agent it is a WARNING that requires negative triggers.
      Where: `.claude/agents/unit-test-runner.md:4` (description) vs. the `quality-gate` skill in `nolte-shared`.
      Fix: Add explicit negative triggers to `description` ("nicht für taskfile-aware Lint+Typecheck+Test über das ganze Repo — dafür `quality-gate` Skill; dieser Agent gibt schnelles Unit-Test-Feedback im Implement→Test-Loop und editiert Test-Dateien autonom"). Also note the boundary: this agent edits test files autonomously, the skill orchestrates and reports.
      Verify: `description` contains "nicht für" naming the `quality-gate` skill and stating the autonomous-edit boundary.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona, then style-guide pointer, then "Regeln", then steps; output shape only emerges in Step 6. Role-then-output-then-method ordering SHOULD is not honored.
      Where: `.claude/agents/unit-test-runner.md:10-217`.
      Fix: Restructure: persona paragraph → "Output contract" → procedure (Steps 1-6) → guardrails (Regeln, Timeout-Verhalten, Abgrenzung). Style-guide pointer can stay at the top under the persona.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; `quality-gate` would apply per `agent-management.tag-vocabulary` SHOULD; the agent's own description ("Tests + Lint + statische Analyse") matches the starter vocabulary verbatim.
      Where: `.claude/agents/unit-test-runner.md:1-8` (frontmatter).
      Fix: Add `tags: [quality-gate]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront that the agent writes (test) code; "Regel 1" says "no feature implementation" but the test-edit boundary needs an upfront one-line declaration per `agent-management.recommendations` SHOULD.
      Where: `.claude/agents/unit-test-runner.md:10-217`.
      Fix: Add one sentence near the top (after persona): "This agent runs tests and edits test files only; production code is never edited — only reported as `[PROD-FIX]` findings for the fullstack-developer agent."
      Verify: One sentence near the top names "edits test files only" and "no production-code edits".

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named; for this agent a plausible counter is the broad capability of the `quality-gate` skill (taskfile orchestration vs. fast feedback loop).
      Where: `.claude/agents/unit-test-runner.md:1-217` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming the `quality-gate` skill's broader scope as the counter-dimension and explain why an agent here is preferable for the implement→test loop (autonomous edits, scope-narrowed to unit tests).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.english-body] Description and body are German throughout; per the revised `agent-management.Structure` exception this is acceptable for `distribution: project` agents in a project whose `CLAUDE.md` authorizes German for agent prose. Kamerplanter's `CLAUDE.md` lines 9-11 declare German as the project documentation language. Recorded as INFO, not BLOCKER.
      Where: `.claude/agents/unit-test-runner.md:4` (description), lines 10-217 (body).
      Fix: n/a (observation — language exception applies).
      Verify: n/a.

- [ ] [agent-management.no-hard-coded-absolute-paths] The Quick-Wins iteration replaced the hard-coded `/home/nolte/...` paths with repo-relative paths (`cd src/backend`, `cd src/frontend`) and stated the cwd assumption explicitly (lines 16-18). The iteration-1 BLOCKER on this rule is resolved.
      Where: `.claude/agents/unit-test-runner.md:16-18, 42-43, 64-65, 86, 92, 147-148, 152`.
      Fix: n/a (observation — already fixed).
      Verify: `grep "/home/nolte" .claude/agents/unit-test-runner.md` returns zero matches.

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: haiku` with rationale ("Tests ausfuehren + Fehler nach klaren Patterns klassifizieren … haiku ausreichend fuer Mustererkennung"); satisfies `agent-management.model-selection` SHOULD. Per `agent-review.model-choice-checks` plausibility, haiku for a quality-gate agent that does pattern-based error classification is defensible.
      Where: `.claude/agents/unit-test-runner.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/unit-test-runner.md:1-217`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
