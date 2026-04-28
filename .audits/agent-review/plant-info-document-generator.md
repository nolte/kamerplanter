---
review-type: agent-review
target: ".claude/agents/plant-info-document-generator.md"
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

# Agent Review: plant-info-document-generator

## Scope

Target: `.claude/agents/plant-info-document-generator.md` (frontmatter + 481-line body, no sibling assets under `agents/plant-info-document-generator/`).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent` (rev 0e3b6f9), `review-plan` (rev 0e3b6f9), `agent-review` (rev 7772341).
Narrowing: none — full re-review (Iteration 2). The relaxed language SHOULD applies; Kamerplanter `CLAUDE.md` lines 9-11 authorize German body+description, so language drops from BLOCKER to INFO. The agent forms a pipeline with `plant-info-to-seed-yaml` (no overlap, complementary).
Explicitly out of scope: runtime behavior of WebSearch/WebFetch, Vale/markdown style, factual accuracy of the generated plant documents.

## Summary

- BLOCKER: 1
- WARNING: 3
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — one BLOCKER (rationale section) remains.
Next concrete action: author adds a skill-vs-agent rationale section and addresses model-rationale + side-effect-documentation WARNINGs.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.Rationale-documentation] No rationale section names a decisive skill-vs-agent dimension for the agent-over-skill choice.
      Where: `.claude/agents/plant-info-document-generator.md` body (no "Begruendung"/"Rationale" section).
      Fix: Add a short "Skill-vs-Agent-Begruendung" section naming the decisive dimensions (e.g. context-window protection for heavy WebSearch/WebFetch traffic, parallelism for batch plant generation, specialization for botanical research).
      Verify: `grep -i 'rationale\|begruendung\|skill-vs-agent'` returns at least one body-level match.

### WARNING

- [ ] [agent-management.Model-selection-justification] Pinned `model: sonnet` carries only a one-line frontmatter comment; the body never repeats the rationale.
      Where: frontmatter line 6 (comment) — body has no model-rationale paragraph.
      Fix: Add a body-level model-rationale (e.g. under "Qualitaetsregeln"): "sonnet for botanical research with structured markdown output; haiku would underfit cross-source synthesis".
      Verify: `grep -i 'sonnet\|modell' .claude/agents/plant-info-document-generator.md` returns a body-level mention.

- [ ] [agent-management.Side-effects-documentation] `tools` declares `Write` and the body names the target path (`spec/knowledge/plants/<scientific_name_snake_case>.md`), but no dedicated subsection states the overwrite policy and preconditions.
      Where: frontmatter line 5 — body Phase 3 names the path informally.
      Fix: Add a "Schreibrechte" subsection: target glob `spec/knowledge/plants/*.md`, overwrite policy (overwrite if exists), preconditions (taxonomy resolved, sources cross-checked).
      Verify: Body contains an explicit write-targets section.

- [ ] [agent-management.Tools-bash-preference] `WebSearch` and `WebFetch` are declared as deferred MCP-style tools; the agent procedure relies heavily on them but never disambiguates them from `Read` for local files vs. external research.
      Where: frontmatter line 5 — body Phase 2 lists "WebSearch nach: ..." but never the read/web split.
      Fix: Note in the body that `Read` covers local specs and `spec/knowledge/`, while `WebSearch`/`WebFetch` cover external sources (RHS, USDA, university extension services).
      Verify: Body contains a one-paragraph tool-split rationale.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary] No `tags` field; the catalog cannot place this agent in the plant-knowledge cluster with `plant-info-to-seed-yaml`.
      Where: frontmatter (no `tags` key).
      Fix: Add `tags: [scaffolding, prose]` or a project-specific tag like `plant-info` shared with `plant-info-to-seed-yaml`.
      Verify: Frontmatter parses with a `tags` list of <=5 entries.

### INFO

- [ ] [agent-management.Structure-language] Description and body authored in German.
      Where: frontmatter `description` line 4 + entire body.
      Fix: n/a — Kamerplanter `CLAUDE.md` lines 9-11 authorize German prose for `distribution: project` agents.
      Verify: n/a.

- [ ] [agent-review.Review-procedure] Iteration 2 re-review applies the relaxed language SHOULD; previous language BLOCKER drops to INFO. The pipeline relationship with `plant-info-to-seed-yaml` is complementary, not duplicative.
      Where: this plan's `## Scope`.
      Fix: n/a (procedural note).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
