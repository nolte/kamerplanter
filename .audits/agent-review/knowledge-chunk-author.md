---
review-type: agent-review
target: ".claude/agents/knowledge-chunk-author.md"
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

# Agent Review: knowledge-chunk-author

## Scope

Target: `.claude/agents/knowledge-chunk-author.md` (frontmatter + 284-line body, no sibling assets under `agents/knowledge-chunk-author/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review.
Explicitly out of scope: runtime behavior (does the agent actually produce chunks that pass the eval?), Vale/markdown style, the orchestrating workflow beyond the dispatch direction from `rag-eval-runner`.

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body language and missing rationale block dispatch readiness.
Next concrete action: author rewrites system prompt in English and adds a rationale section pointing at the decisive skill-vs-agent dimensions.

## Findings

### BLOCKER

- [ ] [agent-management.Structure.MUST-english] Agent body is authored in German, including heading text ("Quellen-Hierarchie", "Phase 1: Aufgabe verstehen", "Ausfuehrungsrichtlinien") and every numbered procedure step.
      Where: `.claude/agents/knowledge-chunk-author.md:16-284`.
      Fix: rewrite the system prompt in English; the agent may still be instructed to produce German chunks (project convention), but the prompt scaffolding itself must be English per `agent-management` MUST.
      Verify: `rg -n '[äöüÄÖÜß]' .claude/agents/knowledge-chunk-author.md` returns no hits outside quoted German example data and the description block.

- [ ] [skill-vs-agent.Rationale-documentation.MUST] The body has no rationale section that names a decisive dimension for the agent-over-skill choice.
      Where: `.claude/agents/knowledge-chunk-author.md` (entire body, no rationale block detected).
      Fix: add a short rationale section (one paragraph or 2–4 bullets) that names at least one decisive dimension — likely "specialization" (narrow knowledge-engineer system prompt) and "context-window protection" (heavy reads of `spec/req/`, `spec/nfr/`, `spec/rag-eval/**`).
      Verify: a paragraph or bulleted list explicitly stating the skill-vs-agent dimensions exists in the body.

- [ ] [agent-management.Recommendations.SHOULD-writes-vs-research] The system prompt does not state explicitly whether the agent writes files or only researches, even though `tools` includes `Write` and `Edit`.
      Where: `.claude/agents/knowledge-chunk-author.md:1-16` (frontmatter + opening role statement).
      Fix: add one explicit sentence near the top stating "this agent writes/edits YAML files under `spec/knowledge/rag/` and `spec/rag-eval/topic_synonyms.yaml`"; see Phase 4.1b which writes patterns.
      Verify: the role section names the side effects and the target paths.

### WARNING

- [ ] [skill-vs-agent.Duplicate-prevention.MUST] Agent overlaps in capability scope with the `gen-knowledge` skill (both produce RAG YAML chunks under `spec/knowledge/rag/`).
      Where: `.claude/agents/knowledge-chunk-author.md:4-10` description vs the project's `gen-knowledge` skill.
      Fix: clarify the split in the description — e.g. "agent fixes targeted gaps from eval reports; skill bulk-generates new RAG categories" — or merge one into the other.
      Verify: descriptions of both artifacts read as non-overlapping after the change.

- [ ] [skill-vs-agent.Rationale-documentation.SHOULD] No counter-dimension is named (e.g. interactivity is real here — chunks may need user approval before merge).
      Where: same rationale-section gap as the BLOCKER above.
      Fix: when adding the rationale, also name one dimension that pointed toward "skill" and why it was outweighed.
      Verify: the rationale paragraph mentions both decisive and counter dimensions.

- [ ] [agent-management.Recommendations.SHOULD-length] Body is 284 lines, exceeding the soft ~200-line limit, and supporting material (decision tree for chunk-vs-extend, full enum/conversion tables) is not factored into `agents/knowledge-chunk-author/` siblings.
      Where: `.claude/agents/knowledge-chunk-author.md:111-237` (Phase-3/4 long tables + flowcharts).
      Fix: move the conversion tables, validation flowcharts and topic-synonym example into `agents/knowledge-chunk-author/` reference files referenced by relative path.
      Verify: body line count drops below ~200 after factoring.

- [ ] [agent-review.Tool-scope.SHOULD-bash-vs-dedicated] The procedure uses `grep`-via-Bash phrasing (Phase 1.4, Phase 4.3) but the declared tools include `Grep` directly; either declare and use the dedicated tool or justify Bash.
      Where: `.claude/agents/knowledge-chunk-author.md:69-72,225-229`.
      Fix: rewrite the "Grep in `spec/knowledge/rag/...`" steps to call out the `Grep` tool name explicitly so the procedure matches declared tool affordances.
      Verify: every "grep" instruction in the body maps onto the declared `Grep` tool, not Bash.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary.MAY] Agent has no `tags` frontmatter field; adding one (e.g. `[knowledge, rag, audit]`) would make the catalog peer-cluster with `gen-knowledge`.
      Where: `.claude/agents/knowledge-chunk-author.md:1-14`.
      Fix: add `tags: [knowledge, rag, audit]` (each ≤30 chars, list ≤5) so the duplicate-prevention check has a machine-readable cluster signal.
      Verify: frontmatter parses with valid `tags` and the catalog (if rendered) groups it next to RAG peers.

### INFO

- [ ] [agent-management.Tool-access.MUST] Tools declared (`Read, Write, Edit, Glob, Grep`) match the body's procedure (read specs, write/edit YAML, grep for duplicates) — both directions look consistent on a spot-check.
      Where: `.claude/agents/knowledge-chunk-author.md:11`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-review.Checks-derived-from-skill-vs-agent.MUST-no-skill-dispatch] No `Skill(`, `Skill tool`, or `Skill <name>` invocations were found in the body — the dispatch direction is correct (agent doesn't call skills).
      Where: full body grep clean.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
