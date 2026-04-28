---
review-type: agent-review
target: ".claude/agents/e2e-testcase-extractor.md"
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

# Agent Review: e2e-testcase-extractor

## Scope

Target: `.claude/agents/e2e-testcase-extractor.md` (frontmatter + body, ~197 lines, persistent agent-memory dir at `.claude/agent-memory/e2e-testcase-extractor/`).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent`, `review-plan`, `agent-review` (rev 7772341); revisions in frontmatter.
Iteration: 2 (re-review). Iteration 1 ran against `agent-management` rev `0e3b6f9`; this re-review applies the lockerede language clause from rev `7772341`. The body of this agent is already authored in English, so the project-language exception is not load-bearing here — but the cluster-wide INFO note about the new clause is still recorded for consistency. The Iteration 1 BLOCKER on body language never applied to this agent, so the BLOCKER count delta is zero — but cross-agent harmonization in Iteration 2 still surfaces structural findings the iteration 1 plan flagged.
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, the dispatching skill (`test-extract` is a peer skill flagged below for duplicate prevention), correctness of any specific TC-* output the agent has previously produced.

## Summary

- BLOCKER: 3
- WARNING: 5
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three MUST violations remain (no rationale section, hard-coded absolute path in body, undeclared frontmatter field `memory`). Note also a likely capability duplicate vs. the `test-extract` skill: ship one or the other, not both.
Next concrete action: author addresses the three BLOCKERs (add rationale section anchored in `skill-vs-agent`; replace absolute path `/home/nolte/repos/github/kamerplanter/.claude/agent-memory/...` with a path relative to the project root or document the resolution rule; remove the undocumented `memory: project` frontmatter field or move the memory wiring into a sibling asset).

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`. Especially load-bearing here because the `test-extract` skill exists in parallel — a documented rationale must explain why this is an agent and not (or in addition to) a skill.
      Where: `.claude/agents/e2e-testcase-extractor.md:1-197`.
      Fix: Add a 2-4-bullet rationale near the top — most plausibly *context-window protection* (large multi-REQ extractions), *specialization* (IREB/ISTQB persona sharpens output), *parallelism* (one agent per REQ batch). Cite at least one counter-dimension and explicitly relate to the `test-extract` skill (orchestrator/executor split or replacement).
      Verify: Section "## Rationale" or equivalent exists; grep returns at least one of "specialization", "context-window", "parallelism"; the relationship to `test-extract` is named.

- [ ] [agent-management.no-absolute-paths] Body hard-codes the absolute path `/home/nolte/repos/github/kamerplanter/.claude/agent-memory/e2e-testcase-extractor/`, which `agent-management.acceptance` ("No hard-coded absolute paths; all internal references are relative to the agent file or the project it operates on") MUST forbid.
      Where: `.claude/agents/e2e-testcase-extractor.md:166`.
      Fix: Replace the absolute path with a project-relative reference (`.claude/agent-memory/e2e-testcase-extractor/`) or describe the resolution as "the project root's `.claude/agent-memory/<agent-name>/` directory".
      Verify: `grep -F "/home/" .claude/agents/e2e-testcase-extractor.md` returns no hits.

- [ ] [agent-management.frontmatter-fields] Frontmatter declares `memory: project` (line 8), which is not a documented `agent-management.Structure` field. The spec lists the permitted frontmatter fields (`name`, `description`, `distribution`, `tools`, `model`, `tags`); arbitrary additional fields are not specified and have no defined semantics under the spec.
      Where: `.claude/agents/e2e-testcase-extractor.md:8` (`memory: project`).
      Fix: Either remove the field and capture the persistent-memory contract in body prose under a sibling asset reference, or formally extend `agent-management.Structure` upstream and reference the new field (the latter is out-of-scope for this review). Until the spec extension exists, the field is undocumented frontmatter.
      Verify: Frontmatter contains only fields documented in `agent-management.Structure`, OR an upstream spec change has added `memory` and is referenced.

### WARNING

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with the `test-extract` skill (per the peer skills list — "E2E aus REQ"). The agent's description and the skill's intent both center on extracting E2E test cases from REQ specs; one of the two should orchestrate while the other executes (per the skill-orchestrates-agent pattern in `skill-vs-agent`), rather than both shipping the same capability.
      Where: `.claude/agents/e2e-testcase-extractor.md:4` (description) vs. peer skill `test-extract`.
      Fix: Document the relationship in this agent's rationale section (see BLOCKER above). Either (a) the skill `test-extract` invokes this agent as its executor, or (b) the agent supersedes the skill — propose the deletion/merger in the authoring PR. Until then, the cluster has duplicate-capability risk.
      Verify: Body's rationale section names `test-extract` and the chosen split; OR the skill is removed/superseded.

