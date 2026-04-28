---
review-type: agent-review
target: ".claude/agents/ha-integration-requirements-engineer.md"
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

# Agent Review: ha-integration-requirements-engineer

## Scope

Target: `.claude/agents/ha-integration-requirements-engineer.md` (frontmatter + body, 374 lines; references `spec/ha-integration/HA-CUSTOM-INTEGRATION.md` (exists), `spec/ha-integration/HA-REVIEW-CORE.md` (exists), `spec/ha-integration/HA-REVIEW-SUPPORTING.md` (exists). Iteration-1 dangling reference to `spec/analysis/smart-home-ha-integration-review.md` was fixed in the quick-win iteration; current references all resolve).
Specs applied: `agent-management` rev `7772341`, `skill-vs-agent` rev `0e3b6f9`, `review-plan` rev `0e3b6f9`, `agent-review` rev `7772341` (recorded in frontmatter).
Iteration 2: re-review under the relaxed agent-management language clause. The MUST on English-only frontmatter/body now exempts `distribution: project` agents whose consuming project authorises a non-English documentation language for agent prose; Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German, so German `description`+body becomes INFO. Frontmatter field names and technical identifier values stay English-required.
Narrowing: none — full review surface.
Explicitly out of scope: correctness of derived requirements, three-side-model effectiveness.

## Summary

- BLOCKER: 2
- WARNING: 4
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — rationale and duplicate-prevention with skill `ha-derive` remain BLOCKERs; language BLOCKER from iteration 1 downgraded to INFO; referenced-asset BLOCKER from iteration 1 closed (paths now resolve).
Next concrete action: author resolves the duplicate with skill `ha-derive` (deprecate or restructure into orchestrator/executor pattern) and adds a rationale section.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice — especially critical here because peer skill `ha-derive` covers the same capability.
      Where: `.claude/agents/ha-integration-requirements-engineer.md` body, lines 10-374.
      Fix: add a 2-4-bullet rationale section explicitly contrasting agent vs. skill choice; if `ha-derive` skill duplicates this work, propose a merge or supersede instead of shipping both.
      Verify: rationale section names >=1 decisive dimension and addresses the duplicate with `ha-derive`.
- [ ] [skill-vs-agent.duplicate-prevention] Peer skill `nolte-shared:ha-derive` ("derive HA requirements from REQ") is semantically identical to this agent's stated responsibility ("derive HA-specific integration requirements from existing REQ documents"). Per skill-vs-agent duplicate-prevention MUST, two artifacts MUST NOT cover the same capability within the plugin.
      Where: line 4 description vs. skill `ha-derive` description.
      Fix: choose one of: (a) deprecate this agent and route all "derive HA requirements" calls to skill `ha-derive`; (b) deprecate the skill and keep this agent; (c) restructure so the skill orchestrates and the agent is its executor (allowed by skill-vs-agent hybrid pattern). Document the resolution in the rationale section.
      Verify: only one artifact remains, OR the two have a documented orchestrator/executor relationship.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (a structured markdown report under `spec/ha-integration/HA-REQ-{nnn}_{kurztitel}.md` with 9 sections) is defined at Phase 3 (line 168+) but not stated in the role-opening section.
      Where: lines 10-28 (role) vs. lines 168-345 (output template).
      Fix: hoist a one-paragraph "Output shape" block under the role section.
      Verify: lines 1-40 name the output document and key sections.
- [ ] [agent-management.system-prompt-order] Order: role -> context -> three-side-model -> method (Phase 1-4) -> Leitprinzipien. SHOULD requires role -> output -> method; output is at the end of method.
      Where: full file structure.
      Fix: reorder to role -> output -> method.
      Verify: section ordering follows the SHOULD.
- [ ] [agent-management.system-prompt-length] Body is 374 lines, well over the ~200-line soft target; the report template (lines 178-345) is a prime candidate for a sibling asset under `agents/ha-integration-requirements-engineer/`.
      Where: lines 178-345 (report template).
      Fix: factor the template into `agents/ha-integration-requirements-engineer/report-template.md`.
      Verify: `wc -l` returns ~200.
- [ ] [skill-vs-agent.duplicate-prevention] Softer overlap with peer agent `smart-home-ha-reviewer` (HA-spec review): this agent derives requirements; the reviewer reviews existing specs — boundary is real but not surfaced in the description.
      Where: line 4 description vs. peer `smart-home-ha-reviewer`.
      Fix: add a "don't use for" clause naming `smart-home-ha-reviewer` ("don't use for reviewing existing HA specs — use smart-home-ha-reviewer").
      Verify: description contains a "don't use for" clause.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [home-assistant, requirements]` would aid peer-cluster discovery vs. peers `ha-integration-developer`, `ha-integration-sync`, `smart-home-ha-reviewer`.
      Where: frontmatter (lines 1-8).
      Fix: add `tags: [home-assistant, requirements]` (<=5, lowercase kebab-case, <=30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.english-content-project-exception] Description and body are German. Under the relaxed clause this is allowed because `distribution: project` is declared and Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German for `.claude/agents/` prose. Iteration-1 BLOCKER downgraded.
      Where: line 4 (description), lines 10-374 (body).
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.model-rationale] Model pinned to `sonnet` with rationale ("requirements derivation via three-side model; sonnet adequate for structured spec creation") on line 6 — satisfies the SHOULD. Plausibility passes.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-review.referenced-assets] Iteration-1 BLOCKER on dangling `spec/analysis/smart-home-ha-integration-review.md` is closed: lines 38, 70 now reference `spec/ha-integration/HA-REVIEW-CORE.md` and `HA-REVIEW-SUPPORTING.md`, both of which exist.
      Where: lines 38, 70.
      Fix: n/a (observation — quick-win fix landed).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
