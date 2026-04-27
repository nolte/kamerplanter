---
review-type: agent-review
target: ".claude/agents/casual-houseplant-user-reviewer.md"
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

# Agent Review: casual-houseplant-user-reviewer

## Scope

Target: `.claude/agents/casual-houseplant-user-reviewer.md` (frontmatter + body, ~352 lines, no sibling assets under `agents/casual-houseplant-user-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, the dispatching skill (none declared).

## Summary

- BLOCKER: 4
- WARNING: 6
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — Read-only review agent declares `Write`, body is German, no rationale section, no upfront output contract.
Next concrete action: author addresses the four BLOCKERs (drop `Write`, English-translate body, add rationale section, declare structured output shape).

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write-tools] Read-only review agent (description verbs: "Prüft", "bewertet aus der Perspektive eines lustlosen … Nutzers") declares `Write` in `tools`; `agent-review` MUST forbid write tools on read-only agents.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write`. The Phase 3 instruction "Erstelle `spec/analysis/casual-houseplant-user-review.md`" must be reframed as "return the report shape to the orchestrating skill"; if persistent files are required, refactor into a skill-orchestrates-agent pattern.
      Verify: `tools` lists only `Read, Glob, Grep`.

- [ ] [agent-management.english-body] Body MUST be in English; the persona description, all phase headings, the entire fact tables, and the report template are German.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:10-351`.
      Fix: Translate the body to English. The Fachbegriff-table German-to-easier-German translations are a domain artifact and may stay as data, but section headings, prose, and the report template must be English.
      Verify: A `lang detect` pass on the body returns >95% English.

- [ ] [skill-vs-agent.rationale-section] No rationale section in the body naming a decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent`.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:1-351`.
      Fix: Add a rationale block citing decisive dimensions — most plausibly *specialization* (casual-user persona is a narrow system prompt that sharpens output), *context-window protection* (large multi-spec sweep), and *tool restriction* (read-only research). Optionally cite the four sibling persona reviewers as precedent.
      Verify: A "## Rationale" or equivalent section exists with ≥1 decisive dimension.

- [ ] [agent-management.output-shape] System prompt names a markdown report path and template only in Phase 3, with no upfront output contract; `agent-management.structure` MUST states the expected output shape must be named in the system prompt.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:174-334`.
      Fix: Add an "Output contract" section at the top declaring (a) what is returned to the caller, (b) report sections, (c) write semantics. Currently the Phase 3 imperative implies a file write the prompt never declares with goals/preconditions.
      Verify: An upfront output-contract section exists.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Write` is declared but only used implicitly via the Phase 3 imperative; either drop it (BLOCKER) or document write goals/preconditions explicitly.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:5` and `:176`.
      Fix: After removing `Write`, drop the "Erstelle …" imperative in favor of a return-report contract.
      Verify: No "Erstelle …" imperative remains, or write effects are explicitly declared.

- [ ] [agent-management.tags] No `tags` field is declared; `tags: [review, audience]` would slot it into the persona-reviewer cluster.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:1-8`.
      Fix: Add `tags: [review, audience]`.
      Verify: Frontmatter parses with `tags` matching the lowercase-kebab/length rules.

- [ ] [agent-review.duplicate-prevention] Heavy structural overlap with peer persona reviewers (`agrobiology-requirements-reviewer`, `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer`) — same dispatch shape "Prüft Anforderungsdokumente aus der Perspektive …", different persona; a calling Claude could mis-route. The personas differ but the structural similarity is worth flagging per `agent-review.duplicate-prevention`.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:4`.
      Fix: Add negative triggers to the description — "don't use for grower/expert perspective (use `cannabis-indoor-grower-reviewer`); don't use for botanical-correctness review (use `agrobiology-requirements-reviewer`); don't use for garden/outdoor (use `outdoor-garden-planner-reviewer`)."
      Verify: `description` contains explicit negative triggers naming the closest peers.

- [ ] [agent-management.prompt-structure-order] Body opens with persona, then Phase 1 (read docs), then Phase 2 (alltagsbewertung), then Phase 3 (report), then Phase 4 (chat summary); output shape sits in Phase 3 instead of upfront. `agent-management.recommendations` SHOULD: role → output → method.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:10-351`.
      Fix: Restructure: (1) Role + boundaries (persona), (2) Output contract, (3) Working method (Phases 1-2). Phase 3 becomes the rendering template referenced from the contract.
      Verify: First three sections, in order, are role / output / method.

- [ ] [agent-management.length] Body is ~352 lines, past the ~200-line soft target; the Phase 3 markdown template, the Fachbegriff-table, and the Konkurrenz-comparison block are factor-able into siblings under `agents/casual-houseplant-user-reviewer/`.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:1-351`.
      Fix: Move report template to `report-template.md`, the Fachbegriff-table to `terminology-mapping.md`, the competition-comparison to `competition-matrix.md`. Reference via relative paths.
      Verify: Body ≤200 lines after factoring; sibling folder exists.

- [ ] [agent-management.writes-vs-research] Body does not explicitly state writes-vs-research; Phase 3 implies a write but never declares it as a side effect.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:176`.
      Fix: Add a one-line declaration: "This agent is read-only; the orchestrating skill persists the report at `spec/analysis/casual-houseplant-user-review.md`."
      Verify: An explicit writes-vs-research statement is present.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` plausible for empathetic persona reasoning; comment names the choice but is brief. Consider strengthening with one phrase about empathy + lay-language reasoning being sonnet's sweet spot.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:7`.
      Fix: Append one phrase to the comment: "empathetic lay-user reasoning over multi-spec sweep; haiku underfits, opus over-budgets."
      Verify: Comment names both task character and cost.

### INFO

- [ ] [review-plan.observation] No sibling folder `agents/casual-houseplant-user-reviewer/` exists; needed if length-factoring WARNING is acted on.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-review.observation] The body's "Future: KI/Bilderkennung" reference (N-001 photo-recognition gap) is captured in MEMORY.md; the agent's findings are already feeding into project memory, which is good but worth a follow-up loop in the orchestrating skill so the persistence path is auditable.
      Where: `.claude/agents/casual-houseplant-user-reviewer.md:64` and project MEMORY.md.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
