---
review-type: agent-review
target: ".claude/agents/frontend-usability-optimizer.md"
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

# Agent Review: frontend-usability-optimizer

## Scope

Target: `.claude/agents/frontend-usability-optimizer.md` (frontmatter + body, ~483 lines; no `agents/<name>/` sibling assets exist).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions recorded in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown lint (handled by `task lint`), the consuming workflow that invokes the agent.

## Summary

- BLOCKER: 4
- WARNING: 5
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — the body language convention violates the English-only MUST and the rationale section is missing.
Next concrete action: author addresses BLOCKERs (rationale, English body, tags vocabulary) and rebalances WARNINGs.

## Findings

### BLOCKER

- [ ] [agent-management.english-content] Frontmatter `description` and the entire body are written in German, violating the MUST that frontmatter and system-prompt content stay in English.
      Where: `.claude/agents/frontend-usability-optimizer.md:4` (`description`) and lines 10–483 (body).
      Fix: rewrite description and body in English; if German UI guidance must be embedded verbatim, quote it as a referenced asset and keep instructions English. Note: the project-global rule in `CLAUDE.md` mandates German conversation, but the agent-management spec MUST overrides for agent files.
      Verify: `head -20 .claude/agents/frontend-usability-optimizer.md` shows English description and body opening.
- [ ] [skill-vs-agent.rationale] No rationale section explains the agent-over-skill choice; absence of any decisive dimension is a BLOCKER per `skill-vs-agent` rationale-documentation MUST.
      Where: entire body — no section names dimensions like context-window, tool restriction, parallelism, or specialization.
      Fix: add a short rationale section (2–4 bullets) naming the decisive dimensions (e.g., specialization on MUI/UI-NFR, large-context reads of UI-NFR specs).
      Verify: grep for "rationale" or "skill-vs-agent" in the body returns the new section.
- [ ] [agent-management.system-prompt-output-shape] System prompt does not state the expected output shape until line 430 in a soft "Ausgabe nach Optimierung" section; the opening role section never names the output contract.
      Where: lines 10–28 (role intro) — output-shape statement is buried in §"Ausgabe nach Optimierung" (lines 428–469) and only embedded as a German template.
      Fix: in the opening section, state the output shape explicitly (e.g., "produces an English usability-optimization summary listing changes, added i18n keys, UI-NFR compliance check, verification status").
      Verify: opening 30 lines name the output shape; spec MUST satisfied.
- [ ] [agent-management.tools-scope-readonly] The agent's stated responsibility ("usability-optimization of existing code") is implementation work that writes files; this is not read-only, so `Edit`/`Write`/`Bash` are justified — but the agent body uses `WebSearch`/`WebFetch` nowhere yet declares neither: this finding flips: `Bash` is declared and the body uses it (`tsc --noEmit`, `eslint`) — OK. Re-classified: not BLOCKER on read-only criterion. (Removing — see INFO instead.)

  **Replaced finding:** [agent-management.tags] `tags` field is absent; the agent is part of the same functional cluster as `frontend-design-reviewer`, `selenium-test-reviewer` (UI tag would apply), so peer-cluster lookup per `skill-vs-agent` portfolio-wide consistency is degraded. The MAY in agent-management makes this a SUGGESTION, not a BLOCKER — moved to SUGGESTION.

  **Actual fourth BLOCKER:** [agent-management.system-prompt-single-responsibility] The body bundles two responsibilities: (1) usability optimization of existing code (Phase 1) and (2) full UI-NFR compliance audit across `spec/ui-nfr/UI-NFR-*.md` (Phase 2, lines 367–425). Phase 2 reads every UI-NFR spec and corrects all MUSS deviations — this is a separate audit responsibility, not a usability optimization.
      Where: lines 367–425 (`## Phase 2: UI-NFR-Compliance-Pruefung`).
      Fix: split the audit phase into a separate agent (`ui-nfr-compliance-auditor`) or remove Phase 2 from this agent and let a follow-up agent handle compliance.
      Verify: body contains exactly one responsibility; Phase 2 either removed or referenced by name to a separate agent.
