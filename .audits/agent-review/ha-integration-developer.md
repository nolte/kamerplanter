---
review-type: agent-review
target: ".claude/agents/ha-integration-developer.md"
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

# Agent Review: ha-integration-developer

## Scope

Target: `.claude/agents/ha-integration-developer.md` (frontmatter + body, ~233 lines; references multiple spec files which all exist).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions recorded in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: HA-integration code correctness, Skaffold cluster behavior.

## Summary

- BLOCKER: 3
- WARNING: 5
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body is German, lacks rationale, and overlaps materially with `ha-integration-sync`.
Next concrete action: author addresses BLOCKERs (English body, rationale, duplicate boundary).

## Findings

### BLOCKER

- [ ] [agent-management.english-content] Description and full body are in German, violating the MUST that frontmatter and system-prompt content stay in English.
      Where: lines 4 (`description`), 10–233 (body).
      Fix: rewrite description and body in English. The project's CLAUDE.md German-conversation rule does not override the agent-management English MUST for agent files.
      Verify: `head -20` shows English content.
- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet.
      Where: full body.
      Fix: add a 2–4-bullet rationale section (e.g., specialization on HA-SPEC-* documents, large-context reading of multiple specs, tool restriction not needed because the agent writes code).
      Verify: grep for "rationale" returns the new section.
- [ ] [skill-vs-agent.duplicate-prevention] Material overlap with peer agent `ha-integration-sync`: both edit `custom_components/kamerplanter/` files (api.py, coordinator.py, sensor.py, etc.) and both run the same deploy-verify-fix loop. Their descriptions name different triggers (full implementation vs. backend-API-sync), but the boundary is not visible from description alone.
      Where: line 4 description vs. peer `.claude/agents/ha-integration-sync.md:4`.
      Fix: tighten this agent's description to scope it to "implementing or refactoring against HA-SPEC-* documents from scratch" and add an explicit "don't use for backend-API-driven changes — use ha-integration-sync" negative trigger. Mirror the inverse on the peer agent.
      Verify: both descriptions contain mutual "don't use for" clauses naming each other.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] The output shape (modified files under `custom_components/kamerplanter/` plus a final summary against acceptance criteria) is implied but not stated in the role-opening section; only quality criteria appear at lines 220–232.
      Where: lines 10–22 (role) vs. lines 220–232 (quality criteria).
      Fix: add a one-paragraph "Output shape" block under the role naming the file targets, the lint/deploy gate, and the report shape.
      Verify: lines 1–30 contain the output-shape statement.
- [ ] [agent-management.system-prompt-order] Order: role → reading list → forbidden patterns → implementation order → method → environment → scope → deploy loop → quality criteria. The SHOULD requires role → output → method; output is at the end, environment/scope are middle.
      Where: full file structure.
      Fix: reorder so the output shape and method follow immediately after the role; environment/scope/deploy loop become a single "Procedure" block.
      Verify: section order follows the SHOULD.
- [ ] [agent-management.system-prompt-length] Body is 233 lines, slightly over the ~200-line soft target; the deploy-verify-fix loop (lines 162–217) and forbidden-patterns table are candidates for sibling assets under `agents/ha-integration-developer/`.
      Where: lines 73–86 (forbidden patterns) and 162–217 (deploy loop).
      Fix: factor deploy loop and forbidden-patterns into sibling files.
      Verify: `wc -l` returns ~200.
- [ ] [agent-management.write-effects-documented] Tools include `Write`/`Edit`/`Bash`; goals are documented (deploy-verify-fix loop, line 162+) but preconditions are spread across "Verbotene Patterns" (line 73), "Scope-Einschraenkungen" (line 152), and "Deploy-Verify-Fix-Schleife" (line 162). Hoisting a single preconditions block near the role would satisfy the SHOULD better.
      Where: lines 73–86, 152–158, 162–217.
      Fix: consolidate write-effect preconditions into one block under the role.
      Verify: opening section names goals + preconditions in one place.
- [ ] [agent-management.tools-bash-vs-dedicated] `Bash` is used for `kubectl cp`, `kubectl exec`, `ruff check` — none has a dedicated equivalent, so the SHOULD is satisfied; however, the body should justify Bash explicitly to make the choice auditable.
      Where: frontmatter line 5 vs. body lines 169–211.
      Fix: state in the tool-use rationale that Bash is scoped to lint + kubectl deployment commands.
      Verify: body documents the Bash scope.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [home-assistant, integration]` would aid peer-cluster discovery (paired with `ha-integration-sync`, `ha-integration-requirements-engineer`, `smart-home-ha-reviewer`).
      Where: frontmatter.
      Fix: add `tags: [home-assistant, integration]` (≤5, lowercase kebab-case, ≤30 chars).
      Verify: `grep "^tags:" .claude/agents/ha-integration-developer.md` returns the field.

### INFO

- [ ] [agent-management.model-rationale] Model pinned to `opus` with rationale ("complex implementation against multiple HA-SPEC documents in parallel") on line 6 — satisfies the SHOULD. Plausibility passes for an implementation-heavy agent.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-review.referenced-assets] All referenced assets exist: `spec/style-guides/HA-INTEGRATION.md`, `spec/ha-integration/HA-SPEC-CONFIG-LIFECYCLE.md`, `HA-SPEC-ENTITY-ARCHITECTURE.md`, `HA-SPEC-COORDINATOR-OPTIMIZATION.md`, `HA-SPEC-LOVELACE-CARDS.md`, `HA-SPEC-TESTING.md`, `HA-GAP-ANALYSIS.md`, `HA-DEVELOPER-DOCS-RESEARCH.md`, `HA-DEVELOPER-PATTERNS.md`, `LOVELACE-CARD-PATTERNS.md`. No broken references.
      Where: lines 29–62.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
