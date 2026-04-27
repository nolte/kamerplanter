---
review-type: agent-review
target: ".claude/agents/plant-info-to-seed-yaml.md"
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

# Agent Review: plant-info-to-seed-yaml

## Scope

Target: `.claude/agents/plant-info-to-seed-yaml.md` (frontmatter + 350-line body, no sibling assets under `agents/plant-info-to-seed-yaml/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review.
Explicitly out of scope: schema correctness at runtime (against `plant_info.schema.yaml`), the upstream `plant-info-document-generator` agent (sibling pipeline stage, reviewed separately), the dispatching skill (none documented).

## Summary

- BLOCKER: 3
- WARNING: 3
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body language and missing rationale block dispatch readiness.
Next concrete action: rewrite system prompt in English, add rationale section pointing at the deterministic-extraction dimension that drove the haiku model choice.

## Findings

### BLOCKER

- [ ] [agent-management.Structure.MUST-english] Agent body and frontmatter description are authored in German throughout, including section headings ("Rolle", "VERBINDLICHE Regel", "Phase 0: Schemas einlesen") and rules.
      Where: `.claude/agents/plant-info-to-seed-yaml.md:4` (description) and `:10-350` (entire body).
      Fix: rewrite the system prompt in English; project's seed YAMLs may still be authored with German values where appropriate, but the prompt scaffolding must be English per `agent-management` MUST.
      Verify: `rg -n '[äöüÄÖÜß]' .claude/agents/plant-info-to-seed-yaml.md` returns hits only inside quoted German example strings.

- [ ] [skill-vs-agent.Rationale-documentation.MUST] The body has no rationale section that names a decisive dimension for the agent-over-skill choice.
      Where: `.claude/agents/plant-info-to-seed-yaml.md` (entire body, no rationale block detected).
      Fix: add a short rationale section naming at least one decisive dimension — likely "specialization" (extremely narrow no-invention extraction system prompt) plus "tool surface restriction" plus "context-window protection"; this also justifies the unusual `model: haiku` pin.
      Verify: a paragraph or bulleted list explicitly stating the skill-vs-agent dimensions exists in the body.

- [ ] [agent-management.Recommendations.SHOULD-writes-vs-research] The system prompt does not state explicitly up front that the agent writes/edits YAML seed files, even though `Write`, `Edit`, and `Bash` are declared.
      Where: `.claude/agents/plant-info-to-seed-yaml.md:1-15` (frontmatter + opening role).
      Fix: add an explicit sentence in the role block stating "this agent writes/edits YAML files under `src/backend/app/migrations/seed_data/plant_info_*.yaml`".
      Verify: the role section names the side effect and target paths.

### WARNING

- [ ] [agent-management.Recommendations.SHOULD-length] Body is 350 lines (~1.75× the ~200-line soft target); the YAML structure template, enum-mapping table, and value-conversion table could move into siblings.
      Where: `.claude/agents/plant-info-to-seed-yaml.md:106-289` (mapping tables + YAML template).
      Fix: factor the YAML structure template, the enum-mapping table, and the value-conversion table into `agents/plant-info-to-seed-yaml/` siblings referenced by relative path.
      Verify: body line count drops below ~200 after factoring.

- [ ] [skill-vs-agent.Duplicate-prevention.MUST] Agent is the downstream stage of a 2-step pipeline with `plant-info-document-generator`; no capability overlap, but description does not name the upstream sibling.
      Where: `.claude/agents/plant-info-to-seed-yaml.md:4`.
      Fix: extend the description with the upstream prerequisite ("input: plant info documents produced by `plant-info-document-generator` under `spec/knowledge/plants/`") and add a negative-trigger ("don't use to generate plant info documents — use `plant-info-document-generator` first").
      Verify: description names the pipeline predecessor explicitly.

- [ ] [agent-review.Tool-scope.SHOULD-bash-vs-dedicated] Bash is declared and used in Phase 3 (`grep -r ...` on seed_data/) and Phase 5 (`python -c "import yaml; yaml.safe_load(...)"`); the grep usage could be the dedicated `Grep` tool, the YAML check is a legitimate Bash use case.
      Where: `.claude/agents/plant-info-to-seed-yaml.md:5,86-98,294-298`.
      Fix: rewrite the Phase-3 existence-check steps to use the `Grep` tool name; keep Bash for the YAML-syntax validation only and document that justification.
      Verify: every Bash invocation in the body has a non-grep rationale.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary.MAY] Agent has no `tags` frontmatter field; adding one (e.g. `[knowledge, scaffolding]`) would cluster it with peers in the catalog.
      Where: `.claude/agents/plant-info-to-seed-yaml.md:1-8`.
      Fix: add `tags: [knowledge, scaffolding]` (each ≤30 chars, list ≤5) — same cluster tag as the upstream `plant-info-document-generator`.
      Verify: frontmatter parses with valid `tags`; the upstream sibling carries the same tags.

### INFO

- [ ] [agent-review.Checks-derived-from-skill-vs-agent.MUST-no-skill-dispatch] No `Skill(`, `Skill tool`, or `Skill <name>` invocations were found in the body — dispatch direction is clean.
      Where: full body grep clean.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.Model-selection.MAY] `model: haiku` is pinned with a one-line rationale comment ("Schema-konforme Konvertierung … deterministische Extraktion → haiku optimal") — meets the rationale SHOULD; pure mechanical extraction on haiku is plausible.
      Where: `.claude/agents/plant-info-to-seed-yaml.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