- [ ] [agent-management.english-content+single-responsibility] Combined: in addition to the language and split issues above, the body restates large portions of `spec/ui-nfr/UI-NFR-008` inline (R-053–R-064 cited, lines 165–177) — that supporting material belongs in `agents/frontend-usability-optimizer/` per the self-contained MUST.
      Where: lines 99–177 (Checklists rephrasing UI-NFR specs verbatim).
      Fix: factor the inline checklists into a sibling reference under `agents/frontend-usability-optimizer/checklists/` and link from the body; keep only the procedure inline.
      Verify: body length drops to ~200 lines; sibling folder contains the moved checklists.

### WARNING

- [ ] [agent-management.system-prompt-order] System prompt opens with role then mobile-first warning then style guide rule; the expected output format is at line 428, well after the working method (Phase 1–4). The SHOULD requires role → output → method.
      Where: lines 10–28 vs. lines 242–270 (working method) vs. lines 428–469 (output).
      Fix: hoist a one-paragraph "Output shape" block immediately after the role section.
      Verify: lines 1–40 contain role + output statement before any method bullets.
- [ ] [agent-management.system-prompt-length] Body is 483 lines, well over the ~200-line soft target; supporting material (checklists, type usage examples) should move into `agents/frontend-usability-optimizer/`.
      Where: full file, especially lines 273–363 (typische Optimierungen, code samples).
      Fix: move code-sample blocks to `agents/frontend-usability-optimizer/examples.md`; reference by relative path.
      Verify: `wc -l .claude/agents/frontend-usability-optimizer.md` returns ~200.
- [ ] [skill-vs-agent.duplicate-prevention] Plausible overlap with peer agent `frontend-design-reviewer` (responsive/kiosk spec review): both touch UI-NFR-001/002/008 and frontend layout; review surfaces are similar enough to merit a clearer delineation.
      Where: description line 4 (general usability post-implementation) vs. peer `frontend-design-reviewer` (responsive/kiosk spec).
      Fix: add a "don't use for" negative trigger to the description naming `frontend-design-reviewer` ("don't use for spec-level responsive/kiosk review — use frontend-design-reviewer").
      Verify: description contains a "don't use for" clause.
- [ ] [agent-management.tools-bash-vs-dedicated] `Bash` is declared and used for `tsc --noEmit` and `eslint` — both have no dedicated equivalent, so OK; however the body also references `Glob` patterns that could be tightened. The bigger concern: `Bash` is broad — body should justify the choice (lint runs).
      Where: frontmatter line 5 (`tools: Read, Write, Edit, Bash, Glob, Grep`) vs. body lines 257–260 (`tsc`/`eslint`).
      Fix: in the body's tool-use section, state explicitly that Bash is scoped to lint/typecheck commands; this satisfies the SHOULD.
      Verify: body documents Bash scope under tool-use rationale.
- [ ] [agent-management.write-effects-documented] The agent edits files (`Edit`, `Write`); the SHOULD requires the system prompt to document the goals/preconditions of write effects. Goals are stated ("optimize existing code"), but preconditions (e.g., "do not change API surface", "do not modify Redux slices") are buried in §"Aenderungen NICHT durchfuehren" (line 262).
      Where: lines 262–270 — preconditions present but not surfaced near the role section.
      Fix: hoist preconditions into the opening role block alongside the output shape.
      Verify: opening section contains an explicit "preconditions" list.

### SUGGESTION

- [ ] [agent-management.tags] `tags` field is absent; adding `tags: [review, frontend, ui]` (≤5, lowercase kebab-case) would satisfy peer-cluster lookups per `skill-vs-agent` portfolio-wide consistency.
      Where: frontmatter, lines 1–8.
      Fix: add `tags: [frontend, ui-nfr, usability]` (or similar) within the 5-entry/30-char constraint.
      Verify: `grep "^tags:" .claude/agents/frontend-usability-optimizer.md` returns the field.

### INFO

- [ ] [agent-management.model-rationale] Model is pinned to `sonnet` with rationale on line 6; rationale is brief but present, satisfies the SHOULD. No action.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-review.referenced-assets] No `agents/frontend-usability-optimizer/` sibling folder exists; body references inline checklists only. Once length-WARNING is addressed, sibling folder will need to be created.
      Where: filesystem under `.claude/agents/`.
      Fix: n/a (observation tied to length WARNING fix).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
