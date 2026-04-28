---
review-type: agent-review
target: ".claude/agents/target-audience-analyzer.md"
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

# Agent Review: target-audience-analyzer

## Scope

Iteration 2 of this plan. The `agent-management` and `agent-review` specs have been revised: a project-distribution agent in a project whose root convention file (`CLAUDE.md`) authorizes a non-English documentation language for agent prose may author its `description` and body in that language. Kamerplanter's `CLAUDE.md` lines 9-11 explicitly authorize German for `.claude/agents/`, so what was a German-prose BLOCKER in iteration 1 demotes to INFO here.

Target: `.claude/agents/target-audience-analyzer.md` (frontmatter + body, ~305 lines, no sibling assets).
Specs applied: `agent-management` rev 7772341, `skill-vs-agent`, `review-plan`, `agent-review` rev 7772341 (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, factual correctness of the persona-derivation methodology, the dispatching skill (none declared but the `audience-identify` skill in `nolte-shared` covers a closely-related capability).

## Summary

- BLOCKER: 3
- WARNING: 5
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three remaining MUST violations after the language relaxation: missing rationale section, missing upfront output contract, and consolidated write-effect goals/preconditions for the `Write`-tool side effect (single report path). The duplicate-prevention overlap with the `nolte-shared:audience-identify` skill and the persona-reviewer cluster also needs an explicit negative trigger.
Next concrete action: author addresses the three remaining BLOCKERs (rationale section anchored in `skill-vs-agent`; explicit Output contract block; consolidated write-effects section naming the report path) and clarifies the boundary against the `audience-identify` skill plus the persona-reviewer agents.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/target-audience-analyzer.md:1-305` (no "Why this is an agent" section).
      Fix: Add a short rationale paragraph or 2-4 bullet list near the top naming decisive dimensions — most plausibly context-window protection (large-volume reads of all `spec/req/`, `spec/nfr/`, `spec/stack.md`, `CLAUDE.md`), specialization (15-year UX-research persona narrows the synthesis), and self-contained input/output (single deliverable report).
      Verify: A "Rationale" section near the top names ≥1 decisive dimension; grep returns ≥1 hit for "context-window", "specialization", or "self-contained".

- [ ] [agent-management.output-shape] Expected output shape is described in Phase 4 as a Markdown report skeleton, but the file lacks an upfront "Output contract" stating what the parent caller receives.
      Where: `.claude/agents/target-audience-analyzer.md:169-289`.
      Fix: Add an "Output contract" section near the top stating (a) the written path `spec/analysis/target-audience-report.md`, (b) the report's required sections (Executive Summary, primary/secondary groups, underserved groups, application areas, persona gap matrix, recommendations, ranking), (c) the Phase-5 chat summary shape, (d) the overwrite policy.
      Verify: An "Output contract" section exists near the top; reading it tells a parent caller the deliverable path and shape.

- [ ] [agent-management.write-effects-documented] Agent declares `Write` but the system prompt does not declare the write-effect goals and preconditions per `agent-management` acceptance — the only signal is the report-creation step in Phase 4.
      Where: `.claude/agents/target-audience-analyzer.md:5` (`tools: Read, Write, Glob, Grep`) vs. body lacking an upfront write-goals block.
      Fix: Add a short "File outputs" section consolidating: target path `spec/analysis/target-audience-report.md`, preconditions (full Phase 1+2+3 traversal complete; `spec/analysis/` directory created if missing), and the explicit invariant that no specs and no production code are modified.
      Verify: Body contains a single consolidated write-effects section naming the target path and preconditions.

### WARNING

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap on multiple peers: (a) the `nolte-shared:audience-identify` skill (audience-list creation per spec/project/audience-identification/), (b) the persona-reviewer cluster (`casual-houseplant-user-reviewer`, `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer`) which already produces persona-specific perspectives on the same spec corpus. Per `agent-review.duplicate-prevention` this is a WARNING; the `description` does not declare negative triggers naming any peer.
      Where: `.claude/agents/target-audience-analyzer.md:4` vs. peers in `.claude/agents/*-reviewer.md` and the `audience-identify` skill.
      Fix: Add explicit negative triggers to `description`: "nicht für autoritative Audience-Listen-Erstellung — dafür `audience-identify` Skill; nicht für Persona-spezifische Reviews — dafür Persona-Reviewer-Agents (casual-houseplant-user-reviewer, cannabis-indoor-grower-reviewer, outdoor-garden-planner-reviewer); dieser Agent leistet quer-laufende Marktanalyse + Persona-Gap-Analyse aus den Specs".
      Verify: `description` contains "nicht für" naming at least the `audience-identify` skill and one persona-reviewer agent.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona + Hintergrund, then phases; output shape only emerges in Phase 4. Role-then-output-then-method ordering SHOULD is not honored.
      Where: `.claude/agents/target-audience-analyzer.md:10-289`.
      Fix: Restructure: persona → "Output contract" → procedure (Phasen 1-5).
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; `audience` and `review` would apply per `agent-management.tag-vocabulary` SHOULD; `audience` is a starter-vocabulary term that explicitly clusters audience-related artifacts.
      Where: `.claude/agents/target-audience-analyzer.md:1-8` (frontmatter).
      Fix: Add `tags: [audience, review]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront that the agent writes a report file; per `agent-management.recommendations` SHOULD this distinction must be visible at dispatch time.
      Where: `.claude/agents/target-audience-analyzer.md:10-305`.
      Fix: Add one sentence near the top: "This agent reads all REQ/NFR docs and writes a single audience-analysis report under `spec/analysis/`; it does not modify specs or production code."
      Verify: One sentence near the top names "writes report", "spec/analysis/", and "no spec or production-code edits".

- [ ] [agent-management.body-length] Body is ~305 lines, slightly above the SHOULD soft target of ~200. The Phase-2.2 dimension catalogue (lines 70-112) and the Phase-4 report skeleton (lines 169-289) could move into a sibling asset.
      Where: `.claude/agents/target-audience-analyzer.md:1-305`.
      Fix: Optionally factor the dimension catalogue and the report skeleton into `.claude/agents/target-audience-analyzer/` files referenced by relative path.
      Verify: Body length drops below ~250 lines or the SHOULD is consciously waived in the Scope.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named; for this agent a plausible counter is interactivity (a stakeholder might want to confirm the persona universe before the report is written).
      Where: `.claude/agents/target-audience-analyzer.md:1-305` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming interactivity as the counter-dimension and explain why it was outweighed (e.g. fire-and-forget analysis, single revertable artifact).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.english-body] Description and body are German throughout; per the revised `agent-management.Structure` exception this is acceptable for `distribution: project` agents in a project whose `CLAUDE.md` authorizes German for agent prose. Kamerplanter's `CLAUDE.md` lines 9-11 declare German as the project documentation language. Recorded as INFO, not BLOCKER.
      Where: `.claude/agents/target-audience-analyzer.md:4` (description), lines 10-305 (body).
      Fix: n/a (observation — language exception applies).
      Verify: n/a.

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` with rationale ("Marktanalyse + Persona-Ableitung aus Specs; sonnet adaequat fuer strukturierte Synthese"); satisfies `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/target-audience-analyzer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; no plugin-co-located asset references appear.
      Where: `.claude/agents/target-audience-analyzer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/target-audience-analyzer.md:1-305`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
