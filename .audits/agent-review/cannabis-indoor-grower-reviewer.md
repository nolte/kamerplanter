---
review-type: agent-review
target: ".claude/agents/cannabis-indoor-grower-reviewer.md"
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

# Agent Review: cannabis-indoor-grower-reviewer

## Scope

Target: `.claude/agents/cannabis-indoor-grower-reviewer.md` (frontmatter + body, ~485 lines, no sibling assets under `agents/cannabis-indoor-grower-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, the dispatching skill (none declared), domain factual accuracy of cannabis grow practices in the prompt.

## Summary

- BLOCKER: 4
- WARNING: 6
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — Read-only review agent with `Write`, body in German, no rationale section, no upfront output contract.
Next concrete action: author addresses the four BLOCKERs (drop `Write`, translate body to English, add rationale section, declare structured output shape).

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write-tools] Read-only review agent (description verbs: "Prüft", "bewertet als täglicher Anwender") declares `Write` in `tools`; `agent-review` MUST forbid write/edit/execution tools on read-only agents.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write`. The Phase 3 instruction "Erstelle `spec/analysis/cannabis-indoor-grower-review.md`" must be reframed as "return the report shape to the orchestrating skill"; if persistence is required, refactor into the skill-orchestrates-agent pattern from `skill-vs-agent`.
      Verify: `tools` lists only `Read, Glob, Grep`.

- [ ] [agent-management.english-body] Body MUST be in English; this body is overwhelmingly German (persona description, all phase headings, all checklists, the report template).
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:10-484`.
      Fix: Translate the entire body to English; cannabis-grower jargon (Stretch, Lollipopping, Cola, Trichome, Burping) MAY stay as-is when it is the canonical English term anyway, but section headings ("Phase 1: Dokumente einlesen") and review prose must be English.
      Verify: A `lang detect` pass on the body returns >95% English.

- [ ] [skill-vs-agent.rationale-section] No rationale section in the body naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:1-484` (no rationale paragraph anywhere).
      Fix: Add a rationale near the top citing decisive dimensions — most plausibly *specialization* (grower-persona system prompt sharpens output), *context-window protection* (large multi-doc sweep across `spec/req`, `spec/nfr`, `spec/ui-nfr`), and *tool restriction* (read-only persona review). Optionally reference `agrobiology-requirements-reviewer` and `casual-houseplant-user-reviewer` as precedents.
      Verify: Section reading "## Rationale" or equivalent exists with ≥1 decisive dimension named.

- [ ] [agent-management.output-shape] System prompt names a markdown report path (`spec/analysis/cannabis-indoor-grower-review.md`) and a long template, but the *output contract returned to the parent* is not declared upfront; per `agent-management.structure` MUST, the expected output shape must be stated.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:319-470` (Phase 3 + Phase 4).
      Fix: Add an "Output contract" section at the top stating (a) what the agent returns to the caller (path reference + summary table), (b) the report's structural sections, (c) write semantics — currently the Phase 3 imperative implies a file write the prompt never explicitly declares with goals/preconditions.
      Verify: Reading just the new section tells the caller the deliverable shape without scrolling 300+ lines.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Write` is declared but only used implicitly via "Erstelle `spec/analysis/cannabis-indoor-grower-review.md`"; either remove it (BLOCKER above) or the agent's body MUST document the write goal/preconditions per `agent-management.acceptance`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:5` and `:321`.
      Fix: After resolving the BLOCKER, ensure the residual Phase 3 instruction matches the new tool list (return-report semantics, no Write tool needed).
      Verify: No "Erstelle …" imperative remains, or write effects are explicitly declared.

- [ ] [agent-management.tags] No `tags` field is declared; `tags: [review, audience]` would slot the agent into the persona-reviewer cluster per `agent-management.tag-vocabulary` SHOULD and let `skill-agent-catalog` group it with the four other persona reviewers.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:1-8`.
      Fix: Add `tags: [review, audience]`.
      Verify: Frontmatter parses with `tags` ≤5 entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with peer persona reviewers (`agrobiology-requirements-reviewer`, `casual-houseplant-user-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer`) — the dispatch shape "Prüft Anforderungsdokumente aus der Perspektive …" is identical, and a calling Claude looking at user requests like "review the specs from a grower view" could mis-route to `agrobiology-requirements-reviewer`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:4`.
      Fix: Add negative triggers to `description` — "don't use for academic agrobiology review (use `agrobiology-requirements-reviewer`); don't use for casual zimmerpflanzen perspective (use `casual-houseplant-user-reviewer`); don't use for outdoor garden planning (use `outdoor-garden-planner-reviewer`)."
      Verify: `description` contains explicit negative triggers naming at least the three closest peers.

- [ ] [agent-management.prompt-structure-order] System prompt orders persona/profile → Phase 1 (read docs) → Phase 2 (assessment) → Phase 3 (report) → Phase 4 (chat summary); the role/output/method ordering recommended by `agent-management` SHOULD has output shape buried in Phase 3.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:10-484`.
      Fix: Restructure: (1) Role + boundaries (persona), (2) Output contract (currently in Phase 3+4), (3) Working method (Phases 1-2). Phase 3 becomes the rendering template referenced from the contract.
      Verify: First three sections of the body, in order, are role / output / method.

- [ ] [agent-management.length] Body is ~485 lines, past the ~200-line soft target; the report template, the workflow-coverage matrix, the glossar, and the IPM-Kalender are factor-able into siblings under `agents/cannabis-indoor-grower-reviewer/`.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:1-484`.
      Fix: Move (a) Phase 3 markdown template to `report-template.md`, (b) the Glossar to `glossary.md`, (c) the workflow coverage matrix and ertrags-relevanz-matrix to `matrices.md`. Reference each via relative path from the body.
      Verify: Body ≤250 lines after factoring; sibling folder exists with relative-path references.

- [ ] [agent-management.writes-vs-research] Body does not explicitly state whether the agent writes files or only researches; Phase 3 implies a write but the contract is implicit.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:321`.
      Fix: Add a one-line declaration in the role section — "This agent is read-only; the orchestrating skill persists the report at `spec/analysis/cannabis-indoor-grower-review.md`."
      Verify: Body contains an explicit writes-vs-research statement.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` is plausible for a persona-review with structured findings; the comment names the choice but is brief — strengthening it with one phrase about the multi-doc sweep would help future reviewers.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:7`.
      Fix: Append one phrase to the comment: "structured findings across all REQ/NFR/UI-NFR + workflow matrix; haiku underfits, opus over-budgets."
      Verify: Comment names both task complexity and cost.

### INFO

- [ ] [review-plan.observation] No sibling folder `agents/cannabis-indoor-grower-reviewer/` exists; needed if the length-factoring WARNING is acted on.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-review.legal-context] CanG-compliance section in the body references German legal limits (3 plants, 50g possession); these are factual claims valid as of April 2024 — they are not a spec-rule violation but worth flagging as time-sensitive content that a future reviewer should re-verify if the cannabis law changes.
      Where: `.claude/agents/cannabis-indoor-grower-reviewer.md:281-292`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
