---
review-type: agent-review
target: ".claude/agents/seed-data-validator.md"
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

# Agent Review: seed-data-validator

## Scope

Iteration 2 of this plan. The `agent-management` and `agent-review` specs have been revised: a project-distribution agent in a project whose root convention file (`CLAUDE.md`) authorizes a non-English documentation language for agent prose may author its `description` and body in that language. Kamerplanter's `CLAUDE.md` lines 9-11 explicitly authorize German for `.claude/agents/`, so what was a German-prose BLOCKER in iteration 1 demotes to INFO here.

Target: `.claude/agents/seed-data-validator.md` (frontmatter + body, ~620 lines, no sibling assets under `.claude/agents/seed-data-validator/`).
Specs applied: `agent-management` rev 7772341, `skill-vs-agent`, `review-plan`, `agent-review` rev 7772341 (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, factual correctness of the multi-source-verification methodology, and the dispatching skill (none declared).

## Summary

- BLOCKER: 3
- WARNING: 6
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three remaining MUST violations after the language relaxation: missing rationale section, missing upfront output contract, and consolidated write-effect goals/preconditions for the `Write`-tool side effects (report file + schema modifications under `schemas/`).
Next concrete action: author addresses the three remaining BLOCKERs (rationale section anchored in `skill-vs-agent`; explicit Output contract block; consolidated write-effect declaration covering both the report path and the in-place schema edits) and trims the 620-line body via sibling assets per the SHOULD on length.

## Findings

### BLOCKER

- [x] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/seed-data-validator.md:1-620` (no "Why this is an agent" section).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly context-window protection (large-volume reads of all `seed_data/*.yaml` and Pydantic models), specialization (multi-source verification methodology + agrobiology hand-off), and tool restriction (limited write surface to `schemas/` and `spec/analysis/`).
      Verify: A "Rationale" section near the top names ≥1 decisive dimension; grep returns ≥1 hit for "context-window", "specialization", or "self-contained".

- [x] [agent-management.output-shape] Expected output shape is described only in Phase 4 as a Markdown report skeleton with sub-sections; the file lacks an upfront "Output contract" stating what the parent caller receives and the full set of side-effect targets (report + schema files).
      Where: `.claude/agents/seed-data-validator.md:443-606`.
      Fix: Add an "Output contract" section near the top stating (a) what the parent receives (report path + chat summary shape), (b) the report's required sections, (c) all written paths: `spec/analysis/seed-data-validation-report.md` plus any modified `src/backend/app/migrations/seed_data/schemas/*.schema.yaml`, (d) overwrite policy for both.
      Verify: An "Output contract" section exists near the top; reading it tells a parent caller every deliverable and every side-effect target.

- [x] [agent-management.write-effects-documented] Agent declares `Write`, `Bash`, `WebSearch`, `WebFetch`. Body documents *that* schemas may be extended (Phase 0.4) and that a report is produced, but does not consolidate the goals and preconditions of those side effects upfront per `agent-management` acceptance.
      Where: `.claude/agents/seed-data-validator.md:5` (`tools: Read, Write, Glob, Grep, Bash, WebSearch, WebFetch`) vs. body (Phase 0.4 lines 238-270, Phase 4 lines 443-606).
      Fix: Add a "File outputs" / write-effect section consolidating: target paths (`schemas/*.schema.yaml`, `spec/analysis/seed-data-validation-report.md`), preconditions (Phase 0 findings before schema edits; only enum/field additions allowed, never deletions), overwrite policy, and the explicit invariant that production code under `app/` is never modified.
      Verify: Body contains a single consolidated write-effects section naming target paths and preconditions; grep for "schemas/" and "spec/analysis/" both return hits in that section.

### WARNING

- [ ] [agent-management.body-length] Body is ~620 lines, well above the SHOULD soft target of ~200 lines named in `agent-management.recommendations`. Long-form references (verification source tables, mistake checklists, full report skeleton) could move into `.claude/agents/seed-data-validator/`.
      Where: `.claude/agents/seed-data-validator.md:1-620`.
      Fix: Factor the source-tables (Botanik / Produkte) and the full report skeleton into sibling files under `.claude/agents/seed-data-validator/` and reference them from the body.
      Verify: Body length drops below ~250 lines; sibling folder exists and is referenced by relative path.

- [ ] [agent-review.duplicate-prevention] Description explicitly names a hand-off to `agrobiology-requirements-reviewer` (peer agent). The boundary is documented in prose but not in `description` as a negative trigger; per `agent-review.duplicate-prevention` overlap is a WARNING absent explicit negative triggers.
      Where: `.claude/agents/seed-data-validator.md:4` (description) vs. `.claude/agents/agrobiology-requirements-reviewer.md`.
      Fix: Add a negative trigger to `description`: "nicht für reine botanische Plausibilitätsprüfung — dafür `agrobiology-requirements-reviewer`; dieser Agent prüft Struktur + referenzielle Integrität + Schema und reicht botanische Findings als `[AGROBIO-CHECK]` weiter".
      Verify: `description` contains "nicht für" or equivalent naming the peer agent.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona, then Multi-Source-Rule, then Produkt-Verifikations-Methodik, then phases; the role-then-output-then-method ordering SHOULD is not honored — output shape only emerges in Phase 4.
      Where: `.claude/agents/seed-data-validator.md:10-441`.
      Fix: Restructure: persona → "Output contract" → procedure (Phases 0-5) → guardrails (3-source rule, verification matrix). Move the verification source tables to a sibling asset.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; `audit` and `quality-gate` would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/seed-data-validator.md:1-8` (frontmatter).
      Fix: Add `tags: [audit, quality-gate]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront whether the agent writes code or only researches. The body ultimately *does* edit schemas and produce a report, but the dispatch-time signal is missing.
      Where: `.claude/agents/seed-data-validator.md:10-441`.
      Fix: Add one explicit sentence near the top stating the agent edits `schemas/*.schema.yaml` (additive only) and writes the analysis report; production code is never modified.
      Verify: One sentence near the top names "schema edits", "additive", and "no production-code edits".

- [ ] [agent-review.tools-bidirectional] `Bash` is declared but the body never demonstrably invokes it (Phase 0/1 use Glob/Read/Grep; web verification uses `WebSearch`/`WebFetch`). Possible dead permission per `agent-review.tool-scope`.
      Where: `.claude/agents/seed-data-validator.md:5` (`tools: ..., Bash, ...`).
      Fix: Drop `Bash` from `tools` unless a legitimate bash use case is added (e.g. `python -m jsonschema` validation runs); or document the bash use case explicitly.
      Verify: Either `tools` no longer lists `Bash`, or body contains at least one explicit bash invocation block with rationale.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named; for this agent a plausible counter is interactivity (the user may want to confirm proposed schema additions before they land).
      Where: `.claude/agents/seed-data-validator.md:1-620` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming interactivity as the counter-dimension and explain why it was outweighed (e.g. additive-only constraint plus 3-source verification provides safety without mid-flow confirmation).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.english-body] Description and body are German throughout; per the revised `agent-management.Structure` exception this is acceptable for `distribution: project` agents in a project whose `CLAUDE.md` authorizes German for agent prose. Kamerplanter's `CLAUDE.md` lines 9-11 declare German as the project documentation language. Recorded as INFO, not BLOCKER.
      Where: `.claude/agents/seed-data-validator.md:4` (description), lines 10-620 (body).
      Fix: n/a (observation — language exception applies).
      Verify: n/a.

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` with the comment "datengetriebenes Reasoning"; satisfies `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/seed-data-validator.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; no plugin-co-located asset references appear.
      Where: `.claude/agents/seed-data-validator.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/seed-data-validator.md:1-620`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-27 — skill-vs-agent.rationale-section — added "Rationale: Skill vs Agent" section naming self-contained input/output, specialization, context-window protection plus interactivity counter-dimension — verified: file content review
2026-04-27 — agent-management.output-shape — added "Output Contract" section listing report path, all required report sub-sections, schema-edit targets, chat-summary shape, no go/no-go — verified: file content review
2026-04-27 — agent-management.write-effects-documented — added "Write Effects" section naming schemas/ + spec/analysis/ paths, additive-only invariant, no production-code-edits guard, overwrite/additive idempotency — verified: file content review
