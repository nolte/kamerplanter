---
review-type: agent-review
target: ".claude/agents/knowledge-chunk-author.md"
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

# Agent Review: knowledge-chunk-author

## Scope

Target: `.claude/agents/knowledge-chunk-author.md` (frontmatter + 284-line body, no sibling assets under `agents/knowledge-chunk-author/`).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent` (rev 0e3b6f9), `review-plan` (rev 0e3b6f9), `agent-review` (rev 7772341).
Narrowing: none — full re-review (Iteration 2). The `agent-management` SHOULD on description/body language has been relaxed for `distribution: project` agents in projects with non-English documentation language and explicit authorization. Kamerplanter `CLAUDE.md` lines 9-11 grant that authorization, so German prose drops from BLOCKER to INFO.
Explicitly out of scope: runtime behavior, Vale/markdown style, the orchestrating workflow beyond the dispatch direction from `rag-eval-runner`, and the duplicate-prevention check against the `gen-knowledge` skill (peer artifact under `nolte-shared/skills/`).

## Summary

- BLOCKER: 1
- WARNING: 3
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — one BLOCKER (rationale section) remains.
Next concrete action: author adds a rationale section naming at least one decisive skill-vs-agent dimension; address WARNINGs on duplicate, model rationale, and side-effect documentation.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.Rationale-documentation] No rationale section names a decisive skill-vs-agent dimension for the agent-over-skill choice.
      Where: `.claude/agents/knowledge-chunk-author.md` body (Phase 1 through "Ausfuehrungsrichtlinien").
      Fix: Add a short "Skill-vs-Agent-Begruendung" section (one paragraph or 2-4 bullets) naming dimensions like context-window protection (large knowledge-base reads), specialization (narrow domain prompt), or tool restriction.
      Verify: `grep -i 'rationale\|begruendung\|skill-vs-agent\|warum agent'` returns at least one match in the body.

### WARNING

- [ ] [skill-vs-agent.Duplicate-prevention] Plausible capability overlap with the `nolte-shared/skills/gen-knowledge` skill — both author RAG knowledge-base YAML chunks.
      Where: frontmatter `description` lines 4-10 vs. the `gen-knowledge` skill description.
      Fix: Document the split in the body (e.g. project-specific topic-synonym validation and benchmark-question alignment vs. generic chunk authoring), or propose a merge/rename in a follow-up PR.
      Verify: Body contains a paragraph naming `gen-knowledge` and the boundary; or a follow-up PR link is recorded.

- [ ] [agent-management.Model-selection-justification] Pinned `model: sonnet` carries only a one-line inline frontmatter comment; the system-prompt body never restates the rationale.
      Where: frontmatter line 12 (comment) — body has no model-rationale paragraph.
      Fix: Move/expand the rationale into the body (e.g. under "Ausfuehrungsrichtlinien"): "sonnet because chunk authoring needs nuanced spec-to-prose translation while staying cost-aware".
      Verify: `grep -i 'sonnet\|modell' .claude/agents/knowledge-chunk-author.md` returns a body-level mention beyond the YAML comment.

- [ ] [agent-management.Side-effects-documentation] `tools` declares `Write` and `Edit` but the system prompt never names the goals and preconditions of those side effects in a dedicated section.
      Where: frontmatter line 11 (tools) — body lacks an explicit "writes/edits" boundary statement.
      Fix: Add a short "Schreibrechte" subsection naming the targets (`spec/knowledge/rag/**/*.yaml`, `spec/rag-eval/topic_synonyms.yaml`) and preconditions (Pattern-Match-Validierung passed, Duplikat-Check completed).
      Verify: Body contains an explicit statement of write targets and preconditions.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary] No `tags` field in frontmatter; cluster membership for the catalog and peer-cluster lookups is therefore not machine-checkable.
      Where: frontmatter (no `tags` key).
      Fix: Add `tags: [knowledge, rag]` (or similar from the starter vocabulary) to align with peer artifacts in the RAG cluster.
      Verify: Frontmatter parses with a `tags` list of <=5 lowercase ASCII kebab-case entries.

### INFO

- [ ] [agent-management.Structure-language] Description and body authored in German.
      Where: frontmatter `description` lines 4-10 + entire body.
      Fix: n/a — Kamerplanter `CLAUDE.md` lines 9-11 authorize German for `distribution: project` agent prose under the project-language exception in `agent-management.Structure`.
      Verify: n/a (informational).

- [ ] [agent-review.Review-procedure] Iteration 2 re-review applies the relaxed language SHOULD; previous BLOCKER on description+body language drops to INFO based on the project-language exception.
      Where: this plan's `## Scope`.
      Fix: n/a (procedural note for downstream readers).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