- [ ] [agent-management.tags] No `tags` field declared; tag vocabulary `quality-gate` (E2E test generation supports the test pipeline) and `scaffolding` (generates structured TC-* documents) would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/e2e-testcase-extractor.md:1-9` (frontmatter).
      Fix: Add `tags: [quality-gate, scaffolding]` after the `name`/`description`/`distribution` block.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.description-format] The `description` field is a multi-line, escape-encoded string with embedded `<commentary>` tags and example dialogues, totaling several hundred characters. While this carries useful triggers, it makes the YAML hard to skim and bloats every dispatcher's context. The MUST is that triggers be concrete; the form factor here is a SHOULD-flagged readability concern.
      Where: `.claude/agents/e2e-testcase-extractor.md:4` (description).
      Fix: Move the example dialogues into a sibling asset (`agents/e2e-testcase-extractor/example-invocations.md`) and shorten the `description` to one or two sentences naming concrete triggers — that's enough for routing and keeps frontmatter scannable.
      Verify: `description` value fits on a few lines; example invocations live in a sibling file.

- [ ] [agent-management.writes-vs-research] Body declares `tools: Read, Write, Glob, Grep` (line 5) and writes test-case files to `spec/test-cases/TC-{REQ-ID}.md`. Per `agent-management.recommendations` SHOULD ("when the agent writes files or causes side effects, the system prompt documents the goals and preconditions of those effects"), the body should declare overwrite policy explicitly.
      Where: `.claude/agents/e2e-testcase-extractor.md:113` ("Write test case documents to the path pattern: `spec/test-cases/TC-{REQ-ID}.md`").
      Fix: Add an explicit "Side effects" subsection: target paths, overwrite policy (overwrite vs. append vs. error-on-exists), preconditions (must read source REQ first), idempotency note.
      Verify: Body contains a "Side effects" section naming target path + overwrite policy.

- [ ] [agent-management.prompt-structure-order] Body opens with role, then Context, then Mission, then Methodology, then Output File Convention, then Domain Patterns, then QA checklist, then Language Rules, then Memory wiring. The output-shape paragraph is reachable but not structurally separated from the methodology, fragmenting the role/output/method ordering recommended by `agent-management.recommendations` SHOULD.
      Where: `.claude/agents/e2e-testcase-extractor.md:11-150`.
      Fix: Split into clearly labeled "Role", "Output", "Method" headings; pull "Output File Convention" + the test-case template up to immediately after Role.
      Verify: First three top-level sections, in order, are role / output / method.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` with documented rationale fits structured spec extraction. Consider naming the parallelism dimension explicitly — multiple REQ extractions can run in parallel agent dispatches, which is the textbook agent-bias use case from `skill-vs-agent`.
      Where: `.claude/agents/e2e-testcase-extractor.md:6-7`.
      Fix: Strengthen the rationale comment with one phrase about parallelism: "sonnet adäquat für massen-Extraktion, parallel pro REQ dispatchbar".
      Verify: Comment names parallelism in addition to reasoning depth.

### INFO

- [ ] [agent-management.project-language-exception] Body and `description` are authored in English (default per `agent-management.Structure`); the new project-language exception introduced in rev 7772341 is therefore not load-bearing here. This INFO is recorded for cluster consistency: under the new spec revision, German would also have been permitted, but English remains the safer default and keeps the option open of moving this agent into a plugin distribution later.
      Where: `.claude/agents/e2e-testcase-extractor.md:4` (description) + `:11-197` (body).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is correctly set; this is consistent with kamerplanter's project-only agent setup.
      Where: `.claude/agents/e2e-testcase-extractor.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [review-plan.observation] The persistent agent-memory directory at `.claude/agent-memory/e2e-testcase-extractor/` exists outside the canonical agent sibling location (`agents/<name>/`); this is a pattern that should either be promoted to a portfolio convention or factored back into a sibling. Iteration 1 already noted the precedent.
      Where: `.claude/agents/e2e-testcase-extractor.md:163-166`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.length] Body is ~197 lines, right at the ~200-line soft target — within acceptable range. Flagged for awareness only.
      Where: `.claude/agents/e2e-testcase-extractor.md:1-197`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
