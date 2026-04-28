---
review-type: agent-review
target: ".claude/agents/agrobiology-requirements-reviewer.md"
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

# Agent Review: agrobiology-requirements-reviewer

## Scope

Target: `.claude/agents/agrobiology-requirements-reviewer.md` (frontmatter + body, ~550 lines, no sibling assets under `agents/agrobiology-requirements-reviewer/`).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent`, `review-plan`, `agent-review` (rev 7772341); revisions in frontmatter.
Iteration: 2 (re-review). Iteration 1 ran against `agent-management` rev `0e3b6f9` and recorded the German body as a BLOCKER. The `7772341` revision of `agent-management.Structure` introduces a project-language exception for `distribution: project` agents whose consuming project authorizes non-English agent prose. Kamerplanter's root `CLAUDE.md` (lines 9-11) explicitly authorizes German for `description` and the system-prompt body of project-distributed agents while keeping frontmatter field names and technical identifier values English; the prior body-language BLOCKER is therefore downgraded to an INFO observation in this iteration.
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, the dispatching skill (none declared), domain factual correctness of plant biology claims inside the prompt.

## Summary

- BLOCKER: 3
- WARNING: 6
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three MUST violations remain (read-only agent declares `Write`, no rationale section, output shape stated only as a markdown report path without a structured contract).
Next concrete action: author addresses the three BLOCKERs (drop `Write` from tools or convert to a skill-orchestrates-agent split; add rationale section anchored in `skill-vs-agent`; declare the structured output contract that the dispatching parent consumes).

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write-tools] Read-only review agent (description verbs: "Prüft", "bewertet kritisch") declares `Write` in `tools`, which `agent-review` MUST forbid for read-only agents.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write` from `tools`; the report is a structured deliverable returned to the parent skill, not a write side effect — if persistent files at `spec/analysis/agrobiology-review.md` are intended, refactor into a skill-orchestrates-agent pattern per `skill-vs-agent` so the writing skill calls this read-only agent.
      Verify: `tools` lists only `Read, Glob, Grep`; `grep -E "^tools:" .claude/agents/agrobiology-requirements-reviewer.md` shows no write tool.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:1-549` (no "Why this is an agent" / rationale paragraph anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top (or as a footer before the procedure) naming decisive dimensions — most plausibly *specialization* (agrobiology persona sharpens output quality), *context-window protection* (large-volume reads of all `spec/req`, `spec/nfr`, schemas), and *tool restriction* (read-only research). Cite at least one counter-dimension if applicable.
      Verify: Section reading "## Rationale" or equivalent exists; grep for "specialization", "context-window", or "tool restriction" inside the body returns at least one hit.

- [ ] [agent-management.output-shape] System prompt names a report path (`spec/analysis/agrobiology-review.md`) and a markdown template, but does not name an *expected output shape* the parent consumes; agent dispatch is fire-and-forget per `skill-vs-agent`, so the structured report contract MUST be stated.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:401-535` (Phase 3 + Phase 4 chat summary).
      Fix: Add an explicit "Output contract" section near the top stating: (a) what the agent returns to the caller (path + summary), (b) the report's structural sections, (c) whether the agent writes files (currently implied by the Phase 3 markdown template at `spec/analysis/…`). If the agent does write a file, document the file location, overwrite policy, and preconditions per `agent-management.acceptance` ("targets and preconditions of side effects").
      Verify: A section "Output contract" or equivalent exists; reading just that section tells the caller the deliverable shape.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Write` is declared but only used implicitly by the Phase 3 markdown template instruction ("Erstelle `spec/analysis/agrobiology-review.md`"); even if BLOCKER is resolved by removing `Write`, the residual instruction would silently demand a write tool the body never explicitly lists with goals/preconditions.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:401`.
      Fix: After removing `Write`, replace the imperative "Erstelle … " with "Return the following report shape to the caller; the orchestrating skill is responsible for persistence." Alternatively, if writes stay, declare goals/preconditions of the write per `agent-management.recommendations` SHOULD.
      Verify: Phase 3 instruction either no longer uses imperative "Erstelle" + path, or the body documents file-write goals and preconditions explicitly.

