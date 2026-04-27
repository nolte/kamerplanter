---
review-type: agent-review
target: ".claude/agents/outdoor-garden-planner-reviewer.md"
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

# Agent Review: outdoor-garden-planner-reviewer

## Scope

Target: `.claude/agents/outdoor-garden-planner-reviewer.md` (frontmatter + 466-line body, no sibling assets under `agents/outdoor-garden-planner-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review.
Explicitly out of scope: factual correctness of the persona's gardening expertise, the report template's downstream consumers, the dispatching skill (none documented).

## Summary

- BLOCKER: 4
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body language, missing rationale, and read-only-vs-Write tool mismatch block dispatch readiness.
Next concrete action: rewrite system prompt in English, add rationale section, and either drop `Write` from tools or stop calling this a "review" agent.

## Findings

### BLOCKER

- [ ] [agent-management.Structure.MUST-english] Agent body and frontmatter description are authored in German throughout.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md:4` (description) and `:10-466` (entire body).
      Fix: rewrite the system prompt in English; the persona may still be instructed to produce German review reports (project convention), but the prompt scaffolding must be English per `agent-management` MUST.
      Verify: `rg -n '[äöüÄÖÜß]' .claude/agents/outdoor-garden-planner-reviewer.md` returns hits only inside quoted German example strings.

- [ ] [skill-vs-agent.Rationale-documentation.MUST] The body has no rationale section that names a decisive dimension for the agent-over-skill choice.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md` (entire body, no rationale block detected).
      Fix: add a short rationale section naming at least one decisive dimension — likely "specialization" (sharp persona system prompt) and "context-window protection" (heavy spec reads).
      Verify: a paragraph or bulleted list explicitly stating the skill-vs-agent dimensions exists in the body.

- [ ] [agent-review.Checks-derived-from-agent-management.MUST-readonly-tools] Agent self-describes as "Reviewer" (read-only role: review, audit, report) but declares `Write` in `tools`, which the agent-only invariants reject for read-only agents.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md:5` (`tools: Read, Write, Glob, Grep`) vs `:1` `name: outdoor-garden-planner-reviewer` and `:4` description "Prüft Anforderungsdokumente".
      Fix: drop `Write` from tools and let the calling skill or main thread persist the report; or, if file writing is genuinely required, rewrite the role as authoring rather than reviewing.
      Verify: `tools` list matches the read-only role; or role explicitly authorizes writes with target paths declared.

- [ ] [agent-management.Recommendations.SHOULD-writes-vs-research] If `Write` stays declared, the system prompt must state the side-effect target (Phase 3 writes `spec/analysis/outdoor-garden-planner-review.md`) up front, not just inside Phase 3.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md:5,267`.
      Fix: add an explicit "this agent writes a single report file at `spec/analysis/outdoor-garden-planner-review.md`" sentence in the role block; or remove `Write` per the BLOCKER above.
      Verify: the role section names the side effect and the absolute target path.

### WARNING

- [ ] [skill-vs-agent.Duplicate-prevention.MUST] Agent is structurally identical to other persona-spec-reviewer agents (`agrobiology-requirements-reviewer`, `cannabis-indoor-grower-reviewer`, `casual-houseplant-user-reviewer`, `smart-home-ha-reviewer`, `it-security-requirements-reviewer`, `target-audience-analyzer`) — same workflow shape, same report-template pattern, only the persona changes.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md` overall structure vs peers in `.claude/agents/`.
      Fix: extract the shared workflow into a `review-spec` skill that takes a persona parameter, or accept the parallel-personas pattern explicitly and document it in each agent's rationale section.
      Verify: either a single skill replaces the persona agents, or every persona-reviewer agent's rationale explicitly references the parallel-persona pattern.

- [ ] [skill-vs-agent.Rationale-documentation.SHOULD] No counter-dimension is named for the skill-vs-agent choice (a `review-spec` skill with persona parameter is a real alternative).
      Where: same rationale-section gap as the BLOCKER above.
      Fix: when adding the rationale, name "skill with persona parameter" as the considered counter and the reason it was rejected (e.g. context isolation per persona, parallel runs in one batch).
      Verify: rationale paragraph explicitly addresses the skill alternative.

- [ ] [agent-management.Recommendations.SHOULD-length] Body is 466 lines (~2.3× the ~200-line soft target), and the embedded report template + monthly task table + comparison matrix could live in `agents/outdoor-garden-planner-reviewer/` siblings.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md:267-449` (report template + tables).
      Fix: factor the report template, monthly-task table, app-comparison matrix and "Überwinterungs-Checkliste" into sibling files referenced by relative path.
      Verify: body line count drops below ~200 after factoring.

- [ ] [agent-management.Recommendations.SHOULD-negative-triggers] Description has only positive triggers; with five+ persona-reviewer agents in the portfolio, negative cases ("don't use for cannabis indoor; that's `cannabis-indoor-grower-reviewer`") would help routing.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md:4`.
      Fix: add 1–3 explicit "don't use for X — use Y" sentences pointing at peer persona reviewers.
      Verify: description contains explicit negative-trigger phrasing.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary.MAY] Agent has no `tags` frontmatter field; tagging persona reviewers (e.g. `[review, audience]`) would form a verifiable cluster in the catalog tag index.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md:1-8`.
      Fix: add `tags: [review, audience]` (each ≤30 chars, list ≤5) consistently across all persona reviewers.
      Verify: frontmatter parses with valid `tags`; the same tags appear on the peer persona reviewers.

### INFO

- [ ] [agent-review.Checks-derived-from-skill-vs-agent.MUST-no-skill-dispatch] No `Skill(`, `Skill tool`, or `Skill <name>` invocations were found in the body — dispatch direction is clean.
      Where: full body grep clean.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.Model-selection.MAY] `model: sonnet` is pinned with a one-line rationale comment ("Persona-basierter Anforderungs-Review … sonnet adaequat") — meets the rationale SHOULD; persona-review on sonnet is plausible.
      Where: `.claude/agents/outdoor-garden-planner-reviewer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
