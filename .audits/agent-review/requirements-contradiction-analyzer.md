---
review-type: agent-review
target: ".claude/agents/requirements-contradiction-analyzer.md"
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

# Agent Review: requirements-contradiction-analyzer

## Scope

Target: `.claude/agents/requirements-contradiction-analyzer.md` (frontmatter + body, ~237 lines, no sibling assets under `.claude/agents/requirements-contradiction-analyzer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, factual correctness of the RAG/contradiction methodology, the dispatching skill (none declared).

## Summary

- BLOCKER: 4
- WARNING: 5
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations: body is German, no rationale section, output contract not declared upfront, `Write` declared on a research-shaped agent without write-effect goals/preconditions documented and with potential overlap to a write-orchestrator skill.
Next concrete action: author addresses the four BLOCKERs (translate body to English, add rationale section anchored in `skill-vs-agent`, declare an explicit output contract upfront, document goals/preconditions of file writes or refactor into skill-orchestrates-agent pattern).

## Findings

### BLOCKER

- [ ] [agent-management.english-body] Frontmatter `description` and the entire system-prompt body are in German; `agent-management` Structure-MUST requires English content for token efficiency and portability.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:4` (description) and lines 10-237 (entire body, all phase headings, bullets, tables).
      Fix: Translate description, all section headings ("Phase 1: Dokumente sammeln" → "Phase 1: Collect documents"), bullets, tables, and example strings to English; keep German only when literally quoting spec terms or German-only requirement IDs. Note: project CLAUDE.md German-default convention does not override the `agent-management` MUST — agents are tooling artifacts.
      Verify: A `lang detect` pass on body returns >95% English; `## Phase 1:` reads English; description names triggers in English.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-237` (no "Why this is an agent" section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly *context-window protection* (large-volume reads of all `spec/req/`, `spec/nfr/`, `spec/ui-nfr/`), *specialization* (RAG cross-document reasoning), and *self-contained input/output* (single deliverable report). Cite at least one counter-dimension if applicable.
      Verify: Section reading "## Rationale" or equivalent exists naming ≥1 decisive dimension; grep for "context-window", "specialization", or "self-contained" inside the body returns ≥1 hit.

- [ ] [agent-management.output-shape] System prompt's expected output shape is described only in Phase 3/4 as a Markdown report path plus a JSON file, but the file does not declare a single explicit "Output contract" upfront stating what the agent returns to the parent.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:131-236` (Phase 3-4 block).
      Fix: Add an "Output contract" section near the top stating: (a) what is returned to the caller (path + chat summary shape), (b) the report's required structural sections, (c) explicit acknowledgement that the agent writes files at `spec/analysis/contradiction-report.md` and `spec/analysis/requirements-index.json` (file-write side effects), (d) the overwrite policy. Per `agent-management.acceptance`, write-side-effect targets and preconditions MUST be documented.
      Verify: A "Output contract" section exists near the top; reading just that section tells a parent caller the exact deliverable shape and the two written paths.

- [ ] [agent-management.write-effects-documented] Agent declares `Write` and `Bash` (write/execution tools) but the system prompt does not document the goals and preconditions of those side effects per `agent-management` acceptance criterion (file writes targets, preconditions, overwrite behavior).
      Where: `.claude/agents/requirements-contradiction-analyzer.md:5` (`tools: Read, Write, Glob, Grep, Bash`) vs. body lacking write-goals declaration.
      Fix: Either (a) add a "File outputs" subsection naming the two written paths, when they are written, what triggers an overwrite, and what preconditions must hold (e.g. `spec/analysis/` directory exists or is created); or (b) refactor into a skill-orchestrates-agent pattern (research agent returns the report content, an orchestrator skill persists it). Option (a) is the lower-friction fix.
      Verify: Body contains an explicit "File outputs" / write-goals section naming both target paths and preconditions.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Bash` is declared but the body never demonstrably invokes it — Phase 1 names "Glob-Patterns" only (covered by `Glob`), and no bash command appears in any phase. Dead permission per `agent-review.tool-scope` SHOULD prefer dedicated tools.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:5` (`tools: Read, Write, Glob, Grep, Bash`).
      Fix: Drop `Bash` from `tools` unless a legitimate bash use case is added to the procedure (e.g. counting files, computing hashes); or document the bash use case in the body. Prefer dedicated `Glob`/`Grep`/`Read` for read-only research per `agent-management.tool-access` SHOULD.
      Verify: Either `tools` no longer lists `Bash`, or body contains at least one explicit bash invocation block with rationale.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with `tech-stack-architect`: both surface contradictions and gaps across REQ/NFR specs. Description triggers ("Anforderungsqualität sicherstellen", "Spezifikationsreviews", "QA-Vorbereitung") could be matched by either agent.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:4` (description) vs. peer `tech-stack-architect`.
      Fix: Add explicit negative triggers to `description` ("don't use for tech-stack architectural review — use `tech-stack-architect`; don't use for spec status overview — use the `spec-status` skill"). Negative triggers are SHOULD when overlap is plausible.
      Verify: `description` contains "don't use for" or equivalent negation naming at least one closest peer.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona statement and immediately enters Phase 1; the role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is not honored — output shape only emerges in Phase 3.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:10-130`.
      Fix: Restructure so that after the role paragraph the next section is "Output contract" (what the parent gets), then the procedure (Phases 1-4). Move Phase 3 report skeleton up as the contract reference.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; tag vocabulary `review` and `audit` would apply per `agent-management.tag-vocabulary` SHOULD and would let `skill-agent-catalog` cluster this with other review-type artifacts.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, audit]` after the existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare whether the agent writes code or only researches; per `agent-management.recommendations` SHOULD the calling Claude must be able to read this distinction at dispatch time.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:10-237`.
      Fix: Add a one-line explicit statement near the top: "This agent researches and emits a report — it does not modify production source code; the only files it writes are the analysis artifacts under `spec/analysis/`."
      Verify: One sentence near the top declares "researches", "no source-code edits", and names the only written paths.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is *interactivity* (the user might want to confirm the contradiction list before files are written, which would push toward a skill).
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-237` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming interactivity (mid-flow confirmation) as the counter-dimension and the reason it was outweighed (e.g. fire-and-forget RAG run, results inspected post-hoc).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: opus` and the comment line states a rationale ("RAG-basierte Widerspruchsanalyse … grosse Spec-Mengen … tiefes Cross-Document-Reasoning"), satisfying `agent-management.model-selection` SHOULD; informational, no action required.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value, and the agent contains no plugin-co-located asset references; matches the project-scoped reuse pattern.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user (no `Skill(`, `Skill tool`, or equivalent dispatch phrasing); satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-237`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
