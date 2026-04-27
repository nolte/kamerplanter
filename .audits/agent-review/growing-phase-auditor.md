---
review-type: agent-review
target: ".claude/agents/growing-phase-auditor.md"
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

# Agent Review: growing-phase-auditor

## Scope

Target: `.claude/agents/growing-phase-auditor.md` (frontmatter + body, ~298 lines; no `agents/<name>/` sibling assets).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions recorded in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: botanical correctness of the cited reference patterns, validity of cited data sources.

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body is German, lacks rationale, and the read-only "auditor" framing conflicts with the declared write/execution tools.
Next concrete action: author addresses BLOCKERs (English body, rationale, tool-scoping clarification).

## Findings

### BLOCKER

- [ ] [agent-management.english-content] Description and full body are in German, violating the MUST for English frontmatter and system-prompt content.
      Where: lines 4 (`description`), 10–298 (body).
      Fix: rewrite description and body in English; the project's German-conversation rule does not override the agent-management spec's English MUST.
      Verify: `head -20` shows English content.
- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; the rationale-documentation MUST is unmet.
      Where: full body.
      Fix: add a 2–4-bullet rationale section (e.g., context-window protection — multi-source web research; specialization on phenology + 3-source rule; tool restriction — WebSearch/WebFetch reduce hallucination risk).
      Verify: grep for "rationale" returns the new section.
- [ ] [agent-management.tools-scope-readonly+system-prompt-single-responsibility] The `description` (line 4) calls the agent both "Prueft" (audits/reviews — read-only verb) and "korrigiert" (corrects — writes); the responsibility statement bundles audit + correction. agent-review's read-only invariant is therefore ambiguous, and the audit-only naming "auditor" conflicts with the declared `Write`/`Edit`/`Bash` tools. Additionally, the body Phase 4 (line 239) writes corrections directly to YAML files.
      Where: line 4 (`Prueft und korrigiert`), line 5 (`tools: ... Write, Edit, ... Bash, WebSearch, WebFetch`), lines 239–245 (Phase 4 writes).
      Fix: either (a) rename to `growing-phase-auditor-and-corrector` and explicitly justify Edit/Write in the body's tool-use rationale; or (b) split into a read-only auditor (Read/Glob/Grep/WebSearch/WebFetch only) plus a separate corrector agent. Document the chosen direction in the rationale section.
      Verify: agent name + description + tools list are internally consistent; read-only invariant is either satisfied or explicitly waived with justification.

### WARNING

- [ ] [agent-management.system-prompt-output-shape] Output shape (structured per-species report with status/findings/correction/sources/confidence) is defined but only at lines 175–222 (Phase 2); the role-opening section never names it. The MUST requires the output shape to be stated.
      Where: lines 10–18 (role) vs. lines 175–222 (output template).
      Fix: hoist a one-paragraph "Output shape" block under the role section.
      Verify: lines 1–30 name the report shape.
- [ ] [agent-management.system-prompt-order] Order is role → multi-source rule → data model → check rules → method → reference data. The SHOULD requires role → output → method; output and method are split across the document.
      Where: lines 21–67 (multi-source rule) precedes any method/output statement.
      Fix: reorder to role → output → method (Phase 1–4) → reference data → multi-source rule (or move multi-source rule into method as preconditions).
      Verify: section ordering follows the SHOULD.
- [ ] [agent-management.system-prompt-length] Body is ~298 lines, over the ~200-line soft target; the multi-source rule, data model, check rules and reference patterns are candidates for sibling assets.
      Where: full file, especially lines 91–155 (check rules), 249–298 (typical phase chains).
      Fix: factor reference data and check rules into `agents/growing-phase-auditor/`.
      Verify: `wc -l` returns ~200.
- [ ] [agent-management.write-effects-documented] The agent edits YAML seed files; goals are present (Phase 4 lines 239–245) but preconditions are partially documented (only-write-✅GESICHERT). Adding explicit "do not add new schema fields" and "verify YAML syntax after each edit" is present (line 245) — close to satisfying the SHOULD but should be hoisted near the role.
      Where: lines 239–245.
      Fix: hoist write preconditions into the role-opening block.
      Verify: opening section names the write preconditions.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [audit, seeds, botany]` would aid peer-cluster discovery per `skill-vs-agent` portfolio-wide consistency.
      Where: frontmatter.
      Fix: add `tags: [audit, seeds, botany]` (≤5, lowercase kebab-case, ≤30 chars).
      Verify: `grep "^tags:" .claude/agents/growing-phase-auditor.md` returns the field.

### INFO

- [ ] [agent-management.model-rationale] Model pinned to `sonnet` with rationale ("botanical validation with web research, structured reasoning") on line 6; satisfies the SHOULD. Plausibility passes.
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [skill-vs-agent.duplicate-prevention] Plausible overlap with peer agent `seed-data-validator` (validates YAML seeds) — they are described as different (validator vs. phase-specific corrector), but description should clarify the boundary explicitly.
      Where: description line 4 vs. peer `seed-data-validator`.
      Fix: add a "don't use for" negative trigger naming `seed-data-validator` ("don't use for general seed-YAML schema validation — use seed-data-validator").
      Verify: description contains a "don't use for" clause. (Soft-flagged as INFO because the boundary is genuinely narrower than "duplicate".)

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
