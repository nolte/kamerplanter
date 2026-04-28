---
review-type: agent-review
target: ".claude/agents/frontend-design-reviewer.md"
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

# Agent Review: frontend-design-reviewer

## Scope

Target: `.claude/agents/frontend-design-reviewer.md` (frontmatter + body, ~455 lines, no sibling assets).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent`, `review-plan`, `agent-review` (rev 7772341); revisions in frontmatter.
Iteration: 2 (re-review). Iteration 1 ran against `agent-management` rev `0e3b6f9` and recorded the German body as a BLOCKER. The `7772341` revision introduces a project-language exception for `distribution: project` agents whose project authorizes non-English prose; Kamerplanter's `CLAUDE.md` (lines 9-11) explicitly authorizes German for project-distributed agents. The body-language BLOCKER is therefore downgraded to INFO in this iteration.
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, the dispatching skill (none declared), correctness of any specific UX heuristic claim in the prompt.

## Summary

- BLOCKER: 3
- WARNING: 6
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — three MUST violations remain (read-only agent declares `Write`, no rationale section, output shape stated only as report-path imperative without a structured contract).
Next concrete action: author addresses the three BLOCKERs (drop `Write` or restructure into skill→agent pair; add rationale section per `skill-vs-agent`; declare structured output contract).

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write-tools] Read-only persona-review agent (description verb: "Prüft Anforderungsdokumente aus der Perspektive …") declares `Write` in `tools`, which `agent-review` MUST forbid.
      Where: `.claude/agents/frontend-design-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write` from `tools`; if persistence at `spec/analysis/frontend-design-review.md` is intended, the orchestrating skill performs the write while this agent stays read-only — a textbook skill-orchestrates-agent split per `skill-vs-agent`.
      Verify: `tools` lists only `Read, Glob, Grep`; `grep -E "^tools:" .claude/agents/frontend-design-reviewer.md` shows no write tool.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/frontend-design-reviewer.md:1-455`.
      Fix: Add a 2-4-bullet rationale near the top — likely *specialization* (frontend-designer persona sharpens UX/Kiosk findings), *context-window protection* (sweeps every REQ + NFR + UI-NFR + frontend codebase glance), *tool restriction* (read-only). Cite at least one counter-dimension.
      Verify: Section "## Rationale" or equivalent exists; grep returns at least one of "specialization", "context-window", "tool restriction".

- [ ] [agent-management.output-shape] System prompt names a report path (`spec/analysis/frontend-design-review.md`) and a markdown template, but the structured output shape the parent consumes is not stated upfront; agent dispatch is fire-and-forget per `skill-vs-agent`.
      Where: `.claude/agents/frontend-design-reviewer.md:245-438` (Phase 3 + Phase 4).
      Fix: Add an "Output contract" section at the top stating (a) what the agent returns to the caller (report path + summary), (b) the report's structural sections, (c) whether the agent writes the file or only returns the markdown body. If writes stay, document file location, overwrite policy, preconditions per `agent-management.acceptance`.
      Verify: A section "Output contract" or equivalent exists; reading just that section tells the caller the deliverable shape.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Write` is declared but only used implicitly by Phase 3's "Erstelle `spec/analysis/frontend-design-review.md`"; even after BLOCKER removal, the residual imperative would silently demand a write tool not declared with goals/preconditions.
      Where: `.claude/agents/frontend-design-reviewer.md:247`.
      Fix: After removing `Write`, replace "Erstelle …" with "Return the following report shape to the caller; the orchestrating skill is responsible for persistence."
      Verify: Phase 3 instruction either no longer uses imperative "Erstelle" + path, or the body documents file-write goals/preconditions explicitly.

- [ ] [agent-management.tags] No `tags` field declared; tag vocabulary `review` and `audience` would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/frontend-design-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, audience]` after the `name`/`description`/`distribution` block.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with peer persona reviewers (`agrobiology-requirements-reviewer`, `cannabis-indoor-grower-reviewer`, `casual-houseplant-user-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer`, `target-audience-analyzer`) and with `frontend-usability-optimizer` (which optimizes React/MUI code rather than reviewing design specs — but the dispatch line could collide). Solve via explicit negative triggers — the cluster-wide pattern recommended by `agent-management.recommendations`.
      Where: `.claude/agents/frontend-design-reviewer.md:4` vs. peer agents.
      Fix: Append negative triggers to `description` ("nicht für React/MUI-Code-Optimierung → `frontend-usability-optimizer`; nicht für allgemeine Pflanzen-Specs → `agrobiology-requirements-reviewer`; nicht für Casual-User-Empathie → `casual-houseplant-user-reviewer`; nicht für Smart-Home-HA-Sicht → `smart-home-ha-reviewer`.").
      Verify: `description` contains "nicht für" / "don't use for" or equivalent negation naming at least the four closest peers.

