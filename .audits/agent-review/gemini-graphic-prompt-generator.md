---
review-type: agent-review
target: ".claude/agents/gemini-graphic-prompt-generator.md"
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

# Agent Review: gemini-graphic-prompt-generator

## Scope

Target: `.claude/agents/gemini-graphic-prompt-generator.md` (frontmatter + body, ~300 lines; references `spec/design/KAMI-CHARACTER-REFERENCE.md` which exists).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions recorded in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime correctness of the generated Gemini prompts, the actual image-generation tool's behavior.

## Summary

- BLOCKER: 3
- WARNING: 4
- SUGGESTION: 2
- INFO: 2

Go/no-go: FAIL — body is German, lacks a rationale section, and bundles two writing responsibilities.
Next concrete action: author addresses BLOCKERs (English body, rationale, single-responsibility split or re-scope).

## Findings

### BLOCKER

- [ ] [agent-management.english-content] Body and frontmatter description are in German (with English design-domain terms), violating the MUST that frontmatter and system-prompt content stay in English.
      Where: `.claude/agents/gemini-graphic-prompt-generator.md:4` (`description`) and lines 10–300.
      Fix: rewrite description and body in English; the project's German-conversation rule does not override agent-management's English MUST for agent files.
      Verify: `head -20` shows English content.
- [ ] [skill-vs-agent.rationale] No rationale section names the decisive dimensions for the agent-over-skill choice; absence is a BLOCKER per the rationale-documentation MUST.
      Where: full body — no section discusses skill-vs-agent choice.
      Fix: add a 2–4-bullet rationale section under "Rolle" or as a footer (e.g., specialization on Gemini prompt syntax + corporate design palette; fire-and-forget output shape).
      Verify: grep for "rationale" or "skill-vs-agent" in the body returns the new section.
- [ ] [agent-management.system-prompt-output-shape] The expected output shape (a markdown prompt-document under `spec/design/<typ>_<beschreibung>.md` with a fixed structure) is described but the system prompt does not state it in the role-opening section; it is reached only at Phase 3 (lines 186–260). The MUST requires the output shape to be stated as part of the role/output/method ordering.
      Where: lines 10–22 (role) vs. lines 186+ (output document spec).
      Fix: add a one-paragraph "Output shape" block right after the role section naming the output file path, sections, and Light/Dark variants.
      Verify: lines 1–40 contain the output-shape statement.

### WARNING

- [ ] [agent-management.system-prompt-order] Order is role → context (corporate design reference) → method (Phase 0–5) → output document spec embedded in Phase 3 → quality rules. The SHOULD requires role → output → method; the long corporate-design block delays the output and method statements.
      Where: lines 22–73 (corporate design data block) before any method or output content.
      Fix: move the corporate-design palette block into a sibling asset under `agents/gemini-graphic-prompt-generator/palette.md` and reference it; keep only role + output + method inline.
      Verify: lines 10–80 follow role → output → method ordering.
- [ ] [agent-management.system-prompt-length] Body is ~300 lines, modestly over the ~200-line soft target; the corporate-design table and the output-document template (lines 200–260) are prime candidates for sibling files.
      Where: full file.
      Fix: factor palette and output template into `agents/gemini-graphic-prompt-generator/`.
      Verify: `wc -l` returns ~200.
- [ ] [agent-management.write-effects-documented] Tools include `Write`; the SHOULD requires goals + preconditions of write effects. The body names targets (`spec/design/<typ>_<beschreibung>.md`) and the document structure but does not state preconditions ("do not overwrite existing files without confirmation", "create missing directory only inside spec/design/").
      Where: lines 186–195 (Phase 3 file naming).
      Fix: add a preconditions block before Phase 3 naming overwrite/conflict policy.
      Verify: body contains an explicit "preconditions" or "side-effects boundary" block.
- [ ] [skill-vs-agent.duplicate-prevention] Plausible overlap with peer agent `plant-info-document-generator` — both are generators that produce structured markdown documents under `spec/`. Functional cluster differs (visual prompts vs. plant info), but description-level negative triggers should make this explicit.
      Where: description line 4 (broad generator description).
      Fix: add a "don't use for" clause naming `plant-info-document-generator` (and skills like `gen-knowledge`).
      Verify: description contains "don't use for" clause.

### SUGGESTION

- [ ] [agent-management.tags] No `tags` field; adding `tags: [design, prompt-engineering]` would aid peer-cluster discovery per `skill-vs-agent` portfolio-wide consistency.
      Where: frontmatter, lines 1–8.
      Fix: add `tags: [design, prompts]` (≤5, lowercase kebab-case, ≤30 chars).
      Verify: `grep "^tags:" .claude/agents/gemini-graphic-prompt-generator.md` returns the field.
- [ ] [skill-vs-agent.rationale-counter] When adding the rationale section, naming at least one counter-dimension (e.g., "skill-bias: lifecycle — generation may be invoked many times") would satisfy the SHOULD.
      Where: future rationale section.
      Fix: include a counter-dimension bullet.
      Verify: rationale section names ≥1 counter-dimension.

### INFO

- [ ] [agent-management.model-rationale] Model pinned to `haiku` with rationale ("low reasoning, high throughput") on line 6 — satisfies the SHOULD. Plausibility check passes (template-based generation is haiku-appropriate).
      Where: frontmatter line 6.
      Fix: n/a (observation).
      Verify: n/a.
- [ ] [agent-review.referenced-assets] Body references `spec/design/KAMI-CHARACTER-REFERENCE.md` (line 86); file exists. No further sibling assets under `agents/gemini-graphic-prompt-generator/`.
      Where: filesystem.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
