---
review-type: agent-review
target: ".claude/agents/cannabis-indoor-grower-reviewer.md"
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
status: in-progress
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: cannabis-indoor-grower-reviewer

## Scope

Target: `.claude/agents/cannabis-indoor-grower-reviewer.md` (frontmatter + body, ~485 lines, no sibling assets).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent`, `review-plan`, `agent-review` (rev 7772341); revisions in frontmatter.
Iteration: 2 (re-review). Iteration 1 ran against `agent-management` rev `0e3b6f9` and recorded the German body as a BLOCKER. The `7772341` revision introduces a project-language exception for `distribution: project` agents whose project authorizes non-English prose; Kamerplanter's `CLAUDE.md` (lines 9-11) explicitly authorizes German for project-distributed agents. The body-language BLOCKER is therefore downgraded to INFO in this iteration.
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, the dispatching skill (none declared), factual correctness of cannabis-grow domain claims inside the prompt.

## Summary

- BLOCKER: 3
- WARNING: 6
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — three MUST violations remain (read-only agent declares `Write`, no rationale section, output shape stated only as report-path imperative without a structured contract).
Next concrete action: author addresses the three BLOCKERs (drop `Write` or restructure into skill→agent pair; add rationale section per `skill-vs-agent`; declare structured output contract for the parent).

## Findings

### BLOCKER

- [x] [agent-review.read-only-no-write-tools] Read-only persona-review agent (description verb: "Prüft Anforderungsdokumente aus der Perspektive …") declares `Write` in `tools`, which `agent-review` MUST forbid.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write` from `tools`; if persistence at `spec/analysis/cannabis-indoor-grower-review.md` is intended, the orchestrating skill performs the write while this agent stays read-only — a textbook skill-orchestrates-agent split per `skill-vs-agent`.
      Verify: `tools` lists only `Read, Glob, Grep`; `grep -E "^tools:" .claude/agents/cannabis-indoor-grower-reviewer.md` shows no write tool.

- [x] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:1-485`.
      Fix: Add a 2-4-bullet rationale near the top — likely *specialization* (cannabis-grower persona sharpens output), *context-window protection* (sweeps every REQ + NFR + UI-NFR), *tool restriction* (read-only). Cite at least one counter-dimension.
      Verify: Section "## Rationale" or equivalent exists; grep returns at least one of "specialization", "context-window", "tool restriction".

- [x] [agent-management.output-shape] System prompt names a report path (`spec/analysis/cannabis-indoor-grower-review.md`) and a markdown template, but the structured output shape the parent consumes is not stated upfront; agent dispatch is fire-and-forget per `skill-vs-agent`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:319-467` (Phase 3 + Phase 4 chat summary).
      Fix: Add an "Output contract" section at the top stating (a) what the agent returns to the caller (report path + summary), (b) the report's structural sections, (c) whether the agent writes the file or only returns the markdown body. If writes stay, document file location, overwrite policy, and preconditions per `agent-management.acceptance`.
      Verify: A section "Output contract" or equivalent exists; reading just that section tells the caller the deliverable shape.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Write` is declared but only used implicitly by Phase 3's "Erstelle `spec/analysis/cannabis-indoor-grower-review.md`"; even after BLOCKER removal, the residual imperative would silently demand a write tool not declared with goals/preconditions.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:321`.
      Fix: After removing `Write`, replace "Erstelle …" with "Return the following report shape to the caller; the orchestrating skill is responsible for persistence."
      Verify: Phase 3 instruction either no longer uses imperative "Erstelle" + path, or the body documents file-write goals/preconditions explicitly.

