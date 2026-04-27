---
review-type: agent-review
target: ".claude/agents/i18n-completeness-checker.md"
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

# Agent Review: i18n-completeness-checker

## Scope

Target: `.claude/agents/i18n-completeness-checker.md` (frontmatter + body, ~120 lines; references `src/frontend/src/i18n/locales/{de,en}/translation.json` and `src/frontend/src/**/*.{ts,tsx}`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions recorded in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: i18n-key correctness in the actual translation files, react-i18next runtime behavior.

## Summary

- BLOCKER: 3
- WARNING: 2
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body is German, lacks rationale, and `Bash` is declared without justification on a read-only checker.
Next concrete action: author addresses BLOCKERs (English body, rationale, Bash scoping).

## Findings

### BLOCKER

- [ ] [agent-management.english-content] Description and full body are in German, violating the MUST that frontmatter and system-prompt content stay in English.
      Where: lines 4 (`description`), 10–120 (body).
      Fix: rewrite description and body in English.
      Verify: `head -20` shows English content.
- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet.
      Where: full body.
      Fix: add a 2–4-bullet rationale section (e.g., context-window protection — large JSON + code traversal; tool restriction — read-only; specialization not strong but parallelism + report shape favor agent).
      Verify: grep for "rationale" returns the new section.
- [ ] [agent-management.tools-scope-readonly] Body explicitly states "Du aenderst KEINE Dateien. Du erstellst nur einen Report als Text-Ausgabe" (line 12) — agent is read-only by stated responsibility — yet `Bash` is declared in `tools` (line 5). The agent-review read-only invariant rejects write/edit/execution tools on read-only agents; `Bash` is execution. The MUST in agent-review treats Edit/Write/Bash/NotebookEdit on a read-only agent as a BLOCKER.
      Where: line 5 (`tools: Read, Glob, Grep, Bash`) vs. line 12 (read-only declaration).
      Fix: remove `Bash` from `tools` unless a concrete read-only Bash use is documented in the body (e.g., `git ls-files`); none is shown. Restrict to `Read, Glob, Grep`.
      Verify: `tools` line excludes `Bash`; agent body works without it.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (a structured markdown report with summary table + sections per severity) is defined at lines 76–115; the role-opening section names "structured report" but does not state the shape until step 5. The MUST is technically satisfied (output shape is in the prompt) but the SHOULD on role → output → method ordering is violated because output is at step 5, not step 1.
      Where: lines 10–14 (role) vs. lines 76–115 (output format).
      Fix: hoist the report-shape preview into the role section (one paragraph).
      Verify: lines 1–30 name the report's sections.
- [ ] [agent-management.system-prompt-order] Order is role → step 1 (load) → step 2 (compare) → step 3 (code check) → step 4 (quality) → step 5 (report). The SHOULD requires role → output → method.
      Where: full file structure.
      Fix: reorder to role → output → method (steps 1–5).
      Verify: section ordering follows the SHOULD.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [audit, i18n, frontend]` would aid peer-cluster discovery.
      Where: frontmatter.
      Fix: add `tags: [audit, i18n, frontend]` (≤5, lowercase kebab-case, ≤30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.model-rationale] Model pinned to `haiku` with rationale ("pure consistency check of DE/EN JSON files against code usage with clear rules; haiku optimal for fast bulk checks") on line 6 — satisfies the SHOULD. Plausibility passes (read-only consistency-checking task is haiku-appropriate).
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [skill-vs-agent.duplicate-prevention] No clear peer overlap: peer skills `pre-pr` and `quality-gate` may incorporate i18n checks, but no agent or skill duplicates the description-level capability. INFO only.
      Where: peer list (31 agents + 18 skills).
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
