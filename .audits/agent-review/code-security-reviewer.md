---
review-type: agent-review
target: ".claude/agents/code-security-reviewer.md"
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

# Agent Review: code-security-reviewer

## Scope

Target: `.claude/agents/code-security-reviewer.md` (frontmatter + body; no sibling assets exist under `.claude/agents/code-security-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review per `agent-review` Phase 1–4.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, the tooling that executes ruff/eslint/tsc.

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — undeclared `Write` tool, German body, and missing skill-vs-agent rationale block acceptance.
Next concrete action: declare `Write` in `tools`, translate frontmatter and body to English, add a skill-vs-agent rationale section.

## Findings

### BLOCKER

- [ ] [agent-management.tools-used-not-declared] The agent body instructs "Erstelle `spec/analysis/code-security-review.md`" — that requires the `Write` tool, but `Write` is not declared in the frontmatter `tools` list, so the agent will fail to produce its primary deliverable.
      Where: `.claude/agents/code-security-reviewer.md:5` (tools `Read, Edit, Bash, Glob, Grep`) vs. line 376 (Phase 4: "Erstelle `spec/analysis/code-security-review.md`").
      Fix: add `Write` to the `tools` list (final shape: `Read, Write, Edit, Bash, Glob, Grep`) so file creation is permitted.
      Verify: frontmatter `tools` line includes `Write`; the agent can be dispatched and create a new file in `spec/analysis/`.

- [ ] [agent-management.structure-language] Frontmatter `description` and the entire system-prompt body are written in German, contradicting the MUST that frontmatter and system-prompt content stay in English regardless of authoring language.
      Where: `.claude/agents/code-security-reviewer.md:4` (description) and lines 10–487 (body).
      Fix: translate description and body to English; keep the explicit "report output language: German" instruction as a single English sentence, since the project documentation language is German.
      Verify: `rg -P '[äöüÄÖÜß]' .claude/agents/code-security-reviewer.md` returns no matches in frontmatter or body.

- [ ] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/code-security-reviewer.md` (no rationale section in the body).
      Fix: add a short rationale section naming at least one decisive dimension (for example: context-window protection during cross-file OWASP correlation, narrow tool surface to prevent business-logic edits, specialization via security-only system prompt).
      Verify: a clearly marked rationale paragraph or bullet list references at least one of the seven `skill-vs-agent` decision dimensions; ideally also one counter-dimension.

### WARNING

- [ ] [agent-management.structure-prompt-order] System prompt opens with role/boundaries (good) but the output-format statement (Phase 4 report shape) appears after the audit-method sections (Phase 1–3), violating the SHOULD that role → output format → working method come in that order.
      Where: `.claude/agents/code-security-reviewer.md:10–487` — Phase 4 report shape at line 374, after Phase 2 audit checks at lines 73–340.
      Fix: move the Phase 4 report scaffold immediately after the role/boundaries block (lines 10–34) so the expected output is visible before the working method.
      Verify: the first 60 lines of the body include the report shape from current Phase 4.

- [ ] [agent-management.body-length-200] Body length is approximately 487 lines, well above the soft 200-line target; long-form OWASP checklists (Phase 2.1–2.10) and the report template are not factored into `agents/code-security-reviewer/` sibling files.
      Where: `.claude/agents/code-security-reviewer.md` (487 total lines).
      Fix: move the OWASP-per-category checklists and the report template into `agents/code-security-reviewer/` sibling files (e.g., `owasp-checks.md`, `report-template.md`) and reference them by relative path.
      Verify: `wc -l .claude/agents/code-security-reviewer.md` reports ≤ 200 lines and the sibling folder contains the extracted material.

- [ ] [skill-vs-agent.duplicate-prevention] Capability overlaps with the `security-review` skill ("Complete a security review of the pending changes on the current branch"); both target security review of implemented code, raising a duplicate-capability flag within the project's surface.
      Where: `.claude/agents/code-security-reviewer.md:4` (description) vs. the `security-review` skill listed in the available-skills set.
      Fix: either narrow the agent's `description` to the agent-only role (deep, parallelizable, tool-restricted OWASP audit dispatched by `security-review` or by the `pre-pr` skill), or propose a merge/rename so the user-facing capability lives in exactly one artifact.
      Verify: a side-by-side `description` comparison shows no equivalent user-facing trigger; the agent's description names the orchestrator that dispatches it.

- [ ] [agent-management.tools-bash-vs-dedicated] `Bash` is declared and the only documented Bash use is running `ruff`/`tsc`/`eslint` after fixes — that's legitimate, but the body should justify Bash explicitly so the SHOULD on preferring dedicated tools is met.
      Where: `.claude/agents/code-security-reviewer.md:5` (tools) and lines 364–369 (only Bash use shown).
      Fix: add one English sentence near the tools-usage section stating Bash is used solely for running lint/typecheck commands, all reads use `Read`/`Grep`/`Glob`, all edits use `Edit`.
      Verify: the body contains an explicit Bash-justification sentence.

### SUGGESTION

- [ ] [agent-management.description-negative-triggers] The body contains a strong negative trigger ("du pruefst keine Spezifikationen (dafuer gibt es den `it-security-requirements-reviewer`)") but the frontmatter `description` does not surface that contrast, so dispatch-time disambiguation depends on the long body.
      Where: `.claude/agents/code-security-reviewer.md:4` (description) vs. line 10 (body negative trigger).
      Fix: add one short negative-trigger phrase to the frontmatter `description` (after translation to English): "Don't use for spec/requirements review — use `it-security-requirements-reviewer` for that."
      Verify: the `description` contains both positive triggers and at least one explicit "don't use for…" clause.

### INFO

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
