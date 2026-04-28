---
review-type: agent-review
target: ".claude/agents/ha-integration-requirements-engineer.md"
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
status: in-progress
---

# Agent Review: ha-integration-requirements-engineer

## Scope

Target: `.claude/agents/ha-integration-requirements-engineer.md` (frontmatter + body, ~373 lines; references `spec/ha-integration/HA-CUSTOM-INTEGRATION.md` (exists) and `spec/analysis/smart-home-ha-integration-review.md` (does NOT exist)).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions recorded in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: correctness of derived requirements, three-side-model effectiveness.

## Summary

- BLOCKER: 4
- WARNING: 5
- SUGGESTION: 1
- INFO: 1

Go/no-go: FAIL — body is German, lacks rationale, references a missing asset, and duplicates the existing `ha-derive` skill.
Next concrete action: author addresses BLOCKERs, especially the duplicate with skill `ha-derive` and the missing referenced asset.

## Findings

### BLOCKER

- [ ] [agent-management.english-content] Description and full body are in German, violating the MUST that frontmatter and system-prompt content stay in English.
      Where: lines 4 (`description`), 10–373 (body).
      Fix: rewrite description and body in English.
      Verify: `head -20` shows English content.
- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice — especially critical here because a peer skill (`ha-derive`) covers the same capability.
      Where: full body.
      Fix: add a 2–4-bullet rationale section explicitly contrasting agent vs. skill choice; if `ha-derive` skill duplicates this work, propose a merge or supersede instead of shipping both.
      Verify: rationale section names ≥1 decisive dimension and addresses the duplicate with `ha-derive`.
- [ ] [skill-vs-agent.duplicate-prevention] The peer skill `nolte-shared:ha-derive` ("derive HA requirements from REQ") is semantically identical to this agent's stated responsibility ("derive HA-specific integration requirements from existing REQ documents"). Per `skill-vs-agent` duplicate-prevention MUST, two artifacts MUST NOT cover the same capability within the plugin.
      Where: line 4 description vs. skill `ha-derive` description (in available-skills list).
      Fix: choose one of: (a) deprecate this agent and route all "derive HA requirements" calls to the skill `ha-derive`; (b) deprecate the skill and keep this agent; (c) restructure so the skill orchestrates and the agent is its executor (allowed by `skill-vs-agent` hybrid pattern). Document the resolution in the rationale section.
      Verify: only one artifact remains, or the two have a documented orchestrator/executor relationship.
- [x] [agent-review.referenced-assets] Body references `spec/analysis/smart-home-ha-integration-review.md` (line 38, 70) as MUST-read reference; the file does not exist (`ls` returns "No such file"). The MUST in agent-management on `no hard-coded absolute paths` is OK (path is repo-relative), but the reviewed-asset MUST in agent-review requires the asset to exist.
      Where: lines 38, 70 (`spec/analysis/smart-home-ha-integration-review.md`).
      Fix: either (a) create the missing review document, or (b) remove the references and replace them with available HA-REVIEW documents under `spec/ha-integration/HA-REVIEW-CORE.md` / `HA-REVIEW-SUPPORTING.md`.
      Verify: every referenced path returns 0 from `ls`.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (a structured markdown report under `spec/ha-integration/HA-REQ-{nnn}_{kurztitel}.md` with 9 sections) is defined at Phase 3 (line 168+) but not stated in the role-opening section.
      Where: lines 10–28 (role) vs. lines 168–344 (output template).
      Fix: hoist a one-paragraph "Output shape" block under the role.
      Verify: lines 1–40 name the output document and key sections.
- [ ] [agent-management.system-prompt-order] Order: role → context → three-side-model → method (Phase 1–4) → leitprinzipien. The SHOULD requires role → output → method; output is at the end of method.
      Where: full file structure.
      Fix: reorder to role → output → method.
      Verify: section ordering follows the SHOULD.
- [ ] [agent-management.system-prompt-length] Body is ~373 lines, well over the ~200-line soft target; the report template (lines 178–343) is a prime candidate for a sibling asset under `agents/ha-integration-requirements-engineer/`.
      Where: lines 178–343 (report template).
      Fix: factor template into `agents/ha-integration-requirements-engineer/report-template.md`.
      Verify: `wc -l` returns ~200.
- [ ] [agent-management.write-effects-documented] Tools include `Write`; goals are stated ("create structured markdown report"), but preconditions ("do not invent data not in source REQs", "do not modify HA-CUSTOM-INTEGRATION.md", "create only under spec/ha-integration/") are not surfaced as a precondition block.
      Where: line 170 (file-name pattern) without preconditions block.
      Fix: add a preconditions block under the role naming the write boundary.
      Verify: opening section names goals + preconditions.
- [ ] [skill-vs-agent.duplicate-prevention] In addition to the `ha-derive` skill duplicate (BLOCKER above), there is a softer overlap with peer agent `smart-home-ha-reviewer` (HA-spec review). This agent derives requirements; the reviewer reviews them — boundary is real but should be made explicit in the description.
      Where: line 4 description vs. peer `smart-home-ha-reviewer`.
      Fix: add a "don't use for" clause naming `smart-home-ha-reviewer` ("don't use for reviewing existing HA specs — use smart-home-ha-reviewer").
      Verify: description contains "don't use for" clause.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [home-assistant, requirements]` would aid peer-cluster discovery.
      Where: frontmatter.
      Fix: add `tags: [home-assistant, requirements]` (≤5, lowercase kebab-case, ≤30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.model-rationale] Model pinned to `sonnet` with rationale ("requirements derivation via three-side model; structured spec creation") on line 6 — satisfies the SHOULD. Plausibility passes.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-28 — agent-review.referenced-assets — replace dangling spec/analysis/smart-home-ha-integration-review.md references with existing spec/ha-integration/HA-REVIEW-CORE.md and HA-REVIEW-SUPPORTING.md — verified: re-read agent file, finding condition no longer holds