- [ ] [agent-management.prompt-structure-order] Body opens with persona profile + skills list, then jumps into Phase 1 / Phase 2 procedure; output shape only emerges in Phase 3. The role/output/method ordering required by `agent-management.recommendations` SHOULD is fragmented.
      Where: `.claude/agents/frontend-design-reviewer.md:10-247`.
      Fix: Move output shape (Phase 3 contract) immediately after the role block, before the procedure phases.
      Verify: First three top-level sections, in order, are role / output / method.

- [ ] [agent-management.length] Body is ~455 lines, well past the ~200-line soft target. The phase-2 sub-checklists, the Kiosk-specific touch-target tables, the responsive matrix, and the Phase 3 markdown template are factor-out candidates for `agents/frontend-design-reviewer/` siblings.
      Where: `.claude/agents/frontend-design-reviewer.md:1-455`.
      Fix: Move (a) the responsive/kiosk checklists, (b) the touch-target audit tables, (c) the Phase 3 report template into sibling files (`responsive-checklist.md`, `kiosk-checklist.md`, `report-template.md`) under `agents/frontend-design-reviewer/`; reference via relative paths.
      Verify: Body ≤250 lines after factoring; sibling folder exists with relative-path references.

- [ ] [agent-management.writes-vs-research] Body does not explicitly declare whether the agent writes files or only researches; Phase 3's imperative implies a write but the prompt never names the side effect or its preconditions per the SHOULD in `agent-management.recommendations`.
      Where: `.claude/agents/frontend-design-reviewer.md:247`.
      Fix: Add a one-line declaration near the top: "This agent is read-only; the orchestrating skill persists the report at `spec/analysis/frontend-design-review.md`."
      Verify: Body contains an explicit "writes files: yes/no" sentence in role/output section.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` with documented rationale fits a structured design review without heavy reasoning load. Strengthen the rationale to mention the multi-file spec sweep + frontend-codebase glance, which justifies sonnet over haiku more concretely than "adäquat für strukturierte Findings".
      Where: `.claude/agents/frontend-design-reviewer.md:6-7`.
      Fix: Strengthen the rationale comment with one phrase about context-window load (REQ + NFR + UI-NFR + `src/frontend/`).
      Verify: Comment names both reasoning depth and context volume.

### INFO

- [ ] [agent-management.project-language-exception] Body and `description` are authored in German. Under `agent-management` rev 7772341 this is permitted: the agent declares `distribution: project` and Kamerplanter's `CLAUDE.md` (lines 9-11) explicitly authorizes German for project-distributed agent prose. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`) are correctly English. Iteration 1 had recorded this as a BLOCKER under the prior spec revision; downgrade is the central delta of this re-review.
      Where: `.claude/agents/frontend-design-reviewer.md:4` (description) + `:10-454` (body).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is correctly set; this is consistent with kamerplanter's project-only agent setup and is the precondition activating the project-language exception above.
      Where: `.claude/agents/frontend-design-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [review-plan.observation] No sibling folder `agents/frontend-design-reviewer/` exists; if length-factoring WARNING is acted on, the folder needs to be created.
      Where: `.claude/agents/frontend-design-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
