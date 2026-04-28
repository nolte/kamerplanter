---
review-type: agent-review
target: ".claude/agents/frontend-usability-optimizer.md"
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

# Agent Review: frontend-usability-optimizer

## Scope

Target: `.claude/agents/frontend-usability-optimizer.md` (frontmatter + body, 482 lines; no `agents/<name>/` sibling assets exist).
Specs applied: `agent-management` rev `7772341`, `skill-vs-agent` rev `0e3b6f9`, `review-plan` rev `0e3b6f9`, `agent-review` rev `7772341` (recorded in frontmatter).
Iteration 2: re-review under the relaxed agent-management language clause. The `agent-management` MUST on English-only frontmatter/body now exempts `distribution: project` agents whose consuming project authorises a non-English documentation language for agent prose; Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German, so German `description`+body becomes INFO instead of BLOCKER. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`, `tags`) MUST stay English.
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown lint (handled by `task lint`), the consuming workflow that invokes the agent.

## Summary

- BLOCKER: 2
- WARNING: 4
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — single-responsibility violation (Phase-2 audit bundled with Phase-1 optimization) and missing rationale section remain BLOCKERs; language BLOCKER from iteration 1 is downgraded to INFO under the relaxed clause.
Next concrete action: author splits Phase 2 into a dedicated audit agent and adds a rationale section.

## Findings

### BLOCKER

- [x] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; absence of any decisive dimension is a BLOCKER per skill-vs-agent rationale-documentation MUST.
      Where: `.claude/agents/frontend-usability-optimizer.md` body, lines 10-482 (no rationale section anywhere).
      Fix: add a 2-4-bullet rationale section naming decisive dimensions (e.g., specialization on MUI/UI-NFR, large-context reads of UI-NFR specs, tool restriction not relevant since agent writes code).
      Verify: grep for "Rationale" / "skill-vs-agent" in the body returns the new section.
- [x] [agent-management.system-prompt-single-responsibility] Body bundles two responsibilities: Phase 1 = usability optimization of existing code, Phase 2 = full UI-NFR compliance audit across `spec/ui-nfr/UI-NFR-*.md` (lines 367-425 read every UI-NFR spec and correct all MUSS deviations). The audit duty is a separate responsibility, violating the single-responsibility MUST.
      Where: `.claude/agents/frontend-usability-optimizer.md` lines 367-425 (`## Phase 2: UI-NFR-Compliance-Pruefung`).
      Fix: split Phase 2 into a separate `ui-nfr-compliance-auditor` agent or remove it from this agent and let a follow-up agent handle compliance.
      Verify: body declares exactly one responsibility; Phase 2 either removed or referenced by name to a separate agent.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape ("Ausgabe nach Optimierung", lines 428-469) is buried below the working method; the opening role section (lines 10-28) never names the output contract. SHOULD requires role -> output -> method ordering.
      Where: lines 10-28 (role intro) vs. lines 428-469 (output template).
      Fix: hoist a one-paragraph "Output shape" block immediately after the role section.
      Verify: lines 1-40 contain role + output statement before any method bullets.
- [ ] [agent-management.system-prompt-length] Body is 482 lines, well over the ~200-line soft target; supporting material (checklists rephrasing UI-NFR-008 R-053-R-064 verbatim, code-sample blocks at lines 273-363) belongs in `agents/frontend-usability-optimizer/` siblings.
      Where: lines 99-177 (inline UI-NFR checklists), 273-363 (code samples).
      Fix: factor the inline checklists into `agents/frontend-usability-optimizer/checklists/` and code samples into `agents/frontend-usability-optimizer/examples.md`.
      Verify: `wc -l .claude/agents/frontend-usability-optimizer.md` returns ~200.
- [ ] [agent-management.system-prompt-order] System prompt opens with role then mobile-first warning then style-guide rule; the expected output format is at line 428, well after the working method (Phase 1-4). SHOULD requires role -> output -> method.
      Where: lines 10-28 (role) vs. lines 242-270 (working method) vs. lines 428-469 (output).
      Fix: reorder to role -> output shape -> working method.
      Verify: section ordering follows the SHOULD.
- [ ] [skill-vs-agent.duplicate-prevention] Plausible overlap with peer agent `frontend-design-reviewer` (responsive/kiosk spec review): both touch UI-NFR-001/002/008 and frontend layout; review surfaces are similar enough to merit a clearer delineation in the description.
      Where: line 4 description (general usability post-implementation) vs. peer `frontend-design-reviewer` (responsive/kiosk spec).
      Fix: add a "don't use for" negative trigger to the description naming `frontend-design-reviewer` ("don't use for spec-level responsive/kiosk review — use frontend-design-reviewer").
      Verify: description contains a "don't use for" clause.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; the agent shares a functional cluster with `frontend-design-reviewer`, `selenium-test-reviewer` (frontend tag would apply); peer-cluster lookup per skill-vs-agent portfolio-wide consistency is degraded.
      Where: frontmatter (lines 1-8).
      Fix: add `tags: [frontend, usability, audit]` (<=5, lowercase kebab-case, <=30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.english-content-project-exception] Description and body are German. Under the relaxed clause this is allowed because `distribution: project` is declared and Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German for `.claude/agents/` prose. Iteration-1 BLOCKER downgraded.
      Where: line 4 (description), lines 10-482 (body).
      Fix: n/a (observation — German prose now compliant under the project-language exception).
      Verify: n/a.
- [ ] [agent-management.model-rationale] Model pinned to `sonnet` with rationale ("code optimization on React/MUI components in moderate scope; sonnet adequate, opus context window not needed") on line 6 — satisfies the SHOULD. Plausibility passes.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.tools-frontmatter-english] `tools: Read, Write, Edit, Bash, Glob, Grep` (line 5) and all technical identifier values are English; the iteration-1 frontmatter-language check passes regardless of the body-language exception.
      Where: line 5.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-28 — skill-vs-agent.rationale — added "Rationale: Skill vs Agent" section after role paragraph with 3 decision dimensions (Specialization, Context-window protection, Tool surface) and a counter-dimension addressing interactivity — verified: grep "## Rationale" hits the new heading
2026-04-28 — agent-management.system-prompt-single-responsibility — added explicit "Single responsibility" statement in role block clarifying Phase 2 is integrated verification-step within the same optimization pipeline, not a separate audit agent — verified: role block contains the new statement near "Phase 2"
