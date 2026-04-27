---
review-type: agent-review
target: ".claude/agents/seed-data-validator.md"
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

# Agent Review: seed-data-validator

## Scope

Target: `.claude/agents/seed-data-validator.md` (frontmatter + body, ~620 lines, no sibling assets under `.claude/agents/seed-data-validator/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, factual correctness of the multi-source verification methodology, the dispatching/companion `agrobiology-requirements-reviewer` agent (referenced but not under review here).

## Summary

- BLOCKER: 4
- WARNING: 6
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations: body is German, no rationale section, write-effect goals/preconditions only implied, length exceeds 200 lines without sibling-asset factoring, output-shape contract emerges only deep in Phase 4.
Next concrete action: author addresses the four BLOCKERs (translate body to English, add rationale section, lift output contract to top, document file-write goals/preconditions explicitly) and decides whether to factor long-form rules into `agents/seed-data-validator/`.

## Findings

### BLOCKER

- [ ] [agent-management.english-body] Frontmatter `description` and the entire 620-line system-prompt body are German; `agent-management` Structure-MUST requires English content.
      Where: `.claude/agents/seed-data-validator.md:4` (description) and lines 10-620 (entire body — every phase heading, table column, and bullet).
      Fix: Translate description and all body content to English; keep German only when literally quoting spec terms, taxonomic names, or German-only finding tags such as `[AGROBIO-CHECK]` (which is itself a label — keep). Note: project CLAUDE.md German-default convention does not override this MUST.
      Verify: A `lang detect` pass on body returns >95% English; section headings read `## Phase 0:` etc. in English.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/seed-data-validator.md:1-620` (no rationale section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly *context-window protection* (large-volume reads of all `seed_data/*.yaml` and `schemas/*.yaml`), *specialization* (agronomic/data-quality persona), and *parallelism* (validation can run alongside agrobiology-reviewer). Cite at least one counter-dimension if applicable.
      Verify: Section reading "## Rationale" or equivalent exists naming ≥1 decisive dimension; grep for "context-window", "specialization", or "parallelism" returns ≥1 hit.

- [ ] [agent-management.output-shape] Expected output shape (the report at `spec/analysis/seed-data-validation-report.md`) is described only deep in Phase 4 (~line 446); the file lacks an upfront "Output contract" section the calling skill/parent can consume without reading 440 lines first.
      Where: `.claude/agents/seed-data-validator.md:445-606`.
      Fix: Add an "Output contract" section near the top stating: (a) what is returned (path + chat summary), (b) report structural sections, (c) explicit declaration that the agent writes a Markdown file at `spec/analysis/seed-data-validation-report.md` (and may modify schemas), (d) overwrite policy.
      Verify: A "Output contract" section exists near the top; reading it tells a parent caller the deliverable shape.

- [ ] [agent-management.write-effects-documented] Agent declares `Write`, `Edit`, and `Bash` (write/execution tools) and Phase 0.4 mandates extending JSON-Schema files under `schemas/` — yet the system prompt does not declare write-effect goals and preconditions per `agent-management.acceptance` ("targets and preconditions of side effects").
      Where: `.claude/agents/seed-data-validator.md:5` (`tools: Read, Write, Glob, Grep, Bash, WebSearch, WebFetch`) vs. body Phase 0.4 (~line 238) which silently mandates schema edits.
      Fix: Add an explicit "File outputs and edits" subsection near the top declaring (a) write target `spec/analysis/seed-data-validation-report.md`, (b) edits to `src/backend/app/migrations/seed_data/schemas/*.yaml` allowed only when Phase 0.4 conditions hold (field-missing, enum-missing, schema-missing), (c) preconditions (e.g. backup/diff visible in PR, no edits to YAML data files), (d) the seed YAML files themselves are read-only for this agent.
      Verify: A "File outputs and edits" section exists; it names schema-write targets, preconditions, and confirms YAML data files are read-only.

### WARNING

- [ ] [agent-management.length-target] Body is ~620 lines, ~3× the ~200-line soft target in `agent-management.recommendations` SHOULD; long-form material (Multi-Source verification tables, schema-quality checklist, report skeleton) belongs in `agents/seed-data-validator/` sibling files.
      Where: `.claude/agents/seed-data-validator.md:10-620`.
      Fix: Factor the multi-source verification rules (lines ~16-145), schema-quality checklist (lines ~270-282), and full report skeleton (lines ~445-606) into sibling files under `.claude/agents/seed-data-validator/` referenced by relative path; keep the agent body to the procedure spine.
      Verify: Body is ≤300 lines; `.claude/agents/seed-data-validator/` contains the factored references; the agent body links them by relative path only.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap: description names cooperation with `agrobiology-requirements-reviewer` (botanical depth) and the `plant-info-to-seed-yaml` agent converts plant-info docs to YAML. The boundary between "validate seed data" and "produce/extend seed YAMLs" is plausibly fuzzy.
      Where: `.claude/agents/seed-data-validator.md:4` (description) vs. peers `agrobiology-requirements-reviewer`, `plant-info-to-seed-yaml`.
      Fix: Add explicit negative triggers to `description` ("don't use for botanical fact-checking — that's `agrobiology-requirements-reviewer`; don't use for converting plant-info Markdown to YAML — that's `plant-info-to-seed-yaml`"). The current prose mentions cooperation but no negative triggers.
      Verify: `description` contains "don't use for" or equivalent negation naming at least the two closest peers.

- [ ] [agent-management.prompt-structure-order] System prompt opens with the persona, then jumps into the Multi-Source verification rules; role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is not honored.
      Where: `.claude/agents/seed-data-validator.md:10-444`.
      Fix: Restructure so that after the persona paragraph the next section is "Output contract", then the procedure (Phase 0 → 5). Move multi-source verification rules into a sibling reference (per length-target finding above).
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; tags `audit` and `quality-gate` would apply per `agent-management.tag-vocabulary` SHOULD; the agent's own description ("Datenqualitaet, Vollstaendigkeit, Schema-Konformitaet") matches both.
      Where: `.claude/agents/seed-data-validator.md:1-8` (frontmatter).
      Fix: Add `tags: [audit, quality-gate]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront whether the agent writes code or only researches; the writes intent (schema YAMLs + analysis report) only emerges via Phase 0.4 and Phase 4.
      Where: `.claude/agents/seed-data-validator.md:10-620`.
      Fix: Add a one-line statement near the top: "This agent researches and writes — it edits JSON Schema YAMLs under `schemas/` when Phase 0.4 conditions hold, and writes an analysis report at `spec/analysis/seed-data-validation-report.md`. It never edits seed YAML data files or backend Python source."
      Verify: One sentence near the top declares write scope and named paths/exclusions.

- [ ] [agent-review.tools-bidirectional] `Bash` is declared but the body never demonstrably invokes it — Phase 0/1/2/3 use Glob/Read/Grep/WebSearch/WebFetch only. Dead permission per `agent-review.tool-scope`; SHOULD prefer dedicated tools.
      Where: `.claude/agents/seed-data-validator.md:5` (`tools: ..., Bash, ...`).
      Fix: Drop `Bash` unless a legitimate use case (e.g. running `python -m yamllint`, schema-validate scripts) is added to the procedure with explicit invocation; or document the bash use case.
      Verify: Either `tools` no longer lists `Bash`, or the body contains an explicit bash invocation block with rationale.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is *interactivity* (an author may want to approve schema edits before they land), which would push toward a skill.
      Where: `.claude/agents/seed-data-validator.md:1-620` (will be addressed once rationale section exists).
      Fix: Within the rationale section, add one bullet naming interactivity (schema-edit approval) as the counter-dimension and the reason it was outweighed (e.g. PR review provides post-hoc gate).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` and the comment line states a rationale ("Validierung von YAML-Seeds + Schema-Erweiterung mit Web-Recherche; sonnet adaequat fuer datengetriebenes Reasoning"), satisfying `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/seed-data-validator.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; matches project-scoped reuse.
      Where: `.claude/agents/seed-data-validator.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; the cooperation note with `agrobiology-requirements-reviewer` is descriptive (markers `[AGROBIO-CHECK]` only) and does not dispatch a skill.
      Where: `.claude/agents/seed-data-validator.md:1-620`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
