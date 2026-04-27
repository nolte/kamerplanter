---
review-type: agent-review
target: ".claude/agents/ha-integration-sync.md"
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

# Agent Review: ha-integration-sync

## Scope

Target: `.claude/agents/ha-integration-sync.md` (frontmatter + body, ~199 lines; references `custom_components/kamerplanter/`, multiple backend paths under `src/backend/app/api/v1/`, and HA-INTEGRATION specs which exist).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions recorded in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: HA-integration runtime correctness, Skaffold cluster behavior.

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body is German, lacks rationale, and overlaps with `ha-integration-developer`.
Next concrete action: author addresses BLOCKERs (English body, rationale, duplicate boundary with `ha-integration-developer`).

## Findings

### BLOCKER

- [ ] [agent-management.english-content] Description and full body are in German, violating the MUST that frontmatter and system-prompt content stay in English.
      Where: lines 4 (`description`), 10–199 (body).
      Fix: rewrite description and body in English.
      Verify: `head -20` shows English content.
- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet.
      Where: full body.
      Fix: add a 2–4-bullet rationale section (e.g., specialization on Backend↔HA schema mapping; tool restriction not needed because writes are bounded; mechanical, fire-and-forget output).
      Verify: grep for "rationale" returns the new section.
- [ ] [skill-vs-agent.duplicate-prevention] Material overlap with peer agent `ha-integration-developer`: both edit the same files (`custom_components/kamerplanter/api.py`, `coordinator.py`, `sensor.py`, `binary_sensor.py`, `calendar.py`, `todo.py`, `button.py`, `services.yaml`, `config_flow.py`, `const.py`) and both run the same kubectl deploy loop. Sync's stated scope is narrower (only API-driven changes), but the boundary is not visible from descriptions alone.
      Where: line 4 description vs. peer `.claude/agents/ha-integration-developer.md:4`.
      Fix: add an explicit "don't use for" negative trigger naming `ha-integration-developer` ("don't use for HA-SPEC-driven implementation or refactoring — use ha-integration-developer"); mirror the inverse on the peer.
      Verify: both descriptions contain mutual "don't use for" clauses naming each other.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (delta table + changed-files list + non-changed confirmation + deploy command + open issues) is named at lines 190–198 but not in the role-opening section. The MUST requires the output shape to be stated.
      Where: lines 10–14 (role) vs. lines 190–198 (output format).
      Fix: hoist a one-paragraph "Output shape" block under the role.
      Verify: lines 1–30 name the output shape.
- [ ] [agent-management.system-prompt-order] Order: role → method (Phase 1–3) → environment → rules → deploy workflow → reference files → output format. The SHOULD requires role → output → method.
      Where: full file structure.
      Fix: reorder to role → output → method.
      Verify: section ordering follows the SHOULD.
- [ ] [agent-management.write-effects-documented] Tools include `Write`/`Edit`/`Bash`; goals are stated ("synchronize HA integration with backend API"), but preconditions are scattered: "NICHT AENDERN" list (line 110), "Code-Stil" (line 126), "Deployment-Workflow" (line 135). The SHOULD asks for goals + preconditions in the system prompt.
      Where: lines 110–135.
      Fix: hoist a single preconditions block under the role.
      Verify: opening section names goals + preconditions.
- [ ] [agent-management.tools-bash-vs-dedicated] `Bash` is used for `ruff check`, `kubectl cp`, `kubectl exec`, `kubectl wait`, `kubectl logs` — none has a dedicated equivalent. Acceptable, but the body should justify Bash explicitly.
      Where: frontmatter line 5 vs. body lines 138–150.
      Fix: state in tool-use rationale that Bash is scoped to lint + kubectl deploy commands.
      Verify: body documents Bash scope.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [home-assistant, sync]` would aid peer-cluster discovery (paired with `ha-integration-developer`, `ha-integration-requirements-engineer`).
      Where: frontmatter.
      Fix: add `tags: [home-assistant, sync]` (≤5, lowercase kebab-case, ≤30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.model-rationale] Model pinned to `sonnet` with rationale ("mechanical API-schema mapping without new architecture decisions; opus was over-dimensioned") on line 6 — satisfies the SHOULD. Plausibility passes; downgrade from opus to sonnet is justified.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-review.referenced-assets] All referenced assets exist: `custom_components/kamerplanter/*.py`, `src/backend/app/api/v1/*/router.py`, `*/schemas.py`, `spec/style-guides/BACKEND.md`, `spec/ha-integration/HA-CUSTOM-INTEGRATION.md`, `HA-REVIEW-CORE.md`, `HA-REVIEW-SUPPORTING.md`, `HA-REQ-004_Duenge-Logik.md`. No broken references.
      Where: lines 156–186.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
