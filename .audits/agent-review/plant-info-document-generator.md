---
review-type: agent-review
target: ".claude/agents/plant-info-document-generator.md"
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

# Agent Review: plant-info-document-generator

## Scope

Target: `.claude/agents/plant-info-document-generator.md` (frontmatter + 481-line body, no sibling assets under `agents/plant-info-document-generator/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review.
Explicitly out of scope: factual correctness of the botanical research it produces, the downstream `plant-info-to-seed-yaml` agent (sibling pipeline stage, reviewed separately), the dispatching skill (none documented).

## Summary

- BLOCKER: 3
- WARNING: 3
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body language and missing rationale block dispatch readiness.
Next concrete action: rewrite system prompt in English, add rationale section, factor the long document template into a sibling file.

## Findings

### BLOCKER

- [ ] [agent-management.Structure.MUST-english] Agent body and frontmatter description are authored in German throughout, including section headings ("Rolle", "Auftrag", "Workflow", "Phase 1: Eingabe analysieren") and rules.
      Where: `.claude/agents/plant-info-document-generator.md:4` (description) and `:10-481` (entire body).
      Fix: rewrite the system prompt in English; the agent may still be instructed to produce German plant-info documents (project convention), but the prompt scaffolding must be English per `agent-management` MUST.
      Verify: `rg -n '[äöüÄÖÜß]' .claude/agents/plant-info-document-generator.md` returns hits only inside quoted German example strings.

- [ ] [skill-vs-agent.Rationale-documentation.MUST] The body has no rationale section that names a decisive dimension for the agent-over-skill choice.
      Where: `.claude/agents/plant-info-document-generator.md` (entire body, no rationale block detected).
      Fix: add a short rationale section naming at least one decisive dimension — likely "context-window protection" (heavy WebSearch/WebFetch reads per plant) plus "parallelism" (multiple plants in one batch) plus "specialization" (narrow botanist persona).
      Verify: a paragraph or bulleted list explicitly stating the skill-vs-agent dimensions exists in the body.

- [ ] [agent-management.Recommendations.SHOULD-writes-vs-research] The system prompt does not state explicitly up front that the agent writes files (only Phase 3 mentions output paths), even though `Write` is declared.
      Where: `.claude/agents/plant-info-document-generator.md:1-12` (frontmatter + opening role).
      Fix: add an explicit sentence in the role block stating "this agent writes one Markdown file per plant under `spec/knowledge/plants/<scientific_name_snake_case>.md`".
      Verify: the role section names the side effect and target paths.

### WARNING

- [ ] [agent-management.Recommendations.SHOULD-length] Body is 481 lines (~2.4× the ~200-line soft target), with the entire document template + CSV examples + quality rules inlined.
      Where: `.claude/agents/plant-info-document-generator.md:121-462` (document template + CSV examples).
      Fix: factor the document template, CSV import examples, and the quality-rules block into `agents/plant-info-document-generator/` siblings referenced by relative path; keep the body to procedural guidance.
      Verify: body line count drops below ~200 after factoring.

- [ ] [skill-vs-agent.Duplicate-prevention.MUST] Agent is the upstream stage of a 2-step pipeline with `plant-info-to-seed-yaml` (generation → conversion) — no overlap, but the description does not name the downstream sibling, so callers may stop after this stage.
      Where: `.claude/agents/plant-info-document-generator.md:4`.
      Fix: extend description with negative-trigger phrasing pointing at `plant-info-to-seed-yaml` ("for YAML seed conversion, dispatch `plant-info-to-seed-yaml` after this agent finishes").
      Verify: description names the pipeline successor explicitly.

- [ ] [agent-management.Recommendations.SHOULD-negative-triggers] Description has only positive triggers; with overlap risk against `knowledge-chunk-author` (both produce plant content from specs/research) and `plant-info-to-seed-yaml` (downstream YAML), explicit negatives would help routing.
      Where: `.claude/agents/plant-info-document-generator.md:4`.
      Fix: add "don't use for RAG-chunk authoring (use `knowledge-chunk-author`); don't use for YAML seed conversion (use `plant-info-to-seed-yaml`)".
      Verify: description contains explicit negative-trigger phrasing.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary.MAY] Agent has no `tags` frontmatter field; tagging it (e.g. `[knowledge, scaffolding]`) would cluster it with peers in the catalog.
      Where: `.claude/agents/plant-info-document-generator.md:1-8`.
      Fix: add `tags: [knowledge, scaffolding]` (each ≤30 chars, list ≤5).
      Verify: frontmatter parses with valid `tags`.

### INFO

- [ ] [agent-review.Checks-derived-from-skill-vs-agent.MUST-no-skill-dispatch] No `Skill(`, `Skill tool`, or `Skill <name>` invocations were found in the body — dispatch direction is clean.
      Where: full body grep clean.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.Tool-access.MUST] Tools declared (`Read, Write, Glob, Grep, WebSearch, WebFetch`) all map to documented procedure steps (read specs, web research, write docs) — bidirectional check passes on spot-check.
      Where: `.claude/agents/plant-info-document-generator.md:5`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
