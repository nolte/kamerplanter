---
review-type: agent-review
target: ".claude/agents/tech-stack-architect.md"
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

# Agent Review: tech-stack-architect

## Scope

Target: `.claude/agents/tech-stack-architect.md` (frontmatter + body; no sibling assets exist under `.claude/agents/tech-stack-architect/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review per `agent-review` Phase 1–4.
Explicitly out of scope: runtime behavior, Vale/markdown style, the actual content of `spec/stack.md` (target is the agent file, not what it would produce).

## Summary

- BLOCKER: 3
- WARNING: 5
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — read-only-agent rule violation on `Write`, German body, and missing skill-vs-agent rationale block acceptance.
Next concrete action: resolve the `Write`-tool conflict, translate the body to English, add a skill-vs-agent rationale section.

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write] The agent is described as a reviewer/auditor ("prüft… identifiziert Lücken, Widersprüche, Überarchitektur") — a read-only role per `agent-review` Review-procedure — yet declares `Write` in `tools` to emit `spec/analysis/tech-stack-review.md`; the spec marks the presence of `Write` in a read-only agent's `tools` list as a `BLOCKER`.
      Where: `.claude/agents/tech-stack-architect.md:4` (read-only description) vs. line 5 (`tools: Read, Write, Glob, Grep, WebSearch, WebFetch`).
      Fix: pick one of two paths and document it: (a) drop `Write` and have the agent emit the structured tech-stack report inline so the parent conversation persists it, matching the read-only contract; or (b) keep `Write` and revise the description to characterize the agent as a *report-producing* architecture analyst (e.g., "Verfasst Tech-Stack-Bewertungsbericht…") so the read-only classification no longer applies — and add an English note in the body explaining why `Write` is needed.
      Verify: either `Write` is absent from `tools`, or the description and body explicitly classify the agent as report-producing with the `Write` target documented.

- [ ] [agent-management.structure-language] Frontmatter `description` and the entire system-prompt body are written in German, contradicting the MUST that frontmatter and system-prompt content stay in English.
      Where: `.claude/agents/tech-stack-architect.md:4` (description) and lines 10–390 (body).
      Fix: translate description and body to English; preserve any "produce report in German" instruction as a single explicit English sentence.
      Verify: `rg -P '[äöüÄÖÜß]' .claude/agents/tech-stack-architect.md` returns no matches in frontmatter or the body's English narrative.

- [ ] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/tech-stack-architect.md` (no rationale section).
      Fix: add a rationale section naming at least one decisive dimension (for example: context-window protection during full `spec/req`+`spec/nfr`+`spec/ui-nfr`+`spec/stack.md` traversal, parallelism alongside other architecture reviewers, narrow read-only tool surface for spec audit) and at least one counter-dimension.
      Verify: a marked rationale section explicitly references one of the seven `skill-vs-agent` decision dimensions.

### WARNING

- [ ] [agent-management.structure-prompt-order] The system prompt does not open with role/boundaries followed by the expected output format and only then the working method; the report shape from Phase 6 (line 240) appears after Phases 1–5 of the working method (lines 28–235).
      Where: `.claude/agents/tech-stack-architect.md:10–390`.
      Fix: reorder so role/boundaries come first, then the Phase 6 report scaffold, then Phases 1–5 procedure.
      Verify: the first 80 lines of the body include the role block followed by the report-shape block.

- [ ] [agent-management.writes-or-researches] The system prompt does not explicitly state whether the agent writes code or only researches; with `Write` declared, an explicit "this agent only produces an analysis report; it never edits stack.md, REQ/NFR specs, or source code in place" sentence is needed per the SHOULD.
      Where: `.claude/agents/tech-stack-architect.md:10–25` (role section).
      Fix: add one explicit English sentence stating "This agent only produces an analysis report under `spec/analysis/`; it never modifies `spec/stack.md`, REQ/NFR specs, or source code."
      Verify: the role section contains a one-liner that names the writes-vs-research stance.

- [ ] [agent-management.body-length-200] Body length is approximately 390 lines, well above the soft 200-line target; the per-phase tables, the cross-cutting checklist, and the report template are not factored into `agents/tech-stack-architect/` sibling files.
      Where: `.claude/agents/tech-stack-architect.md` (390 total lines).
      Fix: move the Phase-2 evaluation matrix, the Phase-4.2 cross-cutting checklist, and the Phase-6 report template into sibling files under `agents/tech-stack-architect/`; reference them by relative path.
      Verify: `wc -l .claude/agents/tech-stack-architect.md` reports ≤ 200 lines.

- [ ] [agent-management.write-target-documentation] `Write` is declared but the body does not state the goal and preconditions of the write effect (target path, overwrite vs. append on rerun, what happens if `spec/analysis/` does not exist) per the SHOULD.
      Where: `.claude/agents/tech-stack-architect.md:5` (Write declared) and line 240 (only mention: "Erstelle …").
      Fix: add a short "Write target" block naming the absolute output path (`spec/analysis/tech-stack-review.md`), the overwrite behavior on rerun, and the precondition for directory existence.
      Verify: the body contains a "Write target" or equivalent block that documents path, overwrite policy, and preconditions.

- [ ] [skill-vs-agent.duplicate-prevention] Capability overlaps with the `requirements-contradiction-analyzer` agent — both detect contradictions across REQ/NFR documents (this agent's Phase 4.3 explicitly produces a contradiction table), raising a duplicate-capability flag.
      Where: `.claude/agents/tech-stack-architect.md:4, 192–199` (Phase 4.3 contradictions) vs. the `requirements-contradiction-analyzer` peer agent.
      Fix: either narrow this agent's scope to stack-vs-requirement contradictions only (and have it dispatch `requirements-contradiction-analyzer` for REQ-vs-REQ contradictions), or document the overlap in a "boundary with peer agents" subsection.
      Verify: a side-by-side `description` comparison shows the two agents' contradiction-finding scopes are non-overlapping or the overlap is explicitly explained.

### SUGGESTION

- [ ] [agent-management.description-negative-triggers] The `description` enumerates positive triggers but lists no negative cases against peer agents (`requirements-contradiction-analyzer`, `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer` all read REQ/NFR documents); explicit negatives reduce mis-dispatch.
      Where: `.claude/agents/tech-stack-architect.md:4`.
      Fix: append "don't use for…" clauses in the translated description naming each peer that operates on the same source surface.
      Verify: the `description` contains at least one explicit negative-trigger phrase per overlapping peer.

### INFO

- [ ] [agent-management.distribution] `distribution: project` is declared and the file lives at `.claude/agents/` — consistent.
      Where: `.claude/agents/tech-stack-architect.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] `model: opus` is pinned with an inline rationale (architecture decisions across all REQ/NFR/UI-NFR, high follow-cost / migration risk); the rationale is defensible for a deep cross-spec audit, although the read-only nature would make `sonnet` a viable alternative for cost — acceptable as authored.
      Where: `.claude/agents/tech-stack-architect.md:6–7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
