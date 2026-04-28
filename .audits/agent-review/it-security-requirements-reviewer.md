---
review-type: agent-review
target: ".claude/agents/it-security-requirements-reviewer.md"
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

# Agent Review: it-security-requirements-reviewer

## Scope

Target: `.claude/agents/it-security-requirements-reviewer.md` (frontmatter + body; no sibling assets exist under `.claude/agents/it-security-requirements-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review per `agent-review` Phase 1–4.
Explicitly out of scope: runtime behavior, Vale/markdown style, the `code-security-reviewer` peer agent (referenced for delineation only).

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — read-only-agent rule violation, German body, and missing skill-vs-agent rationale block acceptance.
Next concrete action: resolve the `Write`-tool conflict (either drop `Write` and emit the report through the parent conversation, or restate the agent as report-producing rather than read-only and document the deviation), translate body to English, add rationale.

## Findings

### BLOCKER

- [x] [agent-review.read-only-no-write] The agent is described as a reviewer ("Prüft Anforderungsdokumente") — a read-only role per `agent-review` Review-procedure — yet declares `Write` in `tools` to emit `spec/analysis/it-security-review.md`; the spec marks the presence of `Write` in a read-only agent's `tools` list as a `BLOCKER`.
      Where: `.claude/agents/it-security-requirements-reviewer.md:4` (read-only description) vs. line 5 (`tools: Read, Write, Glob, Grep`).
      Fix: pick one of two paths and document it: (a) drop `Write` and have the agent emit the structured report inline so the parent conversation persists it, matching the read-only contract; or (b) keep `Write` and revise the description to characterize the agent as a *report-producing* security analyst (not "Prüft" but "Verfasst Sicherheitsbewertungsbericht…") so the read-only classification no longer applies — and add an English note in the body explaining why `Write` is needed.
      Verify: either `Write` is absent from `tools`, or the description and body explicitly classify the agent as report-producing with the `Write` target documented.

- [ ] [agent-management.structure-language] Frontmatter `description` and the entire system-prompt body are written in German, contradicting the MUST that frontmatter and system-prompt content stay in English.
      Where: `.claude/agents/it-security-requirements-reviewer.md:4` (description) and lines 10–390 (body).
      Fix: translate description and body to English; preserve any "produce report in German" instruction as a single explicit English sentence.
      Verify: `rg -P '[äöüÄÖÜß]' .claude/agents/it-security-requirements-reviewer.md` returns no matches in frontmatter or the body's English narrative.

- [ ] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/it-security-requirements-reviewer.md` (no rationale section).
      Fix: add a rationale section naming at least one decisive dimension (for example: context-window protection during full `spec/req`+`spec/nfr` traversal, parallelism alongside other reviewers, narrow tool surface for read-only audit) and at least one counter-dimension.
      Verify: a marked rationale section explicitly references one of the seven `skill-vs-agent` decision dimensions.

### WARNING

- [ ] [agent-management.structure-prompt-order] The system prompt does not open with role/boundaries followed by the expected output format and only then the working method; the report shape from Phase 3 (line 268) appears after the full audit checklist in Phase 2 (lines 55–266).
      Where: `.claude/agents/it-security-requirements-reviewer.md:10–390`.
      Fix: reorder so role/boundaries come first, then the Phase 3 report scaffold, then Phase 1–2 working method.
      Verify: the first 70 lines of the body include the role block followed by the report-shape block.

- [ ] [agent-management.writes-or-researches] The system prompt does not explicitly state whether the agent writes code or only researches; with `Write` declared, an explicit "this agent only produces an analysis report; it never edits source code or specs in place" sentence is needed per the SHOULD.
      Where: `.claude/agents/it-security-requirements-reviewer.md:10–34` (role section).
      Fix: add one explicit English sentence stating "This agent only produces an analysis report under `spec/analysis/`; it never modifies REQ/NFR specs, source code, or seed data."
      Verify: the role section contains a one-liner that names the writes-vs-research stance.

- [ ] [agent-management.body-length-200] Body length is approximately 390 lines, almost twice the soft 200-line target; the OWASP/DSGVO/RAG checklists and the report template are not factored into `agents/it-security-requirements-reviewer/` sibling files.
      Where: `.claude/agents/it-security-requirements-reviewer.md` (390 total lines).
      Fix: move the per-category checklists (2.1–2.8) and the Phase 3 report template into sibling files under `agents/it-security-requirements-reviewer/`; reference them by relative path.
      Verify: `wc -l .claude/agents/it-security-requirements-reviewer.md` reports ≤ 200 lines.

- [ ] [agent-management.write-target-documentation] `Write` is declared but the body does not state the goal and preconditions of the write effect (target path, overwrite vs. append, idempotency, what happens on rerun) per the SHOULD.
      Where: `.claude/agents/it-security-requirements-reviewer.md:5` (Write declared) and line 268 (only mention: "Erstelle …").
      Fix: add a short "Write target" subsection naming the absolute output path (`spec/analysis/it-security-review.md`), the overwrite behavior on rerun, and the precondition that the path exists or will be created.
      Verify: the body contains a "Write target" or equivalent block that documents path, overwrite policy, and preconditions.

### SUGGESTION

- [ ] [agent-management.description-negative-triggers] The agent's `description` lists positive triggers but does not name `code-security-reviewer` as the negative-trigger peer (that one reviews code, this one reviews specs); body line 10 makes the distinction clear, but the dispatch decision happens against the description alone.
      Where: `.claude/agents/it-security-requirements-reviewer.md:4` (description) vs. the peer `code-security-reviewer` agent.
      Fix: append a "don't use for…" clause in the description (after translation): "Don't use for reviewing implemented code — that's `code-security-reviewer`."
      Verify: the `description` field contains at least one explicit negative-trigger phrase referencing the peer.

### INFO

- [ ] [agent-management.distribution] `distribution: project` is declared and the file lives at `.claude/agents/` — consistent.
      Where: `.claude/agents/it-security-requirements-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] `model: opus` is pinned with an inline rationale (DSGVO/auth/crypto depth, compliance consequences); the rationale is defensible for a deep spec audit.
      Where: `.claude/agents/it-security-requirements-reviewer.md:6–7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-28 — agent-review.read-only-no-write — rewrite description to author-shape (Verfasst…Bewertungsbericht); agent is no longer a read-only reviewer — verified: re-read agent file, finding condition no longer holds
