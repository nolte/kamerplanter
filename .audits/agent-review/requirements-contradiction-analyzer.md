---
review-type: agent-review
target: ".claude/agents/requirements-contradiction-analyzer.md"
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

# Agent Review: requirements-contradiction-analyzer

## Scope

Iteration 2 of this plan. The `agent-management` and `agent-review` specs have been revised: a project-distribution agent in a project whose root convention file (`CLAUDE.md`) authorizes a non-English documentation language for agent prose may author its `description` and body in that language. Kamerplanter's `CLAUDE.md` lines 9-11 explicitly authorize German for `.claude/agents/`, so what was a German-prose BLOCKER in iteration 1 demotes to INFO here. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`, `tags`) MUST remain English.

Target: `.claude/agents/requirements-contradiction-analyzer.md` (frontmatter + body, ~237 lines, no sibling assets under `.claude/agents/requirements-contradiction-analyzer/`).
Specs applied: `agent-management` rev 7772341, `skill-vs-agent`, `review-plan`, `agent-review` rev 7772341 (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, factual correctness of the RAG/contradiction methodology, the dispatching skill (none declared).

## Summary

- BLOCKER: 3
- WARNING: 5
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three MUST violations remain after the language relaxation: missing rationale section, missing upfront output contract, and write-effect goals/preconditions undocumented despite `Write`/`Bash` in tools.
Next concrete action: author addresses the three remaining BLOCKERs (rationale section anchored in `skill-vs-agent`; explicit Output contract block; consolidated write-effect goals/preconditions for the two written analysis paths).

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-237` (no "Why this is an agent" section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly context-window protection (large-volume reads of all `spec/req/`, `spec/nfr/`, `spec/ui-nfr/`), specialization (RAG cross-document reasoning), and self-contained input/output (single deliverable report).
      Verify: A "Rationale" section near the top names ≥1 decisive dimension; grep for "context-window", "specialization", or "self-contained" inside the body returns ≥1 hit.

- [ ] [agent-management.output-shape] System prompt's expected output shape is described only in Phase 3/4 as a Markdown report path plus a JSON file; the file does not declare a single explicit "Output contract" upfront stating what the agent returns to the parent.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:131-236` (Phase 3-4 block).
      Fix: Add an "Output contract" section near the top stating (a) what is returned to the caller (path + chat summary shape), (b) the report's required structural sections, (c) the two written paths `spec/analysis/contradiction-report.md` and `spec/analysis/requirements-index.json`, (d) the overwrite policy.
      Verify: An "Output contract" section exists near the top; reading it tells a parent caller the exact deliverable shape and the two written paths.

- [ ] [agent-management.write-effects-documented] Agent declares `Write` and `Bash` (write/execution tools) but the system prompt does not consolidate the goals and preconditions of those side effects per the `agent-management` acceptance criterion (file-write targets, preconditions, overwrite behavior).
      Where: `.claude/agents/requirements-contradiction-analyzer.md:5` (`tools: Read, Write, Glob, Grep, Bash`) vs. body lacking a write-goals declaration.
      Fix: Add a "File outputs" subsection naming the two written paths, when they are written, what triggers an overwrite, and what preconditions must hold (e.g. `spec/analysis/` directory exists or is created by the agent).
      Verify: Body contains an explicit "File outputs" / write-goals section naming both target paths and preconditions.

### WARNING

- [ ] [agent-review.tools-bidirectional] `Bash` is declared but the body never demonstrably invokes it — Phase 1 names "Glob-Patterns" only (covered by `Glob`), and no bash command appears in any phase. Dead permission per `agent-review.tool-scope`; SHOULD prefer dedicated tools.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:5` (`tools: Read, Write, Glob, Grep, Bash`).
      Fix: Drop `Bash` from `tools` unless a legitimate bash use case is added to the procedure; or document a bash use case (e.g. file counts, hashes) in the body.
      Verify: Either `tools` no longer lists `Bash`, or body contains at least one explicit bash invocation block with rationale.

- [ ] [agent-review.duplicate-prevention] Plausible capability overlap with `tech-stack-architect`: both surface contradictions and gaps across REQ/NFR specs. Description triggers ("Anforderungsqualität sicherstellen", "Spezifikationsreviews", "QA-Vorbereitung") could be matched by either agent.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:4` (description) vs. peer `.claude/agents/tech-stack-architect.md`.
      Fix: Add explicit negative triggers to `description` ("nicht für tech-stack-architektonische Reviews — dafür `tech-stack-architect`; nicht für Spec-Status-Übersicht").
      Verify: `description` contains "nicht für" or equivalent negation naming at least one closest peer.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona statement and immediately enters Phase 1; the role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is not honored — output shape only emerges in Phase 3.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:10-130`.
      Fix: Restructure so the role paragraph is followed by the new "Output contract" section, then the procedure (Phases 1-4).
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; `review` and `audit` would apply per `agent-management.tag-vocabulary` SHOULD and would let `skill-agent-catalog` cluster this with other review-type artifacts.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, audit]` after the existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare whether the agent writes code or only researches; per `agent-management.recommendations` SHOULD the calling Claude must be able to read this distinction at dispatch time.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:10-237`.
      Fix: Add a one-line explicit statement near the top: "This agent researches and emits a report — it does not modify production source code; the only files it writes are the analysis artifacts under `spec/analysis/`."
      Verify: One sentence near the top names "researches", "no source-code edits", and the only written paths.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is interactivity (the user might want to confirm the contradiction list before files are written).
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-237` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming interactivity as the counter-dimension and the reason it was outweighed (e.g. fire-and-forget RAG run, results inspected post-hoc).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.english-body] Description and body are German throughout; per the revised `agent-management.Structure` exception this is acceptable for `distribution: project` agents in a project whose `CLAUDE.md` authorizes German for agent prose. Kamerplanter's `CLAUDE.md` lines 9-11 declare German as the project documentation language. Recorded as INFO, not BLOCKER.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:4` (description), lines 10-237 (body).
      Fix: n/a (observation — language exception applies).
      Verify: n/a.

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: opus` and the comment line states a rationale ("RAG-basierte Widerspruchsanalyse … grosse Spec-Mengen … tiefes Cross-Document-Reasoning"), satisfying `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; no plugin-co-located asset references appear.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user (no `Skill(`, `Skill tool`, or equivalent dispatch phrasing); satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/requirements-contradiction-analyzer.md:1-237`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
