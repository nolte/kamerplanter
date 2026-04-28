---
review-type: agent-review
target: ".claude/agents/fullstack-developer.md"
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
supersedes: "previous iteration of this plan (status: in-progress) — see git history of this file"
---

# Agent Review: fullstack-developer

## Scope

Target: `.claude/agents/fullstack-developer.md` (frontmatter + body; no sibling assets exist under `.claude/agents/fullstack-developer/`).
Specs applied: `agent-management` (rev `7772341`), `skill-vs-agent` (rev `0e3b6f9`), `review-plan` (rev `0e3b6f9`), `agent-review` (rev `7772341`).
Narrowing: none — full review per `agent-review` Phase 1–4.
Iteration: 2. The first iteration ran against spec revision `0e3b6f9`. The `agent-management.Structure` and `agent-review.Checks-derived-from-agent-management` clauses were relaxed at revision `7772341`: `distribution: project` agents in a project that declares a non-English documentation language and authorizes that language for agent prose may author the `description` value and the system-prompt body in the project language. Kamerplanter's `CLAUDE.md` (lines 9–11) declares German as the documentation language and explicitly authorizes German for `.claude/agents/` prose. Consequence: the iteration-1 `BLOCKER` for German body+description is downgraded to `INFO` here. Frontmatter field names and technical identifier values (`name`, `distribution`, `tools`, `model`, `tags`) MUST remain English — those are still hard rules. No iteration-1 quick-wins have landed for this agent; all carry-over findings remain open.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style (handled by linting), the orchestrator that dispatches this agent.

## Summary

- BLOCKER: 1
- WARNING: 5
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — the missing skill-vs-agent rationale section still blocks acceptance.
Next concrete action: add a rationale section that names at least one decisive `skill-vs-agent` dimension; address the body-length and prompt-order WARNINGs in the same pass.

## Findings

### BLOCKER

- [x] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/fullstack-developer.md` (no rationale section anywhere in the body).
      Fix: add a short rationale section (paragraph or 2–4 bullets) naming at least one decisive dimension from the `skill-vs-agent` table (for example: context-window protection during multi-file edits, specialization via narrow stack focus, parallelism alongside review/test agents); name at least one counter-dimension when the call was close.
      Verify: a section header or bullet list explicitly references one of the seven decision dimensions from `skill-vs-agent`.

### WARNING

- [ ] [agent-management.tools-bash-vs-dedicated] `Bash` is declared without the body documenting which operations require it beyond what `Read`/`Grep`/`Glob`/`Edit` already cover; only running ruff/eslint/tsc is mentioned as a Bash use case.
      Where: `.claude/agents/fullstack-developer.md:5` (tools list) and lines around 138–142 (only Bash use shown).
      Fix: add one sentence in the body stating Bash is used solely for running lint/typecheck/test commands and confirming dedicated tools are used for reads, searches, and edits.
      Verify: the body contains an explicit Bash-justification sentence naming the specific operations that require it.

- [ ] [agent-management.structure-prompt-order] The system prompt does not open with role and boundaries followed by expected output format and only then the working method; the long "Pflichtlektuere" section (style guides, NFRs, UI-NFRs, project structure) precedes the output-shape statement at lines 135–141.
      Where: `.claude/agents/fullstack-developer.md:14–141` (procedure precedes output format).
      Fix: reorder so role/boundaries come first, then "Output: files in correct project structure + tests + ruff/eslint clean + tsc clean", then the working method (style-guide reading, project structure, etc.).
      Verify: the first three top-level sections follow the role → output → procedure order.

- [ ] [agent-management.body-length-200] Body length is approximately 246 lines, exceeding the soft 200-line target without factoring long-form material (style-guide pointers, project tree, post-implementation handoff blocks) into `agents/fullstack-developer/` sibling files.
      Where: `.claude/agents/fullstack-developer.md` (file ends at line 246).
      Fix: move the project-tree diagram, the UI-NFR cheat-sheet, and the three downstream-handoff blocks (UI-Review, Security-Review, Documentation) into sibling files under `agents/fullstack-developer/` and reference them by relative path.
      Verify: `wc -l .claude/agents/fullstack-developer.md` reports ≤ 200 lines.

- [ ] [skill-vs-agent.duplicate-prevention] Capability statement overlaps with the `implement` skill ("Feature aus REQ implementieren") — both cover full-stack feature implementation from REQ documents, raising a duplicate-capability concern within the project's surface.
      Where: `.claude/agents/fullstack-developer.md:4` (description) vs. the `implement` skill listed in the available-skills set.
      Fix: either narrow the agent's `description` so its trigger surface no longer overlaps with `implement` (for example, "execution layer dispatched by the `implement` skill, not invoked directly by the user"), or document the orchestration relationship in the rationale section.
      Verify: a side-by-side comparison of the two `description` lines shows no equivalent trigger phrasing.

- [ ] [agent-management.write-target-documentation] `Write` and `Edit` are declared but the body does not state the goals and preconditions of those write effects (which directories the agent may create files in, when overwrite is allowed, what happens on rerun) per the `agent-management` acceptance criterion for write-capable agents.
      Where: `.claude/agents/fullstack-developer.md:5` (tools include `Write`, `Edit`) and lines 137–141 ("Ausgabe nach Implementierung").
      Fix: add a short "Write targets and preconditions" block naming the project-tree directories the agent is permitted to write into (`src/backend/app/...`, `src/frontend/src/...`, `src/helm/...`, `src/backend/tests/...`), the overwrite policy on rerun, and the precondition that the file's containing directory follows the documented project structure.
      Verify: the body contains a "Write targets" or equivalent block that documents permitted paths, overwrite policy, and preconditions.

### SUGGESTION

- [ ] [agent-management.tags-vocabulary] No `tags` field is declared, so the catalog and peer-cluster lookups (`skill-vs-agent` Portfolio-wide consistency) cannot place this agent in a functional cluster.
      Where: `.claude/agents/fullstack-developer.md:1–8` (frontmatter).
      Fix: add a `tags` list with at most five lowercase kebab-case entries (e.g., `[implementation, backend, frontend, fullstack]`); reuse starter-vocabulary terms where they fit.
      Verify: frontmatter contains a `tags` field whose entries each match `^[a-z][a-z0-9-]{0,29}$` and the list has ≤5 items.

### INFO

- [ ] [agent-management.structure-language] Frontmatter `description` and the system-prompt body are authored in German. Per the relaxed `agent-management.Structure` clause (revision `7772341`) and Kamerplanter's project-language authorization in `CLAUDE.md` lines 9–11, German prose is permitted for this `distribution: project` agent. Iteration 1 flagged this as a `BLOCKER`; under the current spec revision the finding is reclassified as a neutral observation.
      Where: `.claude/agents/fullstack-developer.md:4` (description) and lines 10–246 (body).
      Fix: n/a (observation; project authorization in place).
      Verify: n/a.

- [ ] [agent-management.distribution] `distribution: project` is declared and matches the file's residence under `.claude/agents/`; no plugin-bundle path is referenced from the body.
      Where: `.claude/agents/fullstack-developer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] `model: opus` is pinned with an inline rationale comment (line 6: complex multi-file changes, large context window, NFR compliance); the rationale is plausible for an implementation agent.
      Where: `.claude/agents/fullstack-developer.md:6–7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-28 — skill-vs-agent.rationale — added rationale section naming 3 decisive dimensions (context-window impact, specialization, parallelism) and 1 counter-dimension (interactivity) — verified: section header `## Rationale: Skill vs Agent` exists in body
