---
review-type: agent-review
target: ".claude/agents/target-audience-analyzer.md"
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

# Agent Review: target-audience-analyzer

## Scope

Target: `.claude/agents/target-audience-analyzer.md` (frontmatter + body, ~305 lines, no sibling assets under `.claude/agents/target-audience-analyzer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, factual correctness of the persona/JTBD methodology, the dispatching skill (none declared).

## Summary

- BLOCKER: 4
- WARNING: 5
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations: body is German, no rationale section, no upfront output contract, the agent declares `Write` but the body imperatively creates a report file without documented goals/preconditions per `agent-management.acceptance`. Plausible overlap with the persona-review agents and the `audience-identify` skill.
Next concrete action: author addresses the four BLOCKERs (translate body, add rationale, lift output contract, document the report-file write goals/preconditions or refactor into skill-orchestrates-agent) and clarifies the boundary against `audience-identify` (skill) and persona-reviewer agents.

## Findings

### BLOCKER

- [ ] [agent-management.english-body] Frontmatter `description` and the entire body are German; `agent-management` Structure-MUST requires English content for token efficiency and portability.
      Where: `.claude/agents/target-audience-analyzer.md:4` (description) and lines 10-305 (entire body — phase headings, table columns, persona bullets).
      Fix: Translate description, all section headings ("Phase 1: Anforderungsdokumente einlesen" → "Phase 1: Read requirement documents"), persona dimensions, and report skeleton to English. Keep German only when literally quoting REQ/NFR identifiers.
      Verify: A `lang detect` pass on body returns >95% English; section headings read `## Phase 1:` etc. in English.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/target-audience-analyzer.md:1-305` (no rationale section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly *specialization* (UX-research/JTBD persona sharpens audience derivation), *context-window protection* (large reads of `spec/req/`, `spec/nfr/`, `spec/stack.md`, `CLAUDE.md`), and *self-contained input/output* (REQ/NFR set in, audience report out). Cite at least one counter-dimension.
      Verify: Section reading "## Rationale" or equivalent exists naming ≥1 decisive dimension; grep returns ≥1 hit for "specialization" or "context-window".

- [ ] [agent-management.output-shape] Expected output shape is described only in Phase 4 as a Markdown report skeleton at `spec/analysis/target-audience-report.md` plus the Phase 5 chat summary; the file lacks an upfront "Output contract" stating what the parent caller receives.
      Where: `.claude/agents/target-audience-analyzer.md:170-305`.
      Fix: Add an "Output contract" section near the top stating: (a) what is returned (path + chat summary), (b) the report's seven required structural sections (Executive Summary, primäre/sekundäre Zielgruppen, unterversorgte Nutzergruppen, Anwendungsgebiete, Persona-Gap, Matrix, Empfehlungen), (c) explicit acknowledgement of the file-write side effect.
      Verify: A "Output contract" section exists near the top; reading it tells a parent caller the deliverable shape.

- [ ] [agent-management.write-effects-documented] Agent declares `Write` and Phase 4 imperatively says "Erstelle `spec/analysis/target-audience-report.md`"; per `agent-management.acceptance` write goals and preconditions MUST be documented when the agent performs side effects.
      Where: `.claude/agents/target-audience-analyzer.md:5` (`tools: Read, Write, Glob, Grep`) vs. body line 171 ("Erstelle `spec/analysis/target-audience-report.md`").
      Fix: Add an explicit "File outputs" subsection near the top declaring (a) the single write target `spec/analysis/target-audience-report.md`, (b) overwrite policy (always overwrite vs. append), (c) preconditions (e.g. directory exists or is created). Alternatively, refactor into a skill-orchestrates-agent pattern (the agent returns the report content, an orchestrator skill persists it) — drop `Write` in that case.
      Verify: A "File outputs" section exists naming target + preconditions, OR `Write` is removed and the body returns content rather than persisting.

### WARNING

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with the `audience-identify` skill (audience identification per `spec/project/audience-identification/`) and with the persona-review agents (`agrobiology-requirements-reviewer`, `cannabis-indoor-grower-reviewer`, `casual-houseplant-user-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer`) which already adopt persona perspectives.
      Where: `.claude/agents/target-audience-analyzer.md:4` (description) vs. peers `audience-identify` (skill) and the persona-reviewer agents.
      Fix: Add explicit negative triggers to `description` ("don't use for canonical audience-list authoring per `audience-identify` spec — use the `audience-identify` skill; don't use for reviewing requirements through a single fixed persona — use the matching persona-reviewer agent"). Per `skill-vs-agent.duplicate-prevention` plausibly-overlapping artifacts SHOULD propose a clearer split.
      Verify: `description` contains "don't use for" naming at least the closest skill and the persona-reviewer cluster.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona ("Du bist ein erfahrener Produkt-Stratege"), then a Hintergrund-bullet list, then jumps into Phase 1; the role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is not honored — output shape only emerges in Phase 4.
      Where: `.claude/agents/target-audience-analyzer.md:10-305`.
      Fix: Restructure: persona paragraph → "Output contract" → method (Phases 1-5). Move the Hintergrund bullets after the contract.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; tags `review` and `audience` would apply per `agent-management.tag-vocabulary` SHOULD; the agent's own description ("Zielgruppen erfassen, Nutzerprofile ableiten, Persona-Analysen durchführen") matches `audience` directly.
      Where: `.claude/agents/target-audience-analyzer.md:1-8` (frontmatter).
      Fix: Add `tags: [audience, review]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront whether the agent writes code or only researches; the writes intent (single Markdown report) is implicit and only surfaces in Phase 4. Per `agent-management.recommendations` SHOULD this distinction must be visible at dispatch time.
      Where: `.claude/agents/target-audience-analyzer.md:10-305`.
      Fix: Add a one-line statement near the top: "This agent researches and writes a single analysis file — `spec/analysis/target-audience-report.md`. It does not modify source code or any other documentation."
      Verify: One sentence near the top declares write scope and the single named target path.

- [ ] [skill-vs-agent.no-skill-dispatch-strict-check] Spec MUST forbids body invoking the Skill tool. The body of this agent does not invoke the Skill tool, but the agent is thematically adjacent to the `audience-identify` skill, so reviewers should explicitly verify no future "see audience-identify" prose drifts toward dispatch syntax.
      Where: `.claude/agents/target-audience-analyzer.md:1-305` (no `Skill(` references currently).
      Fix: Keep this finding informational — it is currently a SHOULD-tier hygiene check. If the body is later updated to mention `audience-identify`, the wording must remain descriptive (e.g. "this audience-list is similar in scope to the `audience-identify` skill"), never a dispatch (`Skill audience-identify`).
      Verify: `grep -E "Skill\(|Skill tool|Skill <" .claude/agents/target-audience-analyzer.md` returns zero matches now and after future edits.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is *interactivity* (a product-strategy author may want to approve the persona list mid-flow), which would push toward a skill.
      Where: `.claude/agents/target-audience-analyzer.md:1-305` (will be addressed once rationale section exists).
      Fix: Within the rationale section, add one bullet naming interactivity (persona-list approval) as the counter-dimension and the reason it was outweighed (e.g. post-hoc inspection of the report).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` and the comment line states a rationale ("Marktanalyse + Persona-Ableitung aus Specs; sonnet adaequat fuer strukturierte Synthese"), satisfying `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/target-audience-analyzer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; matches project-scoped reuse.
      Where: `.claude/agents/target-audience-analyzer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-review.tools-bidirectional-clean] Each declared tool (`Read`, `Write`, `Glob`, `Grep`) has a demonstrable use in the procedure (Read/Glob/Grep in Phase 1; Write implicit in Phase 4 — addressed by BLOCKER above). No dead permissions and no missing-but-needed tools (no Bash use in body).
      Where: `.claude/agents/target-audience-analyzer.md:5`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
