---
review-type: agent-review
target: ".claude/agents/agrobiology-requirements-reviewer.md"
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

# Agent Review: agrobiology-requirements-reviewer

## Scope

Target: `.claude/agents/agrobiology-requirements-reviewer.md` (frontmatter + body, ~550 lines, no sibling assets under `agents/agrobiology-requirements-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, the dispatching skill (none declared), domain factual correctness of plant biology claims inside the prompt.

## Summary

- BLOCKER: 4
- WARNING: 6
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations (Read-only agent declares `Write`, body is German, no rationale section, output shape stated only as a Markdown report path without contract).
Next concrete action: author addresses the four BLOCKERs (drop `Write` from tools, translate body to English, add rationale section anchored in `skill-vs-agent`, declare the structured output contract that the dispatching parent consumes).

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write-tools] Read-only review agent (description verbs: "Prüft", "bewertet kritisch") declares `Write` in `tools`, which `agent-review` MUST forbid for read-only agents.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write` from `tools`; the report is a structured deliverable returned to the parent skill, not a write-side-effect — if persistent files at `spec/analysis/agrobiology-review.md` are intended, refactor into a skill-orchestrates-agent pattern per `skill-vs-agent` so the writing skill calls this read-only agent.
      Verify: `tools` lists only `Read, Glob, Grep`; `grep -E "^tools:" .claude/agents/agrobiology-requirements-reviewer.md` shows no write tool.

- [ ] [agent-management.english-body] Frontmatter and system-prompt content MUST be in English; the body is overwhelmingly German (every section heading, every bullet) violating `agent-management` Structure-MUST.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:10-549` (entire body).
      Fix: Translate the whole body, including section headings ("Phase 0: …", "Phase 1: …"), to English; keep German only where literally quoting spec terms or plant-care vocabulary that has no concise English equivalent. Note that the project CLAUDE.md German-default convention does not override the `agent-management` MUST — agents are tooling artifacts, not user-facing prose.
      Verify: A `lang detect` pass on the body returns >95% English; section headings read `## Phase 0:` etc. in English.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:1-549` (no "Why this is an agent" / rationale paragraph anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top (or as a footer before the procedure) naming decisive dimensions — most plausibly *specialization* (agrobiology persona sharpens output quality), *context-window protection* (large-volume reads of all `spec/req`, `spec/nfr`, schemas), and *tool restriction* (read-only research). Cite at least one counter-dimension if applicable.
      Verify: Section reading "## Rationale" or equivalent exists, names ≥1 decisive dimension; grep for "specialization", "context-window", or "tool restriction" inside the body returns ≥1 hit.

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

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with peer persona reviewers (`cannabis-indoor-grower-reviewer`, `casual-houseplant-user-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer`): all five describe themselves as "Prüft Anforderungsdokumente aus der Perspektive …". The personas differ but the dispatch shape is identical, so a calling Claude could plausibly mis-route.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:4` (description) vs. peer agents.
      Fix: Add explicit negative triggers to `description` ("don't use for indoor cannabis-grower review — use `cannabis-indoor-grower-reviewer`; don't use for casual-houseplant casual-user perspective — use `casual-houseplant-user-reviewer`; don't use for outdoor garden planning — use `outdoor-garden-planner-reviewer`."). Negative triggers are a SHOULD when overlap is plausible.
      Verify: `description` contains "don't use for" or equivalent negation naming at least the three closest peers.

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

- [ ] [review-plan.observation] No sibling folder `agents/agrobiology-requirements-reviewer/` exists at `.claude/agents/`; if the length-factoring WARNING is acted on, the folder would need to be created at the source-tree path the agent's distribution implies.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [review-plan.observation] `memory: project` field is not declared, but the body's instruction set is large; if the agent ever needs persistent learning, `e2e-testcase-extractor`'s `memory: project + /home/.../.claude/agent-memory/<name>/` pattern is the precedent.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:1-8`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is correctly set to one of the two enum values; this is consistent with the absence of plugin packaging for kamerplanter agents.
      Where: `.claude/agents/agrobiology-requirements-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
