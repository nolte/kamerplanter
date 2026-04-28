---
review-type: agent-review
target: ".claude/agents/ha-integration-sync.md"
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

# Agent Review: ha-integration-sync

## Scope

Target: `.claude/agents/ha-integration-sync.md` (frontmatter + body, 198 lines; references `spec/ha-integration/HA-CUSTOM-INTEGRATION.md` (exists), `spec/ha-integration/HA-REVIEW-CORE.md` (exists), `spec/ha-integration/HA-REVIEW-SUPPORTING.md` (exists), `spec/ha-integration/HA-REQ-004_Duenge-Logik.md` (exists), `spec/style-guides/BACKEND.md` (exists), `src/backend/app/api/v1/...` (exists), and the runtime path `custom_components/kamerplanter/` (NOT in repo working tree — deployed via kubectl cp per MEMORY.md)).
Specs applied: `agent-management` rev `7772341`, `skill-vs-agent` rev `0e3b6f9`, `review-plan` rev `0e3b6f9`, `agent-review` rev `7772341` (recorded in frontmatter).
Iteration 2: re-review under the relaxed agent-management language clause. The MUST on English-only frontmatter/body now exempts `distribution: project` agents whose consuming project authorises a non-English documentation language for agent prose; Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German, so German `description`+body becomes INFO. Frontmatter field names and technical identifier values stay English-required.
Narrowing: none — full review surface.
Explicitly out of scope: correctness of API-schema-mapping logic, kubectl deploy runtime behavior.

## Summary

- BLOCKER: 1
- WARNING: 3
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — rationale section still missing; language BLOCKER from iteration 1 is downgraded to INFO under the relaxed clause. Duplicate with `ha-integration-developer` becomes a WARNING.
Next concrete action: author adds a rationale section and clarifies boundary vs. `ha-integration-developer`.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet. Critical here because peer agent `ha-integration-developer` overlaps in HA-code modification scope.
      Where: `.claude/agents/ha-integration-sync.md` body, lines 10-198.
      Fix: add a 2-4-bullet rationale section naming decisive dimensions (e.g., specialization on mechanical API-schema-mapping; context-window protection — parallel reads of backend routers + HA api.py; tool restriction not desirable since agent writes Python). Address the overlap with `ha-integration-developer` explicitly.
      Verify: grep for "Rationale" returns the new section AND description names the boundary vs. `ha-integration-developer`.

### WARNING

- [ ] [skill-vs-agent.duplicate-prevention] Plausible overlap with peer agent `ha-integration-developer`: both modify HA-integration Python files (api.py, coordinator.py, sensor.py, etc.). Boundary is real (sync = mirror backend-API changes mechanically; developer = build new features against HA-SPEC docs) but not surfaced in the description.
      Where: line 4 description vs. peer `ha-integration-developer` line 4.
      Fix: add a "don't use for" clause: "don't use for new HA-feature implementation against HA-SPEC docs — use ha-integration-developer".
      Verify: description contains the negative trigger naming the peer.
- [ ] [agent-management.system-prompt-output-shape] Output shape (delta table + list of changed files + non-changed business logic + deploy instruction + open points) is named in §"Ausgabeformat" (lines 191-198) but not in the role-opening section.
      Where: lines 10-13 (role) vs. lines 191-198 (output).
      Fix: hoist a one-paragraph "Output shape" block under the role.
      Verify: lines 1-40 name the output sections.
- [ ] [agent-management.no-hardcoded-runtime-paths] References `custom_components/kamerplanter/api.py` etc. (lines 27, 158-172) without disambiguating source-vs-runtime — same issue as `ha-integration-developer`. The HA integration is not in the repo working tree under that path; per MEMORY.md it lives under `src/ha-integration/custom_components/kamerplanter/` (also absent here) and is deployed via kubectl cp.
      Where: lines 27, 158-172.
      Fix: declare the source path explicitly (where the agent edits files) vs. the runtime path (where files are deployed); reconcile with MEMORY's kubectl cp workflow.
      Verify: source path declared once and consistently.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [home-assistant, integration, sync]` would aid peer-cluster discovery vs. peers `ha-integration-developer`, `ha-integration-requirements-engineer`.
      Where: frontmatter (lines 1-8).
      Fix: add `tags: [home-assistant, integration, sync]` (<=5, lowercase kebab-case, <=30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.english-content-project-exception] Description and body are German. Under the relaxed clause this is allowed because `distribution: project` is declared and Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German for `.claude/agents/` prose. Iteration-1 BLOCKER downgraded.
      Where: line 4 (description), lines 10-198 (body).
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.model-rationale] Model pinned to `sonnet` with rationale ("mechanical API-schema mapping between backend and HA integration without new architecture decisions -> sonnet sufficient, opus was overdimensioned") on line 6 — satisfies the SHOULD. Plausibility passes.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.tools-scope] Tools `Read, Write, Edit, Bash, Glob, Grep` (line 5) match the stated responsibility (modify HA-integration Python files, run ruff, deploy via kubectl); not a read-only agent.
      Where: line 5.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.system-prompt-length] Body is 198 lines — within the ~200-line soft target.
      Where: full file.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