- [ ] [agent-management.tags] No `tags` field declared; tag vocabulary `review` and `audience` would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, audience]` after the `name`/`description`/`distribution` block.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with peer persona reviewers (`agrobiology-requirements-reviewer`, `casual-houseplant-user-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer`, `frontend-design-reviewer`, `target-audience-analyzer`); all open with "Prüft Anforderungsdokumente aus der Perspektive …". Solve via explicit negative triggers — the cluster-wide pattern recommended by `agent-management.recommendations`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:4` vs. peer agents.
      Fix: Append negative triggers to `description` ("nicht für allgemeine Pflanzen-Specs → `agrobiology-requirements-reviewer`; nicht für Casual-Houseplant-Sicht → `casual-houseplant-user-reviewer`; nicht für Outdoor-Beet → `outdoor-garden-planner-reviewer`; nicht für Frontend-UX → `frontend-design-reviewer`.").
      Verify: `description` contains "nicht für" / "don't use for" or equivalent negation naming at least the four closest peers.

- [ ] [agent-management.prompt-structure-order] Body opens with persona profile, then a thinking-pattern block, then the procedure; output shape only emerges in Phase 3. The role/output/method ordering required by `agent-management.recommendations` SHOULD is fragmented.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:10-319`.
      Fix: Move output shape (Phase 3 contract) immediately after the role block, before the procedure phases.
      Verify: First three top-level sections, in order, are role / output / method.

- [ ] [agent-management.length] Body is ~485 lines, well past the ~200-line soft target. The per-phase checklists, workflow matrices, and Phase 3 markdown template are prime candidates for `agents/cannabis-indoor-grower-reviewer/` siblings.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:1-485`.
      Fix: Move (a) the per-phase checklists, (b) the workflow/coverage matrices, (c) the Phase 3 report template into sibling files (`workflow-checklists.md`, `report-template.md`) under `agents/cannabis-indoor-grower-reviewer/`; reference via relative paths.
      Verify: Body ≤250 lines after factoring; sibling folder exists with relative-path references.

- [ ] [agent-management.writes-vs-research] Body does not explicitly declare whether the agent writes files or only researches; Phase 3's imperative implies a write but the prompt never names the side effect or its preconditions per the SHOULD in `agent-management.recommendations`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:321`.
      Fix: Add a one-line declaration near the top: "This agent is read-only; the orchestrating skill persists the report at `spec/analysis/cannabis-indoor-grower-review.md`."
      Verify: Body contains an explicit "writes files: yes/no" sentence in role/output section.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` with documented rationale fits a structured persona review without heavy reasoning load. Consider strengthening the rationale to mention the multi-file spec sweep (REQ + NFR + UI-NFR), which justifies sonnet over haiku more concretely than "adäquat für strukturierte Findings".
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:6-7`.
      Fix: Strengthen the rationale comment with one phrase about context-window load.
      Verify: Comment names both reasoning depth and context volume.

### INFO

- [ ] [agent-management.project-language-exception] Body and `description` are authored in German. Under `agent-management` rev 7772341 this is permitted: the agent declares `distribution: project` and Kamerplanter's `CLAUDE.md` (lines 9-11) explicitly authorizes German for project-distributed agent prose. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`) are correctly English. Iteration 1 had recorded this as a BLOCKER under the prior spec revision; downgrade is the central delta of this re-review.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:4` (description) + `:10-484` (body).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is correctly set; this is consistent with kamerplanter's project-only agent setup and is the precondition activating the project-language exception above.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [review-plan.observation] No sibling folder `agents/cannabis-indoor-grower-reviewer/` exists; if length-factoring WARNING is acted on, the folder needs to be created.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->

2026-04-28 — agent-review.read-only-no-write-tools — removed `Write` from `tools`, prefixed `description` with "Verfasst einen strukturierten Praxis-Bewertungsbericht (`spec/analysis/cannabis-indoor-grower-review.md`) zu Anforderungsdokumenten" — verified: re-read frontmatter line 5
2026-04-28 — skill-vs-agent.rationale-section — added "## Rationale: Skill vs Agent" section after opening paragraph naming Specialization, Context-window protection, Parallelism with Interactivity counter — verified: grep matches in body
2026-04-28 — agent-management.output-shape — added "## Output Contract" section directly after Rationale stating report path, required sections, and FAIL/PASS go/no-go statement — verified: re-read body
