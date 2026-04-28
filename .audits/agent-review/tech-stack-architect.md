---
review-type: agent-review
target: ".claude/agents/tech-stack-architect.md"
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

# Agent Review: tech-stack-architect

## Scope

Target: `.claude/agents/tech-stack-architect.md` (frontmatter + body; no sibling assets exist under `.claude/agents/tech-stack-architect/`).
Specs applied: `agent-management` (rev `7772341`), `skill-vs-agent` (rev `0e3b6f9`), `review-plan` (rev `0e3b6f9`), `agent-review` (rev `7772341`).
Narrowing: none — full review per `agent-review` Phase 1–4.
Iteration: 2. The first iteration ran against spec revision `0e3b6f9`. Two changes since then are load-bearing: (1) `agent-management.Structure` at revision `7772341` permits German prose for `distribution: project` agents in projects that authorize it; Kamerplanter's `CLAUDE.md` lines 9–11 provides that authorization, so the iteration-1 `BLOCKER` for German body+description is downgraded to `INFO` here. (2) The agent's `description` was rewritten from a reviewer/auditor framing ("prüft… identifiziert Lücken") to "Verfasst einen strukturierten Tech-Stack-Bewertungsbericht…" — under `agent-review.Checks-derived-from-agent-management` the read-only-agent classification is detected from the description verbs; "verfasst" is an authoring verb, so this agent is no longer classified read-only and `Write` in `tools` is consistent with the new role. The iteration-1 `BLOCKER` "read-only-no-write" is therefore closed by description rewording. Frontmatter field names and technical identifier values remain English.
Explicitly out of scope: runtime behavior, Vale/markdown style, the actual content of `spec/stack.md` (target is the agent file, not what it would produce).

## Summary

