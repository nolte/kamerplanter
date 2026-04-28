---
review-type: agent-review
target: ".claude/agents/gemini-graphic-prompt-generator.md"
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

# Agent Review: gemini-graphic-prompt-generator

## Scope

Target: `.claude/agents/gemini-graphic-prompt-generator.md` (frontmatter + body, 299 lines; references `spec/design/KAMI-CHARACTER-REFERENCE.md` (exists), `src/frontend/src/theme/palette.ts`, `src/frontend/src/theme/tokens.ts`, `src/frontend/src/layouts/Sidebar.tsx`).
Specs applied: `agent-management` rev `7772341`, `skill-vs-agent` rev `0e3b6f9`, `review-plan` rev `0e3b6f9`, `agent-review` rev `7772341` (recorded in frontmatter).
Iteration 2: re-review under the relaxed agent-management language clause. The MUST on English-only frontmatter/body now exempts `distribution: project` agents whose consuming project authorises a non-English documentation language for agent prose; Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German, so German `description`+body becomes INFO. Frontmatter field names and technical identifier values stay English-required.
Narrowing: none — full review surface.
Explicitly out of scope: actual prompt-engineering quality, Gemini API behavior.

## Summary

- BLOCKER: 1
- WARNING: 3
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — rationale section still missing; language BLOCKER from iteration 1 is downgraded to INFO under the relaxed clause.
Next concrete action: author adds a rationale section and addresses ordering / output-shape WARNINGs.

## Findings

### BLOCKER

- [x] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet.
      Where: `.claude/agents/gemini-graphic-prompt-generator.md` body, lines 10-299.
      Fix: add a 2-4-bullet rationale section (e.g., specialization on Kamerplanter corporate design + Gemini prompt syntax; isolation from main conversation; write-only output).
      Verify: grep for "Rationale" returns the new section.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (a structured prompt-document under `spec/design/<grafiktyp>_<beschreibung_snake_case>.md` with a defined template) is named in Phase 3 (lines 188-260) but not stated in the role-opening section.
      Where: lines 10-22 (role) vs. lines 188-260 (output template).
      Fix: hoist a one-paragraph "Output shape" block under the role section.
      Verify: lines 1-40 name the output document path and key sections.
- [ ] [agent-management.system-prompt-order] Order: role -> corporate-design reference -> Auftrag -> Workflow (Phase 0-5) -> Qualitaetsregeln -> Kommunikationsstil. SHOULD requires role -> output -> method; output is at Phase 3, four phases deep.
      Where: full file structure.
      Fix: reorder to role -> output -> method (Phase 0-5).
      Verify: section ordering follows the SHOULD.
- [ ] [agent-management.system-prompt-length] Body is 299 lines, over the ~200-line soft target; the corporate-design reference (lines 22-72) and the prompt-document template (lines 200-260) are prime candidates for sibling assets under `agents/gemini-graphic-prompt-generator/`.
      Where: lines 22-72 (color palette + design-language tables), 200-260 (prompt template).
      Fix: factor the design-system reference and the template into `agents/gemini-graphic-prompt-generator/` siblings.
      Verify: `wc -l` returns ~200.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [design, prompts, kami]` would aid peer-cluster discovery vs. peer agent `plant-info-document-generator` (also a generator).
      Where: frontmatter (lines 1-8).
      Fix: add `tags: [design, prompts, kami]` (<=5, lowercase kebab-case, <=30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.english-content-project-exception] Description and body are German. Under the relaxed clause this is allowed because `distribution: project` is declared and Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German for `.claude/agents/` prose. Iteration-1 BLOCKER downgraded.
      Where: line 4 (description), lines 10-299 (body).
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.model-rationale] Model pinned to `haiku` with rationale ("prompt templating against a clearly defined corporate-design style guide; low reasoning, high throughput requirement -> haiku optimal") on line 6 — satisfies the SHOULD. Plausibility passes for a templating task.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [skill-vs-agent.duplicate-prevention] Peer agent `plant-info-document-generator` is also a generator but operates in the plants-domain (markdown plant info) vs. this agent's design-domain (Gemini prompts) — no semantic overlap, no duplicate.
      Where: peer list.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-28 — skill-vs-agent.rationale — added "Rationale: Skill vs Agent" section after role profile with 3 decision dimensions (Specialization, Self-contained, Context-window protection) and a counter-dimension on lifecycle — verified: grep "## Rationale" hits the new heading
