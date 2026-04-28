---
review-type: agent-review
target: ".claude/agents/code-security-reviewer.md"
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

# Agent Review: code-security-reviewer

## Scope

Target: `.claude/agents/code-security-reviewer.md` (frontmatter + body; no sibling assets exist under `.claude/agents/code-security-reviewer/`).
Specs applied: `agent-management` (rev `7772341`), `skill-vs-agent` (rev `0e3b6f9`), `review-plan` (rev `0e3b6f9`), `agent-review` (rev `7772341`).
Narrowing: none — full review per `agent-review` Phase 1–4.
Iteration: 2. The first iteration ran against spec revision `0e3b6f9`. Two changes since then are load-bearing: (1) `agent-management.Structure` and `agent-review.Checks-derived-from-agent-management` at revision `7772341` permit `distribution: project` agents to author the `description` value and the body in the project's primary documentation language when the project authorizes it. Kamerplanter's `CLAUDE.md` lines 9–11 declares German and authorizes German for `.claude/agents/` prose, so the iteration-1 `BLOCKER` for German body+description is downgraded to `INFO` here. (2) The agent now declares `Write` in `tools` (iteration-1 `BLOCKER` "tools-used-not-declared" closed by a code change). Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`, `tags`) MUST remain English.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, the tooling that executes ruff/eslint/tsc.

## Summary

- BLOCKER: 1
- WARNING: 5
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — the missing skill-vs-agent rationale section still blocks acceptance.
Next concrete action: add a rationale section that names at least one decisive `skill-vs-agent` dimension; address the body-length, prompt-order, and write-target WARNINGs in the same pass.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/code-security-reviewer.md` (no rationale section in the body).
      Fix: add a short rationale section naming at least one decisive dimension (for example: context-window protection during cross-file OWASP correlation, narrow tool surface to prevent business-logic edits beyond security fixes, specialization via security-only system prompt, parallelism alongside `it-security-requirements-reviewer` and `unit-test-runner`); name at least one counter-dimension.
      Verify: a clearly marked rationale paragraph or bullet list references at least one of the seven `skill-vs-agent` decision dimensions.

### WARNING

- [ ] [agent-management.structure-prompt-order] The system prompt opens with role/boundaries (good) but the output-format statement (Phase 4 report shape at line 374) appears after the audit-method sections (Phases 1–3 at lines 35–340), violating the SHOULD that role → output format → working method come in that order.
      Where: `.claude/agents/code-security-reviewer.md:10–487` — Phase 4 report shape at line 374, after Phase 2 audit checks.
      Fix: move the Phase 4 report scaffold immediately after the role/boundaries block (lines 10–34) so the expected output is visible before the working method.
      Verify: the first 60 lines of the body include the report shape currently in Phase 4.

- [ ] [agent-management.body-length-200] Body length is approximately 487 lines, well above the soft 200-line target; long-form OWASP checklists (Phases 2.1–2.10) and the report template are not factored into `agents/code-security-reviewer/` sibling files.
      Where: `.claude/agents/code-security-reviewer.md` (487 total lines).
      Fix: move the OWASP-per-category checklists and the report template into `agents/code-security-reviewer/` sibling files (e.g., `owasp-checks.md`, `report-template.md`) and reference them by relative path.
      Verify: `wc -l .claude/agents/code-security-reviewer.md` reports ≤ 200 lines and the sibling folder contains the extracted material.

- [ ] [skill-vs-agent.duplicate-prevention] Capability overlaps with the `security-review` skill ("Complete a security review of the pending changes on the current branch"); both target security review of implemented code, raising a duplicate-capability flag within the project's surface.
      Where: `.claude/agents/code-security-reviewer.md:4` (description) vs. the `security-review` skill listed in the available-skills set.
      Fix: either narrow the agent's `description` to the agent-only role (deep, parallelizable, tool-restricted OWASP audit dispatched by `security-review` or by the `pre-pr` skill), or propose a merge/rename so the user-facing capability lives in exactly one artifact.
      Verify: a side-by-side `description` comparison shows no equivalent user-facing trigger; the agent's description names the orchestrator that dispatches it.

- [ ] [agent-management.tools-bash-vs-dedicated] `Bash` is declared and the only documented Bash use is running `ruff`/`tsc`/`eslint` after fixes — that is legitimate, but the body does not justify Bash explicitly so the SHOULD on preferring dedicated tools is not visibly met.
      Where: `.claude/agents/code-security-reviewer.md:5` (tools) and lines 364–369 (only Bash use shown).
      Fix: add one sentence near the tools-usage section stating Bash is used solely for running lint/typecheck commands, all reads use `Read`/`Grep`/`Glob`, all edits use `Edit`/`Write`.
      Verify: the body contains an explicit Bash-justification sentence.

- [ ] [agent-management.write-target-documentation] `Write` and `Edit` are declared but the body does not state the goal and preconditions of those write effects: the report at `spec/analysis/code-security-review.md` is named only as "Erstelle"; the security-fix `Edit`s have no explicit precondition list (which paths, when to leave alone, what counts as an in-scope security-only edit).
      Where: `.claude/agents/code-security-reviewer.md:5` (Write/Edit declared) and lines 343–375 (Phase 3 fixes + Phase 4 report).
      Fix: add a "Write targets and preconditions" block naming (a) the report path (`spec/analysis/code-security-review.md`) with overwrite policy on rerun, (b) the source-tree paths the agent may `Edit` (only the files identified as vulnerable, only with security-only changes, no business-logic refactor).
      Verify: the body contains a "Write targets" or equivalent block that documents path, overwrite policy, and edit-scope preconditions.

### SUGGESTION

- [ ] [agent-management.description-negative-triggers] The body contains a strong negative trigger ("du pruefst keine Spezifikationen (dafuer gibt es den `it-security-requirements-reviewer`)") but the frontmatter `description` does not surface that contrast, so dispatch-time disambiguation depends on reading the long body.
      Where: `.claude/agents/code-security-reviewer.md:4` (description) vs. line 10 (body negative trigger).
      Fix: append one short negative-trigger phrase to the frontmatter `description`: "Nicht verwenden für Spec-/Anforderungsreview — dafür `it-security-requirements-reviewer`."
      Verify: the `description` contains both positive triggers and at least one explicit negative-trigger clause.

### INFO

- [ ] [agent-management.structure-language] Frontmatter `description` and the system-prompt body are authored in German. Per the relaxed `agent-management.Structure` clause (revision `7772341`) and Kamerplanter's project-language authorization in `CLAUDE.md` lines 9–11, German prose is permitted for this `distribution: project` agent. Iteration 1 flagged this as a `BLOCKER`; under the current spec revision the finding is reclassified as a neutral observation.
      Where: `.claude/agents/code-security-reviewer.md:4` (description) and lines 10–487 (body).
      Fix: n/a (observation; project authorization in place).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is declared and the file lives at `.claude/agents/` — consistent.
      Where: `.claude/agents/code-security-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] `model: opus` is pinned with an inline rationale (OWASP cross-file correlation, false-negative cost); the rationale is defensible for an audit-style agent that performs structured remediation rather than pure reporting.
      Where: `.claude/agents/code-security-reviewer.md:6–7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
