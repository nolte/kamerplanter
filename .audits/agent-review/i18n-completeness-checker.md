---
review-type: agent-review
target: ".claude/agents/i18n-completeness-checker.md"
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
status: in-progress
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: i18n-completeness-checker

## Scope

Target: `.claude/agents/i18n-completeness-checker.md` (frontmatter + body, 119 lines; references `src/frontend/src/i18n/locales/{de,en}/translation.json` and `src/frontend/src/**/*.{ts,tsx}`).
Specs applied: `agent-management` rev `7772341`, `skill-vs-agent` rev `0e3b6f9`, `review-plan` rev `0e3b6f9`, `agent-review` rev `7772341` (recorded in frontmatter).
Iteration 2: re-review under the relaxed agent-management language clause. The MUST on English-only frontmatter/body now exempts `distribution: project` agents whose consuming project authorises a non-English documentation language for agent prose; Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German, so German `description`+body becomes INFO. Frontmatter field names and technical identifier values stay English-required. The iteration-1 quick-win fix removed `Bash` from `tools` — the read-only-no-write BLOCKER from iteration 1 is closed.
Narrowing: none — full review surface.
Explicitly out of scope: i18n-key correctness in the actual translation files, react-i18next runtime behavior.

## Summary

- BLOCKER: 1
- WARNING: 2
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — rationale section still missing; language BLOCKER from iteration 1 downgraded to INFO; tools-scope BLOCKER from iteration 1 closed (Bash removed in quick-win iteration).
Next concrete action: author adds a rationale section and addresses the role -> output -> method ordering WARNING.

## Findings

### BLOCKER

- [x] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet.
      Where: `.claude/agents/i18n-completeness-checker.md` body, lines 10-119.
      Fix: add a 2-4-bullet rationale section (e.g., context-window protection — large JSON + code traversal; tool restriction — read-only checker; report-shape contract favors agent over skill).
      Verify: grep for "Rationale" returns the new section.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (a structured markdown report with summary table + sections per severity) is defined at Step 5 (lines 75-115); the role-opening section names "structured report" but does not state the shape until step 5. SHOULD on role -> output -> method ordering is violated.
      Where: lines 10-14 (role) vs. lines 75-115 (output format).
      Fix: hoist the report-shape preview into the role section (one paragraph).
      Verify: lines 1-30 name the report's sections.
- [ ] [agent-management.system-prompt-order] Order is role -> step 1 (load) -> step 2 (compare) -> step 3 (code check) -> step 4 (quality) -> step 5 (report). SHOULD requires role -> output -> method.
      Where: full file structure.
      Fix: reorder to role -> output -> method (steps 1-5).
      Verify: section ordering follows the SHOULD.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [audit, i18n, frontend]` would aid peer-cluster discovery.
      Where: frontmatter (lines 1-8).
      Fix: add `tags: [audit, i18n, frontend]` (<=5, lowercase kebab-case, <=30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.english-content-project-exception] Description and body are German. Under the relaxed clause this is allowed because `distribution: project` is declared and Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German for `.claude/agents/` prose. Iteration-1 BLOCKER downgraded.
      Where: line 4 (description), lines 10-119 (body).
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.tools-scope-readonly] Iteration-1 BLOCKER closed: `tools: Read, Glob, Grep` (line 5) — `Bash` was removed in the quick-win iteration. Read-only agent now correctly has no Edit/Write/Bash/NotebookEdit.
      Where: line 5.
      Fix: n/a (observation — quick-win fix landed).
      Verify: n/a.
- [ ] [agent-management.model-rationale] Model pinned to `haiku` with rationale ("pure consistency check of DE/EN JSON files against code usage with clear rules; haiku optimal for fast bulk checks") on line 6 — satisfies the SHOULD. Plausibility passes (read-only consistency-checking task is haiku-appropriate).
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [skill-vs-agent.duplicate-prevention] No clear peer overlap: peer skills `pre-pr` and `quality-gate` may incorporate i18n checks, but no agent or skill duplicates the description-level capability.
      Where: peer list.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-28 — skill-vs-agent.rationale — added "Rationale: Skill vs Agent" section after role intro with 3 decision dimensions (Self-contained, Specialization, Tool surface) and a counter-dimension on lifecycle/sprint-cadence — verified: grep "## Rationale" hits the new heading