- [ ] [agent-management.tags] No `tags` field declared; tag vocabulary `review` and `audience` would apply per `agent-management.tag-vocabulary` SHOULD and would let `skill-agent-catalog` cluster this with other persona reviewers.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, audience]` (or `[review]` alone) after the `name`/`description`/`distribution` block.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with peer persona reviewers (`cannabis-indoor-grower-reviewer`, `casual-houseplant-user-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer`, `frontend-design-reviewer`, `target-audience-analyzer`): all describe themselves as "Prüft Anforderungsdokumente aus der Perspektive …". The personas differ but the dispatch shape is identical, so a calling Claude could plausibly mis-route.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:4` (description) vs. peer agents.
      Fix: Add explicit negative triggers to `description` ("nicht für Cannabis-Indoor-Grow → `cannabis-indoor-grower-reviewer`; nicht für Casual-Houseplant-Casual-User → `casual-houseplant-user-reviewer`; nicht für Outdoor-Beet-Planung → `outdoor-garden-planner-reviewer`; nicht für Frontend-Design-Review → `frontend-design-reviewer`."). Negative triggers are a SHOULD when overlap is plausible.
      Verify: `description` contains "nicht für" / "don't use for" or equivalent negation naming at least the four closest peers.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona statement, then the "Faktenintegrität" rule, then the procedure; the role/output/method ordering required by `agent-management.recommendations` SHOULD is fragmented (output shape only emerges in Phase 3, no upfront output statement).
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:10-409`.
      Fix: Restructure body opening to: (1) Role + boundaries, (2) Output shape (structured report contract per BLOCKER above), (3) Working method (Phases 0-4); move the "Faktenintegrität" rule under method or into a sibling reference file under `agents/agrobiology-requirements-reviewer/fact-integrity.md` if the body grows.
      Verify: First three top-level sections of the body, in order, are role / output / method.

- [ ] [agent-management.length] Body is ~550 lines, well past the ~200-line soft target; the long fact-integrity manifesto, schema list, and report template are prime candidates for factoring into `agents/agrobiology-requirements-reviewer/` siblings.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:1-549`.
      Fix: Move (a) the "Drei-Quellen-Regel" + Offene-Recherchepunkte template, (b) the schema list, (c) the Phase 3 markdown report template into sibling files (`fact-integrity.md`, `schema-inventory.md`, `report-template.md`) under `agents/agrobiology-requirements-reviewer/`; reference them via relative paths from the body.
      Verify: Body ≤250 lines after factoring; sibling folder exists with relative-path references in the body.

- [ ] [agent-management.writes-vs-research] Body does not explicitly declare whether the agent writes files or only researches — Phase 3's "Erstelle `spec/analysis/agrobiology-review.md`" implies a write but the prompt never names the side effect or its preconditions per `agent-management.recommendations` SHOULD.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:401`.
      Fix: Add an explicit one-line declaration near the top — "This agent is read-only; the orchestrating skill persists the report at `spec/analysis/agrobiology-review.md`." (preferred path), or document goals/preconditions of the write if `Write` stays in tools.
      Verify: Body contains an explicit "writes files: yes/no" sentence in role/output section.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` with documented rationale — fits a structured spec-review task; consider that long context (reading every `spec/req` + `spec/nfr` + 12 schema files) may justify pinning to `sonnet` over `haiku` more strongly than the comment currently states.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:7`.
      Fix: Strengthen the existing rationale comment with one phrase about context-window load ("multi-file spec + schema sweep, sonnet's reasoning quality earns its cost over haiku").
      Verify: Comment names both reasoning depth and context volume.

### INFO

- [ ] [agent-management.project-language-exception] Body and `description` are authored in German. Under `agent-management` rev 7772341 this is permitted: the agent declares `distribution: project` and Kamerplanter's `CLAUDE.md` (lines 9-11) explicitly authorizes German for project-distributed agent prose. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`) are correctly English. Iteration 1 had recorded this as a BLOCKER under the prior spec revision; downgrade is the central delta of this re-review.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:4` (description) + `:10-549` (body).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [review-plan.observation] No sibling folder `agents/agrobiology-requirements-reviewer/` exists at `.claude/agents/`; if the length-factoring WARNING is acted on, the folder needs to be created at the source-tree path the agent's distribution implies.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is correctly set to one of the two enum values; this is consistent with the absence of plugin packaging for kamerplanter agents and is the precondition that activates the project-language exception above.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] The `# Modellwahl:` comment above `model: sonnet` satisfies the SHOULD that pinned models be justified; the rationale is short but present, so model-plausibility stays at SUGGESTION level only.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
