---
review-type: agent-review
target: ".claude/agents/it-security-requirements-reviewer.md"
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
supersedes: "previous iteration of this plan (status: in-progress) — see git history of this file"
---

# Agent Review: it-security-requirements-reviewer

## Scope

Target: `.claude/agents/it-security-requirements-reviewer.md` (frontmatter + body; no sibling assets exist under `.claude/agents/it-security-requirements-reviewer/`).
Specs applied: `agent-management` (rev `7772341`), `skill-vs-agent` (rev `0e3b6f9`), `review-plan` (rev `0e3b6f9`), `agent-review` (rev `7772341`).
Narrowing: none — full review per `agent-review` Phase 1–4.
Iteration: 2. The first iteration ran against spec revision `0e3b6f9`. Two changes since then are load-bearing: (1) `agent-management.Structure` at revision `7772341` permits German prose for `distribution: project` agents in projects that authorize it; Kamerplanter's `CLAUDE.md` lines 9–11 provides that authorization, so the iteration-1 `BLOCKER` for German body+description is downgraded to `INFO` here. (2) The agent's `description` was rewritten from "Prüft Anforderungsdokumente" to "Verfasst einen strukturierten IT-Security-Bewertungsbericht…" — under `agent-review.Checks-derived-from-agent-management` the read-only-agent classification is detected from the description verbs (review/audit/research/lint/report); "verfasst" is an authoring verb, so this agent is no longer classified read-only and `Write` in `tools` is consistent with the new role. The iteration-1 `BLOCKER` "read-only-no-write" is therefore closed by description rewording. Frontmatter field names and technical identifier values remain English.
Explicitly out of scope: runtime behavior, Vale/markdown style, the `code-security-reviewer` peer agent (referenced for delineation only).

## Summary

- BLOCKER: 1
- WARNING: 4
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — the missing skill-vs-agent rationale section still blocks acceptance.
Next concrete action: add a rationale section that names at least one decisive `skill-vs-agent` dimension; address the prompt-order, body-length, writes-vs-research, and write-target WARNINGs.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/it-security-requirements-reviewer.md` (no rationale section).
      Fix: add a rationale section naming at least one decisive dimension (for example: context-window protection during full `spec/req`+`spec/nfr`+`spec/ui-nfr` traversal, parallelism alongside other reviewers, narrow tool surface for spec audit + report writing) and at least one counter-dimension.
      Verify: a marked rationale section explicitly references one of the seven `skill-vs-agent` decision dimensions.

### WARNING

- [ ] [agent-management.structure-prompt-order] The system prompt does not open with role/boundaries followed by the expected output format and only then the working method; the report shape from Phase 3 (line 268) appears after the full audit checklist in Phase 2 (lines 55–266).
      Where: `.claude/agents/it-security-requirements-reviewer.md:10–390`.
      Fix: reorder so role/boundaries come first, then the Phase 3 report scaffold, then Phase 1–2 working method.
      Verify: the first 70 lines of the body include the role block followed by the report-shape block.

- [ ] [agent-management.writes-or-researches] The system prompt does not explicitly state whether the agent writes code or only researches; with `Write` declared and the description framed as "verfasst einen Bewertungsbericht", an explicit "this agent only produces an analysis report; it never edits source code, REQ/NFR specs, or seed data in place" sentence is needed per the SHOULD.
      Where: `.claude/agents/it-security-requirements-reviewer.md:10–34` (role section).
      Fix: add one explicit sentence stating "Dieser Agent erzeugt ausschliesslich einen Analysebericht unter `spec/analysis/`; er aendert keine REQ/NFR-Specs, keinen Source-Code und keine Seed-Daten."
      Verify: the role section contains a one-liner that names the writes-vs-research stance.

- [ ] [agent-management.body-length-200] Body length is approximately 390 lines, almost twice the soft 200-line target; the OWASP/DSGVO/RAG checklists and the report template are not factored into `agents/it-security-requirements-reviewer/` sibling files.
      Where: `.claude/agents/it-security-requirements-reviewer.md` (390 total lines).
      Fix: move the per-category checklists (Phase 2.1–2.8) and the Phase 3 report template into sibling files under `agents/it-security-requirements-reviewer/`; reference them by relative path.
      Verify: `wc -l .claude/agents/it-security-requirements-reviewer.md` reports ≤ 200 lines.

- [ ] [agent-management.write-target-documentation] `Write` is declared but the body does not state the goal and preconditions of the write effect (target path, overwrite vs. append on rerun, what happens if `spec/analysis/` does not yet exist) per the SHOULD.
      Where: `.claude/agents/it-security-requirements-reviewer.md:5` (Write declared) and line 270 (only mention: "Erstelle `spec/analysis/it-security-review.md`").
      Fix: add a "Write target" subsection naming the absolute output path (`spec/analysis/it-security-review.md`), the overwrite behavior on rerun (single canonical report; rerun replaces it), and the precondition that the path is created if missing.
      Verify: the body contains a "Write target" or equivalent block that documents path, overwrite policy, and preconditions.

### SUGGESTION

- [ ] [agent-management.description-negative-triggers] The agent's `description` lists positive triggers but does not name `code-security-reviewer` as the negative-trigger peer (that one reviews implemented code, this one reviews specs); the dispatch decision happens against the description alone.
      Where: `.claude/agents/it-security-requirements-reviewer.md:4` (description) vs. the peer `code-security-reviewer` agent.
      Fix: append a "nicht verwenden für…" clause in the description: "Nicht verwenden für die Pruefung von implementiertem Code — dafuer `code-security-reviewer`."
      Verify: the `description` field contains at least one explicit negative-trigger phrase referencing the peer.

### INFO

- [ ] [agent-management.structure-language] Frontmatter `description` and the system-prompt body are authored in German. Per the relaxed `agent-management.Structure` clause (revision `7772341`) and Kamerplanter's project-language authorization in `CLAUDE.md` lines 9–11, German prose is permitted for this `distribution: project` agent. Iteration 1 flagged this as a `BLOCKER`; under the current spec revision the finding is reclassified as a neutral observation.
      Where: `.claude/agents/it-security-requirements-reviewer.md:4` (description) and lines 10–390 (body).
      Fix: n/a (observation; project authorization in place).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is declared and the file lives at `.claude/agents/` — consistent.
      Where: `.claude/agents/it-security-requirements-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] `model: opus` is pinned with an inline rationale (DSGVO/auth/crypto depth, compliance consequences); the rationale is defensible for a deep spec audit producing a structured report.
      Where: `.claude/agents/it-security-requirements-reviewer.md:6–7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
