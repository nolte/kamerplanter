---
review-type: agent-review
target: ".claude/agents/e2e-testcase-extractor.md"
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
status: open
---

# Agent Review: e2e-testcase-extractor

## Scope

Target: `.claude/agents/e2e-testcase-extractor.md` (frontmatter + body, ~196 lines, no sibling assets — but body references `/home/nolte/repos/github/kamerplanter/.claude/agent-memory/e2e-testcase-extractor/MEMORY.md`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, the `test-extract` skill referenced as overlap target.

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — Body declares Write effects (test-case markdown files) without spec'd goals/preconditions in role section, no rationale section, hard-coded absolute path in body.
Next concrete action: author addresses the three BLOCKERs (add rationale section, document write goals/preconditions explicitly, replace absolute path with relative).

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] No rationale section in the body naming a decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent`.
      Where: `.claude/agents/e2e-testcase-extractor.md:1-196`.
      Fix: Add a rationale block citing decisive dimensions — most plausibly *context-window protection* (reads every spec/req + spec/nfr), *specialization* (IREB/ISTQB QA-architect persona sharpens output), and *parallelism* (one extractor per requirement document can run in parallel). Note this directly intersects with the `test-extract` skill, which is the orchestrator wrapping this executor (canonical skill-orchestrates-agent pattern).
      Verify: A "## Rationale" or equivalent section exists naming ≥1 decisive dimension.

- [ ] [agent-management.no-absolute-paths] Body contains a hard-coded user-absolute path `/home/nolte/repos/github/kamerplanter/.claude/agent-memory/e2e-testcase-extractor/`; `agent-management.acceptance` MUST forbids hard-coded absolute paths.
      Where: `.claude/agents/e2e-testcase-extractor.md:166`.
      Fix: Replace with a relative reference like `.claude/agent-memory/e2e-testcase-extractor/` or `${PROJECT_ROOT}/.claude/agent-memory/<name>/`. The body's "Persistent Agent Memory" boilerplate would benefit from a project-root-relative form so the agent stays portable to any consuming project.
      Verify: `grep "/home/" .claude/agents/e2e-testcase-extractor.md` returns zero matches; the memory path is project-relative.

- [ ] [agent-management.writes-vs-research] Body uses Write but does not document the goals and preconditions of the file write per `agent-management.acceptance` MUST ("If the agent writes files or performs side effects, the targets and preconditions are documented in the system prompt"). It writes `spec/test-cases/TC-{REQ-ID}.md` and updates memory files, but no upfront write contract.
      Where: `.claude/agents/e2e-testcase-extractor.md:111-116` (output convention) and `:154-192` (memory).
      Fix: Add a "Side effects" or "Write contract" section near the top stating: (a) creates/overwrites `spec/test-cases/TC-<REQ-ID>.md` (one file per requirement), (b) creates/updates memory under `.claude/agent-memory/e2e-testcase-extractor/`, (c) preconditions: target directories exist, source spec is committed.
      Verify: An explicit write-contract section exists naming both target paths and preconditions.

### WARNING

- [ ] [agent-management.tags] No `tags` field declared; `tags: [scaffolding, review]` or `tags: [scaffolding]` would fit per `agent-management.tag-vocabulary` (the agent generates artifacts from specs — scaffolding nature). Default would be no tag at all over a poorly chosen one, but a single applicable tag aids cluster lookup.
      Where: `.claude/agents/e2e-testcase-extractor.md:1-9`.
      Fix: Add `tags: [scaffolding]` after the `memory: project` line.
      Verify: Frontmatter parses with `tags` matching the rules.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with the `nolte-shared:test-extract` skill (mentioned in the user's instructions for this review): the skill orchestrates extraction, this agent does the heavy reading; that is the canonical skill-orchestrates-agent pattern from `skill-vs-agent`. The overlap is not a duplicate but the relationship MUST be documented in the rationale section so a calling Claude routes via the skill, not the agent.
      Where: `.claude/agents/e2e-testcase-extractor.md:4` (description does not name `test-extract`).
      Fix: In the rationale section being added per the skill-vs-agent BLOCKER, name `test-extract` as the dispatching skill and clarify negative trigger: "don't dispatch directly when the user asks for a multi-REQ test-extraction workflow — use the `test-extract` skill, which dispatches this agent per REQ."
      Verify: `description` or rationale section names `test-extract` as the orchestrator.

- [ ] [agent-management.prompt-structure-order] Body opens with role, then Context, then Mission, then Methodology Phase 1-4, then Output File Convention, then Domain Patterns, then QA Checklist, then Language Rules, then Memory boilerplate. Output convention is at line 111 — past the methodology, instead of upfront per `agent-management.recommendations` SHOULD.
      Where: `.claude/agents/e2e-testcase-extractor.md:11-196`.
      Fix: Restructure: (1) Role + boundaries, (2) Output contract (file naming + per-test-case structure currently at lines 62-110), (3) Working method (Methodology Phase 1-4 + Domain Patterns + QA Checklist).
      Verify: First three top-level sections, in order, are role / output / method.

- [ ] [agent-management.length] Body is ~196 lines — at the ~200-line soft target, with the Persistent Agent Memory boilerplate (~50 lines) being prime factor-able material. Per `agent-management.recommendations` SHOULD, supporting reference material moves to `agents/<name>/` files.
      Where: `.claude/agents/e2e-testcase-extractor.md:154-196`.
      Fix: Move the Persistent-Agent-Memory boilerplate to a sibling `memory-instructions.md` referenced from the body; keep only a short pointer in the main body.
      Verify: Body shrinks below 150 lines after factoring; sibling exists.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` plausible for structured extraction with templates; the comment names the choice but is brief. Strengthening with one phrase about template-driven extraction being sonnet's sweet spot would help future reviewers.
      Where: `.claude/agents/e2e-testcase-extractor.md:7`.
      Fix: Append to the comment: "template-driven structured extraction over multi-spec sweep; haiku underfits the IREB/ISTQB reasoning, opus over-budgets."
      Verify: Comment names task character.

### INFO

- [ ] [agent-management.memory-field] `memory: project` is declared; this is a non-standard frontmatter field not listed in `agent-management.structure` MUSTs. Worth noting that the field is undocumented in the spec but the agent uses it correctly per project convention.
      Where: `.claude/agents/e2e-testcase-extractor.md:8`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.description-style] `description` uses the embedded-examples style (long YAML string with literal `\n` user/assistant/commentary blocks). This is verbose but unusually rich on triggers; a calling Claude has plenty to match against. No spec rule violated.
      Where: `.claude/agents/e2e-testcase-extractor.md:4`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [review-plan.observation] No sibling folder `agents/e2e-testcase-extractor/` exists; will be needed if the length WARNING leads to factoring memory boilerplate out.
      Where: `.claude/agents/e2e-testcase-extractor.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