- BLOCKER: 1
- WARNING: 5
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — the missing skill-vs-agent rationale section still blocks acceptance.
Next concrete action: add a rationale section that names at least one decisive `skill-vs-agent` dimension; address the prompt-order, body-length, writes-vs-research, write-target, and duplicate-prevention WARNINGs.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/tech-stack-architect.md` (no rationale section).
      Fix: add a rationale section naming at least one decisive dimension (for example: context-window protection during full `spec/req`+`spec/nfr`+`spec/ui-nfr`+`spec/stack.md` traversal, parallelism alongside other architecture reviewers, specialization via architect-only system prompt covering polyglot persistence and cloud-native patterns) and at least one counter-dimension.
      Verify: a marked rationale section explicitly references one of the seven `skill-vs-agent` decision dimensions.

### WARNING

- [ ] [agent-management.structure-prompt-order] The system prompt does not open with role/boundaries followed by the expected output format and only then the working method; the report shape from Phase 6 (line 240) appears after Phases 1–5 of the working method (lines 28–235).
      Where: `.claude/agents/tech-stack-architect.md:10–390`.
      Fix: reorder so role/boundaries come first, then the Phase 6 report scaffold, then Phases 1–5 procedure.
      Verify: the first 80 lines of the body include the role block followed by the report-shape block.

- [ ] [agent-management.writes-or-researches] The system prompt does not explicitly state whether the agent writes code or only researches; with `Write` declared and the description framed as "verfasst einen Bewertungsbericht", an explicit "this agent only produces an analysis report; it never edits stack.md, REQ/NFR specs, or source code in place" sentence is needed per the SHOULD.
      Where: `.claude/agents/tech-stack-architect.md:10–25` (role section).
      Fix: add one explicit sentence stating "Dieser Agent erzeugt ausschliesslich einen Analysebericht unter `spec/analysis/`; er aendert weder `spec/stack.md` noch REQ/NFR-Specs noch Source-Code in place."
      Verify: the role section contains a one-liner that names the writes-vs-research stance.

- [ ] [agent-management.body-length-200] Body length is approximately 390 lines, well above the soft 200-line target; the per-phase tables, the cross-cutting checklist, and the report template are not factored into `agents/tech-stack-architect/` sibling files.
      Where: `.claude/agents/tech-stack-architect.md` (390 total lines).
      Fix: move the Phase-2 evaluation matrix, the Phase-4.2 cross-cutting checklist, and the Phase-6 report template into sibling files under `agents/tech-stack-architect/`; reference them by relative path.
      Verify: `wc -l .claude/agents/tech-stack-architect.md` reports ≤ 200 lines.

- [ ] [agent-management.write-target-documentation] `Write` is declared but the body does not state the goal and preconditions of the write effect (target path, overwrite vs. append on rerun, what happens if `spec/analysis/` does not yet exist) per the SHOULD. The same gap applies to the `WebSearch`/`WebFetch` tools (their use case — version/CVE plausibility checks — is implied but not stated as a precondition).
      Where: `.claude/agents/tech-stack-architect.md:5` (tools include `Write`, `WebSearch`, `WebFetch`) and line 240 (only mention: "Erstelle `spec/analysis/tech-stack-review.md`").
      Fix: add a "Write target" block naming the absolute output path (`spec/analysis/tech-stack-review.md`), the overwrite behavior on rerun, and the precondition for directory existence; add a sentence explaining when `WebSearch`/`WebFetch` are used (version/EOL/CVE checks) and confirming no PII or project-internal data is sent to those tools.
      Verify: the body contains a "Write target" or equivalent block plus a `WebSearch`/`WebFetch` use-case sentence.

- [ ] [skill-vs-agent.duplicate-prevention] Capability overlaps with the `requirements-contradiction-analyzer` agent — both detect contradictions across REQ/NFR documents (this agent's Phase 4.3 explicitly produces a contradiction table), raising a duplicate-capability flag.
      Where: `.claude/agents/tech-stack-architect.md:4, 192–199` (Phase 4.3 contradictions) vs. the `requirements-contradiction-analyzer` peer agent listed in the available-agents set.
      Fix: either narrow this agent's scope to stack-vs-requirement contradictions only (and have it dispatch `requirements-contradiction-analyzer` for REQ-vs-REQ contradictions), or document the overlap in a "boundary with peer agents" subsection of the rationale.
      Verify: a side-by-side `description` comparison shows the two agents' contradiction-finding scopes are non-overlapping or the overlap is explicitly explained in the body.

### SUGGESTION

- [ ] [agent-management.description-negative-triggers] The `description` enumerates positive triggers but lists no negative cases against peer agents (`requirements-contradiction-analyzer`, `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer` — all read REQ/NFR documents); explicit negatives reduce mis-dispatch.
      Where: `.claude/agents/tech-stack-architect.md:4`.
      Fix: append "nicht verwenden für…" clauses in the description naming each peer that operates on the same source surface.
      Verify: the `description` contains at least one explicit negative-trigger phrase per overlapping peer cluster (security, agrobiology, smart-home, outdoor, contradictions).

### INFO

- [ ] [agent-management.structure-language] Frontmatter `description` and the system-prompt body are authored in German. Per the relaxed `agent-management.Structure` clause (revision `7772341`) and Kamerplanter's project-language authorization in `CLAUDE.md` lines 9–11, German prose is permitted for this `distribution: project` agent. Iteration 1 flagged this as a `BLOCKER`; under the current spec revision the finding is reclassified as a neutral observation.
      Where: `.claude/agents/tech-stack-architect.md:4` (description) and lines 10–390 (body).
      Fix: n/a (observation; project authorization in place).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is declared and the file lives at `.claude/agents/` — consistent.
      Where: `.claude/agents/tech-stack-architect.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] `model: opus` is pinned with an inline rationale (architecture decisions across all REQ/NFR/UI-NFR, high follow-cost / migration risk); the rationale is defensible for a deep cross-spec audit, although the report-producing nature would make `sonnet` a viable cost alternative — acceptable as authored.
      Where: `.claude/agents/tech-stack-architect.md:6–7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
