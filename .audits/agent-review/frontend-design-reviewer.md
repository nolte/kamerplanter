---
review-type: agent-review
target: ".claude/agents/frontend-design-reviewer.md"
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

# Agent Review: frontend-design-reviewer

## Scope

Target: `.claude/agents/frontend-design-reviewer.md` (frontmatter + body, ~454 lines, no sibling assets).
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

- [ ] [agent-review.read-only-no-write-tools] Read-only review agent (description verbs: "Prüft", "geprüft werden sollen") declares `Write` in `tools`; `agent-review` MUST forbids write tools on read-only agents.
      Where: `.claude/agents/frontend-design-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write`. The Phase 3 instruction "Erstelle `spec/analysis/frontend-design-review.md`" must be reframed to return-report semantics; if persistence is required, use the skill-orchestrates-agent pattern.
      Verify: `tools` lists only `Read, Glob, Grep`.

- [ ] [agent-management.english-body] Body MUST be in English; the entire body is German — persona, all phase headings, all tables, the Phase 3 report template.
      Where: `.claude/agents/frontend-design-reviewer.md:10-453`.
      Fix: Translate the body to English. UI/MUI domain terms (Touch-Target, Skeleton-Screen, Container Query, FAB) MAY stay where they are the canonical English term anyway, but all section headings ("Phase 2: Design-Bewertung") and prose must be English.
      Verify: A `lang detect` pass returns >95% English.

- [ ] [skill-vs-agent.rationale-section] No rationale section in the body naming a decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent`.
      Where: `.claude/agents/frontend-design-reviewer.md:1-453`.
      Fix: Add a rationale block citing decisive dimensions — most plausibly *specialization* (15-year frontend-designer persona sharpens output), *context-window protection* (large multi-spec sweep over `spec/req`, `spec/nfr`, `spec/ui-nfr`, `spec/stack.md`, plus the frontend codebase scan), and *tool restriction* (read-only review).
      Verify: A "## Rationale" or equivalent section exists with ≥1 decisive dimension.

- [ ] [agent-management.output-shape] System prompt names a markdown report path and a long template only in Phase 3; no upfront output contract per `agent-management.structure` MUST.
      Where: `.claude/agents/frontend-design-reviewer.md:247-437`.
      Fix: Add an "Output contract" section near the top stating (a) what is returned to the caller, (b) the report's structural sections (Gesamtbewertung, Kritisch/Unvollständig/Optimierung/Positiv, Kiosk-Detailbewertung, Responsive-Matrix, Touch-Target-Audit), (c) write semantics — currently the Phase 3 imperative implies a write that is not declared with goals/preconditions.
      Verify: Reading just the upfront section tells the caller the deliverable shape.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Write` is declared but only used implicitly via the Phase 3 imperative "Erstelle `spec/analysis/frontend-design-review.md`"; either drop it (BLOCKER) or document write goals/preconditions explicitly.
      Where: `.claude/agents/frontend-design-reviewer.md:5` and `:247`.
      Fix: After removing `Write`, drop the "Erstelle …" imperative in favor of return-report semantics.
      Verify: No "Erstelle …" imperative remains, or write effects are explicitly declared.

- [ ] [agent-management.tags] No `tags` field declared; `tags: [review]` would fit per `agent-management.tag-vocabulary` SHOULD; alternatively `tags: [review, audience]` to slot it into the persona-reviewer cluster.
      Where: `.claude/agents/frontend-design-reviewer.md:1-8`.
      Fix: Add `tags: [review]`.
      Verify: Frontmatter parses with `tags` matching the rules.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with `frontend-usability-optimizer` (post-implementation usability) and partly with `casual-houseplant-user-reviewer` (UX/Onboarding from a casual user's perspective). The boundary — `frontend-design-reviewer` reviews *design specs* (responsive, kiosk, accessibility), `frontend-usability-optimizer` reviews *implementation* — is not stated in the description.
      Where: `.claude/agents/frontend-design-reviewer.md:4`.
      Fix: Add negative triggers: "don't use for post-implementation React/MUI usability review (use `frontend-usability-optimizer`); don't use for casual end-user perspective on the spec (use `casual-houseplant-user-reviewer`)."
      Verify: `description` contains negative triggers naming both peers.

- [ ] [agent-management.prompt-structure-order] Body opens with role, then Phase 1 (read docs), Phase 2 (design assessment), Phase 3 (report), Phase 4 (chat summary); output sits in Phase 3 instead of upfront. `agent-management.recommendations` SHOULD: role → output → method.
      Where: `.claude/agents/frontend-design-reviewer.md:10-453`.
      Fix: Restructure: (1) Role + boundaries, (2) Output contract, (3) Working method (Phases 1-2). Phase 3 becomes the rendering template referenced from the contract.
      Verify: First three top-level sections, in order, are role / output / method.

- [ ] [agent-management.length] Body is ~454 lines, well past the ~200-line soft target; the Phase 3 report template, the Kiosk ASCII wireframe, the Responsive-Matrix, the Touch-Target-Audit, and the Glossar are all factor-able into siblings under `agents/frontend-design-reviewer/`.
      Where: `.claude/agents/frontend-design-reviewer.md:1-453`.
      Fix: Move (a) Phase 3 markdown template to `report-template.md`, (b) the kiosk wireframe + matrix to `kiosk-reference.md`, (c) the Glossar to `glossary.md`. Reference each via relative path.
      Verify: Body ≤200 lines after factoring; sibling folder exists.

- [ ] [agent-management.writes-vs-research] Body does not explicitly declare writes-vs-research; Phase 3 implies a write but the contract is implicit.
      Where: `.claude/agents/frontend-design-reviewer.md:247`.
      Fix: Add a one-line declaration in the role section: "This agent is read-only; the orchestrating skill persists the report at `spec/analysis/frontend-design-review.md`."
      Verify: An explicit writes-vs-research statement is present.

### SUGGESTION

- [ ] [agent-management.model-plausibility] `model: sonnet` plausible for design-heuristic reasoning with structured findings; the comment names the choice but is brief. Strengthening with a phrase about multi-context (Mobile/Tablet/Desktop/Kiosk) reasoning being sonnet's sweet spot would help future reviewers.
      Where: `.claude/agents/frontend-design-reviewer.md:7`.
      Fix: Append one phrase to the comment: "multi-context responsive + kiosk reasoning over multi-spec sweep; haiku underfits, opus over-budgets unless wireframes are screenshot-analyzed."
      Verify: Comment names task character.

### INFO

- [ ] [review-plan.observation] No sibling folder `agents/frontend-design-reviewer/` exists; will be needed for the length-factoring WARNING.
      Where: `.claude/agents/frontend-design-reviewer.md` (no sibling).
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-review.observation] Body Phase 1.2 instructs the agent to scan `src/frontend/src/components/**/*.tsx` etc. — large-volume reads that strongly justify the agent-over-skill choice via context-window protection, reinforcing the rationale section being added per the skill-vs-agent BLOCKER.
      Where: `.claude/agents/frontend-design-reviewer.md:42-48`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
