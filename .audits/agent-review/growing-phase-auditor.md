---
review-type: agent-review
target: ".claude/agents/growing-phase-auditor.md"
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
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: growing-phase-auditor

## Scope

Target: `.claude/agents/growing-phase-auditor.md` (frontmatter + body, 297 lines; references `src/backend/app/migrations/seed_data/plant_info*.yaml` (exist) and `spec/knowledge/plants/*.md` (exists)).
Specs applied: `agent-management` rev `7772341`, `skill-vs-agent` rev `0e3b6f9`, `review-plan` rev `0e3b6f9`, `agent-review` rev `7772341` (recorded in frontmatter).
Iteration 2: re-review under the relaxed agent-management language clause. The MUST on English-only frontmatter/body now exempts `distribution: project` agents whose consuming project authorises a non-English documentation language for agent prose; Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German, so German `description`+body becomes INFO. Frontmatter field names and technical identifier values stay English-required.
Narrowing: none — full review surface.
Explicitly out of scope: botanical correctness of the 3-source-rule, RHS/LWG source quality.

## Summary

- BLOCKER: 1
- WARNING: 3
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — rationale section still missing; language BLOCKER from iteration 1 is downgraded to INFO under the relaxed clause. Tools-vs-responsibility check passes (auditor with Edit/Write justified by stated correction-writing duty).
Next concrete action: author adds a rationale section, hoists the output shape, and addresses length WARNING.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; rationale-documentation MUST is unmet.
      Where: `.claude/agents/growing-phase-auditor.md` body, lines 10-297.
      Fix: add a 2-4-bullet rationale section (e.g., specialization on phenology + multi-source verification; context-window protection — large YAML traversal across 9 seed files; tool restriction would harm the agent because it must Edit YAML and WebFetch sources).
      Verify: grep for "Rationale" returns the new section.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (structured per-species report with status, findings, correction proposal, sources) is shown at Phase 2 (lines 175-221) but not previewed in the role-opening section.
      Where: lines 10-19 (role) vs. lines 175-221 (report template).
      Fix: hoist a one-paragraph "Output shape" block under the role section.
      Verify: lines 1-40 name the report sections.
- [ ] [agent-management.system-prompt-order] Order: role -> 3-Quellen-Regel -> Datenmodell -> Pruefregeln (R1-R5) -> Arbeitsweise (Phase 1-4) -> Referenz-Phasenketten -> Hinweise. SHOULD requires role -> output -> method; output appears mid-Arbeitsweise.
      Where: full file structure.
      Fix: reorder to role -> output -> method.
      Verify: section ordering follows the SHOULD.
- [ ] [agent-management.system-prompt-length] Body is 297 lines, over the ~200-line soft target; the reference phenology table (lines 248-289) and the rules section (lines 92-155) are candidates for siblings under `agents/growing-phase-auditor/`.
      Where: lines 92-155 (rules), 248-289 (reference phenology).
      Fix: factor reference material into `agents/growing-phase-auditor/` siblings.
      Verify: `wc -l` returns ~200.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [audit, plants, seed-data]` would aid peer-cluster discovery vs. peers `seed-data-validator`, `plant-info-document-generator`.
      Where: frontmatter (lines 1-8).
      Fix: add `tags: [audit, plants, seed-data]` (<=5, lowercase kebab-case, <=30 chars).
      Verify: `grep "^tags:"` returns the field.

### INFO

- [ ] [agent-management.english-content-project-exception] Description and body are German. Under the relaxed clause this is allowed because `distribution: project` is declared and Kamerplanter's `CLAUDE.md` (lines 9-11) authorises German for `.claude/agents/` prose. Iteration-1 BLOCKER downgraded.
      Where: line 4 (description), lines 10-297 (body).
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.model-rationale] Model pinned to `sonnet` with rationale ("botanical validation with web research (3-source rule), structured reasoning without extreme complexity; sonnet adequate") on line 7 — satisfies the SHOULD. Plausibility passes.
      Where: frontmatter line 7.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-management.tools-scope] Tools `Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch` (line 5) match the stated responsibility (audit YAML files AND apply corrections); not a read-only agent because corrections are written, so Edit/Write are justified per the body's Phase-4 directive.
      Where: line 5.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [skill-vs-agent.duplicate-prevention] Peer agent `seed-data-validator` shares the seed-YAML domain but validates schema/structure, not phenology; peer `plant-info-document-generator` writes new docs vs. auditing data — no semantic overlap, but a "don't use for" clause naming `seed-data-validator` would sharpen the boundary.
      Where: line 4 description.
      Fix: n/a (informational; could be promoted to WARNING if duplicates surface).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
