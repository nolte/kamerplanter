---
review-type: agent-review
target: ".claude/agents/smart-home-ha-reviewer.md"
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

# Agent Review: smart-home-ha-reviewer

## Scope

Iteration 2 of this plan. Two changes since iteration 1: (a) the `agent-management` and `agent-review` specs have been revised — a project-distribution agent in a project whose `CLAUDE.md` authorizes a non-English documentation language for agent prose may author its `description` and body in that language. Kamerplanter's `CLAUDE.md` lines 9-11 explicitly authorize German for `.claude/agents/`, so what was a German-prose BLOCKER in iteration 1 demotes to INFO here. (b) The Quick-Wins iteration rewrote the `description` from "Reviewt …" to "Verfasst einen strukturierten Smart-Home-HA-Integrationsbericht" — `Write` is now legitimately scoped to writing the report file, so the iteration-1 read-only-no-write BLOCKER is resolved.

Target: `.claude/agents/smart-home-ha-reviewer.md` (frontmatter + body, ~432 lines, no sibling assets).
Specs applied: `agent-management` rev 7772341, `skill-vs-agent`, `review-plan`, `agent-review` rev 7772341 (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, factual correctness of the HA terminology, the dispatching skill (none declared).

## Summary

- BLOCKER: 3
- WARNING: 5
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three remaining MUST violations after the language relaxation: missing rationale section, missing upfront output contract, and consolidated write-effect goals/preconditions for the report file (`Write` is legitimate but the goal/precondition declaration required by `agent-management` acceptance is still missing).
Next concrete action: author addresses the three remaining BLOCKERs (rationale section anchored in `skill-vs-agent`; explicit Output contract block; consolidated write-effects section naming the single report path) and clarifies the boundary against `ha-integration-requirements-engineer`.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-432` (no "Why this is an agent" section).
      Fix: Add a short rationale paragraph or 2-4 bullet list near the top naming decisive dimensions — most plausibly specialization (HA-Power-User persona narrowing the review surface), context-window protection (large-volume reads of all `spec/req/`, `spec/nfr/`, `spec/ui-nfr/`, `spec/stack.md`), and self-contained input/output (single deliverable report).
      Verify: A "Rationale" section near the top names ≥1 decisive dimension; grep returns ≥1 hit for "specialization", "context-window", or "self-contained".

- [ ] [agent-management.output-shape] Expected output shape is described in Phase 3 as a Markdown report skeleton, but the file lacks an upfront "Output contract" stating what the parent caller receives.
      Where: `.claude/agents/smart-home-ha-reviewer.md:234-416`.
      Fix: Add an "Output contract" section near the top stating (a) the written path `spec/analysis/smart-home-ha-integration-review.md`, (b) the report's required tables (Integrations-Architektur, Integrationslandkarte sides A/B/C, Optionalitätscheckliste, Top-5-Maßnahmen, Feature-Relevanz), (c) the Phase-4 chat summary shape, (d) the overwrite policy.
      Verify: An "Output contract" section exists near the top; reading it tells a parent caller the deliverable path and shape.

- [ ] [agent-management.write-effects-documented] Agent declares `Write` (the description-rewrite legitimately scoped this) but the system prompt does not declare the write-effect goals and preconditions per `agent-management` acceptance — the only signal is the report-creation step in Phase 3.
      Where: `.claude/agents/smart-home-ha-reviewer.md:5` (`tools: Read, Write, Glob, Grep`) vs. body lacking an upfront write-goals block.
      Fix: Add a short "File outputs" section consolidating: target path `spec/analysis/smart-home-ha-integration-review.md`, preconditions (full Phase 1+2 traversal complete; `spec/analysis/` directory created if missing), and the explicit invariant that no specs and no production code are modified.
      Verify: Body contains a single consolidated write-effects section naming the target path and preconditions.

### WARNING

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with `ha-integration-requirements-engineer` (peer agent, same HA surface). Both consume REQ/NFR docs and produce HA-integration analysis; the boundary (review vs. requirements engineering) needs an explicit negative trigger.
      Where: `.claude/agents/smart-home-ha-reviewer.md:4` vs. peer `.claude/agents/ha-integration-requirements-engineer.md`.
      Fix: Add explicit negative trigger to `description`: "nicht für Anforderungs-Engineering der HA-Integration — dafür `ha-integration-requirements-engineer`; dieser Agent reviewt aus Smart-Home-Power-User-Perspektive und liefert einen Bewertungsbericht".
      Verify: `description` contains "nicht für" naming the peer agent.

- [ ] [agent-management.body-length] Body is ~432 lines, above the SHOULD soft target of ~200. The HA-terminology checklists (Phase 2 lines 138-231) and the report skeleton (Phase 3 lines 238-416) could move into sibling assets under `.claude/agents/smart-home-ha-reviewer/`.
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-432`.
      Fix: Factor the Phase-2 checklists and the Phase-3 report skeleton into sibling files referenced by relative path.
      Verify: Body length drops below ~250 lines; sibling folder exists.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona + profile + denkmuster, then "Kernkonzept", then phases; output shape only emerges in Phase 3. Role-then-output-then-method ordering SHOULD is not honored.
      Where: `.claude/agents/smart-home-ha-reviewer.md:10-432`.
      Fix: Restructure: persona → "Output contract" → procedure (Phasen 1-4) → reference checklists (in sibling folder).
      Verify: Reading the first 80 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; `review` and `audit` would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, audit]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront that the agent writes a report file; per `agent-management.recommendations` SHOULD this distinction must be visible at dispatch time.
      Where: `.claude/agents/smart-home-ha-reviewer.md:10-432`.
      Fix: Add one sentence near the top: "This agent reviews HA-integration-relevant requirements and writes a single report file under `spec/analysis/`; it does not modify specs or production code."
      Verify: One sentence near the top names "writes report", "spec/analysis/", and "no spec or production-code edits".

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named; for this agent a plausible counter is interactivity (the user might want to confirm Side A/B/C scope before report generation).
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-432` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming interactivity as the counter-dimension and explain why it was outweighed (e.g. fire-and-forget review, post-hoc inspection of the single report file).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.english-body] Description and body are German (with significant unicode-escaped sections). Per the revised `agent-management.Structure` exception this is acceptable for `distribution: project` agents in a project whose `CLAUDE.md` authorizes German for agent prose. Kamerplanter's `CLAUDE.md` lines 9-11 declare German as the project documentation language. Recorded as INFO, not BLOCKER. The unicode-escape sequences in the rendered file are a separate readability concern but not a spec violation.
      Where: `.claude/agents/smart-home-ha-reviewer.md:4` (description), lines 10-432 (body).
      Fix: n/a (observation — language exception applies). Optional: post-process unicode escapes for readability.
      Verify: n/a.

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` with rationale ("Persona-basierter Anforderungs-Review aus Smart-Home-Sicht (HA-Trennung, MQTT, Aktorik); sonnet adaequat"); satisfies `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/smart-home-ha-reviewer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; no plugin-co-located asset references appear.
      Where: `.claude/agents/smart-home-ha-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-432`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
