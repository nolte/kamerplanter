---
review-type: agent-review
target: ".claude/agents/ha-integration-developer.md"
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

# Agent Review: ha-integration-developer

## Scope

Target: `.claude/agents/ha-integration-developer.md` (frontmatter + body, 232 lines; references `spec/style-guides/HA-INTEGRATION.md` (exists), `spec/ha-integration/HA-SPEC-CONFIG-LIFECYCLE.md` (exists), `spec/ha-integration/HA-SPEC-ENTITY-ARCHITECTURE.md` (exists), `spec/ha-integration/HA-SPEC-COORDINATOR-OPTIMIZATION.md` (exists), `spec/ha-integration/HA-SPEC-LOVELACE-CARDS.md` (exists), `spec/ha-integration/HA-SPEC-TESTING.md` (exists), `spec/ha-integration/HA-GAP-ANALYSIS.md` (exists), and the runtime path `custom_components/kamerplanter/` (NOT in repo working tree — deployed via kubectl cp per MEMORY.md)).
Specs applied: `agent-management` rev `7772341`, `skill-vs-agent` rev `0e3b6f9`, `review-plan` rev `0e3b6f9`, `agent-review` rev `7772341` (recorded in frontmatter).
Iteration 2: re-review under the relaxed agent-management language clause. The MUST on English-only frontmatter/body now exempts `distribution: project` agents whose consuming project authorises a non-English documentation language for agent prose; Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German, so German `description`+body becomes INFO. Frontmatter field names and technical identifier values stay English-required.
Narrowing: none — full review surface.
Explicitly out of scope: HA Quality-Scale correctness, kubectl deploy steps' runtime behavior.

## Summary

- BLOCKER: 1
- WARNING: 4
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — rationale section still missing; language BLOCKER from iteration 1 is downgraded to INFO under the relaxed clause. Duplicate-prevention with peer `ha-integration-sync` becomes a WARNING.
Next concrete action: author adds a rationale section, clarifies the boundary vs. `ha-integration-sync`, and hoists the output shape.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet. Critical here because peer agent `ha-integration-sync` overlaps in HA-code modification scope.
      Where: `.claude/agents/ha-integration-developer.md` body, lines 10-232.
      Fix: add a 2-4-bullet rationale section naming decisive dimensions (specialization on multi-spec HA-development; context-window protection — parallel reads of 5 HA-SPEC docs; tool restriction not desirable since agent writes Python). Address the overlap with `ha-integration-sync` explicitly.
      Verify: grep for "Rationale" returns the new section AND the description names the boundary vs. `ha-integration-sync`.

### WARNING

- [ ] [skill-vs-agent.duplicate-prevention] Plausible overlap with peer agent `ha-integration-sync`: both modify HA-integration Python files (api.py, coordinator.py, sensor.py, etc.). Boundary is real (developer = build new features against HA-SPEC docs vs. sync = mirror backend-API changes mechanically) but not surfaced in the description.
      Where: line 4 description (this agent) vs. peer `ha-integration-sync` line 4.
      Fix: add a "don't use for" clause to both agents, e.g., here: "don't use for mechanical backend-API sync — use ha-integration-sync".
      Verify: description contains the negative trigger naming the peer.
- [ ] [agent-management.system-prompt-output-shape] Output shape (modified Python files, ruff-clean code, deploy-verify-fix loop result) is implied by the Quality-Criteria checklist (lines 220-232) but the role-opening section (lines 10-21) does not state it. SHOULD requires the system prompt to name the expected output shape up front.
      Where: lines 10-21 (role) vs. lines 220-232 (criteria).
      Fix: hoist a one-paragraph "Output shape" block under the role.
      Verify: lines 1-40 name the output shape.
- [ ] [agent-management.system-prompt-order] Order: role -> Pflichtlektuere -> Verbotene Patterns -> Implementierungsreihenfolge -> Arbeitsweise (Phase 1-4) -> Entwicklungsumgebung -> Scope -> Deploy-Verify-Fix-Schleife -> Qualitaetskriterien. SHOULD requires role -> output -> method; output is at the end.
      Where: full file structure.
      Fix: reorder to role -> output -> method.
      Verify: section ordering follows the SHOULD.
- [ ] [agent-management.no-hardcoded-runtime-paths] References `custom_components/kamerplanter/` (lines 64, 70, 154-156, 178-185) as a working-directory path; per MEMORY.md the HA integration is NOT under that path in the repo working tree (it is deployed via `kubectl cp` and edited under a different source location, e.g., `src/ha-integration/custom_components/kamerplanter/` which is also absent in this checkout). The agent's references therefore point at a runtime-only location, blurring the source-vs-runtime separation.
      Where: lines 64, 70, 154-156, 178-185.
      Fix: state the source path explicitly (where the agent should Edit files) vs. the runtime path (where files are deployed); reconcile with MEMORY's `kubectl cp` workflow.
      Verify: source path declared once and consistently; runtime path appears only in the deploy section.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [home-assistant, integration, development]` would aid peer-cluster discovery with `ha-integration-sync` and `ha-integration-requirements-engineer`.
      Where: frontmatter (lines 1-8).
      Fix: add `tags: [home-assistant, integration, development]` (<=5, lowercase kebab-case, <=30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.english-content-project-exception] Description and body are German. Under the relaxed clause this is allowed because `distribution: project` is declared and Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German for `.claude/agents/` prose. Iteration-1 BLOCKER downgraded.
      Where: line 4 (description), lines 10-232 (body).
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.model-rationale] Model pinned to `opus` with rationale ("complex implementation against multiple HA-SPEC documents in parallel, high code share -> opus") on line 6 — satisfies the SHOULD. Plausibility passes for parallel-spec implementation work.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.tools-scope] Tools `Read, Write, Edit, Bash, Glob, Grep` (line 5) match the stated responsibility (Implement and refactor Python files, run ruff, deploy via kubectl); not a read-only agent.
      Where: line 5.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.write-effects-documented] Body documents write goals + preconditions in §"Scope-Einschraenkungen" (lines 152-159) and §"Deploy-Verify-Fix-Schleife" (lines 162-217), satisfying the write-effects SHOULD.
      Where: lines 152-217.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
